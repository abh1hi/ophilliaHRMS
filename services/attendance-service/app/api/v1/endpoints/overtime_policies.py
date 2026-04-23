"""Overtime policy CRUD — thresholds, multipliers, jurisdiction, compliance templates."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole
from app.core.responses import ok
from app.services.overtime_service import OvertimeService
from app.schemas.overtime import (
    OvertimePolicyCreate, OvertimePolicyUpdate, OvertimePolicyResponse,
    OvertimeTemplateCreate, OvertimePolicyAuditResponse,
)

router = APIRouter(prefix="/overtime/policies", tags=["overtime"])

_HR_ROLES = require_role(UserRole.HR, UserRole.ADMIN, UserRole.SUPER_ADMIN)


def _svc(db: AsyncSession = Depends(get_db_with_tenant)) -> OvertimeService:
    return OvertimeService(db)


@router.get("")
async def list_overtime_policies(
    employee_id: UUID | None = Query(None),
    department_id: UUID | None = Query(None),
    location_id: UUID | None = Query(None),
    _: TokenPayload = Depends(get_current_user),
    svc: OvertimeService = Depends(_svc),
):
    items, _ = await svc.list_policies()
    return ok([OvertimePolicyResponse.model_validate(p).model_dump(mode="json") for p in items])


@router.post("", status_code=201)
async def create_overtime_policy(
    data: OvertimePolicyCreate,
    current_user: TokenPayload = Depends(_HR_ROLES),
    svc: OvertimeService = Depends(_svc),
):
    policy = await svc.create_policy(data.model_dump(), changed_by=UUID(current_user.sub))
    return ok(OvertimePolicyResponse.model_validate(policy).model_dump(mode="json"))


@router.post("/from-template", status_code=201)
async def create_from_template(
    data: OvertimeTemplateCreate,
    current_user: TokenPayload = Depends(_HR_ROLES),
    svc: OvertimeService = Depends(_svc),
):
    policy = await svc.create_from_template(
        data.template_key, changed_by=UUID(current_user.sub)
    )
    return ok(OvertimePolicyResponse.model_validate(policy).model_dump(mode="json"))


@router.patch("/{policy_id}")
async def update_overtime_policy(
    policy_id: UUID,
    data: OvertimePolicyUpdate,
    current_user: TokenPayload = Depends(_HR_ROLES),
    svc: OvertimeService = Depends(_svc),
):
    policy = await svc.update_policy(
        policy_id,
        data.model_dump(exclude_none=True),
        changed_by=UUID(current_user.sub),
    )
    return ok(OvertimePolicyResponse.model_validate(policy).model_dump(mode="json"))


@router.delete("/{policy_id}", status_code=204)
async def delete_overtime_policy(
    policy_id: UUID,
    current_user: TokenPayload = Depends(_HR_ROLES),
    svc: OvertimeService = Depends(_svc),
):
    await svc.delete_policy(policy_id, changed_by=UUID(current_user.sub))


@router.get("/{policy_id}/audit")
async def get_overtime_policy_audit(
    policy_id: UUID,
    _: TokenPayload = Depends(_HR_ROLES),
    svc: OvertimeService = Depends(_svc),
):
    await svc.get_policy(policy_id)  # 404 if not found
    from app.repositories.overtime_policy_repository import OvertimePolicyRepository
    repo = svc.repo
    from app.models.overtime_policy import OvertimePolicyAudit
    from sqlalchemy import select
    result = await svc._db.execute(
        select(OvertimePolicyAudit)
        .where(OvertimePolicyAudit.policy_id == policy_id)
        .order_by(OvertimePolicyAudit.timestamp.desc())
    )
    entries = result.scalars().all()
    return ok([OvertimePolicyAuditResponse.model_validate(e).model_dump(mode="json") for e in entries])
