# app/agents/news_collection.py
import os
import logging
import uuid
import re
import warnings
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from zipfile import BadZipFile

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# embeddings
from sentence_transformers import SentenceTransformer

# text
import nltk


def ensure_nltk_resource(resource_key: str, download_name: Optional[str] = None) -> None:
    """Ensure required NLTK resource exists, re-downloading if corrupt."""
    logger = logging.getLogger("news_collection")
    try:
        nltk.data.find(resource_key)
        return
    except LookupError:
        logger.info("NLTK resource %s missing. Downloading...", resource_key)
    except Exception as exc:
        if isinstance(exc, BadZipFile):
            logger.warning("NLTK resource %s appears corrupted. Re-downloading...", resource_key)
        else:
            logger.warning("Error loading NLTK resource %s (%s). Re-downloading...", resource_key, exc)

    nltk.download(download_name or resource_key.split("/")[-1], quiet=True, force=True)


ensure_nltk_resource("tokenizers/punkt", "punkt")
ensure_nltk_resource("tokenizers/punkt_tab", "punkt_tab")

from nltk.tokenize import sent_tokenize

load_dotenv()

logger = logging.getLogger("news_collection")
logger.setLevel(getattr(logging, os.getenv("NEWS_COLLECTION_LOG_LEVEL", "WARNING").upper(), logging.WARNING))
logger.propagate = True

# Keep transformer/library warnings out of terminal noise for production runs.
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    module=r"transformers\..*",
)

# Config (env)
NEWS_API_KEYS = [os.getenv("NEWS_API_KEY1"), os.getenv("NEWS_API_KEY2")]
SENTENCE_TRANSFORMER_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-mpnet-base-v2")
MAX_CHARS_PER_CHUNK = int(os.getenv("MAX_CHARS_PER_CHUNK", 1500))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
STRICT_SOURCE_FILTER = os.getenv("NEWS_STRICT_SOURCE_FILTER", "1").strip().lower() in {"1", "true", "yes", "on"}
MIN_STRICT_FILTERED_ARTICLES = max(1, int(os.getenv("NEWS_MIN_STRICT_ARTICLES", "5")))

_DEFAULT_ALLOWED_SOURCE_NAMES = {
    "reuters",
    "associated press",
    "bbc news",
    "the hindu",
    "indian express",
    "business standard",
    "livemint",
    "the economic times",
    "hindustan times",
    "times of india",
    "the print",
    "the wire",
    "ani news",
    "pib",
}

_DEFAULT_BLOCKED_DOMAINS = {
    "globalresearch.ca",
}

allowed_names_env = {
    p.strip().lower()
    for p in (os.getenv("NEWS_ALLOWED_SOURCE_NAMES", "")).split(",")
    if p.strip()
}
blocked_domains_env = {
    p.strip().lower()
    for p in (os.getenv("NEWS_BLOCKED_DOMAINS", "")).split(",")
    if p.strip()
}

ALLOWED_SOURCE_NAMES = allowed_names_env or _DEFAULT_ALLOWED_SOURCE_NAMES
BLOCKED_DOMAINS = blocked_domains_env or _DEFAULT_BLOCKED_DOMAINS

_DEFAULT_FALLBACK_QUERIES = [
    "India AND current affairs",
    "UPSC current affairs India government policy",
    "Parliament OR Supreme Court OR RBI OR Election Commission India",
]
FALLBACK_QUERIES = [
    q.strip()
    for q in (os.getenv("NEWS_FALLBACK_QUERIES", "")).split("||")
    if q.strip()
] or _DEFAULT_FALLBACK_QUERIES

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# -----------------------
# Helper: choose API key
# -----------------------
def _choose_key() -> Optional[str]:
    for k in NEWS_API_KEYS:
        if k and k.strip():
            return k.strip()
    return None


def _domain_from_url(url: str) -> str:
    try:
        host = (urlparse(url).netloc or "").strip().lower()
        if host.startswith("www."):
            return host[4:]
        return host
    except Exception:
        return ""


