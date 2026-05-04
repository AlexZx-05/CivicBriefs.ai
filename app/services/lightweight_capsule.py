from __future__ import annotations

import logging
import os
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List

import requests

from app.services.news_store import news_store

logger = logging.getLogger(__name__)

_CATEGORY_KEYWORDS: Dict[str, tuple[str, ...]] = {
    "Polity & Governance": ("parliament", "supreme court", "governance", "bill", "act", "policy"),
    "Economy": ("economy", "inflation", "rbi", "gdp", "fiscal", "rupee", "bank"),
    "International Relations": ("diplomacy", "bilateral", "un", "summit", "foreign minister", "geopolitics"),
    "Environment & Ecology": ("climate", "environment", "forest", "biodiversity", "wildlife", "pollution"),
    "Science & Technology": ("technology", "ai", "space", "isro", "quantum", "biotech"),
    "Social Issues": ("education", "health", "poverty", "welfare", "gender", "employment"),
    "Security": ("security", "defense", "terror", "military", "border", "cyber"),
    "History & Culture": ("heritage", "culture", "archaeology", "history", "festival", "museum"),
    "Geography": ("geography", "river", "monsoon", "earthquake", "glacier", "cyclone"),
    "Ethics & Society": ("ethics", "social justice", "transparency", "accountability", "rights"),
}


def _choose_news_api_key() -> str:
    for key_name in ("NEWS_API_KEY1", "NEWS_API_KEY2"):
        key = (os.getenv(key_name) or "").strip()
        if key:
            return key
    return ""


def _categorize_article(title: str, text: str) -> str:
    merged = f"{title} {text}".lower()
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(word in merged for word in keywords):
            return category
    return "Polity & Governance"


def _summary_lines(title: str, description: str, content: str) -> List[str]:
    snippet = (description or content or title or "").strip()
    if not snippet:
        return ["None"]
    snippet = snippet.replace("\r", " ").replace("\n", " ").strip()
    if len(snippet) > 240:
        snippet = snippet[:240].rsplit(" ", 1)[0] + "..."
    return [snippet]


def generate_lightweight_daily_capsule(*, capsule_date: str, fetch_limit: int = 15) -> bool:
    api_key = _choose_news_api_key()
    if not api_key:
        logger.warning("lightweight_capsule: NEWS_API_KEY1/2 not configured; skipping generation.")
        return False

    try:
        target_date = date.fromisoformat(str(capsule_date)[:10])
    except ValueError:
        target_date = datetime.utcnow().date()
    from_date = target_date - timedelta(days=1)
    params = {
        "q": os.getenv("CAPSULE_NEWS_QUERY", "UPSC OR current affairs OR India policy"),
        "from": from_date.isoformat(),
        "to": target_date.isoformat(),
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": max(1, int(fetch_limit)),
        "apiKey": api_key,
    }

    try:
        response = requests.get(
            "https://newsapi.org/v2/everything",
            params=params,
            headers={"Accept": "application/json"},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        logger.warning("lightweight_capsule: news fetch failed: %s", exc)
        return False

    articles = payload.get("articles") if isinstance(payload, dict) else None
    if not isinstance(articles, list) or not articles:
        logger.info("lightweight_capsule: no articles returned by news API.")
        return False

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for article in articles:
        if not isinstance(article, dict):
            continue
        title = str(article.get("title") or "").strip()
        source = str(((article.get("source") or {}).get("name")) or "News").strip()
        url = str(article.get("url") or "").strip()
        description = str(article.get("description") or "").strip()
        content = str(article.get("content") or "").strip()
        if not title:
            continue
        category = _categorize_article(title, f"{description} {content}")
        grouped[category].append(
            {
                "title": title,
                "source": source,
                "url": url,
                "chunk_count": 1,
                "summary": (
                    f"### {title} - Summary\n"
                    + "\n".join(_summary_lines(title, description, content))
                    + "\n\n**Relevant PYQ**\n- None\n\n**Relevant Syllabus**\n- None\n"
                ),
            }
        )

    structure = {category: items for category, items in grouped.items() if items}
    if not structure:
        return False

    persisted = news_store.save_capsule(
        capsule_payload={"structure": structure},
        capsule_date=capsule_date,
        capsule_type="daily",
    )
    if persisted:
        logger.info("lightweight_capsule: saved daily capsule for %s.", capsule_date)
    return bool(persisted)
