from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.v1.dependencies import get_current_user, require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole
from app.schemas.holiday_list import (
    HolidayListCreate, HolidayListUpdate, HolidayListResponse,
    HolidayListEntryCreate, HolidayListEntryResponse,
    HolidayListAssignmentCreate, HolidayListAssignmentResponse,
)
from app.schemas.response import APIResponse
from app.services import holiday_list_service

router = APIRouter()


@router.get("/", response_model=APIResponse[list[HolidayListResponse]])
async def list_holiday_lists(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(get_current_user),
):
    items = await holiday_list_service.list_holiday_lists(db, include_inactive)
    return APIResponse(success=True, data=items)


@router.get("/{list_id}", response_model=APIResponse[HolidayListResponse])
async def get_holiday_list(
    list_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(get_current_user),
):
    item = await holiday_list_service.get_holiday_list(db, list_id)
    return APIResponse(success=True, data=item)


@router.post("/", response_model=APIResponse[HolidayListResponse], status_code=201)
async def create_holiday_list(
    data: HolidayListCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    item = await holiday_list_service.create_holiday_list(db, data)
    return APIResponse(success=True, data=item)


@router.patch("/{list_id}", response_model=APIResponse[HolidayListResponse])
async def update_holiday_list(
    list_id: UUID,
    data: HolidayListUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    item = await holiday_list_service.update_holiday_list(db, list_id, data)
    return APIResponse(success=True, data=item)


@router.post("/{list_id}/entries", response_model=APIResponse[list[HolidayListEntryResponse]])
async def add_entries(
    list_id: UUID,
    entries: list[HolidayListEntryCreate],
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    item = await holiday_list_service.add_entries(db, list_id, entries)
    return APIResponse(success=True, data=item.entries)


# ── Assignments ───────────────────────────────────────────────────────────────

@router.get("/assignments/", response_model=APIResponse[list[HolidayListAssignmentResponse]])
async def list_assignments(
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(get_current_user),
):
    items = await holiday_list_service.list_assignments(db)
    return APIResponse(success=True, data=items)


@router.post("/assignments/", response_model=APIResponse[HolidayListAssignmentResponse], status_code=201)
async def create_assignment(
    data: HolidayListAssignmentCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    _: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    item = await holiday_list_service.create_assignment(db, data)
    return APIResponse(success=True, data=item)
