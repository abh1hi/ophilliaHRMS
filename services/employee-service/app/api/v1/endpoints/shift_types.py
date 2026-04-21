from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole
from app.core.responses import ok
from app.services.shift_type_service import ShiftTypeService
from app.schemas.shift_type import ShiftTypeCreate, ShiftTypeUpdate, ShiftTypeResponse

router = APIRouter(prefix="/shift-types", tags=["shift-types"])


def _get_service(request: Request, db: AsyncSession = Depends(get_db_with_tenant)) -> ShiftTypeService:
    return ShiftTypeService(db, request.app.state.event_publisher)


@router.get("")
async def list_shift_types(
    include_inactive: bool = Query(False),
    _: TokenPayload = Depends(get_current_user),
    service: ShiftTypeService = Depends(_get_service),
):
    items, _ = await service.list_all(include_inactive=include_inactive)
    return ok([ShiftTypeResponse.model_validate(x).model_dump(mode="json") for x in items])


@router.get("/{shift_type_id}")
async def get_shift_type(
    shift_type_id: UUID,
    _: TokenPayload = Depends(get_current_user),
    service: ShiftTypeService = Depends(_get_service),
):
    return ok(ShiftTypeResponse.model_validate(await service.get(shift_type_id)).model_dump(mode="json"))


@router.post("", status_code=201)
async def create_shift_type(
    data: ShiftTypeCreate,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: ShiftTypeService = Depends(_get_service),
):
    return ok(ShiftTypeResponse.model_validate(await service.create(data)).model_dump(mode="json"))


@router.patch("/{shift_type_id}")
async def update_shift_type(
    shift_type_id: UUID,
    data: ShiftTypeUpdate,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: ShiftTypeService = Depends(_get_service),
):
    return ok(ShiftTypeResponse.model_validate(await service.update(shift_type_id, data)).model_dump(mode="json"))


@router.delete("/{shift_type_id}")
async def delete_shift_type(
    shift_type_id: UUID,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: ShiftTypeService = Depends(_get_service),
):
    return ok(ShiftTypeResponse.model_validate(await service.soft_delete(shift_type_id)).model_dump(mode="json"))
