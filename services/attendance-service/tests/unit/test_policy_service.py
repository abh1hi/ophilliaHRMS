"""Unit tests for PolicyService — conflict detection, geofence_ids wiring, location tier."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException

from app.services.policy_service import PolicyService, _get_scope
from app.schemas.attendance import PolicyCreate, PolicyUpdate, AttendanceMethod
from app.models.attendance_policy import AttendancePolicy


def _make_db():
    db = AsyncMock()
    db.info = {"company_id": str(uuid4())}
    return db


@pytest.fixture
def db():
    return _make_db()


@pytest.fixture
def service(db):
    return PolicyService(db)


class TestGetScope:
    def test_employee_wins_over_location_and_department(self):
        eid, lid, did = uuid4(), uuid4(), uuid4()
        scope_type, scope_id = _get_scope(eid, lid, did)
        assert scope_type == "employee"
        assert scope_id == eid

    def test_location_wins_over_department(self):
        lid, did = uuid4(), uuid4()
        scope_type, scope_id = _get_scope(None, lid, did)
        assert scope_type == "location"
        assert scope_id == lid

    def test_department_when_no_employee_or_location(self):
        did = uuid4()
        scope_type, scope_id = _get_scope(None, None, did)
        assert scope_type == "department"
        assert scope_id == did

    def test_global_when_all_none(self):
        scope_type, scope_id = _get_scope(None, None, None)
        assert scope_type == "global"
        assert scope_id is None


class TestCreatePolicy:
    @pytest.mark.asyncio
    async def test_conflict_raises_409(self, service):
        data = PolicyCreate(method=AttendanceMethod.MANUAL)
        conflict = MagicMock(spec=AttendancePolicy)
        conflict.id = uuid4()
        service.repo.get_conflicting_policy = AsyncMock(return_value=conflict)

        with pytest.raises(HTTPException) as exc:
            await service.create_policy(data, changed_by=uuid4())
        assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_geofence_ids_wired_to_junction_repo(self, service):
        gid1, gid2 = uuid4(), uuid4()
        data = PolicyCreate(
            method=AttendanceMethod.GEOFENCE,
            geofence_ids=[gid1, gid2],
        )
        mock_policy = MagicMock(spec=AttendancePolicy)
        mock_policy.id = uuid4()
        mock_policy.company_id = uuid4()

        service.repo.get_conflicting_policy = AsyncMock(return_value=None)
        service.repo.create = AsyncMock(return_value=mock_policy)
        service.audit_repo.create = AsyncMock()
        service.geofence_repo.replace = AsyncMock()

        with patch("app.services.policy_service._invalidate_policy_cache", AsyncMock()):
            await service.create_policy(data, changed_by=uuid4())

        service.geofence_repo.replace.assert_called_once_with(mock_policy.id, [gid1, gid2])

    @pytest.mark.asyncio
    async def test_no_geofence_ids_skips_junction_write(self, service):
        data = PolicyCreate(method=AttendanceMethod.MANUAL)
        mock_policy = MagicMock(spec=AttendancePolicy)
        mock_policy.id = uuid4()
        mock_policy.company_id = uuid4()

        service.repo.get_conflicting_policy = AsyncMock(return_value=None)
        service.repo.create = AsyncMock(return_value=mock_policy)
        service.audit_repo.create = AsyncMock()
        service.geofence_repo.replace = AsyncMock()

        with patch("app.services.policy_service._invalidate_policy_cache", AsyncMock()):
            await service.create_policy(data, changed_by=uuid4())

        service.geofence_repo.replace.assert_not_called()


class TestUpdatePolicy:
    @pytest.mark.asyncio
    async def test_update_geofence_ids_calls_replace(self, service):
        gid = uuid4()
        policy_id = uuid4()
        data = PolicyUpdate(geofence_ids=[gid])

        existing = MagicMock(spec=AttendancePolicy)
        existing.employee_id = None
        existing.location_id = None
        existing.department_id = None
        existing.company_id = uuid4()

        service.repo.get_by_id = AsyncMock(return_value=existing)
        service.repo.update = AsyncMock(return_value=existing)
        service.audit_repo.create = AsyncMock()
        service.geofence_repo.replace = AsyncMock()

        with patch("app.services.policy_service._invalidate_policy_cache", AsyncMock()):
            await service.update_policy(policy_id, data, changed_by=uuid4())

        service.geofence_repo.replace.assert_called_once_with(existing.id, [gid])

    @pytest.mark.asyncio
    async def test_update_without_geofence_ids_skips_replace(self, service):
        policy_id = uuid4()
        data = PolicyUpdate(work_hours_per_day=9.0)

        existing = MagicMock(spec=AttendancePolicy)
        existing.employee_id = None
        existing.location_id = None
        existing.department_id = None
        existing.company_id = uuid4()

        service.repo.get_by_id = AsyncMock(return_value=existing)
        service.repo.update = AsyncMock(return_value=existing)
        service.audit_repo.create = AsyncMock()
        service.geofence_repo.replace = AsyncMock()

        with patch("app.services.policy_service._invalidate_policy_cache", AsyncMock()):
            await service.update_policy(policy_id, data, changed_by=uuid4())

        service.geofence_repo.replace.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_not_found_raises_404(self, service):
        service.repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await service.update_policy(uuid4(), PolicyUpdate(work_hours_per_day=9.0), uuid4())
        assert exc.value.status_code == 404
