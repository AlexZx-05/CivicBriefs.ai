from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from app.agents.news.news_collection import collect_news_embeddings as _real_collect_news_embeddings

logger = logging.getLogger("news_collection_proxy")


def collect_news_embeddings(
    from_api: bool = True,
    query: str = "UPSC OR civil services OR current affairs",
    fetch_limit: int = 25,
    extra_urls: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Stable import path used by capsule generators.
    Defaults to real collector; can be disabled with NEWS_COLLECTION_MODE=disabled.
    """
    mode = (os.getenv("NEWS_COLLECTION_MODE", "real") or "real").strip().lower()
    if mode == "disabled":
        logger.warning("NEWS_COLLECTION_MODE=disabled -> returning no chunks.")
        return []

    try:
        return _real_collect_news_embeddings(
            from_api=from_api,
            query=query,
            fetch_limit=fetch_limit,
            extra_urls=extra_urls or [],
        )
    except Exception:
        logger.exception("Real news collection failed; returning no chunks.")
        return []
