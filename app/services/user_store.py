from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import bcrypt
from bson import ObjectId
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
        self.password_resets_mem: Dict[str, dict] = {}
        self.users_col: Optional[Collection] = None
        self.sessions_col: Optional[Collection] = None
        self.password_resets_col: Optional[Collection] = None

        try:
            self.users_col = get_collection("users")
            self.users_col.create_index("id", unique=True)
            self.users_col.create_index("email", unique=True)
        except PyMongoError:
            self.users_col = None
        try:
            self.sessions_col = get_collection("sessions")
            self.sessions_col.create_index("token", unique=True)
            self.sessions_col.create_index("user_id")
            self.sessions_col.create_index("expires_at", expireAfterSeconds=0)
        except PyMongoError:
            self.sessions_col = None
        try:
            self.password_resets_col = get_collection("password_resets")
            self.password_resets_col.create_index("token", unique=True)
            self.password_resets_col.create_index("user_id")
            self.password_resets_col.create_index("expires_at", expireAfterSeconds=0)
        except PyMongoError:
            self.password_resets_col = None

    @property
    def _mongo_ready(self) -> bool:
        return (
            self.users_col is not None
            and self.sessions_col is not None
            and self.password_resets_col is not None
        )

    @property
    def _users_mongo_ready(self) -> bool:
        return self.users_col is not None

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

    # ---------- PASSWORD RESET ----------
    def create_password_reset_token(self, *, email: str, ttl_minutes: int = 30) -> Optional[str]:
        email_norm = email.lower().strip()
        token = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=max(5, int(ttl_minutes)))

        if self._mongo_ready:
            assert self.users_col is not None
            assert self.password_resets_col is not None
            user = self.users_col.find_one({"email": email_norm}, projection={"id": 1, "_id": 1})
            if not user:
                return None
            # Support both new docs (string id field) and legacy docs (_id only).
            user_id = str(user.get("id") or user.get("_id"))
            self.password_resets_col.delete_many({"user_id": user_id})
            self.password_resets_col.insert_one(
                {
                    "token": token,
                    "user_id": user_id,
                    "created_at": now,
                    "expires_at": expires_at,
                }
            )
            return token

        user = None
        for candidate in self.users_mem.values():
            if candidate["email"] == email_norm:
                user = candidate
                break
        if not user:
            return None
        user_id = str(user["id"])
        stale = [t for t, rec in self.password_resets_mem.items() if rec.get("user_id") == user_id]
        for t in stale:
            self.password_resets_mem.pop(t, None)
        self.password_resets_mem[token] = {"user_id": user_id, "expires_at": expires_at}
        return token

    def reset_password_with_token(self, *, token: str, new_password: str) -> bool:
        token = (token or "").strip()
        if not token:
            return False
        new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        now = datetime.now(timezone.utc)

        def _is_expired(value: object) -> bool:
            if not isinstance(value, datetime):
                return True
            expires_at = value
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            return expires_at < now

        if self._mongo_ready:
            assert self.password_resets_col is not None
            assert self.users_col is not None
            rec = self.password_resets_col.find_one({"token": token})
            if not rec:
                return False
            expires_at = rec.get("expires_at")
            if _is_expired(expires_at):
                self.password_resets_col.delete_one({"token": token})
                return False
            user_id = str(rec.get("user_id", ""))
            if not user_id:
                self.password_resets_col.delete_one({"token": token})
                return False
            update = self.users_col.update_one({"id": user_id}, {"$set": {"password_hash": new_hash}})
            if update.modified_count == 0 and ObjectId.is_valid(user_id):
                update = self.users_col.update_one({"_id": ObjectId(user_id)}, {"$set": {"password_hash": new_hash}})
            self.password_resets_col.delete_one({"token": token})
            if update.modified_count == 1:
                # Revoke active sessions so old sessions cannot continue after password reset.
                self.sessions_col.delete_many({"user_id": user_id})
                return True
            return False

        rec = self.password_resets_mem.get(token)
        if not rec:
            return False
        expires_at = rec.get("expires_at")
        if _is_expired(expires_at):
            self.password_resets_mem.pop(token, None)
            return False
        user_id = rec.get("user_id")
        user = self.users_mem.get(user_id)
        self.password_resets_mem.pop(token, None)
        if not user:
            return False
        user["password_hash"] = new_hash
        stale_sessions = [session_token for session_token, uid in self.sessions_mem.items() if uid == user_id]
        for session_token in stale_sessions:
            self.sessions_mem.pop(session_token, None)
        return True

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

    def list_registered_users(self) -> List[dict]:
        if self._users_mongo_ready:
            assert self.users_col is not None
            docs = self.users_col.find({}, projection={"name": 1, "email": 1})
            out: List[dict] = []
            for doc in docs:
                email = str(doc.get("email", "")).strip().lower()
                if not email:
                    continue
                out.append({"name": str(doc.get("name", "")).strip(), "email": email})
            return out

        out: List[dict] = []
        for user in self.users_mem.values():
            email = str(user.get("email", "")).strip().lower()
            if not email:
                continue
            out.append({"name": str(user.get("name", "")).strip(), "email": email})
        return out

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
