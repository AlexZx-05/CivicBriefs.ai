from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import bcrypt
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.services.mongo import get_collection


class UserStore:
    """
    Mongo-backed user/session store.
    Falls back to in-memory dictionaries when Mongo is unavailable.
    """

    def __init__(self) -> None:
        self.users_mem: Dict[str, dict] = {}
        self.sessions_mem: Dict[str, str] = {}
        self.users_col: Optional[Collection] = None
        self.sessions_col: Optional[Collection] = None

        try:
            self.users_col = get_collection("users")
            self.sessions_col = get_collection("sessions")
            self.users_col.create_index("id", unique=True)
            self.users_col.create_index("email", unique=True)
            self.sessions_col.create_index("token", unique=True)
            self.sessions_col.create_index("user_id")
            self.sessions_col.create_index("expires_at", expireAfterSeconds=0)
        except PyMongoError:
            self.users_col = None
            self.sessions_col = None

    @property
    def _mongo_ready(self) -> bool:
        return self.users_col is not None and self.sessions_col is not None

    # ---------- CREATE USER ----------
    def create_user(self, *, name: str, email: str, password: str, phone_number: str | None):
        email_norm = email.lower().strip()
        payload = {
            "id": str(uuid.uuid4()),
            "name": name.strip(),
            "email": email_norm,
            "password_hash": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
            "phone_number": (phone_number or "").strip() or None,
            "created_at": datetime.now(timezone.utc),
        }

        if self._mongo_ready:
            assert self.users_col is not None
            existing = self.users_col.find_one({"email": email_norm}, projection={"_id": 1})
            if existing:
                raise ValueError("User already exists")
            try:
                self.users_col.insert_one(payload)
                return self._public_user_from_doc(payload)
            except PyMongoError as exc:
                raise ValueError("Unable to create user at this time") from exc

        for u in self.users_mem.values():
            if u["email"] == email_norm:
                raise ValueError("User already exists")
        self.users_mem[payload["id"]] = payload
        return self._public_user_from_doc(payload)

    # ---------- LOGIN ----------
    def verify_credentials(self, *, email: str, password: str):
        email_norm = email.lower().strip()
        if self._mongo_ready:
            assert self.users_col is not None
            user = self.users_col.find_one({"email": email_norm})
            if not user:
                raise ValueError("User not found")
            if not bcrypt.checkpw(password.encode(), str(user.get("password_hash", "")).encode()):
                raise ValueError("Invalid password")
            return self._public_user_from_doc(user)

        for user in self.users_mem.values():
            if user["email"] == email_norm:
                if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
                    return self._public_user_from_doc(user)
                raise ValueError("Invalid password")
        raise ValueError("User not found")

    # ---------- SESSION ----------
    def create_session(self, *, user_id: str):
        token = str(uuid.uuid4())
        if self._mongo_ready:
            assert self.sessions_col is not None
            now = datetime.now(timezone.utc)
            session_doc = {
                "token": token,
                "user_id": user_id,
                "created_at": now,
                "expires_at": now + timedelta(days=7),
            }
            try:
                self.sessions_col.insert_one(session_doc)
                return token
            except PyMongoError:
                # Fallback path if Mongo write fails transiently.
                self.sessions_mem[token] = user_id
                return token

        self.sessions_mem[token] = user_id
        return token

    def resolve_token(self, token: str):
        if not token:
            return None
        if self._mongo_ready:
            assert self.sessions_col is not None
            assert self.users_col is not None
            session_doc = self.sessions_col.find_one({"token": token})
            if not session_doc:
                return None
            user = self.users_col.find_one({"id": session_doc.get("user_id")})
            if not user:
                return None
            return self._public_user_from_doc(user)

        user_id = self.sessions_mem.get(token)
        if not user_id:
            return None
        user = self.users_mem.get(user_id)
        return self._public_user_from_doc(user) if user else None

    def drop_session(self, token: str):
        if self._mongo_ready:
            assert self.sessions_col is not None
            self.sessions_col.delete_one({"token": token})
        self.sessions_mem.pop(token, None)

    @staticmethod
    def _public_user_from_doc(doc: Optional[dict]) -> Optional[dict]:
        if not doc:
            return None
        return {
            "id": doc.get("id"),
            "name": doc.get("name"),
            "email": doc.get("email"),
            "phone_number": doc.get("phone_number"),
            "created_at": doc.get("created_at"),
        }


user_store = UserStore()
