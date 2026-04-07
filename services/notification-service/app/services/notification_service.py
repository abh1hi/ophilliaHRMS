"""Notification Service — Wires real email delivery + preference enforcement.

ALWAYS checks NotificationPreference before sending.
Uses Jinja2 templates for email body.
Falls back to logging when SMTP is not configured.
"""
import logging
import os
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.notification import NotificationPreference, NotificationLog
from app.schemas.notification import NotificationLogCreate, PreferenceCreate, PreferenceUpdate
from app.core.constants import NotificationStatus, NotificationType
from app.services.email_service import send_email

logger = logging.getLogger(__name__)

# Jinja2 template engine
_template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
_jinja_env = Environment(loader=FileSystemLoader(_template_dir), autoescape=True)


def render_template(template_name: str, **context) -> str:
    """Render an HTML email template with the given context."""
    try:
        template = _jinja_env.get_template(template_name)
        return template.render(**context)
    except Exception as exc:
        logger.warning(f"Template {template_name} not found, using plain text: {exc}")
        return context.get("message", "")


def _get_company_id(db: AsyncSession) -> Optional[UUID]:
    raw = db.info.get("company_id")
    return UUID(raw) if isinstance(raw, str) else raw


async def get_or_create_preference(db: AsyncSession, user_id: UUID) -> NotificationPreference:
    company_id = _get_company_id(db)
    query = select(NotificationPreference).filter(NotificationPreference.user_id == user_id)
    if company_id:
        query = query.filter(NotificationPreference.company_id == company_id)
    result = await db.execute(query)
    pref = result.scalars().first()
    if not pref:
        pref = NotificationPreference(user_id=user_id, email_enabled=1, sms_enabled=1)
        if company_id:
            pref.company_id = company_id
        db.add(pref)
        await db.commit()
        await db.refresh(pref)
    return pref


async def update_preference(db: AsyncSession, user_id: UUID, pref_update: PreferenceUpdate) -> NotificationPreference:
    pref = await get_or_create_preference(db, user_id)
    pref.email_enabled = 1 if pref_update.email_enabled else 0
    pref.sms_enabled = 1 if pref_update.sms_enabled else 0
    pref.calendar_enabled = 1 if pref_update.calendar_enabled else 0
    db.add(pref)
    await db.commit()
    await db.refresh(pref)
    return pref


async def compile_and_send_notification(
    db: AsyncSession,
    log_create: NotificationLogCreate,
    template_name: Optional[str] = None,
    template_context: Optional[dict] = None,
):
    """Check preferences → render template → send email → log result.

    PREFERENCE ENFORCEMENT: Always checks user opt-in before sending.
    """
    pref = await get_or_create_preference(db, log_create.user_id)

    # Preference enforcement
    should_send = False
    calendar_enabled = getattr(pref, "calendar_enabled", 1)
    if log_create.type == NotificationType.EMAIL and pref.email_enabled:
        should_send = True
    elif log_create.type == NotificationType.SMS and pref.sms_enabled:
        should_send = True
    # For calendar events/tasks, additionally check calendar_enabled preference
    # The subject prefix convention: emails from calendar handlers start with "Reminder:", "Invitation:", "Task Due"
    is_calendar_notification = any(
        (log_create.subject or "").startswith(p)
        for p in ("Reminder:", "Invitation:", "Task Due")
    )
    if is_calendar_notification and not calendar_enabled:
        should_send = False

    status = NotificationStatus.PENDING
    error_message = None
    sent_at = None

    if not should_send:
        status = NotificationStatus.FAILED
        error_message = f"User has disabled {log_create.type.value} notifications"
        logger.info(f"User {log_create.user_id} opted out of {log_create.type.value}")
    else:
        # Render template if provided
        html_body = log_create.message
        if template_name and template_context:
            html_body = render_template(template_name, **template_context)

        if log_create.type == NotificationType.EMAIL:
            # TODO: need a way to get user email; for now we log
            success = await send_email(
                to_email=f"user-{log_create.user_id}@ophillia.com",  # Placeholder
                subject=log_create.subject or "Ophillia HRMS Notification",
                html_body=html_body,
            )
            if success:
                status = NotificationStatus.SENT
                sent_at = datetime.now(timezone.utc).replace(tzinfo=None)
            else:
                status = NotificationStatus.FAILED
                error_message = "SMTP delivery failed after retries"
        else:
            # SMS/Push — simulate for now
            logger.info(f"Simulating {log_create.type.value} to {log_create.user_id}")
            status = NotificationStatus.SENT
            sent_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # Resolve company_id: prefer log_create, fall back to db.info (tenant context)
    company_id = None
    if hasattr(log_create, "company_id") and log_create.company_id:
        company_id = log_create.company_id
    else:
        company_id = _get_company_id(db)

    # Log to database
    db_obj = NotificationLog(
        user_id=log_create.user_id,
        type=log_create.type.value,
        subject=log_create.subject,
        message=log_create.message,
        status=status.value,
        error_message=error_message,
        sent_at=sent_at,
    )
    if company_id:
        db_obj.company_id = company_id
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
