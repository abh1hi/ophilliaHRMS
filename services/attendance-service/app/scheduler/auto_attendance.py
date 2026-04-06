"""Auto-attendance scheduler wrapper.

Registered in main.py to run periodically (default: every 30 minutes).
Processes yesterday's unprocessed EmployeeCheckin logs and creates
AttendanceRecords via run_auto_attendance().
"""

import logging
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auto_attendance_service import run_auto_attendance
from app.events.publisher import EventPublisher

logger = logging.getLogger(__name__)


async def process_auto_attendance(
    db: AsyncSession,
    event_publisher: EventPublisher | None = None,
    target_date: date | None = None,
) -> int:
    """Entry point for the scheduler loop. Delegates to run_auto_attendance()."""
    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    try:
        count = await run_auto_attendance(db, event_publisher, target_date)
        if count:
            logger.info(f"Auto-attendance scheduler: {count} records created for {target_date}")
        return count
    except Exception:
        logger.exception(f"Auto-attendance scheduler error for {target_date}")
        return 0
