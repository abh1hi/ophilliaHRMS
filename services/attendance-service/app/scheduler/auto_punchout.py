"""Auto punch-out scheduler (fail-safe, idempotent).

Runs periodically to auto-close attendance records that were not punched out
by the auto_clock_out_at snapshot saved from the employee's assigned schedule.

Uses SELECT FOR UPDATE SKIP LOCKED to:
- Prevent conflicts with manual punch-outs happening concurrently
- Allow multiple scheduler instances without double-processing
- Skip records that are currently being modified by another transaction

Records are marked as AUTO_CLOSED and an event is published to notify admins.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_record import AttendanceRecord
from app.events.publisher import EventPublisher

logger = logging.getLogger(__name__)


async def _try_close_record(
    record: AttendanceRecord,
    now: datetime,
    event_publisher: EventPublisher | None,
) -> bool:
    """Attempt to auto-close a single open record. Returns True if closed."""
    if record.clock_out is not None:
        logger.debug(
            f"Auto-close skipped (already closed): employee={record.employee_id}",
            extra={"user_id": str(record.employee_id), "service_task": "auto_punchout"},
        )
        return False

    if record.auto_clock_out_at is None or now < record.auto_clock_out_at:
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
            "schedule_id": str(record.schedule_id) if record.schedule_id else None,
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
    """Auto-close open records whose schedule auto_clock_out_at has passed."""
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(AttendanceRecord).where(
            and_(
                AttendanceRecord.clock_out.is_(None),
                AttendanceRecord.auto_clock_out_at.isnot(None),
                AttendanceRecord.auto_clock_out_at <= now,
            )
        ).with_for_update(skip_locked=True)
    )
    open_records = list(result.scalars().all())

    if not open_records:
        return 0

    closed_count = sum([
        1 if await _try_close_record(record, now, event_publisher) else 0
        for record in open_records
    ])

    if closed_count > 0:
        await db.commit()

    logger.info(
        f"Auto punch-out completed: {closed_count} records closed (of {len(open_records)} open)"
    )
    return closed_count
