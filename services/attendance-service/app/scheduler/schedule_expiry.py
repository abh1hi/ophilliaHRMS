"""Schedule validity expiry checker and auto-extender.

Runs daily at 00:01 IST. Performs two actions:
  1. Finds assignments expiring today → sends 5-day-warning notifications to HR.
  2. Finds expired assignments (effective_to = yesterday) → auto-extends by 10 days
     and sends daily "still expired" notification until HR updates the schedule.
"""
import logging
from datetime import date, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift_schedule_assignment import ShiftScheduleAssignment
from app.models.shift_schedule import ShiftSchedule

logger = logging.getLogger(__name__)

AUTO_EXTEND_DAYS = 10
WARNING_DAYS_BEFORE = 5


async def run_schedule_expiry_check(db: AsyncSession) -> None:
    today = date.today()
    warning_date = today + timedelta(days=WARNING_DAYS_BEFORE)
    yesterday = today - timedelta(days=1)

    # ── 1. Five-day warning ──
    expiring_soon = await db.execute(
        select(ShiftScheduleAssignment).where(
            ShiftScheduleAssignment.effective_to == warning_date
        )
    )
    for assignment in expiring_soon.scalars().all():
        schedule = await db.get(ShiftSchedule, assignment.schedule_id)
        if schedule:
            logger.info(
                f"Schedule expiry warning: schedule='{schedule.name}' "
                f"expires in {WARNING_DAYS_BEFORE} days (company={schedule.company_id})"
            )
            # Notification fired via notification_service (company HR IDs resolved externally)
            # Events consumer picks this up to send to HR users
            try:
                from app.events.publisher import get_publisher
                publisher = await get_publisher()
                if publisher:
                    await publisher.publish("schedule.expiry_warning", {
                        "company_id": str(schedule.company_id),
                        "schedule_id": str(schedule.id),
                        "schedule_name": schedule.name,
                        "days_until_expiry": WARNING_DAYS_BEFORE,
                        "expiry_date": str(warning_date),
                    })
            except Exception as e:
                logger.warning(f"Failed to publish schedule expiry warning event: {e}")

    # ── 2. Auto-extend expired assignments ──
    expired = await db.execute(
        select(ShiftScheduleAssignment).where(
            and_(
                ShiftScheduleAssignment.effective_to == yesterday,
            )
        ).with_for_update(skip_locked=True)
    )
    extended_count = 0
    for assignment in expired.scalars().all():
        new_end = yesterday + timedelta(days=AUTO_EXTEND_DAYS)
        assignment.effective_to = new_end

        schedule = await db.get(ShiftSchedule, assignment.schedule_id)
        if schedule:
            schedule.validity_auto_extended = True
            if schedule.validity_end:
                schedule.validity_end = new_end

            logger.info(
                f"Auto-extended schedule='{schedule.name}' to {new_end} "
                f"(company={schedule.company_id})"
            )
            try:
                from app.events.publisher import get_publisher
                publisher = await get_publisher()
                if publisher:
                    await publisher.publish("schedule.auto_extended", {
                        "company_id": str(schedule.company_id),
                        "schedule_id": str(schedule.id),
                        "schedule_name": schedule.name,
                        "new_expiry_date": str(new_end),
                        "days_until_expiry": 0,
                    })
            except Exception as e:
                logger.warning(f"Failed to publish schedule auto-extended event: {e}")

        extended_count += 1

    if extended_count:
        await db.commit()
        logger.info(f"Auto-extended {extended_count} expired schedule assignment(s)")
