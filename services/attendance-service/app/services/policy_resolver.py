"""Policy resolution: cascade lookup, Redis caching, and exception override."""
import json
import logging
from dataclasses import dataclass
from typing import Optional, List
from uuid import UUID
from datetime import date, time

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.policy_repository import PolicyRepository
from app.repositories.geofence_repository import GeofenceRepository
from app.repositories.policy_exception_repository import PolicyExceptionRepository
from app.core.config import settings

logger = logging.getLogger(__name__)

_POLICY_CACHE_TTL = 300  # seconds


@dataclass
class _CachedGeofence:
    """Lightweight stand-in for GeofenceLocation when deserializing from Redis."""
    id: str
    name: str
    latitude: float
    longitude: float
    radius_meters: int


def _serialize_geofences(geofences: List) -> List[dict]:
    return [
        {
            "id": str(g.id),
            "name": g.name,
            "latitude": g.latitude,
            "longitude": g.longitude,
            "radius_meters": g.radius_meters,
        }
        for g in (geofences or [])
    ]


def _deserialize_geofences(data: List[dict]) -> List[_CachedGeofence]:
    return [_CachedGeofence(**item) for item in (data or [])]


def _parse_time(value: Optional[str]) -> Optional[time]:
    if not value:
        return None
    try:
        parts = value.split(":")
        return time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)
    except Exception:
        return None


class PolicyResolver:
    """Resolves the effective attendance policy for an employee.

    Resolution order (highest priority first):
      1. Redis cache (5-min TTL, full resolved object)
      2. Active PolicyException (temporary per-employee override)
      3. Field-level cascade: employee → location → department → global → defaults

    Returns a 6-tuple:
      (method, geofences, work_hours_per_day, work_start_time, late_grace_period_minutes, allow_night_shift)

    where geofences is a List of GeofenceLocation (or _CachedGeofence from Redis).
    Clock-in succeeds if the employee is within ANY geofence in the list.
    """

    def __init__(self, db: AsyncSession):
        self.policy_repo = PolicyRepository(db)
        self.geofence_repo = GeofenceRepository(db)
        self.exception_repo = PolicyExceptionRepository(db)
        self._company_id = db.info.get("company_id")

    async def resolve(
        self,
        employee_id: UUID,
        department_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
    ) -> tuple[str, List, float, Optional[time], int, bool]:
        cache_key = (
            f"policy:resolve:{self._company_id}:{employee_id}"
            f":{location_id or 'none'}:{department_id or 'none'}"
        )
        cached = await self._read_cache(cache_key)
        if cached:
            return cached

        policy = await self.policy_repo.get_for_employee(employee_id, department_id, location_id)
        exception = await self.exception_repo.get_active_for_employee(employee_id, date.today())

        if exception:
            result = await self._result_from_exception(exception, policy)
        else:
            result = await self._result_from_policy(policy)

        await self._write_cache(cache_key, result)
        return result

    async def _result_from_exception(self, exception, policy) -> tuple:
        """Build result from active exception, inheriting unset fields from underlying policy."""
        geofences = await self._resolve_exception_geofences(exception, policy)
        return (
            exception.override_method or (policy.method if policy else "manual"),
            geofences,
            exception.override_work_hours or (
                policy.work_hours_per_day if policy else settings.DEFAULT_WORK_HOURS_PER_DAY
            ),
            exception.override_work_start_time or (policy.work_start_time if policy else None),
            exception.override_late_grace_minutes if exception.override_late_grace_minutes is not None
            else (policy.late_grace_period_minutes if policy else 0),
            policy.allow_night_shift if policy else False,
        )

    async def _resolve_exception_geofences(self, exception, policy) -> List:
        """Resolve geofences for an active exception: override_geofence_ids > override_geofence_id > policy."""
        if exception.override_geofence_ids:
            from uuid import UUID as _UUID
            geofences = []
            for gid in exception.override_geofence_ids:
                g = await self.geofence_repo.get_by_id(_UUID(gid))
                if g:
                    geofences.append(g)
            return geofences
        if exception.override_geofence_id:
            g = await self.geofence_repo.get_by_id(exception.override_geofence_id)
            return [g] if g else []
        return list(policy.geofences) if policy else []

    async def _result_from_policy(self, policy) -> tuple:
        """Build result from normal cascade policy (or hard defaults)."""
        if policy is None:
            return ("manual", [], settings.DEFAULT_WORK_HOURS_PER_DAY, None, 0, False)
        return (
            policy.method,
            list(policy.geofences),
            policy.work_hours_per_day,
            policy.work_start_time,
            policy.late_grace_period_minutes,
            policy.allow_night_shift,
        )

    async def _read_cache(self, cache_key: str) -> Optional[tuple]:
        try:
            from app.core.token_blacklist import _redis
            if _redis is None:
                return None
            raw = await _redis.get(cache_key)
            if not raw:
                return None
            data = json.loads(raw)
            return (
                data["method"],
                _deserialize_geofences(data.get("geofences", [])),
                data["work_hours_per_day"],
                _parse_time(data.get("work_start_time")),
                data.get("late_grace_period_minutes", 0),
                data.get("allow_night_shift", False),
            )
        except Exception:
            logger.debug("Policy cache read failed — falling back to DB", exc_info=True)
            return None

    async def _write_cache(self, cache_key: str, result: tuple) -> None:
        try:
            from app.core.token_blacklist import _redis
            if _redis is None:
                return
            method, geofences, work_hours, work_start, grace, allow_night_shift = result
            payload = {
                "method": method,
                "geofences": _serialize_geofences(geofences),
                "work_hours_per_day": work_hours,
                "work_start_time": work_start.isoformat() if work_start else None,
                "late_grace_period_minutes": grace,
                "allow_night_shift": allow_night_shift,
            }
            await _redis.set(cache_key, json.dumps(payload), ex=_POLICY_CACHE_TTL)
        except Exception:
            logger.debug("Policy cache write failed — continuing", exc_info=True)
