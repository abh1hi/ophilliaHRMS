from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.v1.dependencies import get_current_user, require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole
from app.schemas.leave_block_list import (
    LeaveBlockListCreate, LeaveBlockListUpdate, LeaveBlockListResponse,
)
from app.schemas.response import APIResponse
from app.services import leave_block_list_service

router = APIRouter()


@router.get("/", response_model=APIResponse[list[LeaveBlockListResponse]])
async def list_block_lists(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(get_current_user),
):
    items = await leave_block_list_service.list_block_lists(db, include_inactive)
    return APIResponse(success=True, data=items)


@router.get("/{block_list_id}", response_model=APIResponse[LeaveBlockListResponse])
async def get_block_list(
    block_list_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(get_current_user),
):
    item = await leave_block_list_service.get_block_list(db, block_list_id)
    return APIResponse(success=True, data=item)


@router.post("/", response_model=APIResponse[LeaveBlockListResponse], status_code=201)
async def create_block_list(
    data: LeaveBlockListCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    item = await leave_block_list_service.create_block_list(db, data)
    return APIResponse(success=True, data=item)


@router.patch("/{block_list_id}", response_model=APIResponse[LeaveBlockListResponse])
async def update_block_list(
    block_list_id: UUID,
    data: LeaveBlockListUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    item = await leave_block_list_service.update_block_list(db, block_list_id, data)
    return APIResponse(success=True, data=item)
