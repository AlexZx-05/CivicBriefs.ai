from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.services.capsule_scheduler import capsule_scheduler

router = APIRouter(prefix="/internal", tags=["internal"])


class DispatchRequest(BaseModel):
    date: str | None = Field(
        default=None,
        description="Optional ISO date (YYYY-MM-DD). If omitted, server's capsule timezone date is used.",
    )


def _resolve_dispatch_token() -> str:
    token = os.getenv("CAPSULE_DISPATCH_TOKEN", "").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dispatch token is not configured on server.",
        )
    return token


def _resolve_today() -> str:
    tz_name = os.getenv("CAPSULE_TIMEZONE", "Asia/Kolkata")
    now = datetime.now(ZoneInfo(tz_name))
    return now.date().isoformat()


@router.post("/capsule/dispatch")
def trigger_capsule_dispatch(
    payload: DispatchRequest | None = None,
    x_dispatch_token: str | None = Header(default=None, alias="X-Dispatch-Token"),
):
    expected = _resolve_dispatch_token()
    if not x_dispatch_token or x_dispatch_token.strip() != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid dispatch token.",
        )

    date_str = (payload.date if payload and payload.date else _resolve_today())
    sent_count = capsule_scheduler.dispatch_for_date(date_str)
    return {"status": "success", "date": date_str, "sent": sent_count}
