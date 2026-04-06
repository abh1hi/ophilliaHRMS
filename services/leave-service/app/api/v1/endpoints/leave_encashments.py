from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.v1.dependencies import get_current_user, require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole
from app.schemas.leave_encashment import (
    LeaveEncashmentCreate, LeaveEncashmentResponse, LeaveEncashmentListResponse,
)
from app.schemas.response import APIResponse
from app.services import leave_encashment_service

router = APIRouter()


@router.get("/", response_model=APIResponse[LeaveEncashmentListResponse])
async def list_encashments(
    employee_id: UUID | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(get_current_user),
):
    items, total = await leave_encashment_service.list_encashments(db, employee_id, skip, limit)
    return APIResponse(success=True, data=LeaveEncashmentListResponse(
        total=total, skip=skip, limit=limit, encashments=items
    ))


@router.get("/{encashment_id}", response_model=APIResponse[LeaveEncashmentResponse])
async def get_encashment(
    encashment_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(get_current_user),
):
    item = await leave_encashment_service.get_encashment(db, encashment_id)
    return APIResponse(success=True, data=item)


@router.post("/", response_model=APIResponse[LeaveEncashmentResponse], status_code=201)
async def create_encashment(
    data: LeaveEncashmentCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    item = await leave_encashment_service.create_encashment(db, data)
    return APIResponse(success=True, data=item)


@router.patch("/{encashment_id}/cancel", response_model=APIResponse[LeaveEncashmentResponse])
async def cancel_encashment(
    encashment_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    item = await leave_encashment_service.cancel_encashment(db, encashment_id)
    return APIResponse(success=True, data=item)
