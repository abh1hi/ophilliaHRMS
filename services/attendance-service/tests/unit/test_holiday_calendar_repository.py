"""Unit tests for HolidayCalendarRepository — location cascade, company fallback."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import date

from app.repositories.holiday_calendar_repository import HolidayCalendarRepository
from app.models.holiday_calendar import Holiday


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.info = {"company_id": str(uuid4())}
    return db


@pytest.fixture
def repo(mock_db):
    return HolidayCalendarRepository(mock_db)


def _make_holiday(holiday_type: str = "national") -> Holiday:
    h = MagicMock(spec=Holiday)
    h.holiday_type = holiday_type
    return h


class TestGetForDate:
    @pytest.mark.asyncio
    async def test_location_calendar_takes_priority(self, repo):
        """Should return location holiday when both location and company calendars have it."""
        company_id = uuid4()
        location_id = uuid4()
        target = date(2026, 8, 15)
        location_holiday = _make_holiday("national")

        repo._query_holiday = AsyncMock(side_effect=[location_holiday, None])

        result = await repo.get_for_date(company_id, target, location_id=location_id)

        assert result is location_holiday
        assert repo._query_holiday.call_count == 1

    @pytest.mark.asyncio
    async def test_falls_back_to_company_when_location_miss(self, repo):
        """Should check company calendar when location calendar returns None."""
        company_id = uuid4()
        location_id = uuid4()
        target = date(2026, 1, 26)
        company_holiday = _make_holiday("national")

        repo._query_holiday = AsyncMock(side_effect=[None, company_holiday])

        result = await repo.get_for_date(company_id, target, location_id=location_id)

        assert result is company_holiday
        assert repo._query_holiday.call_count == 2

    @pytest.mark.asyncio
    async def test_no_location_id_skips_location_query(self, repo):
        """Without location_id, only company calendar is queried."""
        company_id = uuid4()
        target = date(2026, 12, 25)
        company_holiday = _make_holiday("national")

        repo._query_holiday = AsyncMock(return_value=company_holiday)

        result = await repo.get_for_date(company_id, target, location_id=None)

        assert result is company_holiday
        repo._query_holiday.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_holiday_returns_none(self, repo):
        """Should return None when no holiday found in any calendar."""
        company_id = uuid4()
        target = date(2026, 6, 15)

        repo._query_holiday = AsyncMock(return_value=None)

        result = await repo.get_for_date(company_id, target)

        assert result is None
