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
_cache: dict = {}  # keyed by company_id


async def get_holidays_cached(db: AsyncSession) -> List[date]:
    """Return list of holiday dates. Uses per-tenant in-memory cache with 5-min TTL."""
    company_id = db.info.get("company_id")
    cache_key = str(company_id) if company_id else "__global__"

    now = time.time()
    tenant_cache = _cache.get(cache_key)
    if tenant_cache is not None and now < tenant_cache["expires_at"]:
        return tenant_cache["holidays"]

    query = select(Holiday.date).where(Holiday.is_active == 1)
    if company_id:
        query = query.where(Holiday.company_id == company_id)
    result = await db.execute(query)
    holidays = [row[0] for row in result.all()]
    _cache[cache_key] = {"holidays": holidays, "expires_at": now + CACHE_TTL_SECONDS}
    logger.info(f"Holiday cache refreshed for tenant {cache_key}: {len(holidays)} holidays loaded")
    return holidays


def invalidate_holiday_cache():
    """Call after holiday CRUD operations. Clears all tenant caches."""
    _cache.clear()


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
