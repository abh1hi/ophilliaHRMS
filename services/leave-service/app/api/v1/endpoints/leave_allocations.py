from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.v1.dependencies import get_current_user, require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole
from app.schemas.leave_allocation import (
    LeaveAllocationCreate, LeaveAllocationUpdate, LeaveAllocationResponse,
    LeaveAllocationListResponse, LeaveAdjustmentCreate, LeaveAdjustmentResponse,
)
from app.schemas.response import APIResponse
from app.services import leave_allocation_service

router = APIRouter()


@router.get("/", response_model=APIResponse[LeaveAllocationListResponse])
async def list_allocations(
    employee_id: UUID | None = None,
    leave_type_id: UUID | None = None,
    leave_period_id: UUID | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(get_current_user),
):
    items, total = await leave_allocation_service.list_allocations(
        db, employee_id, leave_type_id, leave_period_id, status, skip, limit
    )
    return APIResponse(success=True, data=LeaveAllocationListResponse(
        total=total, skip=skip, limit=limit, allocations=items
    ))


@router.get("/{allocation_id}", response_model=APIResponse[LeaveAllocationResponse])
async def get_allocation(
    allocation_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(get_current_user),
):
    item = await leave_allocation_service.get_allocation(db, allocation_id)
    return APIResponse(success=True, data=item)


@router.post("/", response_model=APIResponse[LeaveAllocationResponse], status_code=201)
async def create_allocation(
    data: LeaveAllocationCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    item = await leave_allocation_service.create_allocation(db, data)
    return APIResponse(success=True, data=item)


@router.patch("/{allocation_id}", response_model=APIResponse[LeaveAllocationResponse])
async def update_allocation(
    allocation_id: UUID,
    data: LeaveAllocationUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    item = await leave_allocation_service.update_allocation(db, allocation_id, data)
    return APIResponse(success=True, data=item)


@router.post("/{allocation_id}/adjust", response_model=APIResponse[LeaveAdjustmentResponse], status_code=201)
async def adjust_allocation(
    allocation_id: UUID,
    data: LeaveAdjustmentCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    adj_data = data.model_copy(update={"allocation_id": allocation_id})
    item = await leave_allocation_service.adjust_allocation(db, adj_data, UUID(current_user.sub))
    return APIResponse(success=True, data=item)
