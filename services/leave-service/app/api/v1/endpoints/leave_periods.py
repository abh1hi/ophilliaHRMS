from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.v1.dependencies import get_current_user, require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole
from app.schemas.leave_period import LeavePeriodCreate, LeavePeriodUpdate, LeavePeriodResponse
from app.schemas.response import APIResponse
from app.services import leave_period_service

router = APIRouter()


@router.get("/", response_model=APIResponse[list[LeavePeriodResponse]])
async def list_leave_periods(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(get_current_user),
):
    items, _total = await leave_period_service.list_periods(db, include_inactive)
    return APIResponse(success=True, data=items)


@router.get("/{period_id}", response_model=APIResponse[LeavePeriodResponse])
async def get_leave_period(
    period_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(get_current_user),
):
    item = await leave_period_service.get_period(db, period_id)
    return APIResponse(success=True, data=item)


@router.post("/", response_model=APIResponse[LeavePeriodResponse], status_code=201)
async def create_leave_period(
    data: LeavePeriodCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    item = await leave_period_service.create_period(db, data)
    return APIResponse(success=True, data=item)


@router.patch("/{period_id}", response_model=APIResponse[LeavePeriodResponse])
async def update_leave_period(
    period_id: UUID,
    data: LeavePeriodUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    item = await leave_period_service.update_period(db, period_id, data)
    return APIResponse(success=True, data=item)


@router.delete("/{period_id}", response_model=APIResponse[LeavePeriodResponse])
async def delete_leave_period(
    period_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    item = await leave_period_service.delete_period(db, period_id)
    return APIResponse(success=True, data=item)
