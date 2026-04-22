from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, TokenPayload, get_db_with_tenant
from app.core.responses import ok
from app.services.shift_schedule_assignment_service import ShiftScheduleAssignmentService
from app.schemas.shift_schedule_assignment import ShiftScheduleAssignmentCreate, ShiftScheduleAssignmentUpdate, ShiftScheduleAssignmentResponse

router = APIRouter(prefix="/shift-schedule-assignments", tags=["shift-schedule-assignments"])


def _get_service(db: AsyncSession = Depends(get_db_with_tenant)) -> ShiftScheduleAssignmentService:
    return ShiftScheduleAssignmentService(db)


@router.get("")
async def list_shift_schedule_assignments(
    schedule_id: Optional[UUID] = Query(None),
    employee_id: Optional[UUID] = Query(None),
    _: TokenPayload = Depends(get_current_user),
    service: ShiftScheduleAssignmentService = Depends(_get_service),
):
    items, _ = await service.list_all(schedule_id=schedule_id, employee_id=employee_id)
    return ok([ShiftScheduleAssignmentResponse.model_validate(x).model_dump(mode="json") for x in items])


@router.post("", status_code=201)
async def create_shift_schedule_assignment(
    data: ShiftScheduleAssignmentCreate,
    _: TokenPayload = Depends(get_current_user),
    service: ShiftScheduleAssignmentService = Depends(_get_service),
):
    return ok(ShiftScheduleAssignmentResponse.model_validate(await service.assign(data)).model_dump(mode="json"))


@router.delete("/{assignment_id}", status_code=204)
async def delete_shift_schedule_assignment(
    assignment_id: UUID,
    _: TokenPayload = Depends(get_current_user),
    service: ShiftScheduleAssignmentService = Depends(_get_service),
):
    await service.remove(assignment_id)


@router.patch("/{assignment_id}")
async def update_shift_schedule_assignment(
    assignment_id: UUID,
    data: ShiftScheduleAssignmentUpdate,
    _: TokenPayload = Depends(get_current_user),
    service: ShiftScheduleAssignmentService = Depends(_get_service),
):
    return ok(ShiftScheduleAssignmentResponse.model_validate(await service.update(assignment_id, data)).model_dump(mode="json"))
