"""Async SMTP email delivery service with retry + exponential backoff.

NEVER blocks the caller — all SMTP operations are non-blocking via aiosmtplib.
Retries up to 3 times with exponential backoff before giving up.
"""
import asyncio
import logging
from email.message import EmailMessage
from typing import Optional

import aiosmtplib
from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BASE_DELAY = 1  # seconds


async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
) -> bool:
    """Send an email via async SMTP with retry and exponential backoff.

    Returns True if sent successfully, False otherwise.
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            "SMTP not configured — logging email instead of sending",
            extra={"service_task": "email_send"},
        )
        logger.info(f"[MOCK EMAIL] To: {to_email} | Subject: {subject}")
        return True

    msg = EmailMessage()
    msg["From"] = f"{from_name or settings.SMTP_FROM_NAME} <{from_email or settings.SMTP_FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(html_body, subtype="html")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_USE_TLS,
            )
            logger.info(
                f"Email sent to {to_email}",
                extra={"service_task": "email_send", "attempt": attempt},
            )
            return True

        except aiosmtplib.SMTPException as exc:
            delay = BASE_DELAY * (2 ** (attempt - 1))
            logger.warning(
                f"SMTP failed (attempt {attempt}/{MAX_RETRIES}): {exc}. Retrying in {delay}s",
                extra={"service_task": "email_retry"},
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(delay)
        except Exception as exc:
            logger.error(f"Unexpected email error: {exc}", extra={"service_task": "email_send"})
            break

    logger.error(f"Email delivery failed after {MAX_RETRIES} attempts: {to_email}", extra={"service_task": "email_dlq"})
    return False