def _is_allowed_article_source(article: Dict[str, Any]) -> bool:
    if not STRICT_SOURCE_FILTER:
        return True

    source_name = str(((article.get("source") or {}).get("name") or "")).strip().lower()
    url = str(article.get("url") or "").strip()
    domain = _domain_from_url(url)

    if domain:
        for blocked in BLOCKED_DOMAINS:
            if domain == blocked or domain.endswith(f".{blocked}"):
                return False

    if source_name and source_name in ALLOWED_SOURCE_NAMES:
        return True

    # Domain fallback for known mainstream publications
    mainstream_domain_markers = (
        "reuters.com",
        "apnews.com",
        "bbc.com",
        "thehindu.com",
        "indianexpress.com",
        "business-standard.com",
        "livemint.com",
        "economictimes.indiatimes.com",
        "timesofindia.indiatimes.com",
        "hindustantimes.com",
        "theprint.in",
        "thewire.in",
        "pib.gov.in",
    )
    return any(marker in domain for marker in mainstream_domain_markers)


def _is_not_blocked_domain(url: str) -> bool:
    domain = _domain_from_url(url)
    if not domain:
        return True
    for blocked in BLOCKED_DOMAINS:
        if domain == blocked or domain.endswith(f".{blocked}"):
            return False
    return True


