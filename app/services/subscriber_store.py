from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Protocol

from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.services.mongo import get_collection


class SubscriberStoreProtocol(Protocol):
    def add_subscriber(self, *, name: str, email: str) -> Dict[str, str]:
        ...

    def ensure_subscriber(self, *, name: str, email: str) -> Dict[str, str]:
        ...

    def list_emails(self) -> List[str]:
        ...

    def list_active_subscribers(self) -> List[Dict[str, str]]:
        ...

    def get_status(self, *, email: str) -> Dict[str, bool]:
        ...

    def set_paused(self, *, email: str, paused: bool) -> Dict[str, bool]:
        ...

    def claim_delivery(self, *, email: str, for_date: str) -> bool:
        ...

    def release_delivery_claim(self, *, email: str, for_date: str) -> None:
        ...


class SubscriberStore:
    """
    Mongo-backed subscription store.
    Falls back to in-memory storage if Mongo is unavailable.
    """

    def __init__(self) -> None:
        self.collection: Optional[Collection] = None
        self.subscribers_mem: Dict[str, dict] = {}
        try:
            self.collection = get_collection("subscribers")
            self.collection.create_index("email", unique=True)
            self.collection.create_index("is_subscribed")
            self.collection.create_index("paused")
            self.collection.create_index("last_sent_on")
        except PyMongoError:
            self.collection = None

    @property
    def _mongo_ready(self) -> bool:
        return self.collection is not None

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.lower().strip()

    def add_subscriber(self, *, name: str, email: str) -> Dict[str, str]:
        email_norm = self._normalize_email(email)
        now = datetime.now(timezone.utc)
        doc = {
            "name": name.strip(),
            "email": email_norm,
            "is_subscribed": True,
            "paused": False,
            "created_at": now,
            "updated_at": now,
            "last_sent_on": None,
        }

        if self._mongo_ready:
            assert self.collection is not None
            existing = self.collection.find_one({"email": email_norm}, projection={"_id": 1})
            if existing:
                raise ValueError("This email is already subscribed.")
            try:
                self.collection.insert_one(doc)
                return {"name": doc["name"], "email": doc["email"]}
            except PyMongoError as exc:
                raise ValueError("Unable to subscribe right now.") from exc

        if email_norm in self.subscribers_mem:
            raise ValueError("This email is already subscribed.")
        self.subscribers_mem[email_norm] = doc
        return {"name": doc["name"], "email": doc["email"]}

    def ensure_subscriber(self, *, name: str, email: str) -> Dict[str, str]:
        email_norm = self._normalize_email(email)
        now = datetime.now(timezone.utc)
        payload = {
            "name": name.strip(),
            "email": email_norm,
            "is_subscribed": True,
            "updated_at": now,
        }

        if self._mongo_ready:
            assert self.collection is not None
            self.collection.update_one(
                {"email": email_norm},
                {
                    "$set": payload,
                    "$setOnInsert": {
                        "created_at": now,
                        "paused": False,
                        "last_sent_on": None,
                    },
                },
                upsert=True,
            )
            return {"name": payload["name"], "email": payload["email"]}

        existing = self.subscribers_mem.get(email_norm)
        if not existing:
            self.subscribers_mem[email_norm] = {
                "name": payload["name"],
                "email": email_norm,
                "is_subscribed": True,
                "paused": False,
                "created_at": now,
                "updated_at": now,
                "last_sent_on": None,
            }
        else:
            existing["name"] = payload["name"]
            existing["is_subscribed"] = True
            existing["updated_at"] = now
        return {"name": payload["name"], "email": email_norm}

    def list_emails(self) -> List[str]:
        if self._mongo_ready:
            assert self.collection is not None
            docs = self.collection.find(
                {"is_subscribed": True, "paused": {"$ne": True}},
                projection={"email": 1},
            )
            return [str(doc.get("email", "")).strip() for doc in docs if doc.get("email")]
        return [
            email
            for email, doc in self.subscribers_mem.items()
            if doc.get("is_subscribed") and not doc.get("paused")
        ]

    def list_active_subscribers(self) -> List[Dict[str, str]]:
        if self._mongo_ready:
            assert self.collection is not None
            docs = self.collection.find(
                {"is_subscribed": True, "paused": {"$ne": True}},
                projection={"name": 1, "email": 1},
            )
            return [
                {"name": str(doc.get("name", "")).strip(), "email": str(doc.get("email", "")).strip()}
                for doc in docs
                if doc.get("email")
            ]

        return [
            {"name": str(doc.get("name", "")).strip(), "email": email}
            for email, doc in self.subscribers_mem.items()
            if doc.get("is_subscribed") and not doc.get("paused")
        ]

    def get_status(self, *, email: str) -> Dict[str, bool]:
        email_norm = self._normalize_email(email)
        if self._mongo_ready:
            assert self.collection is not None
            doc = self.collection.find_one(
                {"email": email_norm},
                projection={"is_subscribed": 1, "paused": 1},
            )
            if not doc:
                return {"subscribed": False, "paused": False}
            subscribed = bool(doc.get("is_subscribed"))
            paused = bool(doc.get("paused")) if subscribed else False
            return {"subscribed": subscribed, "paused": paused}

        doc = self.subscribers_mem.get(email_norm)
        if not doc:
            return {"subscribed": False, "paused": False}
        subscribed = bool(doc.get("is_subscribed"))
        paused = bool(doc.get("paused")) if subscribed else False
        return {"subscribed": subscribed, "paused": paused}

    def set_paused(self, *, email: str, paused: bool) -> Dict[str, bool]:
        email_norm = self._normalize_email(email)
        now = datetime.now(timezone.utc)

        if self._mongo_ready:
            assert self.collection is not None
            doc = self.collection.find_one({"email": email_norm}, projection={"is_subscribed": 1})
            if not doc or not doc.get("is_subscribed"):
                raise ValueError("Subscription not found.")
            self.collection.update_one(
                {"email": email_norm},
                {"$set": {"paused": bool(paused), "updated_at": now}},
            )
            return {"subscribed": True, "paused": bool(paused)}

        doc = self.subscribers_mem.get(email_norm)
        if not doc or not doc.get("is_subscribed"):
            raise ValueError("Subscription not found.")
        doc["paused"] = bool(paused)
        doc["updated_at"] = now
        return {"subscribed": True, "paused": bool(paused)}

    def claim_delivery(self, *, email: str, for_date: str) -> bool:
        email_norm = self._normalize_email(email)
        now = datetime.now(timezone.utc)

        if self._mongo_ready:
            assert self.collection is not None
            result = self.collection.update_one(
                {
                    "email": email_norm,
                    "is_subscribed": True,
                    "paused": {"$ne": True},
                    "$or": [{"last_sent_on": {"$ne": for_date}}, {"last_sent_on": {"$exists": False}}],
                },
                {"$set": {"last_sent_on": for_date, "updated_at": now}},
            )
            return result.modified_count == 1

        doc = self.subscribers_mem.get(email_norm)
        if not doc:
            return False
        if not doc.get("is_subscribed") or doc.get("paused"):
            return False
        if doc.get("last_sent_on") == for_date:
            return False
        doc["last_sent_on"] = for_date
        doc["updated_at"] = now
        return True

    def release_delivery_claim(self, *, email: str, for_date: str) -> None:
        email_norm = self._normalize_email(email)

        if self._mongo_ready:
            assert self.collection is not None
            self.collection.update_one(
                {"email": email_norm, "last_sent_on": for_date},
                {"$set": {"last_sent_on": None, "updated_at": datetime.now(timezone.utc)}},
            )
            return

        doc = self.subscribers_mem.get(email_norm)
        if doc and doc.get("last_sent_on") == for_date:
            doc["last_sent_on"] = None
            doc["updated_at"] = datetime.now(timezone.utc)


subscriber_store: SubscriberStoreProtocol = SubscriberStore()
