from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.dependencies import (
    get_current_user,
    require_role,
    TokenPayload,
    get_db_with_tenant
)
from app.core.constants import UserRole
from app.services.department_service import DepartmentService
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentListResponse,
)

router = APIRouter(prefix="/departments", tags=["departments"])


def _get_service(db: AsyncSession = Depends(get_db_with_tenant)) -> DepartmentService:
    return DepartmentService(db)


# ──────────── POST /departments ────────────
@router.post("", response_model=DepartmentResponse, status_code=201)
async def create_department(
    data: DepartmentCreate,
    current_user: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: DepartmentService = Depends(_get_service),
):
    """Create a new department. Requires HR or Super Admin role."""
    return await service.create_department(data)


# ──────────── GET /departments ────────────
@router.get("", response_model=DepartmentListResponse)
async def list_departments(
    include_inactive: bool = Query(False, description="Include soft-deleted departments"),
    current_user: TokenPayload = Depends(get_current_user),
    service: DepartmentService = Depends(_get_service),
):
    """List all departments. Any authenticated user can access."""
    departments, total = await service.list_departments(include_inactive=include_inactive)
    return DepartmentListResponse(total=total, departments=departments)


# ──────────── GET /departments/{id} ────────────
@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: DepartmentService = Depends(_get_service),
):
    """Get a department by ID. Any authenticated user can access."""
    return await service.get_department(department_id)


# ──────────── PATCH /departments/{id} ────────────
@router.patch("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: UUID,
    data: DepartmentUpdate,
    current_user: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: DepartmentService = Depends(_get_service),
):
    """Update a department. Requires HR or Super Admin role."""
    return await service.update_department(department_id, data)


# ──────────── DELETE /departments/{id} ────────────
@router.delete("/{department_id}", response_model=DepartmentResponse)
async def delete_department(
    department_id: UUID,
    current_user: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: DepartmentService = Depends(_get_service),
):
    """Soft-delete a department (sets is_active = 0). Requires HR or Super Admin role."""
    return await service.soft_delete_department(department_id)