def _merge_unique_articles(existing: List[Dict[str, Any]], incoming: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    if limit <= 0:
        return []
    merged = list(existing)
    seen_urls = {str((a or {}).get("url") or "").strip() for a in merged if (a or {}).get("url")}
    for item in incoming:
        if len(merged) >= limit:
            break
        url = str((item or {}).get("url") or "").strip()
        if not url or url in seen_urls:
            continue
        merged.append(item)
        seen_urls.add(url)
    return merged

# -----------------------
# News API fetcher
# (assumes newsapi.org like endpoint)
# -----------------------
class NewsFetcher:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or _choose_key()
        self.base = "https://newsapi.org/v2/everything"
        if not self.api_key:
            logger.warning("No News API key found in .env (NEWS_API_KEY1/2). API fetch will be skipped.")
        else:
            logger.info("News API key loaded successfully")

    def fetch_today(self, q: str = "UPSC OR civil services OR current affairs", language: str = "en", page_size: int = 30) -> List[Dict[str, Any]]:
        if not self.api_key:
            logger.error("Cannot fetch: No API key available")
            return []
        
        # Use yesterday to today to get more results
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        params = {
            "q": q,
            "from": yesterday.isoformat(),
            "to": today.isoformat(),
            "sortBy": "publishedAt",
            "language": language,
            "pageSize": page_size,
            "apiKey": self.api_key,
        }
        
        logger.info(f"Fetching news with query: '{q}' from {yesterday} to {today}")
        
        try:
            r = requests.get(self.base, params=params, headers={"Accept": "application/json"}, timeout=15)
            
            # Log response status
            logger.info(f"News API response status: {r.status_code}")
            
            r.raise_for_status()
            data = r.json()
            
            # Log API response details
            status = data.get("status")
            total_results = data.get("totalResults", 0)
            articles = data.get("articles", [])
            
            logger.info(f"API Status: {status}, Total Results: {total_results}, Articles returned: {len(articles)}")
            
            if status != "ok":
                logger.error(f"API returned non-ok status: {data}")
                return []
            
            if total_results == 0:
                logger.warning(f"No articles found for query: '{q}'. Try a simpler query or different date range.")
            
            return articles
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            return []
        except Exception as e:
            logger.exception("News API fetch error: %s", e)
            return []

# -----------------------
# Scraping utilities
# -----------------------
def fetch_page(url: str, timeout: int = 15) -> Optional[str]:
    try:
        logger.debug(f"Fetching page: {url}")
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        logger.debug(f"Successfully fetched {url} ({len(r.text)} bytes)")
        return r.text
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout fetching {url}")
        return None
    except requests.exceptions.HTTPError as e:
        status_code = getattr(e.response, "status_code", "unknown")
        if status_code == 403:
            logger.info(f"Access blocked (403) for {url}; using API snippet fallback.")
        else:
            logger.warning(f"HTTP error {status_code} for {url}")
        return None
    except Exception as e:
        logger.debug(f"fetch_page failed for {url}: {e}")
        return None

def extract_article_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
        script.decompose()
    
    # Try multiple strategies to find article content
    text = ""
    
    # Strategy 1: Look for <article> tag
    article = soup.find("article")
    if article:
        ps = article.find_all("p")
        if ps and len(ps) >= 2:
            text = "\n\n".join(p.get_text(strip=True) for p in ps if len(p.get_text(strip=True)) > 50)
            if text:
                logger.debug("Extracted text using <article> tag")
                return text

    # Strategy 2: Try common content selectors
    selectors = [
        "div.article-content", "div.article-body", "div.story-body",
        "div.article", "div#content", "div.storyContent", 
        "div.tracking-content", "div.entry-content", "div.post-content",
        "div.td-post-content", "div.content-body", "main article"
    ]
    
    for sel in selectors:
        node = soup.select_one(sel)
        if node:
            ps = node.find_all("p")
            if ps and len(ps) >= 2:
                text = "\n\n".join(p.get_text(strip=True) for p in ps if len(p.get_text(strip=True)) > 50)
                if text:
                    logger.debug(f"Extracted text using selector: {sel}")
                    return text

    # Strategy 3: Find all paragraphs and filter by length
    body = soup.body
    if body:
        ps = body.find_all("p")
        # Filter paragraphs that are likely content (not navigation, etc.)
        content_ps = [p.get_text(strip=True) for p in ps if len(p.get_text(strip=True)) > 50]
        if len(content_ps) >= 2:
            text = "\n\n".join(content_ps)
            logger.debug(f"Extracted text using filtered paragraphs ({len(content_ps)} paragraphs)")
            return text

    logger.debug("Could not extract meaningful article text")
    return ""

def scrape_article(url: str) -> str:
    logger.info(f"Scraping article: {url}")
    html = fetch_page(url)
    if not html:
        logger.debug(f"No HTML returned for {url}")
        return ""
    
    text = extract_article_text(html).strip()
    
    if text:
        logger.info(f"Successfully scraped {len(text)} characters from {url}")
    else:
        logger.debug(f"No text extracted from {url}")
    
    return text

# -----------------------
# Cleaning + chunking
# -----------------------
def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def chunk_text_by_sentences(text: str, max_chars: int = MAX_CHARS_PER_CHUNK, overlap: int = CHUNK_OVERLAP) -> List[str]:
    text = clean_text(text)
    if not text:
        return []
    
    # Minimum text length to chunk
    if len(text) < 100:
        logger.debug(f"Text too short to chunk ({len(text)} chars)")
        return []
    
    try:
        sents = sent_tokenize(text)
    except Exception as e:
        logger.warning(f"Error tokenizing text: {e}. Using simple splitting.")
        # Fallback to simple sentence splitting
        sents = re.split(r'[.!?]+\s+', text)
    
    chunks: List[str] = []
    cur = ""
    
    for sent in sents:
        if len(cur) + len(sent) + 1 <= max_chars:
            cur = (cur + " " + sent).strip()
        else:
            if cur:
                chunks.append(cur)
            cur = sent
    if cur:
        chunks.append(cur)

    # apply simple overlap (prefix of previous chunk)
    if overlap and overlap > 0 and len(chunks) > 1:
        overlapped = []
        for i, c in enumerate(chunks):
            if i == 0:
                overlapped.append(c)
            else:
                prev = overlapped[-1]
                prefix = prev[max(0, len(prev) - overlap):]
                overlapped.append((prefix + " " + c).strip())
        chunks = overlapped
    
    logger.debug(f"Created {len(chunks)} chunks from {len(text)} chars")
    return chunks

# -----------------------
# Embedder
# -----------------------
class Embedder:
    def __init__(self, model_name: str = SENTENCE_TRANSFORMER_MODEL):
        logger.info("Loading SentenceTransformer model: %s", model_name)
        self.model = SentenceTransformer(model_name)

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embs = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return [e.tolist() for e in embs]

# -----------------------
# Main function: produce embeddings list
# -----------------------
def collect_news_embeddings(
    from_api: bool = True,
    query: str = "UPSC OR civil services OR current affairs",
    fetch_limit: int = 25,
    extra_urls: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch news (API + optional extra_urls), scrape/clean/chunk, embed.
    Returns a list of dicts:
      { "id": str, "text": str, "metadata": {...}, "embedding": [...] }
    """
    logger.info("=== Starting news collection ===")
    
    fetcher = NewsFetcher()
    embedder = Embedder()
    docs_with_embeddings: List[Dict[str, Any]] = []

    # 1) From API
    articles = []
    if from_api:
        primary = fetcher.fetch_today(q=query, page_size=fetch_limit)
        articles = _merge_unique_articles([], primary, fetch_limit)

        # If primary query under-fills, backfill with broader but still UPSC-focused queries.
        if len(articles) < fetch_limit:
            for fallback_query in FALLBACK_QUERIES:
                if len(articles) >= fetch_limit:
                    break
                if fallback_query.strip().lower() == query.strip().lower():
                    continue
                remaining = max(1, fetch_limit - len(articles))
                fallback_articles = fetcher.fetch_today(q=fallback_query, page_size=remaining)
                articles = _merge_unique_articles(articles, fallback_articles, fetch_limit)

        if STRICT_SOURCE_FILTER and articles:
            before = len(articles)
            strict_articles = [a for a in articles if _is_allowed_article_source(a)]
            logger.info("Source filter kept %d/%d articles from trusted outlets.", len(strict_articles), before)

            # Safety fallback: if strict filter yields too few items, keep only non-blocked domains
            # so capsule still has useful content instead of becoming empty.
            if len(strict_articles) < MIN_STRICT_FILTERED_ARTICLES:
                relaxed_articles = [a for a in articles if _is_not_blocked_domain(str((a or {}).get("url") or ""))]
                if relaxed_articles:
                    logger.info(
                        "Strict filter underfilled (%d<%d). Relaxed to domain-only safety filter: %d articles.",
                        len(strict_articles),
                        MIN_STRICT_FILTERED_ARTICLES,
                        len(relaxed_articles),
                    )
                    strict_articles = relaxed_articles
            articles = strict_articles
        logger.info(f"Got {len(articles)} articles from News API")

    # process articles from API
    successful_scrapes = 0
    failed_scrapes = 0
    
    for idx, art in enumerate(articles):
        url = art.get("url")
        title = art.get("title", "")
        desc = art.get("description", "")
        src = (art.get("source") or {}).get("name", "newsapi")
        
        if not url:
            logger.debug(f"Article {idx+1} has no URL, skipping")
            continue
        
        logger.info(f"Processing article {idx+1}/{len(articles)}: {title[:60]}...")
        
        # Try to scrape article
        text = scrape_article(url)
        
        # Fallback to API snippets if scraping fails
        if not text or len(text) < 100:
            logger.info(f"Using API text snippet fallback for {url}")
            text = " ".join(
                part for part in [
                    art.get("content", ""),
                    desc,
                    title,
                ] if part
            )
        
        text = clean_text(text)
        
        if len(text) < 100:
            logger.warning(f"Text too short after cleaning ({len(text)} chars), skipping")
            failed_scrapes += 1
            continue
        
        chunks = chunk_text_by_sentences(text)
        
        if not chunks:
            logger.warning(f"No chunks created for {url}")
            failed_scrapes += 1
            continue
        
        successful_scrapes += 1
        embs = embedder.embed(chunks)
        
        for i, chunk in enumerate(chunks):
            docs_with_embeddings.append({
                "id": str(uuid.uuid4()),
                "text": chunk,
                "metadata": {"source": src, "url": url, "title": title, "chunk_index": i},
                "embedding": embs[i]
            })

    logger.info(f"API articles: {successful_scrapes} successful, {failed_scrapes} failed")

    # 2) extra manual URLs (if provided)
    if extra_urls:
        logger.info(f"Processing {len(extra_urls)} extra URLs")
        for url in extra_urls:
            text = scrape_article(url)
            text = text or ""
            text = clean_text(text)
            
            if len(text) < 100:
                logger.warning(f"Skipping {url} - insufficient text")
                continue
            
            chunks = chunk_text_by_sentences(text)
            if not chunks:
                continue
            
            embs = embedder.embed(chunks)
            for i, chunk in enumerate(chunks):
                docs_with_embeddings.append({
                    "id": str(uuid.uuid4()),
                    "text": chunk,
                    "metadata": {"source": "manual", "url": url, "title": url.split("/")[-1], "chunk_index": i},
                    "embedding": embs[i]
                })

    logger.info(f"=== Collected {len(docs_with_embeddings)} embedded chunks ===")
    return docs_with_embeddings

# If run directly, quick smoke test
if __name__ == "__main__":
    # Test with a simpler query
    res = collect_news_embeddings(
        from_api=True,
        query="India",  # Simpler query for testing
        fetch_limit=1,
        extra_urls=[]
    )
    print(f"\nGot {len(res)} embeddings")
    for r in res[:2]:
        print(f"\nID: {r['id']}")
        print(f"Title: {r['metadata']['title']}")
        print(f"Source: {r['metadata']['source']}")
        print(f"Text preview: {r['text'][:200]}...")
