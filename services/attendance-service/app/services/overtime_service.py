"""OvertimeService: CRUD for OvertimePolicy with compliance template application."""
import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.overtime_policy import OvertimePolicy, OvertimePolicyAudit
from app.repositories.overtime_policy_repository import OvertimePolicyRepository
from app.core.compliance_templates import COMPLIANCE_TEMPLATES

logger = logging.getLogger(__name__)


def _policy_to_dict(policy: OvertimePolicy) -> dict:
    return {
        "id": str(policy.id),
        "company_id": str(policy.company_id),
        "jurisdiction": policy.jurisdiction,
        "compliance_profile": policy.compliance_profile,
        "daily_ot_threshold_hours": policy.daily_ot_threshold_hours,
        "weekly_ot_threshold_hours": policy.weekly_ot_threshold_hours,
        "max_daily_hours": policy.max_daily_hours,
        "daily_ot_multiplier": policy.daily_ot_multiplier,
        "weekly_ot_multiplier": policy.weekly_ot_multiplier,
        "weekend_multiplier": policy.weekend_multiplier,
        "holiday_multiplier": policy.holiday_multiplier,
        "prefer_comp_off": policy.prefer_comp_off,
        "comp_off_ratio": policy.comp_off_ratio,
        "is_active": policy.is_active,
    }


class OvertimeService:
    """CRUD for OvertimePolicy plus compliance template application."""

    def __init__(self, db: AsyncSession):
        self.repo = OvertimePolicyRepository(db)
        self._db = db

    async def create_policy(self, data: dict, changed_by: UUID) -> OvertimePolicy:
        policy = OvertimePolicy(**data)
        policy = await self.repo.create(policy)
        await self._write_audit(policy, "created", None, changed_by)
        await self._db.commit()
        return policy

    async def create_from_template(self, template_key: str, changed_by: UUID, **scope_overrides) -> OvertimePolicy:
        """Create an OvertimePolicy from a pre-built compliance template."""
        template = COMPLIANCE_TEMPLATES.get(template_key)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown compliance template '{template_key}'. "
                       f"Valid keys: {list(COMPLIANCE_TEMPLATES)}",
            )
        data = {**template, **scope_overrides}
        return await self.create_policy(data, changed_by)

    async def list_policies(self, skip: int = 0, limit: int = 100) -> tuple[list, int]:
        return await self.repo.get_all(skip=skip, limit=limit)

    async def get_policy(self, policy_id: UUID) -> OvertimePolicy:
        policy = await self.repo.get_by_id(policy_id)
        if not policy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Overtime policy not found")
        return policy

    async def update_policy(self, policy_id: UUID, updates: dict, changed_by: UUID) -> OvertimePolicy:
        policy = await self.get_policy(policy_id)
        old_value = _policy_to_dict(policy)
        policy = await self.repo.update(policy, updates)
        await self._write_audit(policy, "updated", old_value, changed_by)
        await self._db.commit()
        return policy

    async def delete_policy(self, policy_id: UUID, changed_by: UUID) -> None:
        policy = await self.get_policy(policy_id)
        old_value = _policy_to_dict(policy)
        await self.repo.delete(policy)
        audit = OvertimePolicyAudit(
            policy_id=policy_id,
            action="deleted",
            changed_by=changed_by,
            old_value=old_value,
            new_value=None,
        )
        await self.repo.create_audit(audit)
        await self._db.commit()

    async def _write_audit(self, policy: OvertimePolicy, action: str, old_value, changed_by: UUID) -> None:
        audit = OvertimePolicyAudit(
            policy_id=policy.id,
            action=action,
            changed_by=changed_by,
            old_value=old_value,
            new_value=_policy_to_dict(policy),
        )
        await self.repo.create_audit(audit)
