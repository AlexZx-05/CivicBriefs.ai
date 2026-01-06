from __future__ import annotations
from typing import Dict, Optional, Protocol, List
from datetime import datetime, timezone


class UserStoreProtocol(Protocol):
    def create_user(self, name: str, email: str, password_hash: str) -> Dict:
        ...

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        ...


# ----------------------------
# SIMPLE IN MEMORY STORE
# ----------------------------
class InMemoryUserStore(UserStoreProtocol):
    def __init__(self):
        self.users: List[Dict] = []

    def create_user(self, name: str, email: str, password_hash: str) -> Dict:
        email = email.lower().strip()

        # prevent duplicate email
        for u in self.users:
            if u["email"] == email:
                raise ValueError("User already exists")

        user = {
            "name": name.strip(),
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.now(timezone.utc),
        }

        self.users.append(user)
        return user

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        email = email.lower().strip()
        for u in self.users:
            if u["email"] == email:
                return u
        return None


def _build_user_store() -> UserStoreProtocol:
    return InMemoryUserStore()


user_store: UserStoreProtocol = _build_user_store()
