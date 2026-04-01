"""Policy-related business logic.

Contains three service classes:
  - PolicyService      — CRUD for AttendancePolicy with conflict detection,
                         audit trail, and Redis cache invalidation.
  - PolicyTemplateService — CRUD for PolicyTemplate + apply-to-department.
  - PolicyExceptionService — CRUD for PolicyException (employee-level exemptions).
"""

import json
import logging
from typing import Optional
from uuid import UUID
from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_policy import AttendancePolicy
from app.models.policy_audit_log import PolicyAuditLog
from app.models.policy_template import PolicyTemplate
from app.models.policy_exception import PolicyException
from app.repositories.policy_repository import PolicyRepository
from app.repositories.policy_audit_repository import PolicyAuditRepository
from app.repositories.policy_template_repository import PolicyTemplateRepository
from app.repositories.policy_exception_repository import PolicyExceptionRepository
from app.schemas.attendance import (
    PolicyCreate,
    PolicyUpdate,
    PolicyTemplateCreate,
    PolicyTemplateUpdate,
    PolicyExceptionCreate,
    PolicyExceptionUpdate,
)

logger = logging.getLogger(__name__)


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
        logger.warning("Failed to invalidate policy cache — continuing without cache invalidation", exc_info=True)


def _get_scope(data_employee_id, data_department_id) -> tuple[str, Optional[UUID]]:
    """Determine scope_type and scope_id from policy data."""
    if data_employee_id:
        return "employee", data_employee_id
    if data_department_id:
        return "department", data_department_id
    return "global", None


# ──────────────────────────────────────────────────────────────
# PolicyService
# ──────────────────────────────────────────────────────────────

class PolicyService:
    """Business logic for managing AttendancePolicy records."""

    def __init__(self, db: AsyncSession):
        self.repo = PolicyRepository(db)
        self.audit_repo = PolicyAuditRepository(db)

    async def create_policy(self, data: PolicyCreate, changed_by: UUID) -> AttendancePolicy:
        scope_type, scope_id = _get_scope(data.employee_id, data.department_id)
        conflict = await self.repo.get_conflicting_policy(scope_type, scope_id)
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A policy already exists for this {scope_type} scope. "
                       f"Update the existing policy (id={conflict.id}) instead.",
            )

        policy = AttendancePolicy(
            department_id=data.department_id,
            employee_id=data.employee_id,
            method=data.method.value,
            geofence_id=data.geofence_id,
            work_start_time=data.work_start_time,
            work_hours_per_day=data.work_hours_per_day,
            auto_close_time=data.auto_close_time,
            task_planning_grace_minutes=data.task_planning_grace_minutes,
            allow_night_shift=data.allow_night_shift,
            max_shifts_per_day=data.max_shifts_per_day,
            late_grace_period_minutes=data.late_grace_period_minutes,
        )
        policy = await self.repo.create(policy)

        # Audit log
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update"
            )
        if "method" in updates and updates["method"] is not None:
            updates["method"] = updates["method"].value

        # Conflict check if scope is changing
        new_employee_id = updates.get("employee_id", policy.employee_id)
        new_department_id = updates.get("department_id", policy.department_id)
        scope_changed = (
            "employee_id" in updates or "department_id" in updates
        )
        if scope_changed:
            scope_type, scope_id = _get_scope(new_employee_id, new_department_id)
            conflict = await self.repo.get_conflicting_policy(scope_type, scope_id, exclude_id=policy_id)
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A policy already exists for this {scope_type} scope.",
                )

        old_value = _policy_to_dict(policy)
        policy = await self.repo.update(policy, updates)

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


# ──────────────────────────────────────────────────────────────
# PolicyTemplateService
# ──────────────────────────────────────────────────────────────

