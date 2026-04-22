"""Auto-attendance service.

Reads EmployeeCheckin logs for a given date, pairs IN/OUT events, compares
against shift schedule assignments to determine attendance status, and creates
AttendanceRecords automatically.

Uses the same SELECT FOR UPDATE SKIP LOCKED pattern as auto_punchout to
prevent double-processing in concurrent scheduler runs.
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.employee_checkin import EmployeeCheckin
from app.models.attendance_record import AttendanceRecord
from app.models.shift_schedule import ShiftSchedule
from app.models.shift_schedule_assignment import ShiftScheduleAssignment
from app.models.shift_type import ShiftType
from app.events.publisher import EventPublisher

logger = logging.getLogger(__name__)


async def run_auto_attendance(
    db: AsyncSession,
    event_publisher: Optional[EventPublisher] = None,
    target_date: Optional[date] = None,
) -> int:
    """Process checkin logs for target_date and create AttendanceRecords.

    Args:
        db: Async DB session (no tenant scoping — uses raw queries).
        event_publisher: Optional RabbitMQ publisher.
        target_date: Date to process. Defaults to yesterday.

    Returns:
        Number of attendance records created.
    """
    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    day_start = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)
    day_end = datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)

    # ── 1. Fetch all unprocessed checkins for the target date (across all companies) ──
    checkin_result = await db.execute(
        select(EmployeeCheckin).where(
            and_(
                EmployeeCheckin.log_datetime >= day_start,
                EmployeeCheckin.log_datetime <= day_end,
                EmployeeCheckin.skip_auto_attendance == 0,
                EmployeeCheckin.attendance_record_id.is_(None),
            )
        ).with_for_update(skip_locked=True)
        .order_by(EmployeeCheckin.log_datetime.asc())
    )
    all_checkins: List[EmployeeCheckin] = list(checkin_result.scalars().all())

    if not all_checkins:
        logger.info(f"Auto-attendance: no unprocessed checkins for {target_date}")
        return 0

    # ── 2. Group by (company_id, employee_id) ──
    groups: Dict[tuple, List[EmployeeCheckin]] = {}
    for c in all_checkins:
        key = (c.company_id, c.employee_id)
        groups.setdefault(key, []).append(c)

    created_count = 0

    for (company_id, employee_id), checkins in groups.items():
        # ── 3. Find first IN and last OUT ──
        in_logs = [c for c in checkins if c.log_type == "IN"]
        out_logs = [c for c in checkins if c.log_type == "OUT"]

        first_in = in_logs[0] if in_logs else None
        last_out = out_logs[-1] if out_logs else None

        if first_in is None:
            logger.debug(f"Auto-attendance: no IN log for employee={employee_id} on {target_date} — skipping")
            continue

        clock_in_dt = first_in.log_datetime
        clock_out_dt = last_out.log_datetime if last_out else None

        # ── 4. Determine work hours and status ──
        work_hours: Optional[float] = None
        overtime_hours = 0.0
        att_status = "present"

        # Resolve schedule assignment to get expected work hours and grace period.
        shift_result = await db.execute(
            select(ShiftScheduleAssignment, ShiftSchedule, ShiftType)
            .join(ShiftSchedule, ShiftScheduleAssignment.schedule_id == ShiftSchedule.id)
            .join(ShiftType, ShiftSchedule.shift_type_id == ShiftType.id)
            .where(
                and_(
                    ShiftScheduleAssignment.company_id == company_id,
                    ShiftScheduleAssignment.employee_id == employee_id,
                    ShiftScheduleAssignment.is_active == 1,
                    ShiftScheduleAssignment.effective_from <= target_date,
                    (ShiftScheduleAssignment.effective_to == None) | (ShiftScheduleAssignment.effective_to >= target_date),
                    ShiftSchedule.is_active == 1,
                    ShiftType.is_active.is_(True),
                )
            )
            .order_by(ShiftScheduleAssignment.effective_from.desc())
            .limit(1)
        )
        schedule_row = shift_result.first()

        expected_work_hours = 8.0  # default
        grace_minutes = 15
        schedule = None
        shift_type = None
        if schedule_row:
            _, schedule, shift_type = schedule_row
            expected_work_hours = shift_type.work_hours_per_day
            grace_minutes = shift_type.grace_period_minutes

        if clock_out_dt:
            # Make both timezone-naive for arithmetic if needed
            ci = clock_in_dt.replace(tzinfo=None) if clock_in_dt.tzinfo else clock_in_dt
            co = clock_out_dt.replace(tzinfo=None) if clock_out_dt.tzinfo else clock_out_dt
            delta = co - ci
            work_hours = round(delta.total_seconds() / 3600, 2)
            overtime_hours = max(0.0, round(work_hours - expected_work_hours, 2))

            if work_hours < expected_work_hours / 2:
                att_status = "half_day"

        # Check lateness against shift start time (if assignment exists and has a linked shift)
        # We store shift_type_id as a plain UUID — we don't join across services
        # Use clock_in time to assess late: compare against 09:00 default + grace
        from datetime import time
        grace_td = timedelta(minutes=grace_minutes)
        expected_start = datetime.combine(target_date, shift_type.start_time if shift_type else time(9, 0))
        ci_naive = clock_in_dt.replace(tzinfo=None) if clock_in_dt.tzinfo else clock_in_dt
        if ci_naive > expected_start + grace_td and att_status == "present":
            att_status = "late"

        # ── 5. Create AttendanceRecord (upsert via IntegrityError catch) ──
        record = AttendanceRecord(
            company_id=company_id,
            employee_id=employee_id,
            schedule_id=schedule.id if schedule else None,
            clock_in=clock_in_dt,
            clock_out=clock_out_dt,
            scheduled_clock_in_at=expected_start.replace(tzinfo=timezone.utc),
            scheduled_clock_out_at=(
                datetime.combine(target_date, shift_type.end_time, tzinfo=timezone.utc)
                if shift_type
                else None
            ),
            auto_clock_out_at=(
                datetime.combine(target_date, schedule.auto_clock_out_time, tzinfo=timezone.utc)
                if schedule and schedule.auto_clock_out_enabled
                else None
            ),
            tasks_mandatory_snapshot=schedule.tasks_mandatory if schedule else False,
            allowed_clock_in_location_ids_snapshot=schedule.allowed_clock_in_location_ids if schedule else None,
            allowed_clock_out_location_ids_snapshot=schedule.allowed_clock_out_location_ids if schedule else None,
            work_hours=work_hours,
            overtime_hours=overtime_hours,
            status=att_status,
            method="auto_attendance",
            notes="Created by auto-attendance scheduler",
            date=target_date,
            state="completed" if clock_out_dt else "punched_in",
        )

        try:
            db.add(record)
            await db.flush()
            await db.refresh(record)

            # ── 6. Link all processed checkins to this record ──
            for c in checkins:
                c.attendance_record_id = record.id

            await db.commit()
            created_count += 1

            if event_publisher:
                await event_publisher.publish("attendance.auto_attendance_processed", {
                    "company_id": str(company_id),
                    "employee_id": str(employee_id),
                    "date": str(target_date),
                    "record_id": str(record.id),
                    "status": att_status,
                    "work_hours": work_hours,
                })

            logger.info(
                f"Auto-attendance: created record for employee={employee_id} "
                f"status={att_status} hours={work_hours} on {target_date}"
            )

        except IntegrityError:
            await db.rollback()
            logger.debug(
                f"Auto-attendance: record already exists for employee={employee_id} "
                f"on {target_date} — skipping"
            )

    logger.info(f"Auto-attendance completed: {created_count} records created for {target_date}")
    return created_count
