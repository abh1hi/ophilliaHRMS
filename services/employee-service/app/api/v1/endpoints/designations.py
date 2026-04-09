from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole
from app.core.responses import ok
from app.services.designation_service import DesignationService
from app.schemas.designation import DesignationCreate, DesignationUpdate, DesignationResponse

router = APIRouter(prefix="/designations", tags=["designations"])


def _get_service(db: AsyncSession = Depends(get_db_with_tenant)) -> DesignationService:
    return DesignationService(db)


@router.get("")
async def list_designations(
    include_inactive: bool = Query(False),
    _: TokenPayload = Depends(get_current_user),
    service: DesignationService = Depends(_get_service),
):
    items, _ = await service.list_all(include_inactive=include_inactive)
    return ok([DesignationResponse.model_validate(x).model_dump(mode="json") for x in items])


@router.get("/{designation_id}")
async def get_designation(
    designation_id: UUID,
    _: TokenPayload = Depends(get_current_user),
    service: DesignationService = Depends(_get_service),
):
    return ok(DesignationResponse.model_validate(await service.get(designation_id)).model_dump(mode="json"))


@router.post("", status_code=201)
async def create_designation(
    data: DesignationCreate,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: DesignationService = Depends(_get_service),
):
    return ok(DesignationResponse.model_validate(await service.create(data)).model_dump(mode="json"))


@router.patch("/{designation_id}")
async def update_designation(
    designation_id: UUID,
    data: DesignationUpdate,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: DesignationService = Depends(_get_service),
):
    return ok(DesignationResponse.model_validate(await service.update(designation_id, data)).model_dump(mode="json"))


@router.delete("/{designation_id}")
async def delete_designation(
    designation_id: UUID,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: DesignationService = Depends(_get_service),
):
    return ok(DesignationResponse.model_validate(await service.soft_delete(designation_id)).model_dump(mode="json"))
