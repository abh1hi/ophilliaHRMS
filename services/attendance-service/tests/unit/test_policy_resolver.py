"""Unit tests for PolicyResolver — cascade, field inheritance, cache, multi-geofence."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import date, time

from app.services.policy_resolver import PolicyResolver, _CachedGeofence
from app.models.attendance_policy import AttendancePolicy
from app.models.policy_exception import PolicyException


def _make_db(company_id=None):
    db = AsyncMock()
    db.info = {"company_id": str(company_id or uuid4())}
    return db


def _make_policy(**kwargs):
    p = MagicMock(spec=AttendancePolicy)
    p.method = kwargs.get("method", "manual")
    p.geofences = kwargs.get("geofences", [])
    p.work_hours_per_day = kwargs.get("work_hours_per_day", 8.0)
    p.work_start_time = kwargs.get("work_start_time", time(9, 0))
    p.late_grace_period_minutes = kwargs.get("late_grace_period_minutes", 0)
    p.allow_night_shift = kwargs.get("allow_night_shift", False)
    p.geofence_id = kwargs.get("geofence_id", None)
    return p


def _make_exception(**kwargs):
    e = MagicMock(spec=PolicyException)
    e.override_method = kwargs.get("override_method", None)
    e.override_work_hours = kwargs.get("override_work_hours", None)
    e.override_work_start_time = kwargs.get("override_work_start_time", None)
    e.override_late_grace_minutes = kwargs.get("override_late_grace_minutes", None)
    e.override_geofence_id = kwargs.get("override_geofence_id", None)
    e.override_geofence_ids = kwargs.get("override_geofence_ids", None)
    return e


@pytest.fixture
def db():
    return _make_db()


@pytest.fixture
def resolver(db):
    return PolicyResolver(db)


class TestCacheHit:
    @pytest.mark.asyncio
    async def test_returns_cached_result_without_db_query(self, resolver):
        payload = json.dumps({
            "method": "geofence",
            "geofences": [{"id": str(uuid4()), "name": "HQ", "latitude": 1.0, "longitude": 2.0, "radius_meters": 100}],
            "work_hours_per_day": 8.0,
            "work_start_time": "09:00:00",
            "late_grace_period_minutes": 10,
            "allow_night_shift": False,
        })
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=payload)

        with patch("app.services.policy_resolver._redis", mock_redis):
            result = await resolver.resolve(uuid4())

        method, geofences, work_hours, work_start, grace, night = result
        assert method == "geofence"
        assert len(geofences) == 1
        assert isinstance(geofences[0], _CachedGeofence)
        assert grace == 10
        assert work_start == time(9, 0)
        resolver.policy_repo.get_for_employee.assert_not_called()


class TestNormalCascade:
    @pytest.mark.asyncio
    async def test_returns_employee_policy_fields(self, resolver):
        policy = _make_policy(method="both", work_hours_per_day=9.0, late_grace_period_minutes=15)
        resolver.policy_repo.get_for_employee = AsyncMock(return_value=policy)
        resolver.exception_repo.get_active_for_employee = AsyncMock(return_value=None)

        with patch("app.services.policy_resolver._redis", None):
            method, geofences, work_hours, _, grace, _ = await resolver.resolve(uuid4())

        assert method == "both"
        assert work_hours == 9.0
        assert grace == 15

    @pytest.mark.asyncio
    async def test_defaults_when_no_policy(self, resolver):
        resolver.policy_repo.get_for_employee = AsyncMock(return_value=None)
        resolver.exception_repo.get_active_for_employee = AsyncMock(return_value=None)

        with patch("app.services.policy_resolver._redis", None):
            method, geofences, work_hours, work_start, grace, night = await resolver.resolve(uuid4())

        assert method == "manual"
        assert geofences == []
        assert work_start is None
        assert grace == 0
        assert night is False


class TestExceptionFieldInheritance:
    @pytest.mark.asyncio
    async def test_exception_inherits_work_start_from_policy(self, resolver):
        """Bug #2: exception must not drop work_start_time from the underlying policy."""
        policy = _make_policy(work_start_time=time(8, 30), late_grace_period_minutes=10)
        exc = _make_exception(override_method="manual")

        resolver.policy_repo.get_for_employee = AsyncMock(return_value=policy)
        resolver.exception_repo.get_active_for_employee = AsyncMock(return_value=exc)

        with patch("app.services.policy_resolver._redis", None):
            _, _, _, work_start, grace, _ = await resolver.resolve(uuid4())

        assert work_start == time(8, 30)
        assert grace == 10

    @pytest.mark.asyncio
    async def test_exception_override_work_start_takes_precedence(self, resolver):
        policy = _make_policy(work_start_time=time(9, 0))
        exc = _make_exception(override_work_start_time=time(10, 0))

        resolver.policy_repo.get_for_employee = AsyncMock(return_value=policy)
        resolver.exception_repo.get_active_for_employee = AsyncMock(return_value=exc)

        with patch("app.services.policy_resolver._redis", None):
            _, _, _, work_start, _, _ = await resolver.resolve(uuid4())

        assert work_start == time(10, 0)

    @pytest.mark.asyncio
    async def test_exception_override_late_grace_takes_precedence(self, resolver):
        policy = _make_policy(late_grace_period_minutes=5)
        exc = _make_exception(override_late_grace_minutes=30)

        resolver.policy_repo.get_for_employee = AsyncMock(return_value=policy)
        resolver.exception_repo.get_active_for_employee = AsyncMock(return_value=exc)

        with patch("app.services.policy_resolver._redis", None):
            _, _, _, _, grace, _ = await resolver.resolve(uuid4())

        assert grace == 30

    @pytest.mark.asyncio
    async def test_exception_override_geofence_ids_takes_precedence(self, resolver):
        """override_geofence_ids list should replace policy geofences."""
        geofence_id = str(uuid4())
        policy = _make_policy(geofences=[MagicMock()])
        exc = _make_exception(override_geofence_ids=[geofence_id])

        mock_geofence = MagicMock()
        resolver.policy_repo.get_for_employee = AsyncMock(return_value=policy)
        resolver.exception_repo.get_active_for_employee = AsyncMock(return_value=exc)
        resolver.geofence_repo.get_by_id = AsyncMock(return_value=mock_geofence)

        with patch("app.services.policy_resolver._redis", None):
            _, geofences, _, _, _, _ = await resolver.resolve(uuid4())

        assert geofences == [mock_geofence]

    @pytest.mark.asyncio
    async def test_exception_inherits_allow_night_shift_from_policy(self, resolver):
        policy = _make_policy(allow_night_shift=True)
        exc = _make_exception()

        resolver.policy_repo.get_for_employee = AsyncMock(return_value=policy)
        resolver.exception_repo.get_active_for_employee = AsyncMock(return_value=exc)

        with patch("app.services.policy_resolver._redis", None):
            _, _, _, _, _, allow_night = await resolver.resolve(uuid4())

        assert allow_night is True


class TestCacheWrite:
    @pytest.mark.asyncio
    async def test_result_written_to_cache_on_miss(self, resolver):
        policy = _make_policy()
        resolver.policy_repo.get_for_employee = AsyncMock(return_value=policy)
        resolver.exception_repo.get_active_for_employee = AsyncMock(return_value=None)

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        with patch("app.services.policy_resolver._redis", mock_redis):
            await resolver.resolve(uuid4())

        mock_redis.set.assert_called_once()
        key, payload_str = mock_redis.set.call_args[0][:2]
        assert "policy:resolve:" in key
        payload = json.loads(payload_str)
        assert "method" in payload
        assert "geofences" in payload
        assert "allow_night_shift" in payload
