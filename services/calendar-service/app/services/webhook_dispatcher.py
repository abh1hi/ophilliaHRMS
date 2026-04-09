"""Outbound webhook dispatcher with HMAC-SHA256 request signing.

When a CalendarEvent is created or updated on a Calendar that has a
`webhook_url` set, this module fires an HTTP POST to that URL with:

    X-Ophillia-Signature: sha256=<hex_digest>
    X-Ophillia-Event: calendar.event.created | calendar.event.updated | calendar.event.deleted
    Content-Type: application/json

The HMAC is computed over the raw JSON body using the WEBHOOK_SECRET
from settings (UTF-8 encoded).

Delivery is fire-and-forget with a 5-second timeout. Failures are logged
but never propagate to the caller — a webhook delivery failure must never
cause the main API response to fail.
"""
import hashlib
import hmac
import json
import logging
from datetime import timezone

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def _sign_payload(body_bytes: bytes) -> str:
    """Return sha256=<hex> HMAC signature for the given body."""
    secret = settings.WEBHOOK_SECRET.encode("utf-8")
    digest = hmac.new(secret, body_bytes, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


async def dispatch_webhook(
    webhook_url: str,
    event_name: str,
    payload: dict,
) -> None:
    """POST the payload to webhook_url with HMAC signature header.

    Never raises — all errors are swallowed after logging.
    """
    if not webhook_url or not settings.WEBHOOK_SECRET:
        return

    try:
        body_bytes = json.dumps(payload, default=str).encode("utf-8")
        signature = _sign_payload(body_bytes)

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                webhook_url,
                content=body_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-Ophillia-Signature": signature,
                    "X-Ophillia-Event": event_name,
                },
            )
            if resp.is_success:
                logger.info(
                    f"Webhook delivered: {event_name} → {webhook_url} "
                    f"(HTTP {resp.status_code})"
                )
            else:
                logger.warning(
                    f"Webhook non-2xx: {event_name} → {webhook_url} "
                    f"(HTTP {resp.status_code})"
                )
    except Exception as exc:
        logger.warning(f"Webhook delivery failed: {event_name} → {webhook_url}: {exc}")


def _build_event_payload(event, event_name: str) -> dict:
    """Build the standard webhook payload dict from a CalendarEvent ORM object."""
    return {
        "event": event_name,
        "data": {
            "id": str(event.id),
            "calendar_id": str(event.calendar_id),
            "company_id": str(event.company_id),
            "title": event.title,
            "description": event.description,
            "event_type": event.event_type,
            "start_time": event.start_time.isoformat() if event.start_time else None,
            "end_time": event.end_time.isoformat() if event.end_time else None,
            "all_day": event.all_day,
            "status": event.status,
            "created_by": str(event.created_by),
        },
    }


async def fire_event_created(calendar, event) -> None:
    """Fire calendar.event.created webhook if the calendar has a webhook_url."""
    if not calendar or not getattr(calendar, "webhook_url", None):
        return
    payload = _build_event_payload(event, "calendar.event.created")
    await dispatch_webhook(calendar.webhook_url, "calendar.event.created", payload)


async def fire_event_updated(calendar, event) -> None:
    """Fire calendar.event.updated webhook if the calendar has a webhook_url."""
    if not calendar or not getattr(calendar, "webhook_url", None):
        return
    payload = _build_event_payload(event, "calendar.event.updated")
    await dispatch_webhook(calendar.webhook_url, "calendar.event.updated", payload)


async def fire_event_deleted(calendar, event) -> None:
    """Fire calendar.event.deleted webhook if the calendar has a webhook_url."""
    if not calendar or not getattr(calendar, "webhook_url", None):
        return
    payload = _build_event_payload(event, "calendar.event.deleted")
    await dispatch_webhook(calendar.webhook_url, "calendar.event.deleted", payload)
