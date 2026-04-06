from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, TokenPayload, get_db_with_tenant
from app.core.responses import ok
from app.services.shift_request_service import ShiftRequestService
from app.schemas.shift_request import ShiftRequestCreate, ShiftRequestUpdate, ShiftRequestReview, ShiftRequestResponse

router = APIRouter(prefix="/shift-requests", tags=["shift-requests"])


def _get_service(db: AsyncSession = Depends(get_db_with_tenant)) -> ShiftRequestService:
    return ShiftRequestService(db)


@router.get("")
async def list_shift_requests(
    employee_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    _: TokenPayload = Depends(get_current_user),
    service: ShiftRequestService = Depends(_get_service),
):
    items, _ = await service.list_all(employee_id=employee_id, status_filter=status)
    return ok([ShiftRequestResponse.model_validate(x).model_dump(mode="json") for x in items])


@router.get("/{request_id}")
async def get_shift_request(
    request_id: UUID,
    _: TokenPayload = Depends(get_current_user),
    service: ShiftRequestService = Depends(_get_service),
):
    return ok(ShiftRequestResponse.model_validate(await service.get(request_id)).model_dump(mode="json"))


@router.post("", status_code=201)
async def create_shift_request(
    data: ShiftRequestCreate,
    _: TokenPayload = Depends(get_current_user),
    service: ShiftRequestService = Depends(_get_service),
):
    return ok(ShiftRequestResponse.model_validate(await service.create(data)).model_dump(mode="json"))


@router.patch("/{request_id}")
async def update_shift_request(
    request_id: UUID,
    data: ShiftRequestUpdate,
    _: TokenPayload = Depends(get_current_user),
    service: ShiftRequestService = Depends(_get_service),
):
    return ok(ShiftRequestResponse.model_validate(await service.update(request_id, data)).model_dump(mode="json"))


@router.patch("/{request_id}/review")
async def review_shift_request(
    request_id: UUID,
    data: ShiftRequestReview,
    current_user: TokenPayload = Depends(get_current_user),
    service: ShiftRequestService = Depends(_get_service),
):
    reviewed_by = UUID(current_user.sub)
    return ok(ShiftRequestResponse.model_validate(await service.review(request_id, data, reviewed_by)).model_dump(mode="json"))


@router.delete("/{request_id}")
async def cancel_shift_request(
    request_id: UUID,
    _: TokenPayload = Depends(get_current_user),
    service: ShiftRequestService = Depends(_get_service),
):
    return ok(ShiftRequestResponse.model_validate(await service.cancel(request_id)).model_dump(mode="json"))
