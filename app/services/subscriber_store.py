from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, List, Protocol


class SubscriberStoreProtocol(Protocol):
    def add_subscriber(self, *, name: str, email: str) -> Dict[str, str]:
        ...

    def list_emails(self) -> List[str]:
        ...


class InMemorySubscriberStore:
    """Simple in-memory subscriber storage (no MongoDB)."""

    def __init__(self) -> None:
        self.subscribers: List[Dict[str, str]] = []

    def add_subscriber(self, *, name: str, email: str) -> Dict[str, str]:
        email = email.lower().strip()

        # Prevent duplicate email
        for user in self.subscribers:
            if user["email"] == email:
                raise ValueError("This email is already subscribed.")

        doc = {
            "name": name.strip(),
            "email": email,
            "created_at": datetime.now(timezone.utc),
        }

        self.subscribers.append(doc)
        return {"name": doc["name"], "email": doc["email"]}

    def list_emails(self) -> List[str]:
        return [u["email"] for u in self.subscribers]


def _build_store() -> SubscriberStoreProtocol:
    return InMemorySubscriberStore()


subscriber_store: SubscriberStoreProtocol = _build_store()
