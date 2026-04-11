import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.dependencies import (
    get_current_user,
    require_role,
    TokenPayload,
    get_db_with_tenant
)
from app.core.constants import UserRole
from app.core.responses import ok
from app.services.department_service import DepartmentService
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse

router = APIRouter(prefix="/departments", tags=["departments"])


def _get_service(db: AsyncSession = Depends(get_db_with_tenant)) -> DepartmentService:
    return DepartmentService(db)


@router.post("", status_code=201)
async def create_department(
    request: Request,
    data: DepartmentCreate,
    current_user: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: DepartmentService = Depends(_get_service),
):
    dept = await service.create_department(data)

    # Publish department.initialized on first department creation for this company
    from app.core.config import settings as _s
    _, total = await service.list_departments()
    if _s.ENABLE_EVENT_DRIVEN_ONBOARDING and total == 1:
        publisher = getattr(request.app.state, "event_publisher", None)
        if publisher:
            _task = asyncio.create_task(publisher.publish("department.initialized", {
                "company_id": current_user.company_id,
            }))
            request.state._bg_tasks = getattr(request.state, "_bg_tasks", set())
            request.state._bg_tasks.add(_task)
            _task.add_done_callback(request.state._bg_tasks.discard)

    return ok(DepartmentResponse.model_validate(dept).model_dump(mode="json"))


@router.get("")
async def list_departments(
    include_inactive: bool = Query(False, description="Include soft-deleted departments"),
    current_user: TokenPayload = Depends(get_current_user),
    service: DepartmentService = Depends(_get_service),
):
    departments, _ = await service.list_departments(include_inactive=include_inactive)
    return ok([DepartmentResponse.model_validate(d).model_dump(mode="json") for d in departments])


@router.get("/{department_id}")
async def get_department(
    department_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: DepartmentService = Depends(_get_service),
):
    return ok(DepartmentResponse.model_validate(await service.get_department(department_id)).model_dump(mode="json"))


@router.patch("/{department_id}")
async def update_department(
    department_id: UUID,
    data: DepartmentUpdate,
    current_user: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: DepartmentService = Depends(_get_service),
):
    return ok(DepartmentResponse.model_validate(await service.update_department(department_id, data)).model_dump(mode="json"))


@router.delete("/{department_id}")
async def delete_department(
    department_id: UUID,
    current_user: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: DepartmentService = Depends(_get_service),
):
    return ok(DepartmentResponse.model_validate(await service.soft_delete_department(department_id)).model_dump(mode="json"))
