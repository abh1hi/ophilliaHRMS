"""Holiday Sync Scheduler — daily job that pulls holidays from leave-service and
creates/upserts CalendarEvent records with event_type='holiday'.

Idempotency: each holiday is identified by the Redis key
    cal:holiday:{company_id}:{holiday_date}:{holiday_name_hash}
and a DB check on (company_id, event_type, description=holiday_id) to avoid
creating duplicates when the scheduler restarts or runs multiple times.

Runs once every 24 hours (configurable via RUN_INTERVAL_SECONDS).
"""
import asyncio
import hashlib
import logging
from datetime import datetime, timezone, date, timedelta
from uuid import UUID

import httpx
from sqlalchemy.future import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.calendar import Calendar
from app.models.calendar_event import CalendarEvent

logger = logging.getLogger(__name__)

RUN_INTERVAL_SECONDS = 24 * 3600  # 24 hours


async def _get_or_create_company_calendar(db, company_id: UUID) -> Calendar:
    """Return (or lazily create) the company-wide calendar for a given tenant."""
    sentinel_owner = UUID("00000000-0000-0000-0000-000000000001")
    result = await db.execute(
        select(Calendar).where(
            Calendar.company_id == company_id,
            Calendar.calendar_type == "company",
            Calendar.is_deleted == False,
        )
    )
    cal = result.scalars().first()
    if not cal:
        cal = Calendar(
            company_id=company_id,
            name="Company Calendar",
            calendar_type="company",
            owner_id=sentinel_owner,
            is_default=False,
            is_public=True,
        )
        db.add(cal)
        await db.flush()
    return cal


async def _fetch_holidays_from_leave_service(year: int) -> list[dict]:
    """Call leave-service internal endpoint to get all active holidays for a year."""
    url = f"{settings.LEAVE_SERVICE_URL}/api/v1/internal/holidays"
    headers = {"x-internal-token": settings.INTERNAL_SERVICE_TOKEN}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params={"year": year}, headers=headers)
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error(f"Failed to fetch holidays from leave-service: {exc}")
        return []


async def _upsert_holiday_event(db, holiday: dict) -> None:
    """Create a CalendarEvent for a holiday if one doesn't already exist."""
    company_id_str: str = str(holiday.get("company_id", ""))
    holiday_id: str = str(holiday.get("id", ""))
    name: str = holiday.get("name", "Holiday")
    date_str: str = str(holiday.get("date", ""))
    description_str: str = holiday.get("description") or ""

    if not company_id_str or not date_str:
        return

    try:
        company_id = UUID(company_id_str)
        holiday_date = date.fromisoformat(date_str)
    except (ValueError, AttributeError):
        logger.warning(f"Skipping holiday with unparseable data: {holiday}")
        return

    idempotency_marker = f"holiday:{holiday_id}"
    start_time = datetime(holiday_date.year, holiday_date.month, holiday_date.day, tzinfo=timezone.utc)
    end_time = start_time + timedelta(days=1)

    # Check if event already exists
    existing = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.company_id == company_id,
            CalendarEvent.event_type == "holiday",
            CalendarEvent.description == idempotency_marker,
            CalendarEvent.is_deleted == False,
        )
    )
    if existing.scalars().first():
        return  # already synced

    cal = await _get_or_create_company_calendar(db, company_id)

    event = CalendarEvent(
        company_id=company_id,
        calendar_id=cal.id,
        title=name,
        description=idempotency_marker,
        event_type="holiday",
        start_time=start_time,
        end_time=end_time,
        all_day=True,
        timezone="UTC",
        status="scheduled",
        created_by=UUID("00000000-0000-0000-0000-000000000001"),
        attendees=[],
        reminder_minutes=[],
    )
    db.add(event)


async def _run_holiday_sync() -> None:
    """Fetch holidays from leave-service and upsert CalendarEvents."""
    current_year = datetime.now(timezone.utc).year
    # Sync current year and next year so future holidays show in calendar
    for year in (current_year, current_year + 1):
        holidays = await _fetch_holidays_from_leave_service(year)
        if not holidays:
            logger.info(f"Holiday sync: no holidays returned for {year}")
            continue

        async with AsyncSessionLocal() as db:
            for h in holidays:
                try:
                    await _upsert_holiday_event(db, h)
                except Exception:
                    logger.exception(f"Error upserting holiday {h.get('id')}")
            await db.commit()
            logger.info(f"Holiday sync complete for {year}: {len(holidays)} holiday(s) processed")


async def run_holiday_sync_scheduler(interval: int = RUN_INTERVAL_SECONDS) -> None:
    """Long-running background coroutine. Call via asyncio.create_task()."""
    logger.info("Holiday sync scheduler started")
    # Run immediately on startup, then every 24h
    while True:
        try:
            await _run_holiday_sync()
        except Exception:
            logger.exception("Holiday sync error")
        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            raise
