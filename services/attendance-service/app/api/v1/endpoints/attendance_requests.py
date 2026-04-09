from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, TokenPayload, get_db_with_tenant
from app.core.responses import ok
from app.services.attendance_request_service import AttendanceRequestService
from app.schemas.attendance_request import (
    AttendanceRequestCreate, AttendanceRequestReview,
    AttendanceRequestResponse, AttendanceRequestListResponse,
)

router = APIRouter(prefix="/attendance/requests", tags=["attendance-requests"])


def _get_service(db: AsyncSession = Depends(get_db_with_tenant)) -> AttendanceRequestService:
    return AttendanceRequestService(db)


@router.get("")
async def list_attendance_requests(
    employee_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _: TokenPayload = Depends(get_current_user),
    service: AttendanceRequestService = Depends(_get_service),
):
    items, total = await service.list_all(employee_id, status_filter, skip, limit)
    return ok(AttendanceRequestListResponse(
        total=total, skip=skip, limit=limit,
        requests=[AttendanceRequestResponse.model_validate(x) for x in items],
    ).model_dump(mode="json"))


@router.get("/{request_id}")
async def get_attendance_request(
    request_id: UUID,
    _: TokenPayload = Depends(get_current_user),
    service: AttendanceRequestService = Depends(_get_service),
):
    req = await service.get(request_id)
    return ok(AttendanceRequestResponse.model_validate(req).model_dump(mode="json"))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_attendance_request(
    data: AttendanceRequestCreate,
    _: TokenPayload = Depends(get_current_user),
    service: AttendanceRequestService = Depends(_get_service),
):
    req = await service.create(data)
    return ok(AttendanceRequestResponse.model_validate(req).model_dump(mode="json"))


@router.patch("/{request_id}/cancel")
async def cancel_attendance_request(
    request_id: UUID,
    _: TokenPayload = Depends(get_current_user),
    service: AttendanceRequestService = Depends(_get_service),
):
    req = await service.cancel(request_id)
    return ok(AttendanceRequestResponse.model_validate(req).model_dump(mode="json"))


@router.patch("/{request_id}/review")
async def review_attendance_request(
    request_id: UUID,
    data: AttendanceRequestReview,
    current_user: TokenPayload = Depends(get_current_user),
    service: AttendanceRequestService = Depends(_get_service),
):
    reviewed_by = UUID(current_user.sub)
    req = await service.review(request_id, data, reviewed_by)
    return ok(AttendanceRequestResponse.model_validate(req).model_dump(mode="json"))
