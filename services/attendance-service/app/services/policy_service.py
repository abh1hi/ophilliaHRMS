"""PolicyService: CRUD for AttendancePolicy with conflict detection, audit trail,
and Redis cache invalidation.

Shared helpers (_policy_to_dict, _invalidate_policy_cache, _get_scope) are
imported by policy_template_service.py and policy_exception_service.py.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_policy import AttendancePolicy
from app.models.policy_audit_log import PolicyAuditLog
from app.repositories.policy_repository import PolicyRepository
from app.repositories.policy_audit_repository import PolicyAuditRepository
from app.repositories.policy_geofence_repository import PolicyGeofenceRepository
from app.schemas.attendance import PolicyCreate, PolicyUpdate

logger = logging.getLogger(__name__)

_ERR_NO_FIELDS = "No fields to update"


def _policy_to_dict(policy: AttendancePolicy) -> dict:
    """Serialize a policy to a plain dict for audit logging."""
    return {
        "id": str(policy.id),
        "company_id": str(policy.company_id),
        "department_id": str(policy.department_id) if policy.department_id else None,
        "employee_id": str(policy.employee_id) if policy.employee_id else None,
        "method": policy.method,
        "geofence_id": str(policy.geofence_id) if policy.geofence_id else None,
        "work_start_time": policy.work_start_time.isoformat() if policy.work_start_time else None,
        "work_hours_per_day": policy.work_hours_per_day,
        "auto_close_time": policy.auto_close_time.isoformat() if policy.auto_close_time else None,
        "task_planning_grace_minutes": policy.task_planning_grace_minutes,
        "allow_night_shift": policy.allow_night_shift,
        "max_shifts_per_day": policy.max_shifts_per_day,
        "late_grace_period_minutes": policy.late_grace_period_minutes,
        "created_at": policy.created_at.isoformat() if policy.created_at else None,
        "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
    }


async def _invalidate_policy_cache(company_id) -> None:
    """Delete all policy:resolve:{company_id}:* keys from Redis."""
    try:
        from app.core.token_blacklist import _redis
        if _redis is None:
            return
        pattern = f"policy:resolve:{company_id}:*"
        keys = [key async for key in _redis.scan_iter(pattern)]
        if keys:
            await _redis.delete(*keys)
            logger.debug(f"Invalidated {len(keys)} policy cache entries for company {company_id}")
    except Exception:
        logger.warning(
            "Failed to invalidate policy cache — continuing without cache invalidation",
            exc_info=True,
        )


def _get_scope(data_employee_id, data_location_id, data_department_id) -> tuple[str, Optional[UUID]]:
    """Determine scope_type and scope_id from policy data (priority order)."""
    if data_employee_id:
        return "employee", data_employee_id
    if data_location_id:
        return "location", data_location_id
    if data_department_id:
        return "department", data_department_id
    return "global", None


class PolicyService:
    """CRUD for AttendancePolicy with conflict detection and audit trail."""

    def __init__(self, db: AsyncSession):
        self.repo = PolicyRepository(db)
        self.audit_repo = PolicyAuditRepository(db)
        self.geofence_repo = PolicyGeofenceRepository(db)

    async def create_policy(self, data: PolicyCreate, changed_by: UUID) -> AttendancePolicy:
        scope_type, scope_id = _get_scope(data.employee_id, getattr(data, "location_id", None), data.department_id)
        conflict = await self.repo.get_conflicting_policy(scope_type, scope_id)
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"A policy already exists for this {scope_type} scope. "
                    f"Update the existing policy (id={conflict.id}) instead."
                ),
            )

        policy = AttendancePolicy(
            department_id=data.department_id,
            employee_id=data.employee_id,
            location_id=getattr(data, "location_id", None),
            method=data.method.value,
            work_start_time=data.work_start_time,
            work_hours_per_day=data.work_hours_per_day,
            auto_close_time=data.auto_close_time,
            task_planning_grace_minutes=data.task_planning_grace_minutes,
            allow_night_shift=data.allow_night_shift,
            max_shifts_per_day=data.max_shifts_per_day,
            late_grace_period_minutes=data.late_grace_period_minutes,
        )
        policy = await self.repo.create(policy)

        geofence_ids = getattr(data, "geofence_ids", None) or []
        if geofence_ids:
            await self.geofence_repo.replace(policy.id, geofence_ids)

        await self.audit_repo.create(PolicyAuditLog(
            policy_id=policy.id,
            action="created",
            changed_by=changed_by,
            old_value=None,
            new_value=_policy_to_dict(policy),
        ))

        await _invalidate_policy_cache(policy.company_id)
        return policy

    async def list_policies(self, skip: int = 0, limit: int = 100) -> tuple[list, int]:
        return await self.repo.get_all(skip=skip, limit=limit)

    async def update_policy(
        self, policy_id: UUID, data: PolicyUpdate, changed_by: UUID
    ) -> AttendancePolicy:
        policy = await self.repo.get_by_id(policy_id)
        if not policy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")

        updates = data.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=_ERR_NO_FIELDS)

        if "method" in updates and updates["method"] is not None:
            updates["method"] = updates["method"].value

        new_employee_id = updates.get("employee_id", policy.employee_id)
        new_location_id = updates.get("location_id", policy.location_id)
        new_department_id = updates.get("department_id", policy.department_id)
        scope_changed = "employee_id" in updates or "location_id" in updates or "department_id" in updates
        if scope_changed:
            scope_type, scope_id = _get_scope(new_employee_id, new_location_id, new_department_id)
            conflict = await self.repo.get_conflicting_policy(
                scope_type, scope_id, exclude_id=policy_id
            )
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A policy already exists for this {scope_type} scope.",
                )

        old_value = _policy_to_dict(policy)
        geofence_ids = updates.pop("geofence_ids", None)
        policy = await self.repo.update(policy, updates)

        if geofence_ids is not None:
            await self.geofence_repo.replace(policy.id, geofence_ids)

        await self.audit_repo.create(PolicyAuditLog(
            policy_id=policy_id,
            action="updated",
            changed_by=changed_by,
            old_value=old_value,
            new_value=_policy_to_dict(policy),
        ))

        await _invalidate_policy_cache(policy.company_id)
        return policy

    async def delete_policy(self, policy_id: UUID, changed_by: UUID) -> None:
        policy = await self.repo.get_by_id(policy_id)
        if not policy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")

        old_value = _policy_to_dict(policy)
        company_id = policy.company_id

        await self.repo.delete(policy)

        await self.audit_repo.create(PolicyAuditLog(
            policy_id=policy_id,
            action="deleted",
            changed_by=changed_by,
            old_value=old_value,
            new_value=None,
        ))

        await _invalidate_policy_cache(company_id)

    async def get_audit_log(
        self, policy_id: UUID, skip: int = 0, limit: int = 50
    ) -> tuple[list, int]:
        return await self.audit_repo.get_by_policy(policy_id, skip=skip, limit=limit)
