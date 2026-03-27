#!/usr/bin/env python3
"""
generate_news_capsule.py

Main UPSC News Capsule Pipeline:
- Fetch UPSC-relevant articles
- Group chunks into articles
- Classify into UPSC categories
- Retrieve PYQ & Syllabus context from ChromaDB
- Summarize each article using the local Llama server
- Build Markdown + JSON + PDF
"""

import os
import json
import uuid
import logging
import re
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

import numpy as np
import nltk
from nltk.tokenize import sent_tokenize

from sentence_transformers import SentenceTransformer
import chromadb

# -----------------------
# Local Imports (Clean)
# -----------------------
from app.agents.news.news_collection import collect_news_embeddings
from app.utils.llm_utils import local_llama_call
from app.utils.markdown_utils import format_snippets_for_prompt
from app.utils.pdf_utils import build_pdf_from_markdown
from app.services.news_store import news_store

# -----------------------
# Setup NLTK
# -----------------------
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download("punkt", quiet=True)

# -----------------------
# Logging
# -----------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("news_capsule")

# -----------------------
# Config
# -----------------------
CHROMA_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", "app/agents/chroma_store"))
SENTENCE_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-mpnet-base-v2")

LOCAL_LLM_ENDPOINT = os.getenv("LOCAL_LLM_ENDPOINT",
                               "http://localhost:8000/v1/chat/completions")

TOP_K_CHROMA = int(os.getenv("TOP_K_CHROMA", 3))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 512))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.1))
PIPELINE_SEND_EMAIL = os.getenv("NEWS_PIPELINE_SEND_EMAIL", "0").strip().lower() in {"1", "true", "yes", "on"}

TODAY = datetime.utcnow().date().isoformat()
PDF_FILENAME = f"news_capsule_{TODAY}.pdf"
MD_FILENAME = "news_capsules.md"
JSON_FILENAME = "news_capsules.json"

# -----------------------
# UPSC Categories
# -----------------------
CATEGORIES = [
    "Polity & Governance",
    "Economy",
    "International Relations",
    "Environment & Ecology",
    "Science & Technology",
    "Social Issues",
    "Security",
    "History & Culture",
    "Geography",
    "Ethics & Society"
]

INDIA_CONTEXT_KEYWORDS = {
    "india", "indian", "union government", "ministry of", "lok sabha", "rajya sabha",
    "supreme court of india", "high court", "niti aayog", "rbi", "sebi",
    "upsc", "ias", "ips", "gst", "parliament of india", "cag", "epfo",
}

EXAM_USEFUL_KEYWORDS = {
    "policy", "scheme", "bill", "act", "governance", "economy", "inflation",
    "budget", "fiscal", "environment", "ecology", "climate", "biodiversity",
    "science", "technology", "defence", "security", "foreign policy",
    "international relations", "education", "health", "agriculture", "welfare",
    "census", "report", "index", "committee", "regulation",
}

# -----------------------
# Prompt Template
# -----------------------
PROMPT_TEMPLATE = """You are creating an easy-to-read UPSC news capsule for students.

Article: {title}
Source: {source}

Content:
{article_text}

Most relevant PYQ snippets found:
{pyq_snippets}

Most relevant Syllabus topics found:
{syllabus_snippets}

IMPORTANT: Output ONLY in this exact format:

---
### {title} - Summary

**In Simple Words**
- 2-3 short bullets in plain language

**Why It Matters for UPSC**
- 2-3 short bullets (exam relevance only)

**Prelims Pointers**
- 2-3 factual bullets (acts, places, institutions, reports, data)

**Mains Angle**
- 2-3 analytical bullets (GS paper linkage, governance/economy/ethics view)

**Key Terms**
- 2-4 key terms with very short meaning

**Relevant PYQ**
- max 3 bullets

**Relevant Syllabus**
- max 3 bullets
---

RULES:
- Use plain English and short sentences
- Avoid heavy jargon
- Do not invent facts
- If data is missing, write "- Not clearly stated in source"
- Keep each bullet under 24 words
"""

