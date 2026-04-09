from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole
from app.core.responses import ok
from app.services.shift_location_service import ShiftLocationService
from app.schemas.shift_location import ShiftLocationCreate, ShiftLocationUpdate, ShiftLocationResponse

router = APIRouter(prefix="/shift-locations", tags=["shift-locations"])


def _get_service(db: AsyncSession = Depends(get_db_with_tenant)) -> ShiftLocationService:
    return ShiftLocationService(db)


@router.get("")
async def list_shift_locations(
    include_inactive: bool = Query(False),
    _: TokenPayload = Depends(get_current_user),
    service: ShiftLocationService = Depends(_get_service),
):
    items, _ = await service.list_all(include_inactive=include_inactive)
    return ok([ShiftLocationResponse.model_validate(x).model_dump(mode="json") for x in items])


@router.get("/{location_id}")
async def get_shift_location(
    location_id: UUID,
    _: TokenPayload = Depends(get_current_user),
    service: ShiftLocationService = Depends(_get_service),
):
    return ok(ShiftLocationResponse.model_validate(await service.get(location_id)).model_dump(mode="json"))


@router.post("", status_code=201)
async def create_shift_location(
    data: ShiftLocationCreate,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: ShiftLocationService = Depends(_get_service),
):
    return ok(ShiftLocationResponse.model_validate(await service.create(data)).model_dump(mode="json"))


@router.patch("/{location_id}")
async def update_shift_location(
    location_id: UUID,
    data: ShiftLocationUpdate,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: ShiftLocationService = Depends(_get_service),
):
    return ok(ShiftLocationResponse.model_validate(await service.update(location_id, data)).model_dump(mode="json"))


@router.delete("/{location_id}")
async def delete_shift_location(
    location_id: UUID,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: ShiftLocationService = Depends(_get_service),
):
    return ok(ShiftLocationResponse.model_validate(await service.soft_delete(location_id)).model_dump(mode="json"))
