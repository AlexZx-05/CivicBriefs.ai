# app/agents/news/news_collection.py
import os
import logging
import uuid
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# text
import nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download("punkt", quiet=True)

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download("punkt_tab", quiet=True)

from nltk.tokenize import sent_tokenize

load_dotenv()

# =========================
# LOGGER
# =========================
logger = logging.getLogger("news_collection")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(ch)


# =========================
# CONFIG
# =========================
NEWS_API_KEYS = [os.getenv("NEWS_API_KEY1"), os.getenv("NEWS_API_KEY2")]
MAX_CHARS_PER_CHUNK = int(os.getenv("MAX_CHARS_PER_CHUNK", 1500))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}


# =========================
# KEY PICKER
# =========================
def _choose_key() -> Optional[str]:
    for k in NEWS_API_KEYS:
        if k and k.strip():
            return k.strip()
    return None


# =========================
# NEWS FETCHER
# =========================
class NewsFetcher:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or _choose_key()
        self.base = "https://newsapi.org/v2/everything"

        if not self.api_key:
            logger.warning("No News API key found (.env). News API will not work.")
        else:
            logger.info("News API key loaded successfully")

    def fetch_today(self, q="UPSC OR civil services OR current affairs",
                    language="en", page_size=30) -> List[Dict[str, Any]]:

        if not self.api_key:
            return []

        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)

        params = {
            "q": q,
            "from": yesterday.isoformat(),
            "to": today.isoformat(),
            "sortBy": "publishedAt",
            "language": language,
            "pageSize": page_size,
            "apiKey": self.api_key
        }

        try:
            r = requests.get(self.base, params=params, timeout=15)
            r.raise_for_status()

            data = r.json()
            if data.get("status") != "ok":
                logger.error("News API error: %s", data)
                return []

            return data.get("articles", [])

        except Exception as e:
            logger.error(f"News API fetch failed: {e}")
            return []


# =========================
# SCRAPER
# =========================
def fetch_page(url: str):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception:
        return None


def extract_article_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
        script.decompose()

    article = soup.find("article")
    if article:
        ps = [p.get_text(strip=True) for p in article.find_all("p") if len(p.get_text(strip=True)) > 50]
        if len(ps) > 2:
            return "\n\n".join(ps)

    body = soup.body
    if not body:
        return ""

    ps = [p.get_text(strip=True) for p in body.find_all("p") if len(p.get_text(strip=True)) > 50]
    if len(ps) > 2:
        return "\n\n".join(ps)

    return ""


def scrape_article(url: str) -> str:
    html = fetch_page(url)
    if not html:
        return ""
    return extract_article_text(html)


# =========================
# CLEAN + CHUNK
# =========================
def clean_text(text: str) -> str:
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_text_by_sentences(text: str,
                            max_chars=MAX_CHARS_PER_CHUNK,
                            overlap=CHUNK_OVERLAP):
    text = clean_text(text)
    if not text or len(text) < 100:
        return []

    try:
        sents = sent_tokenize(text)
    except:
        sents = re.split(r'[.!?]+\s+', text)

    chunks = []
    cur = ""

    for sent in sents:
        if len(cur) + len(sent) + 1 <= max_chars:
            cur = (cur + " " + sent).strip()
        else:
            chunks.append(cur)
            cur = sent

    if cur:
        chunks.append(cur)

    if overlap > 0 and len(chunks) > 1:
        overlapped = []
        for i, c in enumerate(chunks):
            if i == 0:
                overlapped.append(c)
            else:
                prev = overlapped[-1]
                prefix = prev[max(0, len(prev) - overlap):]
                overlapped.append((prefix + " " + c).strip())
        chunks = overlapped

    return chunks


# =========================
# RAILWAY SAFE EMBEDDER
# =========================
class Embedder:
    def __init__(self, model_name=None):
        logger.info("SentenceTransformer removed for Railway. Using SAFE dummy embeddings.")

    def embed(self, texts: List[str]):
        return [[0.0] * 384 for _ in texts]


# =========================
# MAIN FUNCTION
# =========================
def collect_news_embeddings(from_api=True,
                            query="UPSC OR civil services OR current affairs",
                            fetch_limit=25,
                            extra_urls=None):

    logger.info("News Collection Started")

    fetcher = NewsFetcher()
    embedder = Embedder()

    docs = []

    articles = fetcher.fetch_today(q=query, page_size=fetch_limit) if from_api else []

    for art in articles:
        url = art.get("url")
        title = art.get("title", "")
        desc = art.get("description", "")

        if not url:
            continue

        text = scrape_article(url)
        if not text or len(text) < 100:
            text = desc or title

        text = clean_text(text)

        if len(text) < 100:
            continue

        chunks = chunk_text_by_sentences(text)
        if not chunks:
            continue

        embeddings = embedder.embed(chunks)

        for i, c in enumerate(chunks):
            docs.append({
                "id": str(uuid.uuid4()),
                "text": c,
                "metadata": {
                    "source": "newsapi",
                    "url": url,
                    "title": title,
                    "chunk_index": i
                },
                "embedding": embeddings[i]
            })

    logger.info(f"Collected {len(docs)} news chunks successfully")
    return docs


if __name__ == "__main__":
    res = collect_news_embeddings(from_api=False)
    print(f"News collected: {len(res)}")