# -----------------------
# Helpers
# -----------------------
def l2_normalize(a: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(a, axis=-1, keepdims=True)
    norm[norm == 0] = 1e-8
    return a / norm


def _format_hit_lines(hits: List[Dict[str, Any]], limit: int = 3) -> str:
    lines = []
    for hit in hits[:limit]:
        snippet = _clean_text_fragment(str(hit.get("document", "")))[:200]
        if snippet:
            lines.append(f"- {snippet}")
    return "\n".join(lines) if lines else "- None"




def _first_n_sentences(text: str, n: int = 3) -> str:
    clean = _clean_text_fragment(text or "")
    if not clean:
        return ""
    sents = sent_tokenize(clean)
    picked = [s.strip() for s in sents if s.strip()][:n]
    return " ".join(picked).strip()


def _truncate_words(text: str, max_words: int = 28) -> str:
    words = (text or "").split()
    if not words:
        return ""
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(".,;:") + "..."


def _clean_text_fragment(text: str) -> str:
    cleaned = (text or "").replace("\n", " ")
    replacements = {
        "â€™": "'",
        "â€˜": "'",
        "â€œ": '"',
        "â€": '"',
        "â€“": "-",
        "â€”": "-",
    }
    for src, dst in replacements.items():
        cleaned = cleaned.replace(src, dst)
    cleaned = re.sub(r"([a-z])([A-Z])", r"\1 \2", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _keyword_present(text: str, keyword: str) -> bool:
    kw = keyword.strip().lower()
    if not kw:
        return False
    if " " in kw:
        # phrase-style match with word boundaries on both ends
        pattern = r"\b" + re.escape(kw) + r"\b"
        return re.search(pattern, text) is not None
    pattern = r"\b" + re.escape(kw) + r"\b"
    return re.search(pattern, text) is not None


def _is_upsc_relevant(title: str, text: str, source: str) -> bool:
    joined = f"{title} {source} {text[:1200]}".lower()
    india_hits = sum(1 for kw in INDIA_CONTEXT_KEYWORDS if _keyword_present(joined, kw))
    exam_hits = sum(1 for kw in EXAM_USEFUL_KEYWORDS if _keyword_present(joined, kw))

    # Strong direct UPSC mention is always relevant.
    if "upsc" in joined:
        return True

    # Prefer India + exam utility together.
    if india_hits >= 1 and exam_hits >= 1:
        return True

    return False


# -----------------------
# Main pipeline
# -----------------------
def run(fetch_limit: int = 30):
    logger.info("Loading embedding model: %s", SENTENCE_MODEL)
    embedder = SentenceTransformer(SENTENCE_MODEL)

    # -----------------------
    # Connect to ChromaDB
    # -----------------------
    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        syllabus_col = client.get_or_create_collection(name="upsc_syllabus")
        pyq_col = client.get_or_create_collection(name="upsc_pyq")
        logger.info("Connected to ChromaDB at %s", CHROMA_DIR)
    except Exception as e:
        logger.warning("Failed to connect to ChromaDB: %s", e)
        syllabus_col, pyq_col = None, None

    # -----------------------
    # Check local LLM availability
    # -----------------------
    llm_available = False
    try:
        resp = requests.get(
            LOCAL_LLM_ENDPOINT.replace("/v1/chat/completions", "/v1/models"),
            timeout=3
        )
        if resp.status_code == 200:
            llm_available = True
            logger.info("Local Llama reachable.")
    except:
        logger.warning("Local Llama server not reachable. Using fallback summarizer.")

    # -----------------------
    # Category embeddings
    # -----------------------
    cat_prompts = [
        f"{c} news relevant to UPSC civil services" for c in CATEGORIES
    ]
    cat_embs = embedder.encode(cat_prompts, convert_to_numpy=True)
    cat_embs = l2_normalize(np.array(cat_embs))

    # -----------------------
    # Step 1 â€” News Collection
    # -----------------------
    logger.info("Fetching news chunks...")
    chunks = collect_news_embeddings(
        from_api=True,
        query="India AND (UPSC OR civil services OR current affairs OR government policy OR Parliament OR RBI)",
        fetch_limit=fetch_limit
    )
    logger.info("Fetched %d chunks", len(chunks))

    # -----------------------
    # Step 2 â€” Group chunks into articles
    # -----------------------
    articles = {}
    for item in chunks:
        url = item["metadata"].get("url") or str(uuid.uuid4())
        title = item["metadata"].get("title", url)
        source = item["metadata"].get("source", "newsapi")

        if url not in articles:
            articles[url] = {
                "title": title,
                "source": source,
                "url": url,
                "chunks": [],
                "embs": []
            }

        articles[url]["chunks"].append(item["text"])
        articles[url]["embs"].append(np.array(item["embedding"], dtype=np.float32))

    for url, art in articles.items():
        art["text"] = "\n\n".join(art["chunks"])
        art["embedding"] = l2_normalize(np.mean(np.vstack(art["embs"]), axis=0))
        art["chunk_count"] = len(art["chunks"])

    before_filter = len(articles)
    articles = {
        url: art
        for url, art in articles.items()
        if _is_upsc_relevant(art["title"], art["text"], art["source"])
    }
    logger.info("Relevance filter kept %d/%d articles for capsule.", len(articles), before_filter)

    logger.info("Grouped into %d articles", len(articles))

    # -----------------------
    # Output structure
    # -----------------------
    output = {cat: [] for cat in CATEGORIES}

    # -----------------------
    # Step 3 â€” Process each article
    # -----------------------
    for url, art in articles.items():
        emb = art["embedding"]

        # Category classification
        sims = (cat_embs @ emb)
        category = CATEGORIES[int(np.argmax(sims))]

        # Chroma searches
        pyq_hits, syl_hits = [], []

        if pyq_col:
            try:
                res = pyq_col.query(
                    query_embeddings=[emb.tolist()],
                    n_results=TOP_K_CHROMA,
                    include=["documents", "metadatas", "distances"]
                )
                ids = res["ids"][0]
                docs = res["documents"][0]
                metas = res["metadatas"][0]
                dists = res["distances"][0]

                for i in range(len(ids)):
                    pyq_hits.append({
                        "id": ids[i],
                        "document": docs[i],
                        "metadata": metas[i],
                        "distance": dists[i],
                    })
            except:
                logger.warning("Chroma PYQ query failed.")

        if syllabus_col:
            try:
                res = syllabus_col.query(
                    query_embeddings=[emb.tolist()],
                    n_results=TOP_K_CHROMA,
                    include=["documents", "metadatas", "distances"]
                )
                ids = res["ids"][0]
                docs = res["documents"][0]
                metas = res["metadatas"][0]
                dists = res["distances"][0]

                for i in range(len(ids)):
                    syl_hits.append({
                        "id": ids[i],
                        "document": docs[i],
                        "metadata": metas[i],
                        "distance": dists[i],
                    })
            except:
                logger.warning("Chroma syllabus query failed.")

        # Prompt formatting
        pyq_snips = format_snippets_for_prompt(pyq_hits)
        syl_snips = format_snippets_for_prompt(syl_hits)

        prompt = PROMPT_TEMPLATE.format(
            title=art["title"],
            source=art["source"],
            article_text=art["text"][:4000],
            pyq_snippets=pyq_snips,
            syllabus_snippets=syl_snips,
        )

        # -----------------------
        # Step 4 â€” Summarize (LLM or fallback)
        # -----------------------
        summary_md = ""

        if llm_available:
            llm_out = local_llama_call(
                prompt=prompt,
                max_tokens=LLM_MAX_TOKENS,
                temperature=LLM_TEMPERATURE
            )
            if llm_out and len(llm_out.strip()) > 10:
                summary_md = llm_out
        # fallback extractive summary
        if not summary_md:
            brief = _truncate_words(_first_n_sentences(art["text"], n=2), max_words=28)
            if not brief:
                brief = "Not clearly stated in source."
            summary_md = (
                "---\n"
                f"### {art['title']} - Summary\n\n"
                "**In Simple Words**\n"
                f"- {brief}\n\n"
                "**Why It Matters for UPSC**\n"
                "- Connect this issue with current affairs and static syllabus.\n"
                "- Use it for answer enrichment in GS papers.\n\n"
                "**Prelims Pointers**\n"
                "- Note important names, institutions, schemes, and locations.\n"
                "- Track any factual update asked in objective questions.\n\n"
                "**Mains Angle**\n"
                "- Link the issue to governance, economy, society, or ethics dimensions.\n"
                "- Add balanced analysis with impact and way forward.\n\n"
                "**Key Terms**\n"
                f"- {art['source']}: Primary reporting source.\n\n"
                "**Relevant PYQ**\n"
                f"{_format_hit_lines(pyq_hits)}\n\n"
                "**Relevant Syllabus**\n"
                f"{_format_hit_lines(syl_hits)}\n"
                "---"
            )
        # Store result
        output[category].append({
            "title": art["title"],
            "url": art["url"],
            "source": art["source"],
            "chunk_count": art["chunk_count"],
            "summary": summary_md,
            "pyq_hits": pyq_hits,
            "syllabus_hits": syl_hits
        })

    # -----------------------
    # Step 5 â€” Build Markdown + JSON
    # -----------------------
    md_lines = [f"# News Capsule - Date: {TODAY}\n"]

    for cat in CATEGORIES:
        md_lines.append(f"## {cat}\n")
        if not output[cat]:
            md_lines.append("_No articles in this category_\n")
            continue
        for it in output[cat]:
            md_lines.append(it["summary"].strip() + "\n")
            md_lines.append(f"- Source: {it['source']}")
            md_lines.append(f"- URL: {it['url']}")
            md_lines.append(f"- Chunks: {it['chunk_count']}\n")
            md_lines.append("---\n")

    md_text = "\n".join(md_lines)
    with open(MD_FILENAME, "w", encoding="utf-8") as f:
        f.write(md_text)
    with open(JSON_FILENAME, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    logger.info("Markdown & JSON saved.")

    persisted = news_store.save_capsule(
        capsule_payload={"structure": output, "markdown": md_text},
        capsule_date=TODAY,
        capsule_type="daily",
    )
    if persisted:
        logger.info("News capsule stored in MongoDB collection 'news'.")
    else:
        logger.warning("News capsule could not be stored in MongoDB. Continuing with local artifacts.")

    # -----------------------
    # Step 6 â€” Build PDF
    # -----------------------
    build_pdf_from_markdown(MD_FILENAME, PDF_FILENAME)
    if PIPELINE_SEND_EMAIL:
        from app.services.news_mailer import send_news_capsule_email
        send_news_capsule_email(PDF_FILENAME)
    else:
        logger.info("Email dispatch disabled in pipeline (NEWS_PIPELINE_SEND_EMAIL=0). Scheduler handles daily sending.")

    logger.info("Pipeline completed. PDF: %s", PDF_FILENAME)


if __name__ == "__main__":
    run(fetch_limit=int(os.getenv("FETCH_LIMIT", "5")))

