"""Auto punch-out scheduler (fail-safe, idempotent).

Runs periodically to auto-close attendance records that were not punched out
by the configured auto_close_time (default 23:59).

Uses SELECT FOR UPDATE SKIP LOCKED to:
- Prevent conflicts with manual punch-outs happening concurrently
- Allow multiple scheduler instances without double-processing
- Skip records that are currently being modified by another transaction

Records are marked as AUTO_CLOSED and an event is published to notify admins.
"""

import logging
from datetime import date, datetime, time, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_record import AttendanceRecord
from app.models.attendance_policy import AttendancePolicy
from app.events.publisher import EventPublisher

logger = logging.getLogger(__name__)

DEFAULT_AUTO_CLOSE_TIME = time(23, 59)


async def _get_auto_close_time(db: AsyncSession, employee_id, company_id) -> time:
    """Resolve auto_close_time: employee → department → location → company-wide → default."""
    # Employee-level
    result = await db.execute(
        select(AttendancePolicy.auto_close_time).where(
            and_(
                AttendancePolicy.company_id == company_id,
                AttendancePolicy.employee_id == employee_id,
            )
        ).limit(1)
    )
    row = result.scalar_one_or_none()
    if row is not None:
        return row

    # Department-level
    result = await db.execute(
        select(AttendancePolicy.auto_close_time).where(
            and_(
                AttendancePolicy.company_id == company_id,
                AttendancePolicy.employee_id.is_(None),
                AttendancePolicy.department_id.isnot(None),
                AttendancePolicy.location_id.is_(None),
            )
        ).limit(1)
    )
    row = result.scalar_one_or_none()
    if row is not None:
        return row

    # Location-level
    result = await db.execute(
        select(AttendancePolicy.auto_close_time).where(
            and_(
                AttendancePolicy.company_id == company_id,
                AttendancePolicy.employee_id.is_(None),
                AttendancePolicy.location_id.isnot(None),
            )
        ).limit(1)
    )
    row = result.scalar_one_or_none()
    if row is not None:
        return row

    # Company-wide
    result = await db.execute(
        select(AttendancePolicy.auto_close_time).where(
            and_(
                AttendancePolicy.company_id == company_id,
                AttendancePolicy.employee_id.is_(None),
                AttendancePolicy.location_id.is_(None),
                AttendancePolicy.department_id.is_(None),
            )
        ).limit(1)
    )
    row = result.scalar_one_or_none()
    if row is not None:
        return row

    return DEFAULT_AUTO_CLOSE_TIME


async def _try_close_record(
    db: AsyncSession,
    record: AttendanceRecord,
    now: datetime,
    current_time: time,
    event_publisher: EventPublisher | None,
) -> bool:
    """Attempt to auto-close a single open record. Returns True if closed."""
    if record.clock_out is not None:
        logger.debug(
            f"Auto-close skipped (already closed): employee={record.employee_id}",
            extra={"user_id": str(record.employee_id), "service_task": "auto_punchout"},
        )
        return False

    auto_close = await _get_auto_close_time(db, record.employee_id, record.company_id)
    if current_time < auto_close:
        return False

    delta = now - record.clock_in
    total_hours = round(delta.total_seconds() / 3600, 2)

    record.clock_out = now
    record.work_hours = total_hours
    record.overtime_hours = max(0.0, round(total_hours - 8.0, 2))
    record.status = "auto_closed"
    record.state = "completed"
    record.notes = (record.notes or "") + " [AUTO_CLOSED by system]"
    record.version = (record.version or 1) + 1

    for task in record.tasks:
        if task.status == "pending":
            task.status = "not_completed"
            task.completion_notes = "Auto-closed: employee did not punch out"

    if event_publisher:
        await event_publisher.publish("attendance.auto_closed", {
            "company_id": str(record.company_id),
            "employee_id": str(record.employee_id),
            "record_id": str(record.id),
            "work_hours": total_hours,
            "timestamp": now.isoformat(),
        })

    logger.warning(
        f"Auto-closed attendance: employee={record.employee_id}, hours={total_hours}",
        extra={"user_id": str(record.employee_id), "service_task": "auto_punchout"},
    )
    return True


async def auto_close_stale_records(
    db: AsyncSession,
    event_publisher: EventPublisher | None = None,
) -> int:
    """Auto-close open records whose auto_close_time has passed.

    Uses SELECT FOR UPDATE SKIP LOCKED so concurrent scheduler runs and
    manual punch-outs do not conflict. Returns the number of records closed.
    """
    today = date.today()
    now = datetime.now(timezone.utc)
    current_time = now.time()

    result = await db.execute(
        select(AttendanceRecord).where(
            and_(
                AttendanceRecord.date == today,
                AttendanceRecord.clock_out.is_(None),
            )
        ).with_for_update(skip_locked=True)
    )
    open_records = list(result.scalars().all())

    if not open_records:
        return 0

    closed_count = sum([
        1 if await _try_close_record(db, record, now, current_time, event_publisher) else 0
        for record in open_records
    ])

    if closed_count > 0:
        await db.commit()

    logger.info(
        f"Auto punch-out completed: {closed_count} records closed (of {len(open_records)} open)"
    )
    return closed_count
