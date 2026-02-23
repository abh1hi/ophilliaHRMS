from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user, require_role, TokenPayload
from app.core.constants import UserRole
from app.services.department_service import DepartmentService
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentListResponse,
)

router = APIRouter(prefix="/departments", tags=["departments"])


def _get_service(db: AsyncSession = Depends(get_db)) -> DepartmentService:
    return DepartmentService(db)


# ──────────── POST /departments ────────────
@router.post("", response_model=DepartmentResponse, status_code=201)
async def create_department(
    data: DepartmentCreate,
    current_user: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN)),
    service: DepartmentService = Depends(_get_service),
):
    """Create a new department. Requires HR or Super Admin role."""
    return await service.create_department(data)


# ──────────── GET /departments ────────────
@router.get("", response_model=DepartmentListResponse)
async def list_departments(
    current_user: TokenPayload = Depends(get_current_user),
    service: DepartmentService = Depends(_get_service),
):
    """List all departments. Any authenticated user can access."""
    departments, total = await service.list_departments()
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
    current_user: TokenPayload = Depends(require_role(UserRole.HR, UserRole.SUPER_ADMIN)),
    service: DepartmentService = Depends(_get_service),
):
    """Update a department. Requires HR or Super Admin role."""
    return await service.update_department(department_id, data)
