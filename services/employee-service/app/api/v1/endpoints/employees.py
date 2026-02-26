from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.dependencies import (
    get_current_user,
    require_role,
    verify_service_token,
    TokenPayload,
    get_db_with_tenant
)
from app.core.constants import UserRole
from app.services.employee_service import EmployeeService
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeListResponse,
)
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/employees", tags=["employees"])


def _get_service(db: AsyncSession = Depends(get_db_with_tenant)) -> EmployeeService:
    # Event publisher injected at app level — not here for simplicity.
    # For production, inject via app.state.event_publisher.
    return EmployeeService(db)


# ──────────── GET /employees/me ────────────
@router.get("/me", response_model=EmployeeResponse)
async def get_my_profile(
    current_user: TokenPayload = Depends(get_current_user),
    service: EmployeeService = Depends(_get_service),
):
    """Get the authenticated user's own employee profile."""
    return await service.get_employee_by_user_id(UUID(current_user.sub))


# ──────────── POST /employees ────────────
@router.post("", response_model=EmployeeResponse, status_code=201)
async def create_employee(
    data: EmployeeCreate,
    current_user: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN)),
    service: EmployeeService = Depends(_get_service),
):
    """Create a new employee profile. Requires HR or Super Admin role."""
    return await service.create_employee(data)


# ──────────── GET /employees ────────────
@router.get("", response_model=EmployeeListResponse)
async def list_employees(
    pagination: PaginationParams = Depends(),
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    employment_status: Optional[str] = Query(None, description="Filter by status (active, inactive, terminated)"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.MANAGER)
    ),
    service: EmployeeService = Depends(_get_service),
):
    """List employees with pagination and filters. Requires HR, Super Admin, or Manager role."""
    employees, total = await service.list_employees(
        skip=pagination.skip,
        limit=pagination.limit,
        department_id=department_id,
        employment_status=employment_status,
        search=search,
    )
    return EmployeeListResponse(
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
        employees=employees,
    )


# ──────────── GET /employees/{id} ────────────
@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: EmployeeService = Depends(_get_service),
):
    """Get an employee by ID. Any authenticated user can access."""
    return await service.get_employee(employee_id)


# ──────────── PATCH /employees/{id} ────────────
@router.patch("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: UUID,
    data: EmployeeUpdate,
    current_user: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN)),
    service: EmployeeService = Depends(_get_service),
):
    """Update an employee's profile. Requires HR or Super Admin role."""
    return await service.update_employee(employee_id, data)


# ──────────── DELETE /employees/{id} ────────────
@router.delete("/{employee_id}", response_model=EmployeeResponse)
async def deactivate_employee(
    employee_id: UUID,
    current_user: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN)),
    service: EmployeeService = Depends(_get_service),
):
    """Deactivate (soft-delete) an employee. Requires Super Admin role."""
    return await service.deactivate_employee(employee_id)


# ──────────── INTERNAL: GET /employees/internal/{user_id} ────────────
@router.get(
    "/internal/{user_id}",
    response_model=EmployeeResponse,
    dependencies=[Depends(verify_service_token)],
    include_in_schema=False,
)
async def get_employee_internal(
    user_id: UUID,
    service: EmployeeService = Depends(_get_service),
):
    """Internal endpoint for service-to-service lookup by user_id.
    Protected by X-Service-Token header (not JWT).
    """
    return await service.get_employee_by_user_id(user_id)
