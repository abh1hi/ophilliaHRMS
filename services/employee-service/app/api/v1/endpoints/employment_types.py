from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole
from app.core.responses import ok
from app.services.employment_type_service import EmploymentTypeService
from app.schemas.employment_type import EmploymentTypeCreate, EmploymentTypeUpdate, EmploymentTypeResponse

router = APIRouter(prefix="/employment-types", tags=["employment-types"])


def _get_service(db: AsyncSession = Depends(get_db_with_tenant)) -> EmploymentTypeService:
    return EmploymentTypeService(db)


@router.get("")
async def list_employment_types(
    include_inactive: bool = Query(False),
    _: TokenPayload = Depends(get_current_user),
    service: EmploymentTypeService = Depends(_get_service),
):
    items, _ = await service.list_all(include_inactive=include_inactive)
    return ok([EmploymentTypeResponse.model_validate(x).model_dump(mode="json") for x in items])


@router.get("/{et_id}")
async def get_employment_type(
    et_id: UUID,
    _: TokenPayload = Depends(get_current_user),
    service: EmploymentTypeService = Depends(_get_service),
):
    return ok(EmploymentTypeResponse.model_validate(await service.get(et_id)).model_dump(mode="json"))


@router.post("", status_code=201)
async def create_employment_type(
    data: EmploymentTypeCreate,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: EmploymentTypeService = Depends(_get_service),
):
    return ok(EmploymentTypeResponse.model_validate(await service.create(data)).model_dump(mode="json"))


@router.patch("/{et_id}")
async def update_employment_type(
    et_id: UUID,
    data: EmploymentTypeUpdate,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: EmploymentTypeService = Depends(_get_service),
):
    return ok(EmploymentTypeResponse.model_validate(await service.update(et_id, data)).model_dump(mode="json"))


@router.delete("/{et_id}")
async def delete_employment_type(
    et_id: UUID,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: EmploymentTypeService = Depends(_get_service),
):
    return ok(EmploymentTypeResponse.model_validate(await service.soft_delete(et_id)).model_dump(mode="json"))
