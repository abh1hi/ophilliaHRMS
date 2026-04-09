from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole
from app.core.responses import ok
from app.services.employee_group_service import EmployeeGroupService
from app.schemas.employee_group import EmployeeGroupCreate, EmployeeGroupUpdate, EmployeeGroupResponse, MemberResponse

router = APIRouter(prefix="/employee-groups", tags=["employee-groups"])


class AddMemberRequest(BaseModel):
    employee_id: UUID


def _get_service(db: AsyncSession = Depends(get_db_with_tenant)) -> EmployeeGroupService:
    return EmployeeGroupService(db)


def _serialize(group) -> dict:
    data = EmployeeGroupResponse.model_validate(group).model_dump(mode="json")
    data["members"] = [{"employee_id": str(m.id)} for m in (group.members or [])]
    return data


@router.get("")
async def list_employee_groups(
    include_inactive: bool = Query(False),
    _: TokenPayload = Depends(get_current_user),
    service: EmployeeGroupService = Depends(_get_service),
):
    items, _ = await service.list_all(include_inactive=include_inactive)
    return ok([EmployeeGroupResponse.model_validate(x).model_dump(mode="json") for x in items])


@router.get("/{group_id}")
async def get_employee_group(
    group_id: UUID,
    _: TokenPayload = Depends(get_current_user),
    service: EmployeeGroupService = Depends(_get_service),
):
    return ok(_serialize(await service.get(group_id)))


@router.post("", status_code=201)
async def create_employee_group(
    data: EmployeeGroupCreate,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: EmployeeGroupService = Depends(_get_service),
):
    return ok(EmployeeGroupResponse.model_validate(await service.create(data)).model_dump(mode="json"))


@router.patch("/{group_id}")
async def update_employee_group(
    group_id: UUID,
    data: EmployeeGroupUpdate,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: EmployeeGroupService = Depends(_get_service),
):
    return ok(EmployeeGroupResponse.model_validate(await service.update(group_id, data)).model_dump(mode="json"))


@router.delete("/{group_id}")
async def delete_employee_group(
    group_id: UUID,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: EmployeeGroupService = Depends(_get_service),
):
    return ok(EmployeeGroupResponse.model_validate(await service.soft_delete(group_id)).model_dump(mode="json"))


@router.post("/{group_id}/members", status_code=200)
async def add_member(
    group_id: UUID,
    body: AddMemberRequest,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: EmployeeGroupService = Depends(_get_service),
):
    return ok(_serialize(await service.add_member(group_id, body.employee_id)))


@router.delete("/{group_id}/members/{employee_id}", status_code=200)
async def remove_member(
    group_id: UUID,
    employee_id: UUID,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: EmployeeGroupService = Depends(_get_service),
):
    return ok(_serialize(await service.remove_member(group_id, employee_id)))
