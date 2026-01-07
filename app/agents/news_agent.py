# app/agents/news_agent.py

"""
Lightweight NewsAgent for Railway.
Embeddings + heavy AI model pipeline disabled temporarily.
This version only simulates success and keeps app stable.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class NewsAgent:
    def __init__(self, query: str, fetch_limit: int = 10, from_api: bool = True, extra_urls=None):
        self.query = query
        self.fetch_limit = fetch_limit
        self.from_api = from_api
        self.extra_urls = extra_urls or []

    def run(self):
        logger.info("NewsAgent run() called but embeddings disabled")

        # Instead of running full pipeline, return lightweight response
        return {
            "status": "disabled",
            "message": "News pipeline temporarily disabled on Railway",
            "query": self.query,
            "fetch_limit": self.fetch_limit,
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    agent = NewsAgent(query="UPSC test")
    print(agent.run())
