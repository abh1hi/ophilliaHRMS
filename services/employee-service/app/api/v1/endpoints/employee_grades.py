from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole
from app.core.responses import ok
from app.services.employee_grade_service import EmployeeGradeService
from app.schemas.employee_grade import EmployeeGradeCreate, EmployeeGradeUpdate, EmployeeGradeResponse

router = APIRouter(prefix="/employee-grades", tags=["employee-grades"])


def _get_service(db: AsyncSession = Depends(get_db_with_tenant)) -> EmployeeGradeService:
    return EmployeeGradeService(db)


@router.get("")
async def list_employee_grades(
    include_inactive: bool = Query(False),
    _: TokenPayload = Depends(get_current_user),
    service: EmployeeGradeService = Depends(_get_service),
):
    items, _ = await service.list_all(include_inactive=include_inactive)
    return ok([EmployeeGradeResponse.model_validate(x).model_dump(mode="json") for x in items])


@router.get("/{grade_id}")
async def get_employee_grade(
    grade_id: UUID,
    _: TokenPayload = Depends(get_current_user),
    service: EmployeeGradeService = Depends(_get_service),
):
    return ok(EmployeeGradeResponse.model_validate(await service.get(grade_id)).model_dump(mode="json"))


@router.post("", status_code=201)
async def create_employee_grade(
    data: EmployeeGradeCreate,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: EmployeeGradeService = Depends(_get_service),
):
    return ok(EmployeeGradeResponse.model_validate(await service.create(data)).model_dump(mode="json"))


@router.patch("/{grade_id}")
async def update_employee_grade(
    grade_id: UUID,
    data: EmployeeGradeUpdate,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: EmployeeGradeService = Depends(_get_service),
):
    return ok(EmployeeGradeResponse.model_validate(await service.update(grade_id, data)).model_dump(mode="json"))


@router.delete("/{grade_id}")
async def delete_employee_grade(
    grade_id: UUID,
    _: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: EmployeeGradeService = Depends(_get_service),
):
    return ok(EmployeeGradeResponse.model_validate(await service.soft_delete(grade_id)).model_dump(mode="json"))
