"""Notification service: in-app, email, browser push, and employee app push.

Dispatches notifications across all configured channels for attendance events.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update as sa_update

from app.models.notification import Notification
from app.models.device_push_token import DevicePushToken
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send(
        self,
        company_id: UUID,
        recipient_id: UUID,
        recipient_role: str,
        notif_type: str,
        title: str,
        body: str,
        related_record_id: Optional[UUID] = None,
        related_record_type: Optional[str] = None,
    ) -> Notification:
        """Create in-app notification and dispatch to all enabled channels."""
        n = Notification(
            id=uuid4(),
            company_id=company_id,
            recipient_id=recipient_id,
            recipient_role=recipient_role,
            type=notif_type,
            title=title,
            body=body,
            related_record_id=related_record_id,
            related_record_type=related_record_type,
        )
        self.db.add(n)
        await self.db.flush()

        # Fire-and-forget other channels
        await self._send_push(company_id, recipient_id, title, body)
        await self._send_email(recipient_id, title, body)

        return n

    async def _send_push(
        self, company_id: UUID, recipient_id: UUID, title: str, body: str
    ) -> None:
        """Send push notification to all registered devices for this user."""
        try:
            result = await self.db.execute(
                select(DevicePushToken).where(
                    DevicePushToken.employee_id == recipient_id
                )
            )
            tokens = result.scalars().all()
            for token_record in tokens:
                await self._dispatch_push_token(token_record.token, token_record.platform, title, body)
        except Exception as e:
            logger.warning(f"Push notification failed for {recipient_id}: {e}")

    async def _dispatch_push_token(self, token: str, platform: str, title: str, body: str) -> None:
        """Dispatch to FCM (Android/web) or APNs (iOS).

        Placeholder — wire up Firebase Admin SDK or Web Push in production.
        """
        logger.debug(f"[PUSH:{platform}] {title} → token={token[:20]}…")

    async def _send_email(self, recipient_id: UUID, title: str, body: str) -> None:
        """Send email notification.

        Placeholder — wire up SMTP/SendGrid in production using employee email
        fetched from auth-service or employee-service.
        """
        logger.debug(f"[EMAIL] {title} → recipient={recipient_id}")

    async def get_unread_count(self, recipient_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count(Notification.id)).where(
                and_(
                    Notification.recipient_id == recipient_id,
                    Notification.is_read == False,  # noqa: E712
                )
            )
        )
        return result.scalar() or 0

    async def mark_read(self, notification_id: UUID, recipient_id: UUID) -> None:
        await self.db.execute(
            sa_update(Notification)
            .where(
                and_(
                    Notification.id == notification_id,
                    Notification.recipient_id == recipient_id,
                )
            )
            .values(is_read=True)
        )
        await self.db.commit()

    async def mark_all_read(self, recipient_id: UUID) -> None:
        await self.db.execute(
            sa_update(Notification)
            .where(Notification.recipient_id == recipient_id)
            .values(is_read=True)
        )
        await self.db.commit()

    async def list_notifications(
        self, recipient_id: UUID, skip: int = 0, limit: int = 30
    ) -> list[Notification]:
        result = await self.db.execute(
            select(Notification)
            .where(Notification.recipient_id == recipient_id)
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


# ── Event-driven notification handlers ──
# Called from event consumer or directly after DB operations.

async def notify_early_clockout(
    db: AsyncSession,
    company_id: UUID,
    hr_recipient_ids: list[UUID],
    employee_id: UUID,
    record_id: UUID,
    clock_out_time: datetime,
    actual_hours: float,
) -> None:
    svc = NotificationService(db)
    for hr_id in hr_recipient_ids:
        await svc.send(
            company_id=company_id,
            recipient_id=hr_id,
            recipient_role="hr",
            notif_type="early_clockout",
            title="Employee Left Early",
            body=(
                f"An employee clocked out early at "
                f"{clock_out_time.strftime('%I:%M %p')} IST "
                f"({actual_hours:.1f}h worked). Review required."
            ),
            related_record_id=record_id,
            related_record_type="attendance_record",
        )


async def notify_late_request_submitted(
    db: AsyncSession,
    company_id: UUID,
    hr_recipient_ids: list[UUID],
    employee_id: UUID,
    request_id: UUID,
    for_date: str,
) -> None:
    svc = NotificationService(db)
    for hr_id in hr_recipient_ids:
        await svc.send(
            company_id=company_id,
            recipient_id=hr_id,
            recipient_role="hr",
            notif_type="late_clockin_request",
            title="Late Clock-In Request",
            body=f"An employee submitted a late clock-in request for {for_date}. Approval pending.",
            related_record_id=request_id,
            related_record_type="attendance_request",
        )


async def notify_late_clockin_approved(
    db: AsyncSession,
    company_id: UUID,
    employee_id: UUID,
    request_id: UUID,
    minutes_remaining: int = 10,
) -> None:
    svc = NotificationService(db)
    await svc.send(
        company_id=company_id,
        recipient_id=employee_id,
        recipient_role="employee",
        notif_type="late_clockin_approved",
        title="Clock-In Approved",
        body=f"HR approved your late clock-in request. You have {minutes_remaining} minutes to clock in.",
        related_record_id=request_id,
        related_record_type="attendance_request",
    )


async def notify_schedule_expiry(
    db: AsyncSession,
    company_id: UUID,
    hr_recipient_ids: list[UUID],
    schedule_name: str,
    days_until_expiry: int,
) -> None:
    svc = NotificationService(db)
    is_expired = days_until_expiry <= 0
    title = "Schedule Expired – Auto-Extended" if is_expired else f"Schedule Expiring in {days_until_expiry} Days"
    body = (
        f"Shift schedule '{schedule_name}' has been auto-extended by 10 days. Please renew it."
        if is_expired
        else f"Shift schedule '{schedule_name}' expires in {days_until_expiry} days. Renew before it auto-extends."
    )
    for hr_id in hr_recipient_ids:
        await svc.send(
            company_id=company_id,
            recipient_id=hr_id,
            recipient_role="hr",
            notif_type="schedule_expiry_warning",
            title=title,
            body=body,
        )


async def notify_auto_clockout(
    db: AsyncSession,
    company_id: UUID,
    employee_id: UUID,
    record_id: UUID,
    clock_out_time: datetime,
) -> None:
    svc = NotificationService(db)
    await svc.send(
        company_id=company_id,
        recipient_id=employee_id,
        recipient_role="employee",
        notif_type="auto_clockout",
        title="You Were Auto Clocked Out",
        body=(
            f"Your shift was automatically closed at "
            f"{clock_out_time.strftime('%I:%M %p')} IST. "
            "If you have mandatory tasks, complete them before your next clock-in."
        ),
        related_record_id=record_id,
        related_record_type="attendance_record",
    )
