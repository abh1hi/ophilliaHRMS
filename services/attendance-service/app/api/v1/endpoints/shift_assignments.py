from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, TokenPayload, get_db_with_tenant
from app.core.responses import ok
from app.services.shift_assignment_service import ShiftAssignmentService
from app.schemas.shift_assignment import ShiftAssignmentCreate, ShiftAssignmentUpdate, ShiftAssignmentResponse

router = APIRouter(prefix="/shift-assignments", tags=["shift-assignments"])


def _get_service(db: AsyncSession = Depends(get_db_with_tenant)) -> ShiftAssignmentService:
    return ShiftAssignmentService(db)


@router.get("")
async def list_shift_assignments(
    employee_id: Optional[UUID] = Query(None),
    include_inactive: bool = Query(False),
    _: TokenPayload = Depends(get_current_user),
    service: ShiftAssignmentService = Depends(_get_service),
):
    items, _ = await service.list_all(employee_id=employee_id, include_inactive=include_inactive)
    return ok([ShiftAssignmentResponse.model_validate(x).model_dump(mode="json") for x in items])


@router.get("/{assignment_id}")
async def get_shift_assignment(
    assignment_id: UUID,
    _: TokenPayload = Depends(get_current_user),
    service: ShiftAssignmentService = Depends(_get_service),
):
    return ok(ShiftAssignmentResponse.model_validate(await service.get(assignment_id)).model_dump(mode="json"))


@router.post("", status_code=201)
async def create_shift_assignment(
    data: ShiftAssignmentCreate,
    _: TokenPayload = Depends(get_current_user),
    service: ShiftAssignmentService = Depends(_get_service),
):
    return ok(ShiftAssignmentResponse.model_validate(await service.create(data)).model_dump(mode="json"))


@router.patch("/{assignment_id}")
async def update_shift_assignment(
    assignment_id: UUID,
    data: ShiftAssignmentUpdate,
    _: TokenPayload = Depends(get_current_user),
    service: ShiftAssignmentService = Depends(_get_service),
):
    return ok(ShiftAssignmentResponse.model_validate(await service.update(assignment_id, data)).model_dump(mode="json"))


@router.delete("/{assignment_id}")
async def delete_shift_assignment(
    assignment_id: UUID,
    _: TokenPayload = Depends(get_current_user),
    service: ShiftAssignmentService = Depends(_get_service),
):
    return ok(ShiftAssignmentResponse.model_validate(await service.soft_delete(assignment_id)).model_dump(mode="json"))
