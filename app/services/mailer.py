# app/services/mailer.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
import logging
from contextlib import contextmanager
from dotenv import load_dotenv

# Load .env credentials
load_dotenv()

EMAIL_USER = os.getenv("SMTP_USERNAME")
EMAIL_PASS = os.getenv("SMTP_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "0").strip().lower() in {"1", "true", "yes", "on"}
SMTP_USE_STARTTLS = os.getenv("SMTP_USE_STARTTLS", "1").strip().lower() in {"1", "true", "yes", "on"}
SMTP_TIMEOUT_SECONDS = int(os.getenv("SMTP_TIMEOUT_SECONDS", 30))

logger = logging.getLogger(__name__)


def _validate_smtp_config() -> bool:
    if not EMAIL_USER or not EMAIL_PASS:
        logger.error("mailer: SMTP_USERNAME/SMTP_PASSWORD not configured.")
        return False
    if not SMTP_SERVER:
        logger.error("mailer: SMTP_SERVER not configured.")
        return False
    return True


@contextmanager
def _smtp_connection():
    if SMTP_USE_SSL:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT_SECONDS)
    else:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT_SECONDS)
    try:
        server.ehlo()
        if not SMTP_USE_SSL and SMTP_USE_STARTTLS:
            server.starttls()
            server.ehlo()
        assert EMAIL_USER is not None
        assert EMAIL_PASS is not None
        server.login(EMAIL_USER, EMAIL_PASS)
        yield server
    finally:
        try:
            server.quit()
        except Exception:
            pass


def send_email(recipient: str, subject: str, body: str) -> bool:
    """
    Sends a plain HTML email using SMTP.
    """
    if not _validate_smtp_config():
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = recipient
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "html"))

        with _smtp_connection() as server:
            server.send_message(msg)

        logger.info("mailer: email sent to %s", recipient)
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error("mailer: SMTP auth failed for %s:%s -> %s", SMTP_SERVER, SMTP_PORT, e)
        return False
    except Exception as e:
        logger.exception("mailer: failed to send email to %s: %s", recipient, e)
        return False


def send_mail_with_attachment(to_email: str, subject: str, body: str, attachment_path: str) -> bool:
    """
    Sends an email with a PDF or any file attached.
    """
    if not _validate_smtp_config():
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = subject

        # Email body
        msg.attach(MIMEText(body, "html"))

        # Attach file
        if not os.path.exists(attachment_path):
            logger.error("mailer: attachment not found: %s", attachment_path)
            return False

        with open(attachment_path, "rb") as f:
            file_part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))

        file_part["Content-Disposition"] = f'attachment; filename="{os.path.basename(attachment_path)}"'
        msg.attach(file_part)

        with _smtp_connection() as server:
            server.send_message(msg)

        logger.info("mailer: email with attachment sent to %s", to_email)
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error("mailer: SMTP auth failed for %s:%s -> %s", SMTP_SERVER, SMTP_PORT, e)
        return False
    except Exception as e:
        logger.exception("mailer: failed to send email with attachment to %s: %s", to_email, e)
        return False
