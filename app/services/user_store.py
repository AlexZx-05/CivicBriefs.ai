from __future__ import annotations
import bcrypt
import uuid
from typing import Dict


class InMemoryUserStore:
    def __init__(self):
        self.users: Dict[str, dict] = {}
        self.sessions: Dict[str, str] = {}

    # ---------- CREATE USER ----------
    def create_user(self, *, name: str, email: str, password: str, phone_number: str | None):
        email = email.lower().strip()

        # check duplicate
        for u in self.users.values():
            if u["email"] == email:
                raise ValueError("User already exists")

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "name": name.strip(),
            "email": email,
            "password_hash": hashed,
            "phone_number": phone_number,
        }

        self.users[user_id] = user
        return user

    # ---------- LOGIN ----------
    def verify_credentials(self, *, email: str, password: str):
        email = email.lower().strip()

        for user in self.users.values():
            if user["email"] == email:
                if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
                    return user
                raise ValueError("Invalid password")

        raise ValueError("User not found")

    # ---------- SESSION ----------
    def create_session(self, *, user_id: str):
        token = str(uuid.uuid4())
        self.sessions[token] = user_id
        return token

    def resolve_token(self, token: str):
        user_id = self.sessions.get(token)
        if not user_id:
            return None
        return self.users.get(user_id)

    def drop_session(self, token: str):
        self.sessions.pop(token, None)


user_store = InMemoryUserStore()
