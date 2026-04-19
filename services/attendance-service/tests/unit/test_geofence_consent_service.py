"""Unit tests for GeofenceConsentService — GDPR consent give/withdraw/assert."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from fastapi import HTTPException

from app.services.geofence_consent_service import GeofenceConsentService
from app.models.geofence_consent import GeofenceConsent


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.info = {"company_id": str(uuid4())}
    return db


@pytest.fixture
def service(mock_db):
    svc = GeofenceConsentService(mock_db)
    svc.repo = AsyncMock()
    return svc


class TestGiveConsent:
    @pytest.mark.asyncio
    async def test_give_consent_creates_record(self, service):
        employee_id = uuid4()
        record = MagicMock(spec=GeofenceConsent)
        record.consented = True
        service.repo.give_consent = AsyncMock(return_value=record)

        result = await service.give_consent(employee_id, ip_address="1.2.3.4")

        service.repo.give_consent.assert_called_once_with(employee_id, "1.2.3.4", None)
        assert result.consented is True

    @pytest.mark.asyncio
    async def test_give_consent_commits(self, service):
        employee_id = uuid4()
        service.repo.give_consent = AsyncMock(return_value=MagicMock())

        await service.give_consent(employee_id)

        service._db.commit.assert_called_once()


class TestWithdrawConsent:
    @pytest.mark.asyncio
    async def test_withdraw_existing_consent(self, service):
        employee_id = uuid4()
        record = MagicMock(spec=GeofenceConsent)
        record.consented = False
        service.repo.withdraw_consent = AsyncMock(return_value=record)

        result = await service.withdraw_consent(employee_id)

        assert result is record
        service._db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_withdraw_no_record_raises_404(self, service):
        service.repo.withdraw_consent = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc:
            await service.withdraw_consent(uuid4())
        assert exc.value.status_code == 404


class TestGetConsentStatus:
    @pytest.mark.asyncio
    async def test_no_record_returns_not_consented(self, service):
        service.repo.get_for_employee = AsyncMock(return_value=None)

        status = await service.get_consent_status(uuid4())

        assert status["consented"] is False
        assert status["consent_given_at"] is None

    @pytest.mark.asyncio
    async def test_consented_record_returns_true(self, service):
        now = datetime.now(timezone.utc)
        record = MagicMock(spec=GeofenceConsent)
        record.consented = True
        record.consent_given_at = now
        record.consent_withdrawn_at = None
        service.repo.get_for_employee = AsyncMock(return_value=record)

        status = await service.get_consent_status(uuid4())

        assert status["consented"] is True
        assert status["consent_given_at"] == now


class TestAssertConsent:
    @pytest.mark.asyncio
    async def test_no_record_raises_451(self, service):
        service.repo.get_for_employee = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc:
            await service.assert_consent(uuid4())
        assert exc.value.status_code == 451

    @pytest.mark.asyncio
    async def test_withdrawn_consent_raises_451(self, service):
        record = MagicMock(spec=GeofenceConsent)
        record.consented = False
        service.repo.get_for_employee = AsyncMock(return_value=record)

        with pytest.raises(HTTPException) as exc:
            await service.assert_consent(uuid4())
        assert exc.value.status_code == 451

    @pytest.mark.asyncio
    async def test_active_consent_passes(self, service):
        record = MagicMock(spec=GeofenceConsent)
        record.consented = True
        service.repo.get_for_employee = AsyncMock(return_value=record)

        await service.assert_consent(uuid4())
