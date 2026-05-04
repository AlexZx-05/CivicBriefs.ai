from __future__ import annotations

import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from zoneinfo import ZoneInfo

from app.services.mailer import send_email
from app.services.mailer import send_mail_with_attachment
from app.services.daily_capsule_pdf import build_daily_capsule_pdf
from app.services.lightweight_capsule import generate_lightweight_daily_capsule
from app.services.news_store import news_store
from app.services.news_summary import news_summary_service
from app.services.subscriber_store import subscriber_store
from app.services.user_store import user_store

logger = logging.getLogger(__name__)


class CapsuleScheduler:
    """In-process scheduler for daily 6:00 AM capsule delivery."""

    def __init__(self) -> None:
        self.enabled = os.getenv("CAPSULE_SCHEDULER_ENABLED", "1").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        tz_name = os.getenv("CAPSULE_TIMEZONE", "Asia/Kolkata")
        self.timezone = ZoneInfo(tz_name)
        self.hour = int(os.getenv("CAPSULE_SEND_HOUR", "6"))
        self.minute = int(os.getenv("CAPSULE_SEND_MINUTE", "0"))
        self.poll_seconds = max(15, int(os.getenv("CAPSULE_SCHEDULER_POLL_SECONDS", "30")))
        self.fetch_limit = max(1, int(os.getenv("CAPSULE_FETCH_LIMIT", "15")))
        self.pipeline_mode = (os.getenv("CAPSULE_PIPELINE_MODE", "auto") or "auto").strip().lower()
        self.backfill_days = max(0, int(os.getenv("CAPSULE_BACKFILL_DAYS", "3")))
        self.dispatch_on_startup = os.getenv("CAPSULE_DISPATCH_ON_STARTUP", "1").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._last_dispatch_date: str | None = None

    def start(self) -> None:
        if not self.enabled:
            logger.info("capsule_scheduler: disabled via CAPSULE_SCHEDULER_ENABLED")
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, name="capsule-scheduler", daemon=True)
        self._thread.start()
        # Run startup catch-up in background so FastAPI startup is not blocked
        # by capsule generation/subprocess work.
        threading.Thread(target=self._startup_catchup, name="capsule-startup-catchup", daemon=True).start()
        logger.info(
            "capsule_scheduler: started (daily %02d:%02d %s)",
            self.hour,
            self.minute,
            str(self.timezone),
        )

    def _startup_catchup(self) -> None:
        try:
            self._backfill_recent_days()
            if self.dispatch_on_startup:
                today = datetime.now(self.timezone).date().isoformat()
                # Send once on startup so no manual terminal trigger is needed.
                # Daily dedupe is still enforced per recipient by claim_delivery.
                self._last_dispatch_date = today
                self.dispatch_for_date(today)
            self._tick()
        except Exception:
            logger.exception("capsule_scheduler: startup tick failed")

    def _backfill_recent_days(self) -> None:
        if self.backfill_days <= 0:
            return
        now = datetime.now(self.timezone)
        for offset in range(1, self.backfill_days + 1):
            target_date = (now.date() - timedelta(days=offset)).isoformat()
            if news_store.has_capsule(capsule_date=target_date, capsule_type="daily"):
                continue
            logger.info("capsule_scheduler: backfilling missing daily capsule for %s", target_date)
            generate_lightweight_daily_capsule(capsule_date=target_date, fetch_limit=self.fetch_limit)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        logger.info("capsule_scheduler: stopped")

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._tick()
            except Exception:
                logger.exception("capsule_scheduler: unexpected scheduler error")
            self._stop_event.wait(self.poll_seconds)

    def _tick(self) -> None:
        now = datetime.now(self.timezone)
        today = now.date().isoformat()
        run_time_reached = (now.hour, now.minute) >= (self.hour, self.minute)
        if not run_time_reached:
            return
        if self._last_dispatch_date == today:
            return

        self._last_dispatch_date = today
        self.dispatch_for_date(today)

    def dispatch_to_subscriber(
        self,
        *,
        email: str,
        name: str | None = None,
        date_str: str | None = None,
        ensure_capsule: bool = True,
    ) -> bool:
        target_date = (date_str or datetime.now(self.timezone).date().isoformat()).strip()
        normalized_email = str(email or "").strip().lower()
        if not normalized_email:
            return False

        if ensure_capsule:
            self._generate_capsule_artifacts(target_date)
        self._ensure_daily_pdf(target_date)

        message = self._build_email_message(target_date)
        if message is None:
            message = self._build_fallback_message(target_date)
        subject, body = message
        recipient_name = str(name or "").strip() or "Aspirant"
        # Self-heal subscriber row so claim_delivery cannot fail due to missing record.
        subscriber_store.ensure_subscriber(name=recipient_name, email=normalized_email)

        claimed = subscriber_store.claim_delivery(email=normalized_email, for_date=target_date)
        if not claimed:
            return False

        pdf_path = self._resolve_pdf_path(target_date)
        personalized_body = body.replace("{name}", recipient_name)
        if pdf_path and pdf_path.exists():
            sent_ok = send_mail_with_attachment(
                to_email=normalized_email,
                subject=subject,
                body=personalized_body,
                attachment_path=str(pdf_path),
            )
        else:
            sent_ok = send_email(recipient=normalized_email, subject=subject, body=personalized_body)

        if not sent_ok:
            subscriber_store.release_delivery_claim(email=normalized_email, for_date=target_date)
            return False
        return True

    def dispatch_for_date(self, date_str: str) -> int:
        logger.info("capsule_scheduler: dispatch started for %s", date_str)
        self._generate_capsule_artifacts(date_str)
        self._ensure_daily_pdf(date_str)
        message = self._build_email_message(date_str)
        if message is None:
            # Do not silently skip dispatch; still notify users once/day with dashboard link.
            message = self._build_fallback_message(date_str)
            logger.info("capsule_scheduler: using fallback email body for %s", date_str)
        subject, body = message
        pdf_path = self._resolve_pdf_path(date_str)

        recipients = self._resolve_dispatch_recipients()
        if not recipients:
            logger.info("capsule_scheduler: no recipients resolved")
            return 0

        sent_count = 0
        for subscriber in recipients:
            email = str(subscriber.get("email", "")).strip().lower()
            if not email:
                continue

            recipient_name = str(subscriber.get("name", "")).strip() or "Aspirant"
            # Ensure recipient is claimable even if legacy users have no subscriber row yet.
            subscriber_store.ensure_subscriber(name=recipient_name, email=email)
            claimed = subscriber_store.claim_delivery(email=email, for_date=date_str)
            if not claimed:
                continue

            personalized_body = body.replace("{name}", recipient_name)
            if pdf_path and pdf_path.exists():
                sent_ok = send_mail_with_attachment(
                    to_email=email,
                    subject=subject,
                    body=personalized_body,
                    attachment_path=str(pdf_path),
                )
            else:
                sent_ok = send_email(recipient=email, subject=subject, body=personalized_body)
            if not sent_ok:
                subscriber_store.release_delivery_claim(email=email, for_date=date_str)
                continue
            sent_count += 1

        logger.info("capsule_scheduler: dispatch completed for %s (sent=%d)", date_str, sent_count)
        return sent_count

    def _resolve_dispatch_recipients(self) -> List[dict]:
        """
        Merge active subscribers + registered users so all registered users
        receive daily capsule emails. Deduplication is by normalized email.
        """
        merged: dict[str, dict] = {}
        for row in subscriber_store.list_active_subscribers():
            email = str(row.get("email", "")).strip().lower()
            if not email:
                continue
            merged[email] = {
                "name": str(row.get("name", "")).strip(),
                "email": email,
            }
        for row in user_store.list_registered_users():
            email = str(row.get("email", "")).strip().lower()
            if not email:
                continue
            existing = merged.get(email)
            if existing:
                if not existing.get("name") and row.get("name"):
                    existing["name"] = str(row.get("name", "")).strip()
                continue
            merged[email] = {
                "name": str(row.get("name", "")).strip(),
                "email": email,
            }
        return list(merged.values())

    def _generate_capsule_artifacts(self, date_str: str) -> None:
        """
        Generate latest capsule once a day using the existing pipeline.
        Runs as subprocess so date-based filenames are recomputed correctly each run.
        """
        if self.pipeline_mode == "light":
            generate_lightweight_daily_capsule(capsule_date=date_str, fetch_limit=self.fetch_limit)
            return

        project_root = Path(__file__).resolve().parents[2]
        cmd: List[str] = [sys.executable, "-m", "app.agents.generate_news_capsule"]
        env = os.environ.copy()
        env["FETCH_LIMIT"] = str(self.fetch_limit)
        try:
            result = subprocess.run(cmd, cwd=str(project_root), env=env, check=False, timeout=1800)
            if result.returncode == 0:
                return
            logger.warning("capsule_scheduler: heavy pipeline exited with code %s", result.returncode)
            if self.pipeline_mode == "auto":
                logger.info("capsule_scheduler: using lightweight fallback for %s", date_str)
                generate_lightweight_daily_capsule(capsule_date=date_str, fetch_limit=self.fetch_limit)
        except Exception:
            logger.exception("capsule_scheduler: capsule generation subprocess failed")
            if self.pipeline_mode == "auto":
                generate_lightweight_daily_capsule(capsule_date=date_str, fetch_limit=self.fetch_limit)

    def _build_email_message(self, date_str: str) -> tuple[str, str] | None:
        subject = f"CivicBriefs Daily Capsule - {date_str}"
        intro = "<p>Hi {name},</p><p>Your daily UPSC capsule is ready.</p>"
        try:
            summary = news_summary_service.get_summary("daily")
            totals = summary.get("totals") if isinstance(summary, dict) else {}
            article_count = 0
            if isinstance(totals, dict):
                raw_count = totals.get("articles", 0)
                if isinstance(raw_count, (int, float)):
                    article_count = int(raw_count)
            if article_count <= 0:
                return None

            sections = summary.get("sections") if isinstance(summary, dict) else []
            lines: List[str] = []
            if isinstance(sections, list):
                for section in sections[:4]:
                    if not isinstance(section, dict):
                        continue
                    label = str(section.get("label", "General")).strip()
                    articles = section.get("articles") if isinstance(section.get("articles"), list) else []
                    titles = []
                    for article in articles[:2]:
                        if isinstance(article, dict):
                            title = str(article.get("title", "")).strip()
                            if title:
                                titles.append(title)
                    if not titles:
                        continue
                    joined = "; ".join(titles)
                    lines.append(f"<li><strong>{label}:</strong> {joined}</li>")

            if lines:
                bullets = "<ul>" + "".join(lines) + "</ul>"
            else:
                bullets = "<p>Today's full capsule is available in your dashboard.</p>"
            body = (
                intro
                + bullets
                + "<p>Open your dashboard to read all sections and linked context.</p>"
                + "<p>- CivicBriefs.AI</p>"
            )
            return subject, body
        except Exception:
            logger.exception("capsule_scheduler: failed to build summary email; using fallback content")
            fallback = (
                intro
                + "<p>Your daily capsule has been prepared. Open your dashboard for complete details.</p>"
                + "<p>- CivicBriefs.AI</p>"
            )
            return subject, fallback

    def _build_fallback_message(self, date_str: str) -> tuple[str, str]:
        subject = f"CivicBriefs Daily Capsule - {date_str}"
        body = (
            "<p>Hi {name},</p>"
            "<p>Your daily capsule update is available.</p>"
            "<p>Open your CivicBriefs dashboard to read the latest sections and analysis.</p>"
            "<p>- CivicBriefs.AI</p>"
        )
        return subject, body

    def _resolve_pdf_path(self, date_str: str) -> Path | None:
        project_root = Path(__file__).resolve().parents[2]
        candidate = project_root / f"news_capsule_{date_str}.pdf"
        return candidate if candidate.exists() else None

    def _ensure_daily_pdf(self, date_str: str) -> Path | None:
        existing = self._resolve_pdf_path(date_str)
        if existing is not None:
            return existing
        project_root = Path(__file__).resolve().parents[2]
        output_path = project_root / f"news_capsule_{date_str}.pdf"
        built = build_daily_capsule_pdf(date_str=date_str, output_path=str(output_path))
        return built if built and built.exists() else None


capsule_scheduler = CapsuleScheduler()
