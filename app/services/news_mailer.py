from pathlib import Path
from datetime import datetime

from app.services.mailer import send_mail_with_attachment
from app.services.subscriber_store import subscriber_store


def load_subscribers():
    return subscriber_store.list_emails()


def send_news_capsule_email(pdf_path: str, *, for_date: str | None = None):
    """
    Sends the generated PDF news capsule to all subscribers.
    """
    try:
        pdf = Path(pdf_path)

        if not pdf.exists():
            print(f"ERROR: PDF not found: {pdf_path}")
            return False

        subscribers = load_subscribers()
        if not subscribers:
            print("WARN: No subscribers to send email.")
            return False

        date_str = (for_date or datetime.utcnow().date().isoformat()).strip()
        print(f"Sending news capsule PDF to subscribers for {date_str}...")

        for email in subscribers:
            if not subscriber_store.claim_delivery(email=email, for_date=date_str):
                continue
            sent_ok = send_mail_with_attachment(
                to_email=email,
                subject=f"CivicBriefs Daily Capsule - {date_str}",
                body="Please find attached your news capsule for today.",
                attachment_path=str(pdf)
            )
            if not sent_ok:
                subscriber_store.release_delivery_claim(email=email, for_date=date_str)

        print("News capsule PDF emailed to all subscribers.")
        return True

    except Exception as e:
        print(f"ERROR sending news capsule PDF: {e}")
        return False
