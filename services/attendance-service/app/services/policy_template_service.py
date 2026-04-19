"""PolicyTemplateService: CRUD for reusable PolicyTemplate records."""
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_policy import AttendancePolicy
from app.models.policy_audit_log import PolicyAuditLog
from app.models.policy_template import PolicyTemplate
from app.repositories.policy_audit_repository import PolicyAuditRepository
from app.repositories.policy_repository import PolicyRepository
from app.repositories.policy_template_repository import PolicyTemplateRepository
from app.schemas.attendance import PolicyTemplateCreate, PolicyTemplateUpdate
from app.services.policy_service import _invalidate_policy_cache, _policy_to_dict


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
            updates["method"] = (
                updates["method"].value
                if hasattr(updates["method"], "value")
                else updates["method"]
            )
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

        conflict = await self.policy_repo.get_conflicting_policy("department", dept_id)
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"A policy already exists for this department (id={conflict.id}). "
                    "Delete or update it before applying a template."
                ),
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
