"""Holiday caching for leave calculations.

Caches the holiday list in-memory for 5 minutes to avoid DB hits per leave request.
"""
import logging
import time
from datetime import date
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.leave import Holiday

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 300  # 5 minutes
_cache: dict = {"holidays": None, "expires_at": 0}


async def get_holidays_cached(db: AsyncSession) -> List[date]:
    """Return list of holiday dates. Uses in-memory cache with 5-min TTL."""
    now = time.time()
    if _cache["holidays"] is not None and now < _cache["expires_at"]:
        return _cache["holidays"]

    result = await db.execute(
        select(Holiday.date).where(Holiday.is_active == 1)
    )
    holidays = [row[0] for row in result.all()]
    _cache["holidays"] = holidays
    _cache["expires_at"] = now + CACHE_TTL_SECONDS
    logger.info(f"Holiday cache refreshed: {len(holidays)} holidays loaded")
    return holidays


def invalidate_holiday_cache():
    """Call after holiday CRUD operations."""
    _cache["holidays"] = None
    _cache["expires_at"] = 0


def count_business_days(start: date, end: date, holidays: List[date]) -> int:
    """Count business days between start and end (inclusive), excluding weekends and holidays."""
    if end < start:
        return 0
    count = 0
    current = start
    from datetime import timedelta
    while current <= end:
        if current.weekday() < 5 and current not in holidays:
            count += 1
        current += timedelta(days=1)
    return count
