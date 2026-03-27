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


async def _get_auto_close_time(
    db: AsyncSession,
    employee_id,
    company_id,
) -> time:
    """Resolve the auto_close_time for an employee.

    Priority: employee-level policy > company-level policy > default (23:59).
    """
    # Try employee-specific policy first
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

    # Fall back to company-wide policy (no employee_id set)
    result = await db.execute(
        select(AttendancePolicy.auto_close_time).where(
            and_(
                AttendancePolicy.company_id == company_id,
                AttendancePolicy.employee_id.is_(None),
                AttendancePolicy.department_id.is_(None),
            )
        ).limit(1)
    )
    row = result.scalar_one_or_none()
    if row is not None:
        return row

    return DEFAULT_AUTO_CLOSE_TIME


async def auto_close_stale_records(
    db: AsyncSession,
    event_publisher: EventPublisher | None = None,
) -> int:
    """Find all records for today with no clock_out and auto-close them
    only if the current time has passed their configured auto_close_time.

    Uses SELECT FOR UPDATE SKIP LOCKED so that:
    - Records being punched out manually are skipped (not blocked)
    - Concurrent scheduler runs don't double-process the same record

    Returns the number of records closed.
    """
    today = date.today()
    now = datetime.now(timezone.utc)
    current_time = now.time()

    # SKIP LOCKED: skip rows currently locked by a manual punch-out
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

    closed_count = 0
    for record in open_records:
        # Double-check: record may have been closed between query and lock
        if record.clock_out is not None:
            logger.debug(
                f"Auto-close skipped (already closed): employee={record.employee_id}",
                extra={"user_id": str(record.employee_id), "service_task": "auto_punchout"},
            )
            continue

        # Look up the employee's auto_close_time policy
        auto_close = await _get_auto_close_time(
            db, record.employee_id, record.company_id
        )

        # Only close if current time has passed the auto_close_time
        if current_time < auto_close:
            continue

        # Calculate work hours from clock_in to now
        delta = now - record.clock_in
        total_hours = round(delta.total_seconds() / 3600, 2)

        record.clock_out = now
        record.work_hours = total_hours
        record.overtime_hours = max(0.0, round(total_hours - 8.0, 2))
        record.status = "auto_closed"
        record.state = "completed"
        record.notes = (record.notes or "") + " [AUTO_CLOSED by system]"
        record.version = (record.version or 1) + 1

        # Mark all pending tasks as not_completed
        for task in record.tasks:
            if task.status == "pending":
                task.status = "not_completed"
                task.completion_notes = "Auto-closed: employee did not punch out"

        closed_count += 1

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

    if closed_count > 0:
        await db.commit()

    logger.info(f"Auto punch-out completed: {closed_count} records closed (of {len(open_records)} open)")
    return closed_count
