from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, TokenPayload, get_db_with_tenant
from app.core.responses import ok
from app.services.employee_checkin_service import EmployeeCheckinService
from app.schemas.employee_checkin import (
    CheckinCreate, CheckinUpdate, CheckinResponse, CheckinListResponse
)

router = APIRouter(prefix="/attendance/checkins", tags=["employee-checkins"])


def _get_service(db: AsyncSession = Depends(get_db_with_tenant)) -> EmployeeCheckinService:
    return EmployeeCheckinService(db)


@router.get("")
async def list_checkins(
    employee_id: Optional[UUID] = Query(None),
    from_dt: Optional[datetime] = Query(None),
    to_dt: Optional[datetime] = Query(None),
    log_type: Optional[str] = Query(None, description="IN or OUT"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _: TokenPayload = Depends(get_current_user),
    service: EmployeeCheckinService = Depends(_get_service),
):
    items, total = await service.list_all(employee_id, from_dt, to_dt, log_type, skip, limit)
    return ok(CheckinListResponse(
        total=total, skip=skip, limit=limit,
        checkins=[CheckinResponse.model_validate(x) for x in items],
    ).model_dump(mode="json"))


@router.get("/{checkin_id}")
async def get_checkin(
    checkin_id: UUID,
    _: TokenPayload = Depends(get_current_user),
    service: EmployeeCheckinService = Depends(_get_service),
):
    checkin = await service.get(checkin_id)
    return ok(CheckinResponse.model_validate(checkin).model_dump(mode="json"))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_checkin(
    data: CheckinCreate,
    _: TokenPayload = Depends(get_current_user),
    service: EmployeeCheckinService = Depends(_get_service),
):
    checkin = await service.create(data)
    return ok(CheckinResponse.model_validate(checkin).model_dump(mode="json"))


@router.patch("/{checkin_id}/fetch-shift")
async def fetch_shift_for_checkin(
    checkin_id: UUID,
    _: TokenPayload = Depends(get_current_user),
    service: EmployeeCheckinService = Depends(_get_service),
):
    """Re-resolve shift_type_id from the current active shift assignment."""
    checkin = await service.fetch_shift(checkin_id)
    return ok(CheckinResponse.model_validate(checkin).model_dump(mode="json"))


@router.patch("/{checkin_id}/skip")
async def toggle_skip(
    checkin_id: UUID,
    _: TokenPayload = Depends(get_current_user),
    service: EmployeeCheckinService = Depends(_get_service),
):
    """Toggle skip_auto_attendance flag (0→1 or 1→0)."""
    checkin = await service.skip_toggle(checkin_id)
    return ok(CheckinResponse.model_validate(checkin).model_dump(mode="json"))


@router.patch("/{checkin_id}")
async def update_checkin(
    checkin_id: UUID,
    data: CheckinUpdate,
    _: TokenPayload = Depends(get_current_user),
    service: EmployeeCheckinService = Depends(_get_service),
):
    checkin = await service.update(checkin_id, data)
    return ok(CheckinResponse.model_validate(checkin).model_dump(mode="json"))
