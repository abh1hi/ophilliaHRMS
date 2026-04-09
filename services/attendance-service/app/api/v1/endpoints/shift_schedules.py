from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, TokenPayload, get_db_with_tenant
from app.core.responses import ok
from app.services.shift_schedule_service import ShiftScheduleService
from app.schemas.shift_schedule import ShiftScheduleCreate, ShiftScheduleUpdate, ShiftScheduleResponse

router = APIRouter(prefix="/shift-schedules", tags=["shift-schedules"])


def _get_service(db: AsyncSession = Depends(get_db_with_tenant)) -> ShiftScheduleService:
    return ShiftScheduleService(db)


@router.get("")
async def list_shift_schedules(
    include_inactive: bool = Query(False),
    _: TokenPayload = Depends(get_current_user),
    service: ShiftScheduleService = Depends(_get_service),
):
    items, _ = await service.list_all(include_inactive=include_inactive)
    return ok([ShiftScheduleResponse.model_validate(x).model_dump(mode="json") for x in items])


@router.get("/{schedule_id}")
async def get_shift_schedule(
    schedule_id: UUID,
    _: TokenPayload = Depends(get_current_user),
    service: ShiftScheduleService = Depends(_get_service),
):
    return ok(ShiftScheduleResponse.model_validate(await service.get(schedule_id)).model_dump(mode="json"))


@router.post("", status_code=201)
async def create_shift_schedule(
    data: ShiftScheduleCreate,
    _: TokenPayload = Depends(get_current_user),
    service: ShiftScheduleService = Depends(_get_service),
):
    return ok(ShiftScheduleResponse.model_validate(await service.create(data)).model_dump(mode="json"))


@router.patch("/{schedule_id}")
async def update_shift_schedule(
    schedule_id: UUID,
    data: ShiftScheduleUpdate,
    _: TokenPayload = Depends(get_current_user),
    service: ShiftScheduleService = Depends(_get_service),
):
    return ok(ShiftScheduleResponse.model_validate(await service.update(schedule_id, data)).model_dump(mode="json"))


@router.delete("/{schedule_id}")
async def delete_shift_schedule(
    schedule_id: UUID,
    _: TokenPayload = Depends(get_current_user),
    service: ShiftScheduleService = Depends(_get_service),
):
    return ok(ShiftScheduleResponse.model_validate(await service.soft_delete(schedule_id)).model_dump(mode="json"))
