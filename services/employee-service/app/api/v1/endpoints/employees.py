from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.dependencies import (
    get_current_user,
    require_role,
    verify_service_token,
    TokenPayload,
    get_db_with_tenant
)
from app.core.responses import ok
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.department_repository import DepartmentRepository
from app.core.constants import UserRole
from app.services.employee_service import EmployeeService
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeListResponse,
    BulkEmployeeResponse,
    BulkEmployeeResult,
    BulkEmployeeImportItem,
)
from app.utils.pagination import PaginationParams
from app.core.rate_limit import limiter

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
@limiter.limit("30/minute")
async def create_employee(
    request: Request,
    data: EmployeeCreate,
    current_user: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: EmployeeService = Depends(_get_service),
):
    """Create a new employee profile. Requires HR or Super Admin role."""
    return await service.create_employee(data)


# ──────────── POST /employees/bulk ────────────
@router.post("/bulk", response_model=BulkEmployeeResponse, status_code=200)
@limiter.limit("10/minute")
async def bulk_create_employees(
    request: Request,
    employees: List[EmployeeCreate],
    current_user: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: EmployeeService = Depends(_get_service),
):
    """Bulk import employees from JSON array. Returns per-row results.
    Partial failures do not roll back successful rows.
    """
    raw_results = await service.bulk_create_employees(employees)
    results = [BulkEmployeeResult(**r) for r in raw_results]
    succeeded = sum(1 for r in results if r.success)
    return BulkEmployeeResponse(
        total=len(results),
        succeeded=succeeded,
        failed=len(results) - succeeded,
        results=results,
    )


# ──────────── POST /employees/bulk-import (field-mapped Excel/CSV import) ────────────
@router.post("/bulk-import", response_model=BulkEmployeeResponse, status_code=200)
@limiter.limit("10/minute")
async def bulk_import_employees(
    request: Request,
    current_user: TokenPayload = Depends(
        require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)
    ),
    service: EmployeeService = Depends(_get_service),
):
    """Bulk import employees from field-mapped Excel/CSV data.
    Accepts raw JSON array — each row is validated individually so one bad row
    does not block the rest. Creates auth accounts when initial_password is set.
    """
    import httpx, logging, json as _json
    from pydantic import ValidationError
    from app.core.config import settings

    logger = logging.getLogger(__name__)
    company_id = getattr(current_user, "company_id", None)

    raw_body = await request.body()
    try:
        rows = _json.loads(raw_body)
    except Exception:
        raise HTTPException(status_code=400, detail="Request body must be a JSON array")
    if not isinstance(rows, list):
        raise HTTPException(status_code=400, detail="Request body must be a JSON array")

    results: list = []
    db = service.repo.db  # grab session for rollback on failures

    for idx, raw in enumerate(rows):
        # Guard: each row must be a dict (object), not a string or other type
        if not isinstance(raw, dict):
            results.append({"index": idx, "success": False, "employee": None, "error": f"Row {idx}: expected JSON object, got {type(raw).__name__}"})
            continue

        try:
            # Coerce numeric values to strings for fields that expect str
            for k, v in list(raw.items()):
                if isinstance(v, (int, float)) and k not in (
                    "joining_salary", "last_drawn_salary",
                ):
                    raw[k] = str(int(v)) if isinstance(v, float) and v == int(v) else str(v)

            item = BulkEmployeeImportItem(**raw)
        except (ValidationError, Exception) as e:
            err_msg = str(e)
            if hasattr(e, "errors"):
                errs = e.errors()  # type: ignore
                err_msg = "; ".join(f"{'.'.join(str(p) for p in er['loc'])}: {er['msg']}" for er in errs[:3])
            results.append({"index": idx, "success": False, "employee": None, "error": f"Validation: {err_msg}"})
            continue

        try:
            user_id = item.user_id

            # Step 1: Create auth account if password is provided
            if item.initial_password and not user_id:
                async with httpx.AsyncClient(timeout=10) as client:
                    auth_resp = await client.post(
                        f"{settings.AUTH_SERVICE_URL}/api/v1/auth/register",
                        json={
                            "email": item.email,
                            "password": item.initial_password,
                            "role": item.role or "employee",
                            **({"company_id": str(company_id)} if company_id else {}),
                        },
                    )
                    if auth_resp.status_code in (200, 201):
                        body = auth_resp.json()
                        data = body.get("data") or body
                        user_id = data.get("id")
                    else:
                        body = auth_resp.json()
                        err = body.get("detail") or body.get("error", {}).get("message", "Auth registration failed")
                        results.append({"index": idx, "success": False, "employee": None, "error": f"Auth: {err}"})
                        continue

            # Step 2: Create employee profile
            emp_create = item.to_employee_create(
                user_id_override=UUID(str(user_id)) if user_id else None
            )
            employee = await service.create_employee(emp_create)
            results.append({"index": idx, "success": True, "employee": employee, "error": None})

        except Exception as e:
            logger.warning(f"Bulk import row {idx} failed: {e}")
            results.append({"index": idx, "success": False, "employee": None, "error": str(e)})
            # Roll back the failed transaction so subsequent rows can proceed
            await db.rollback()

    from app.schemas.employee import BulkEmployeeResult as _BER
    typed_results = [_BER(**r) for r in results]
    succeeded = sum(1 for r in typed_results if r.success)
    return BulkEmployeeResponse(
        total=len(typed_results),
        succeeded=succeeded,
        failed=len(typed_results) - succeeded,
        results=typed_results,
    )


# ──────────── GET /employees ────────────
@router.get("", response_model=EmployeeListResponse)
async def list_employees(
    pagination: PaginationParams = Depends(),
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    employment_status: Optional[str] = Query(None, description="Filter by status (active, inactive, terminated)"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.MANAGER)
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


# ──────────── GET /employees/stats ────────────
@router.get("/stats")
async def get_employee_stats(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Company-level employee and department counts."""
    emp_repo = EmployeeRepository(db)
    dept_repo = DepartmentRepository(db)
    _, total_employees = await emp_repo.get_all(skip=0, limit=1)
    _, active_employees = await emp_repo.get_all(skip=0, limit=1, employment_status="active")
    _, total_departments = await dept_repo.get_all(include_inactive=False)
    return ok({
        "total_employees": total_employees,
        "active_employees": active_employees,
        "total_departments": total_departments,
    })


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
@limiter.limit("30/minute")
async def update_employee(
    request: Request,
    employee_id: UUID,
    data: EmployeeUpdate,
    current_user: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: EmployeeService = Depends(_get_service),
):
    """Update an employee's profile. Requires HR or Super Admin role."""
    return await service.update_employee(employee_id, data)


# ──────────── DELETE /employees/{id} ────────────
@router.delete("/{employee_id}", response_model=EmployeeResponse)
@limiter.limit("30/minute")
async def deactivate_employee(
    request: Request,
    employee_id: UUID,
    current_user: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: EmployeeService = Depends(_get_service),
):
    """Deactivate (soft-delete) an employee. Requires HR or Super Admin role."""
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
