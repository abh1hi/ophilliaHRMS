from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.v1.dependencies import get_current_user, require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole
from app.schemas.leave_policy import (
    LeavePolicyCreate, LeavePolicyUpdate, LeavePolicyResponse,
    LeavePolicyAssignmentCreate, LeavePolicyAssignmentResponse,
)
from app.schemas.response import APIResponse
from app.services import leave_policy_service

router = APIRouter()


@router.get("/", response_model=APIResponse[list[LeavePolicyResponse]])
async def list_policies(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(get_current_user),
):
    items = await leave_policy_service.list_policies(db, include_inactive)
    return APIResponse(success=True, data=items)


@router.get("/{policy_id}", response_model=APIResponse[LeavePolicyResponse])
async def get_policy(
    policy_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(get_current_user),
):
    item = await leave_policy_service.get_policy(db, policy_id)
    return APIResponse(success=True, data=item)


@router.post("/", response_model=APIResponse[LeavePolicyResponse], status_code=201)
async def create_policy(
    data: LeavePolicyCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    item = await leave_policy_service.create_policy(db, data)
    return APIResponse(success=True, data=item)


@router.patch("/{policy_id}", response_model=APIResponse[LeavePolicyResponse])
async def update_policy(
    policy_id: UUID,
    data: LeavePolicyUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    item = await leave_policy_service.update_policy(db, policy_id, data)
    return APIResponse(success=True, data=item)


# ── Policy Assignments ────────────────────────────────────────────────────────

@router.get("/assignments/", response_model=APIResponse[list[LeavePolicyAssignmentResponse]])
async def list_policy_assignments(
    employee_id: UUID | None = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(get_current_user),
):
    items = await leave_policy_service.list_assignments(db, employee_id)
    return APIResponse(success=True, data=items)


@router.post("/assignments/", response_model=APIResponse[LeavePolicyAssignmentResponse], status_code=201)
async def assign_policy(
    data: LeavePolicyAssignmentCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    item = await leave_policy_service.create_assignment(db, data)
    return APIResponse(success=True, data=item)


@router.patch("/assignments/{assignment_id}/cancel", response_model=APIResponse[LeavePolicyAssignmentResponse])
async def cancel_policy_assignment(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    item = await leave_policy_service.cancel_assignment(db, assignment_id)
    return APIResponse(success=True, data=item)