class PolicyTemplateService:
    """Business logic for managing reusable PolicyTemplate records."""

    def __init__(self, db: AsyncSession):
        self.template_repo = PolicyTemplateRepository(db)
        self.policy_repo = PolicyRepository(db)
        self.audit_repo = PolicyAuditRepository(db)

    async def create_template(
        self, data: PolicyTemplateCreate, changed_by: UUID
    ) -> PolicyTemplate:
        existing = await self.template_repo.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A policy template named '{data.name}' already exists.",
            )
        template = PolicyTemplate(
            name=data.name,
            description=data.description,
            method=data.method.value if hasattr(data.method, "value") else data.method,
            geofence_id=data.geofence_id,
            work_start_time=data.work_start_time,
            work_hours_per_day=data.work_hours_per_day,
            auto_close_time=data.auto_close_time,
            task_planning_grace_minutes=data.task_planning_grace_minutes,
            allow_night_shift=data.allow_night_shift,
            max_shifts_per_day=data.max_shifts_per_day,
            late_grace_period_minutes=data.late_grace_period_minutes,
        )
        return await self.template_repo.create(template)

    async def list_templates(
        self, skip: int = 0, limit: int = 100, include_inactive: bool = False
    ) -> tuple[list, int]:
        return await self.template_repo.get_all(
            skip=skip, limit=limit, include_inactive=include_inactive
        )

    async def update_template(
        self, template_id: UUID, data: PolicyTemplateUpdate
    ) -> PolicyTemplate:
        template = await self.template_repo.get_by_id(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Policy template not found"
            )
        updates = data.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update"
            )
        if "method" in updates and updates["method"] is not None:
            updates["method"] = updates["method"].value if hasattr(updates["method"], "value") else updates["method"]
        # Name uniqueness check if name is changing
        if "name" in updates and updates["name"] != template.name:
            existing = await self.template_repo.get_by_name(updates["name"])
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A policy template named '{updates['name']}' already exists.",
                )
        return await self.template_repo.update(template, updates)

    async def delete_template(self, template_id: UUID) -> PolicyTemplate:
        """Soft-delete a template (sets is_active=False)."""
        template = await self.template_repo.get_by_id(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Policy template not found"
            )
        if not template.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Policy template is already deactivated",
            )
        return await self.template_repo.update(template, {"is_active": False})

    async def apply_template_to_department(
        self, dept_id: UUID, template_id: UUID, changed_by: UUID
    ) -> AttendancePolicy:
        """Stamp a new AttendancePolicy from a template onto a department."""
        template = await self.template_repo.get_by_id(template_id)
        if not template or not template.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy template not found or is inactive",
            )

        # Conflict check
        conflict = await self.policy_repo.get_conflicting_policy("department", dept_id)
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A policy already exists for this department (id={conflict.id}). "
                       "Delete or update it before applying a template.",
            )

        policy = AttendancePolicy(
            department_id=dept_id,
            employee_id=None,
            method=template.method,
            geofence_id=template.geofence_id,
            work_start_time=template.work_start_time,
            work_hours_per_day=template.work_hours_per_day,
            auto_close_time=template.auto_close_time,
            task_planning_grace_minutes=template.task_planning_grace_minutes,
            allow_night_shift=template.allow_night_shift,
            max_shifts_per_day=template.max_shifts_per_day,
            late_grace_period_minutes=template.late_grace_period_minutes,
        )
        policy = await self.policy_repo.create(policy)

        await self.audit_repo.create(PolicyAuditLog(
            policy_id=policy.id,
            action="created",
            changed_by=changed_by,
            old_value=None,
            new_value={**_policy_to_dict(policy), "_source_template": str(template_id)},
        ))

        await _invalidate_policy_cache(policy.company_id)
        return policy


# ──────────────────────────────────────────────────────────────
# PolicyExceptionService
# ──────────────────────────────────────────────────────────────

class PolicyExceptionService:
    """Business logic for temporary per-employee policy overrides."""

    def __init__(self, db: AsyncSession):
        self.repo = PolicyExceptionRepository(db)

    async def create_exception(
        self, data: PolicyExceptionCreate, approved_by: UUID
    ) -> PolicyException:
        exception = PolicyException(
            employee_id=data.employee_id,
            reason=data.reason,
            from_date=data.from_date,
            to_date=data.to_date,
            override_method=data.override_method,
            override_work_hours=data.override_work_hours,
            override_geofence_id=data.override_geofence_id,
            approved_by=approved_by,
        )
        exc = await self.repo.create(exception)
        # Invalidate cache for this employee
        company_id = self.repo._company_id
        await _invalidate_policy_cache(company_id)
        return exc

    async def list_exceptions(
        self,
        skip: int = 0,
        limit: int = 100,
        employee_id: Optional[UUID] = None,
        include_inactive: bool = False,
    ) -> tuple[list, int]:
        return await self.repo.get_all(
            skip=skip, limit=limit, employee_id=employee_id, include_inactive=include_inactive
        )

    async def get_exception(self, exception_id: UUID) -> PolicyException:
        exc = await self.repo.get_by_id(exception_id)
        if not exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Policy exception not found"
            )
        return exc

    async def update_exception(
        self, exception_id: UUID, data: PolicyExceptionUpdate
    ) -> PolicyException:
        exc = await self.repo.get_by_id(exception_id)
        if not exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Policy exception not found"
            )
        updates = data.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update"
            )
        result = await self.repo.update(exc, updates)
        await _invalidate_policy_cache(self.repo._company_id)
        return result

    async def delete_exception(self, exception_id: UUID) -> None:
        exc = await self.repo.get_by_id(exception_id)
        if not exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Policy exception not found"
            )
        company_id = self.repo._company_id
        await self.repo.delete(exc)
        await _invalidate_policy_cache(company_id)
