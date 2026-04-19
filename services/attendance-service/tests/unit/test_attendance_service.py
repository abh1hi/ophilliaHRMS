"""Unit tests for AttendanceService — clock-in/out, night-shift guard, task grace, GDPR consent."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import date, datetime, timezone, timedelta, time

from fastapi import HTTPException

from app.services.attendance_service import AttendanceService, GeofenceService
from app.schemas.attendance import ClockInRequest, ClockOutRequest, GeofenceCreate
from app.models.attendance_record import AttendanceRecord
from app.models.geofence_location import GeofenceLocation


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.info = {"company_id": str(uuid4())}
    return db


@pytest.fixture
def service(mock_db):
    return AttendanceService(mock_db)


# ──────────── CLOCK IN ────────────

class TestClockIn:
    @pytest.mark.asyncio
    async def test_clock_in_success_manual(self, service):
        """Should create a record when no existing record and method=manual."""
        data = ClockInRequest()
        mock_record = MagicMock(spec=AttendanceRecord)
        mock_record.method = "manual"
        mock_record.status = "present"

        service._policy_resolver.resolve = AsyncMock(
            return_value=("manual", [], 8.0, None, 0, False)
        )
        service.attendance_repo.get_by_employee_and_date_for_update = AsyncMock(return_value=None)
        service.attendance_repo.create = AsyncMock(return_value=mock_record)
        service.attendance_repo.commit = AsyncMock()

        result = await service.clock_in(uuid4(), data)
        assert result.method == "manual"
        service.attendance_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_clock_in_idempotent_returns_existing(self, service):
        """Should return existing open record instead of creating a duplicate."""
        data = ClockInRequest()
        existing = MagicMock(spec=AttendanceRecord)
        existing.clock_out = None

        service._policy_resolver.resolve = AsyncMock(
            return_value=("manual", [], 8.0, None, 0, False)
        )
        service.attendance_repo.get_by_employee_and_date_for_update = AsyncMock(return_value=existing)
        service.attendance_repo.commit = AsyncMock()

        result = await service.clock_in(uuid4(), data)
        assert result is existing
        service.attendance_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_clock_in_late_status_applied(self, service):
        """Should set status=late when clock-in is after grace end."""
        data = ClockInRequest()

        work_start = time(9, 0)
        late_now = datetime(2026, 4, 1, 9, 31, 0, tzinfo=timezone.utc)

        service._policy_resolver.resolve = AsyncMock(
            return_value=("manual", [], 8.0, work_start, 0, False)
        )
        service.attendance_repo.get_by_employee_and_date_for_update = AsyncMock(return_value=None)
        service.attendance_repo.commit = AsyncMock()

        captured = {}

        def capture_create(record):
            captured["status"] = record.status
            return record

        service.attendance_repo.create = AsyncMock(side_effect=capture_create)

        with patch("app.services.attendance_service.datetime") as mock_dt:
            mock_dt.now.return_value = late_now
            mock_dt.combine = datetime.combine
            await service.clock_in(uuid4(), data)

        assert captured.get("status") == "late"


# ──────────── CLOCK OUT ────────────

class TestClockOut:
    @pytest.mark.asyncio
    async def test_clock_out_no_open_record_raises_404(self, service):
        data = ClockOutRequest()
        service.attendance_repo.get_open_record_today_for_update = AsyncMock(return_value=None)
        service.attendance_repo.get_by_employee_and_date = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc:
            await service.clock_out(uuid4(), data)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_clock_out_idempotent_returns_existing(self, service):
        data = ClockOutRequest()
        existing = MagicMock(spec=AttendanceRecord)
        existing.clock_out = datetime.now(timezone.utc)

        service.attendance_repo.get_open_record_today_for_update = AsyncMock(return_value=None)
        service.attendance_repo.get_by_employee_and_date = AsyncMock(return_value=existing)

        result = await service.clock_out(uuid4(), data)
        assert result is existing


# ──────────── NIGHT SHIFT GUARD (Bug #1) ────────────

class TestNightShiftCheck:
    def test_same_day_always_passes(self, service):
        """Clock-out same day as clock-in — never a night shift."""
        record = MagicMock(spec=AttendanceRecord)
        today = date.today()
        record.clock_in = datetime(today.year, today.month, today.day, 9, 0, tzinfo=timezone.utc)

        with patch("app.services.attendance_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(today.year, today.month, today.day, 18, 0, tzinfo=timezone.utc)
            mock_dt.now.return_value.date.return_value = today
            service._check_night_shift(record, allow_night_shift=False)

    def test_midnight_span_with_night_shift_disabled_raises_422(self, service):
        """Shift spanning midnight when allow_night_shift=False must raise 422."""
        yesterday = date.today() - timedelta(days=1)
        record = MagicMock(spec=AttendanceRecord)
        record.clock_in = datetime(yesterday.year, yesterday.month, yesterday.day,
                                   23, 0, tzinfo=timezone.utc)

        with pytest.raises(HTTPException) as exc:
            service._check_night_shift(record, allow_night_shift=False)
        assert exc.value.status_code == 422

    def test_midnight_span_with_night_shift_enabled_passes(self, service):
        """Shift spanning midnight is allowed when allow_night_shift=True."""
        yesterday = date.today() - timedelta(days=1)
        record = MagicMock(spec=AttendanceRecord)
        record.clock_in = datetime(yesterday.year, yesterday.month, yesterday.day,
                                   23, 0, tzinfo=timezone.utc)
        service._check_night_shift(record, allow_night_shift=True)


# ──────────── TASK GRACE ENFORCEMENT (Bug #5) ────────────

class TestTaskGracePeriod:
    @pytest.mark.asyncio
    async def test_within_grace_no_flag(self, service):
        """No note appended when first task added within grace window."""
        record_id = uuid4()
        employee_id = uuid4()

        record = MagicMock(spec=AttendanceRecord)
        record.id = record_id
        record.employee_id = employee_id
        record.state = "punched_in"
        record.notes = None
        record.clock_in = datetime.now(timezone.utc) - timedelta(minutes=10)

        task = MagicMock()
        task.status = "pending"

        policy = MagicMock()
        policy.task_planning_grace_minutes = 30.0

        service.attendance_repo.get_by_id = AsyncMock(return_value=record)
        service.task_repo.get_by_record = AsyncMock(return_value=[task])
        service.policy_repo.get_for_employee = AsyncMock(return_value=policy)
        service.attendance_repo.update = AsyncMock(return_value=record)
        service.attendance_repo.commit = AsyncMock()

        await service.update_state(record_id, employee_id)

        update_calls = service.attendance_repo.update.call_args_list
        note_updates = [c for c in update_calls if "notes" in (c[0][1] if c[0] else c[1])]
        assert not note_updates

    @pytest.mark.asyncio
    async def test_past_grace_appends_flag_note(self, service):
        """LATE_TASK_ENTRY note appended when first task added past grace window."""
        record_id = uuid4()
        employee_id = uuid4()

        record = MagicMock(spec=AttendanceRecord)
        record.id = record_id
        record.employee_id = employee_id
        record.state = "punched_in"
        record.notes = None
        record.clock_in = datetime.now(timezone.utc) - timedelta(minutes=45)

        task = MagicMock()

        policy = MagicMock()
        policy.task_planning_grace_minutes = 30.0

        service.attendance_repo.get_by_id = AsyncMock(return_value=record)
        service.task_repo.get_by_record = AsyncMock(return_value=[task])
        service.policy_repo.get_for_employee = AsyncMock(return_value=policy)
        service.attendance_repo.update = AsyncMock(return_value=record)
        service.attendance_repo.commit = AsyncMock()

        await service.update_state(record_id, employee_id)

        all_updates = [
            call[0][1] if call[0] else call[1]
            for call in service.attendance_repo.update.call_args_list
        ]
        note_update = next((u for u in all_updates if "notes" in u), None)
        assert note_update is not None
        assert "LATE_TASK_ENTRY" in note_update["notes"]

    @pytest.mark.asyncio
    async def test_second_task_no_flag(self, service):
        """Grace check only fires on first task (punched_in → active transition)."""
        record_id = uuid4()
        employee_id = uuid4()

        record = MagicMock(spec=AttendanceRecord)
        record.id = record_id
        record.employee_id = employee_id
        record.state = "active"
        record.notes = None
        record.clock_in = datetime.now(timezone.utc) - timedelta(minutes=60)

        service.attendance_repo.get_by_id = AsyncMock(return_value=record)
        service.task_repo.get_by_record = AsyncMock(return_value=[MagicMock(), MagicMock()])
        service.attendance_repo.update = AsyncMock(return_value=record)
        service.attendance_repo.commit = AsyncMock()

        await service.update_state(record_id, employee_id)

        update_calls = [
            call[0][1] if call[0] else call[1]
            for call in service.attendance_repo.update.call_args_list
        ]
        note_updates = [u for u in update_calls if "notes" in u]
        assert not note_updates


# ──────────── GDPR CONSENT GUARD (Phase 2) ────────────

class TestGdprConsentGuard:
    @pytest.mark.asyncio
    async def test_geofence_clock_in_without_consent_raises_451(self, service):
        """Clock-in via geofence method must raise HTTP 451 when consent not given."""
        employee_id = uuid4()
        data = ClockInRequest(latitude=12.9, longitude=77.6)

        service._policy_resolver.resolve = AsyncMock(
            return_value=("geofence", [MagicMock()], 8.0, None, 0, False)
        )
        service.attendance_repo.get_by_employee_and_date_for_update = AsyncMock(return_value=None)
        service._geofence_validator.validate = AsyncMock()

        service._geofence_consent_service = AsyncMock()
        service._geofence_consent_service.assert_consent = AsyncMock(
            side_effect=HTTPException(status_code=451, detail="Consent required")
        )

        with pytest.raises(HTTPException) as exc:
            await service.clock_in(employee_id, data)
        assert exc.value.status_code == 451

    @pytest.mark.asyncio
    async def test_manual_clock_in_skips_consent_check(self, service):
        """Manual clock-in must NOT call assert_consent."""
        employee_id = uuid4()
        data = ClockInRequest()
        mock_record = MagicMock(spec=AttendanceRecord)
        mock_record.method = "manual"

        service._policy_resolver.resolve = AsyncMock(
            return_value=("manual", [], 8.0, None, 0, False)
        )
        service.attendance_repo.get_by_employee_and_date_for_update = AsyncMock(return_value=None)
        service.attendance_repo.create = AsyncMock(return_value=mock_record)
        service.attendance_repo.commit = AsyncMock()

        consent_mock = AsyncMock()
        service._geofence_consent_service = consent_mock

        await service.clock_in(employee_id, data)

        consent_mock.assert_consent.assert_not_called()
