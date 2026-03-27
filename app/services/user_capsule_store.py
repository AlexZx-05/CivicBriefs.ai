from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.services.mongo import get_collection


class UserCapsuleStore:
    """Track user-level capsule read activity and derive streak metrics."""

    def __init__(self) -> None:
        self.collection: Optional[Collection] = None
        self.reads_mem: Dict[str, set[str]] = {}
        try:
            col = get_collection("user_capsule_reads")
            col.create_index([("user_id", 1), ("capsule_date", 1)], unique=True)
            col.create_index([("user_email", 1), ("capsule_date", 1)])
            self.collection = col
        except PyMongoError:
            self.collection = None

    @staticmethod
    def _normalize_date(value: str | None) -> str:
        if value:
            try:
                return date.fromisoformat(value[:10]).isoformat()
            except ValueError:
                pass
        return datetime.now(timezone.utc).date().isoformat()

    def mark_read(self, *, user_id: str, user_email: str | None, capsule_date: str | None) -> None:
        normalized_date = self._normalize_date(capsule_date)
        email = (user_email or "").strip().lower() or None
        now = datetime.now(timezone.utc)
        if self.collection is not None:
            self.collection.update_one(
                {"user_id": user_id, "capsule_date": normalized_date},
                {
                    "$setOnInsert": {
                        "user_id": user_id,
                        "user_email": email,
                        "capsule_date": normalized_date,
                        "read_at": now,
                        "created_at": now,
                    },
                    "$set": {"updated_at": now},
                },
                upsert=True,
            )
            return

        bucket = self.reads_mem.setdefault(user_id, set())
        bucket.add(normalized_date)

    def stats_for_user(self, *, user_id: str) -> Dict[str, object]:
        dates = self._read_dates(user_id=user_id)
        current_streak, longest_streak = self._streaks(dates)
        return {
            "total_read": len(dates),
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "last_read_on": dates[-1].isoformat() if dates else None,
        }

    def _read_dates(self, *, user_id: str) -> List[date]:
        if self.collection is not None:
            rows = self.collection.find(
                {"user_id": user_id},
                projection={"capsule_date": 1},
            )
            out: List[date] = []
            for row in rows:
                raw = row.get("capsule_date")
                if not isinstance(raw, str):
                    continue
                try:
                    out.append(date.fromisoformat(raw[:10]))
                except ValueError:
                    continue
            out = sorted(set(out))
            return out

        raw_dates = self.reads_mem.get(user_id, set())
        out = []
        for raw in raw_dates:
            try:
                out.append(date.fromisoformat(raw[:10]))
            except ValueError:
                continue
        return sorted(set(out))

    @staticmethod
    def _streaks(dates: List[date]) -> tuple[int, int]:
        if not dates:
            return 0, 0
        longest = 1
        run = 1
        for idx in range(1, len(dates)):
            if dates[idx] == dates[idx - 1] + timedelta(days=1):
                run += 1
                if run > longest:
                    longest = run
            else:
                run = 1

        today = datetime.now(timezone.utc).date()
        current = 0
        cursor = today
        date_set = set(dates)
        while cursor in date_set:
            current += 1
            cursor -= timedelta(days=1)
        return current, longest


user_capsule_store = UserCapsuleStore()
