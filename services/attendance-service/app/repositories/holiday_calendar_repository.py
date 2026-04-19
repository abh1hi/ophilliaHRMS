from typing import Optional
from uuid import UUID
from datetime import date

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holiday_calendar import HolidayCalendar, Holiday


class HolidayCalendarRepository:
    """Lookup public holidays using location-aware cascade:
    location calendar → company calendar → None (not a holiday).
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_for_date(
        self,
        company_id: UUID,
        target_date: date,
        location_id: Optional[UUID] = None,
    ) -> Optional[Holiday]:
        """Return the Holiday record for target_date, or None if not a holiday.

        Checks location-specific calendar first; falls back to company-wide calendar.
        Only considers active calendars for the target year.
        """
        if location_id:
            holiday = await self._query_holiday(company_id, target_date, location_id=location_id)
            if holiday:
                return holiday

        return await self._query_holiday(company_id, target_date, location_id=None)

    async def _query_holiday(
        self,
        company_id: UUID,
        target_date: date,
        location_id: Optional[UUID],
    ) -> Optional[Holiday]:
        location_filter = (
            HolidayCalendar.location_id == location_id
            if location_id
            else HolidayCalendar.location_id.is_(None)
        )
        result = await self.db.execute(
            select(Holiday)
            .join(HolidayCalendar, HolidayCalendar.id == Holiday.calendar_id)
            .where(
                and_(
                    HolidayCalendar.company_id == company_id,
                    HolidayCalendar.year == target_date.year,
                    HolidayCalendar.is_active.is_(True),
                    location_filter,
                    Holiday.date == target_date,
                )
            )
            .limit(1)
        )
        return result.scalars().first()
