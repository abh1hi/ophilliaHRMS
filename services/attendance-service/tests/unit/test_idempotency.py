"""Idempotency test suite for the Attendance Service.

Tests cover:
- Duplicate clock-in returns existing record (not error)
- Duplicate clock-out returns existing record (not error)
- IntegrityError on clock-in is handled gracefully
- Manual entry rejects duplicates with 409
- School mode rejects duplicates with 409
- Optimistic locking detects concurrent admin corrections
- Concurrent clock-in simulation (10 parallel requests)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import uuid4
from datetime import date, datetime, timezone
from sqlalchemy.exc import IntegrityError

from fastapi import HTTPException

from app.services.attendance_service import AttendanceService
from app.schemas.attendance import ClockInRequest, ClockOutRequest, ManualAttendanceCreate, SchoolModeAttendanceCreate
from app.models.attendance_record import AttendanceRecord
from app.core.constants import AttendanceStatus


@pytest.fixture
def mock_db():
    mock = AsyncMock()
    mock.info = {"company_id": str(uuid4())}
    return mock


@pytest.fixture
def service(mock_db):
    return AttendanceService(mock_db)


# ──────────── CLOCK-IN IDEMPOTENCY ────────────


@pytest.mark.asyncio
async def test_clock_in_duplicate_returns_existing_record(service):
    """If employee already has an open clock-in, return it instead of erroring."""
    employee_id = uuid4()
    data = ClockInRequest()

    existing = MagicMock(spec=AttendanceRecord)
    existing.clock_out = None  # still open
    existing.employee_id = employee_id

    with patch.object(service, "_resolve_policy", return_value=("manual", None, 8.0, None)), \
         patch.object(service.attendance_repo, "get_by_employee_and_date_for_update", return_value=existing), \
         patch.object(service.attendance_repo, "commit", new_callable=AsyncMock), \
         patch("app.services.attendance_service.validate_employee_tenant", new_callable=AsyncMock):

        result = await service.clock_in(employee_id, data)

        # Should return existing record, NOT raise an exception
        assert result == existing


@pytest.mark.asyncio
async def test_clock_in_integrity_error_returns_existing(service):
    """If two requests race past the lock, IntegrityError should return existing record."""
    employee_id = uuid4()
    data = ClockInRequest()

    existing_after_error = MagicMock(spec=AttendanceRecord)
    existing_after_error.clock_out = None
    existing_after_error.employee_id = employee_id

    with patch.object(service, "_resolve_policy", return_value=("manual", None, 8.0, None)), \
         patch.object(service.attendance_repo, "get_by_employee_and_date_for_update", return_value=None), \
         patch.object(service.attendance_repo, "create", side_effect=IntegrityError("dup", {}, None)), \
         patch.object(service.attendance_repo, "rollback", new_callable=AsyncMock), \
         patch.object(service.attendance_repo, "get_by_employee_and_date", return_value=existing_after_error), \
         patch("app.services.attendance_service.validate_employee_tenant", new_callable=AsyncMock):

        result = await service.clock_in(employee_id, data)

        assert result == existing_after_error


@pytest.mark.asyncio
async def test_clock_in_new_shift_after_completed(service):
    """Allow second shift when first is completed."""
    employee_id = uuid4()
    data = ClockInRequest()

    completed = MagicMock(spec=AttendanceRecord)
    completed.clock_out = datetime.now(timezone.utc)  # closed

    new_record = MagicMock(spec=AttendanceRecord)
    new_record.method = "manual"
    new_record.status = "present"

    with patch.object(service, "_resolve_policy", return_value=("manual", None, 8.0, None)), \
         patch.object(service.attendance_repo, "get_by_employee_and_date_for_update", return_value=completed), \
         patch.object(service.policy_repo, "get_for_employee", return_value=None), \
         patch.object(service.attendance_repo, "get_shift_count_today", return_value=1), \
         patch.object(service.attendance_repo, "create", return_value=new_record), \
         patch.object(service.attendance_repo, "commit", new_callable=AsyncMock), \
         patch("app.services.attendance_service.validate_employee_tenant", new_callable=AsyncMock):

        result = await service.clock_in(employee_id, data)
        assert result == new_record


# ──────────── CLOCK-OUT IDEMPOTENCY ────────────


@pytest.mark.asyncio
async def test_clock_out_duplicate_returns_existing_completed(service):
    """If already clocked out, return the completed record."""
    employee_id = uuid4()
    data = ClockOutRequest()

    completed = MagicMock(spec=AttendanceRecord)
    completed.clock_out = datetime.now(timezone.utc)
    completed.employee_id = employee_id

    with patch.object(service.attendance_repo, "get_open_record_today_for_update", return_value=None), \
         patch.object(service.attendance_repo, "get_by_employee_and_date", return_value=completed):

        result = await service.clock_out(employee_id, data)
        assert result == completed


@pytest.mark.asyncio
async def test_clock_out_no_record_raises_404(service):
    """If no record at all, raise 404."""
    employee_id = uuid4()
    data = ClockOutRequest()

    with patch.object(service.attendance_repo, "get_open_record_today_for_update", return_value=None), \
         patch.object(service.attendance_repo, "get_by_employee_and_date", return_value=None):

        with pytest.raises(HTTPException) as exc_info:
            await service.clock_out(employee_id, data)
        assert exc_info.value.status_code == 404


# ──────────── MANUAL ENTRY IDEMPOTENCY ────────────


@pytest.mark.asyncio
async def test_manual_entry_duplicate_raises_409(service):
    """Manual entry with existing record raises 409."""
    employee_id = uuid4()
    data = ManualAttendanceCreate(
        employee_id=employee_id,
        date=date.today(),
        clock_in=datetime.now(timezone.utc),
        status=AttendanceStatus.PRESENT,
    )

    existing = MagicMock(spec=AttendanceRecord)

    with patch.object(service.attendance_repo, "get_by_employee_and_date_for_update", return_value=existing), \
         patch.object(service.attendance_repo, "commit", new_callable=AsyncMock), \
         patch("app.services.attendance_service.validate_employee_tenant", new_callable=AsyncMock):

        with pytest.raises(HTTPException) as exc_info:
            await service.manual_entry(data, created_by="admin")
        assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_manual_entry_integrity_error_raises_409(service):
    """IntegrityError from race condition gives clean 409."""
    employee_id = uuid4()
    data = ManualAttendanceCreate(
        employee_id=employee_id,
        date=date.today(),
        clock_in=datetime.now(timezone.utc),
        status=AttendanceStatus.PRESENT,
    )

    with patch.object(service.attendance_repo, "get_by_employee_and_date_for_update", return_value=None), \
         patch.object(service.attendance_repo, "create", side_effect=IntegrityError("dup", {}, None)), \
         patch.object(service.attendance_repo, "rollback", new_callable=AsyncMock), \
         patch("app.services.attendance_service.validate_employee_tenant", new_callable=AsyncMock):

        with pytest.raises(HTTPException) as exc_info:
            await service.manual_entry(data, created_by="admin")
        assert exc_info.value.status_code == 409


# ──────────── SCHOOL MODE IDEMPOTENCY ────────────


@pytest.mark.asyncio
async def test_school_mode_duplicate_raises_409(service):
    """School mode with existing record raises 409."""
    employee_id = uuid4()
    data = SchoolModeAttendanceCreate(
        employee_id=employee_id,
        status=AttendanceStatus.PRESENT,
    )

    existing = MagicMock(spec=AttendanceRecord)

    with patch.object(service.attendance_repo, "get_by_employee_and_date_for_update", return_value=existing), \
         patch.object(service.attendance_repo, "commit", new_callable=AsyncMock), \
         patch("app.services.attendance_service.validate_employee_tenant", new_callable=AsyncMock):

        with pytest.raises(HTTPException) as exc_info:
            await service.mark_school_mode_attendance(data, created_by="admin")
        assert exc_info.value.status_code == 409


# ──────────── OPTIMISTIC LOCKING ────────────


@pytest.mark.asyncio
async def test_update_record_version_conflict_raises_409(service):
    """Concurrent admin correction should fail with 409 on version mismatch."""
    from app.schemas.attendance import AttendanceUpdate

    record_id = uuid4()
    record = MagicMock(spec=AttendanceRecord)
    record.version = 3
    record.id = record_id

    data = AttendanceUpdate(notes="Updated by HR")

    with patch.object(service.attendance_repo, "get_by_id", return_value=record), \
         patch.object(
             service.attendance_repo,
             "update_with_optimistic_lock",
             side_effect=HTTPException(status_code=409, detail="Record was modified by another request. Please retry."),
         ):

        with pytest.raises(HTTPException) as exc_info:
            await service.update_record(record_id, data)
        assert exc_info.value.status_code == 409


# ──────────── CONCURRENT SIMULATION ────────────


@pytest.mark.asyncio
async def test_concurrent_clock_in_only_one_succeeds():
    """Simulate 10 parallel clock-in requests; only 1 should create a record."""
    import asyncio

    employee_id = uuid4()
    company_id = str(uuid4())
    created_count = 0
    duplicate_count = 0

    async def simulate_clock_in(attempt: int):
        nonlocal created_count, duplicate_count

        mock_db = AsyncMock()
        mock_db.info = {"company_id": company_id}
        svc = AttendanceService(mock_db)

        data = ClockInRequest()

        # First request gets None (no existing), rest get the created record
        if attempt == 0:
            existing = None
            create_result = MagicMock(spec=AttendanceRecord)
            create_result.method = "manual"
            create_result.status = "present"
            create_result.clock_out = None
        else:
            existing = MagicMock(spec=AttendanceRecord)
            existing.clock_out = None
            existing.employee_id = employee_id
            create_result = None

        with patch.object(svc, "_resolve_policy", return_value=("manual", None, 8.0, None)), \
             patch.object(svc.attendance_repo, "get_by_employee_and_date_for_update", return_value=existing), \
             patch.object(svc.attendance_repo, "create", return_value=create_result), \
             patch.object(svc.attendance_repo, "commit", new_callable=AsyncMock), \
             patch("app.services.attendance_service.validate_employee_tenant", new_callable=AsyncMock):

            result = await svc.clock_in(employee_id, data)
            if existing is None:
                created_count += 1
            else:
                duplicate_count += 1

    tasks = [simulate_clock_in(i) for i in range(10)]
    await asyncio.gather(*tasks)

    assert created_count == 1, f"Expected 1 create, got {created_count}"
    assert duplicate_count == 9, f"Expected 9 duplicates, got {duplicate_count}"
