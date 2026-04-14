from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse
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
from app.repositories.import_job_repository import ImportJobRepository
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
    SendInviteResponse,
    ImportJobResponse,
    ImportJobUploadResponse,
    ImportPreviewResponse,
    PreviewRowOut,
    RowIssueOut,
    AutoCorrectionOut,
    PreviewSummary,
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
    import logging, json as _json
    from pydantic import ValidationError

    logger = logging.getLogger(__name__)

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
                if isinstance(v, (int, float)) and k not in ("joining_salary", "last_drawn_salary"):
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
            # No auth-service calls: always create employee with user_id=None (account_status=not_registered)
            # HR sends invite separately when ready.
            emp_create = item.to_employee_create(user_id_override=None)

            # Upsert: if email already exists, update profile fields but preserve user_id/account_status
            existing = await service.repo.get_by_email(item.email)
            if existing:
                from app.schemas.employee import EmployeeUpdate as _EU
                update_fields = {
                    k: v for k, v in emp_create.model_dump(exclude_unset=False).items()
                    if k not in ("user_id", "account_status", "invite_expires_at", "email") and v is not None
                }
                employee = await service.update_employee(existing.id, _EU(**update_fields))
                results.append({"index": idx, "success": True, "employee": employee, "error": None, "note": "updated existing"})
            else:
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


# ══════════════════════════════════════════════════════════════════════════════
# NEW BULK IMPORT PIPELINE ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

def _get_import_job_repo(
    current_user: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> ImportJobRepository:
    company_id = UUID(current_user.company_id)
    return ImportJobRepository(db, company_id)


def _parse_upload(content: bytes, filename: str) -> list[dict]:
    """Parse uploaded file bytes → list of raw row dicts."""
    from app.utils.import_sanitizer import validate_file, parse_csv_bytes, parse_xlsx_bytes
    ext = validate_file(filename, content)
    if ext == "xlsx":
        return parse_xlsx_bytes(content)
    return parse_csv_bytes(content)


# ── 3b. POST /employees/bulk-import/preview ──────────────────────────────────
@router.post("/bulk-import/preview", response_model=ImportPreviewResponse)
@limiter.limit("20/minute")
async def preview_bulk_import(
    request: Request,
    file: UploadFile = File(...),
    current_user: TokenPayload = Depends(
        require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)
    ),
):
    """Parse and validate file without creating any ImportJob or DB writes.
    Returns per-row validation status for the preview table UI.
    """
    import logging as _log
    from app.utils.import_sanitizer import sanitize_rows, validate_file

    logger = _log.getLogger(__name__)
    content = await file.read()

    try:
        raw_rows = _parse_upload(content, file.filename or "upload")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = sanitize_rows(raw_rows)

    # Build per-row preview output
    # Group issues by row index
    from collections import defaultdict
    issues_by_row: dict[int, list] = defaultdict(list)
    for issue in result.issues:
        issues_by_row[issue.row].append(issue)

    preview_rows = []
    for idx, row in enumerate(result.rows):
        row_issues = issues_by_row.get(idx, [])
        hard_errors = [i for i in row_issues if not i.is_warning and not i.is_cross_row]
        cross_row = [i for i in row_issues if i.is_cross_row]
        warnings = [i for i in row_issues if i.is_warning]

        if hard_errors:
            status = "error"
        elif cross_row:
            status = "cross_row"
        elif warnings:
            status = "warning"
        else:
            status = "valid"

        preview_rows.append(PreviewRowOut(
            index=idx,
            data=row,
            status=status,
            issues=[RowIssueOut(**vars(i)) for i in row_issues],
        ))

    cross_row_count = sum(1 for i in result.issues if i.is_cross_row)
    valid_count = sum(1 for r in preview_rows if r.status == "valid")
    warning_count = sum(1 for r in preview_rows if r.status == "warning")
    error_count = sum(1 for r in preview_rows if r.status == "error")

    return ImportPreviewResponse(
        rows=preview_rows,
        summary=PreviewSummary(
            valid=valid_count,
            warnings=warning_count,
            errors=error_count,
            auto_corrections=len(result.auto_corrections),
            cross_row_duplicates=cross_row_count,
        ),
        auto_corrections=[AutoCorrectionOut(**vars(c)) for c in result.auto_corrections],
    )


# ── 3a. POST /employees/bulk-import/upload ───────────────────────────────────
@router.post("/bulk-import/upload", response_model=ImportJobUploadResponse, status_code=202)
@limiter.limit("10/minute")
async def upload_bulk_import(
    request: Request,
    file: UploadFile = File(...),
    dry_run: bool = Form(False),
    duplicate_strategy: str = Form("update"),
    current_user: TokenPayload = Depends(
        require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)
    ),
    job_repo: ImportJobRepository = Depends(_get_import_job_repo),
):
    """Upload a CSV or XLSX file to start an async bulk import job.

    - Idempotent: uploading the same file twice returns the existing job.
    - dry_run=true: validates fully but writes nothing to the DB.
    - duplicate_strategy: skip | update | fail
    """
    from app.utils.import_sanitizer import sanitize_rows, compute_idempotency_key

    content = await file.read()
    company_id_str = str(current_user.company_id)

    try:
        raw_rows = _parse_upload(content, file.filename or "upload")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # ── Idempotency check ──────────────────────────────────────────────────
    idem_key = compute_idempotency_key(content, company_id_str)
    existing_job = await job_repo.get_by_idempotency_key(idem_key)
    if existing_job and not dry_run:
        return ImportJobUploadResponse(
            job_id=existing_job.id,
            total_rows=existing_job.total_rows,
            auto_corrections=existing_job.auto_corrections or [],
            cross_row_warnings=[],
            idempotent=True,
        )

    # ── Sanitize (auto-clean + Layer 1 + Layer 2 validation) ──────────────
    result = sanitize_rows(raw_rows)
    cross_row_warnings = [RowIssueOut(**vars(i)) for i in result.issues if i.is_cross_row]

    if duplicate_strategy not in ("skip", "update", "fail"):
        duplicate_strategy = "update"

    # ── Create ImportJob ───────────────────────────────────────────────────
    job = await job_repo.create(
        uploaded_by=UUID(current_user.sub),
        file_name=file.filename or "upload",
        file_size_bytes=len(content),
        idempotency_key=idem_key,
        schema_version="v1",
        status="pending",
        duplicate_strategy=duplicate_strategy,
        total_rows=len(result.rows),
        auto_corrections=[vars(c) for c in result.auto_corrections],
    )

    # ── Enqueue Celery task ────────────────────────────────────────────────
    from app.tasks.import_tasks import process_bulk_import
    process_bulk_import.apply_async(
        args=[str(job.id), result.rows, company_id_str, dry_run, duplicate_strategy],
        queue="employee_import",
    )

    return ImportJobUploadResponse(
        job_id=job.id,
        total_rows=len(result.rows),
        auto_corrections=[AutoCorrectionOut(**vars(c)) for c in result.auto_corrections],
        cross_row_warnings=cross_row_warnings,
        idempotent=False,
    )


# ── 3c. GET /employees/bulk-import/jobs/{job_id} ─────────────────────────────
@router.get("/bulk-import/jobs/{job_id}", response_model=ImportJobResponse)
async def get_import_job(
    job_id: UUID,
    job_repo: ImportJobRepository = Depends(_get_import_job_repo),
):
    """Poll the status and progress of an import job."""
    job = await job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")
    return ImportJobResponse.model_validate(job)


# ── 3d. GET /employees/bulk-import/jobs ──────────────────────────────────────
@router.get("/bulk-import/jobs", response_model=List[ImportJobResponse])
async def list_import_jobs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    job_repo: ImportJobRepository = Depends(_get_import_job_repo),
):
    """List recent import jobs for the company (audit log)."""
    jobs = await job_repo.list_by_company(limit=limit, offset=offset)
    return [ImportJobResponse.model_validate(j) for j in jobs]


# ── 3e. GET /employees/bulk-import/jobs/{job_id}/errors.csv ──────────────────
@router.get("/bulk-import/jobs/{job_id}/errors.csv")
async def download_import_errors(
    job_id: UUID,
    job_repo: ImportJobRepository = Depends(_get_import_job_repo),
):
    """Download the error log for an import job as a CSV file."""
    import csv
    import io as _io

    job = await job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")

    error_log = job.error_log or []
    output = _io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["row_number", "field", "error", "suggested_fix", "original_value"],
        extrasaction="ignore",
    )
    writer.writeheader()
    for entry in error_log:
        writer.writerow({
            "row_number": entry.get("row", ""),
            "field": entry.get("field", ""),
            "error": entry.get("error", ""),
            "suggested_fix": entry.get("suggested_fix", ""),
            "original_value": entry.get("original_value", ""),
        })

    def _iter():
        yield output.getvalue().encode("utf-8-sig")  # BOM for Excel compatibility

    return StreamingResponse(
        _iter(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="import_{job_id}_errors.csv"'},
    )


# ── 3f. GET /employees/bulk-import/failed-chunks/{job_id} ────────────────────
@router.get("/bulk-import/failed-chunks/{job_id}")
async def get_failed_chunks(
    job_id: UUID,
    job_repo: ImportJobRepository = Depends(_get_import_job_repo),
):
    """Return DLQ / error entries for a failed import job (for admin debugging)."""
    job = await job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")
    return {
        "job_id": str(job_id),
        "status": job.status,
        "error_log": job.error_log or [],
    }


# ──────────── GET /employees ────────────
@router.get("", response_model=EmployeeListResponse)
async def list_employees(
    pagination: PaginationParams = Depends(),
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    employment_status: Optional[str] = Query(None, description="Filter by status (active, inactive, terminated)"),
    account_status: Optional[str] = Query(None, description="Filter by account status (not_registered, invited, active, suspended)"),
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
        account_status=account_status,
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


# ──────────── POST /employees/link-account ────────────
# MUST appear before /{employee_id} to avoid routing ambiguity
@router.post("/link-account", response_model=EmployeeResponse)
async def link_employee_account(
    current_user: TokenPayload = Depends(get_current_user),
    service: EmployeeService = Depends(_get_service),
):
    """Called by employee app after accepting an invite. JWT has user_id, email, company_id.
    Idempotent — safe to retry if network failure occurred on first attempt.
    """
    return await service.link_account(
        user_id=UUID(current_user.sub),
        email=current_user.email,
        company_id=current_user.company_id,
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


# ──────────── POST /employees/{id}/send-invite ────────────
@router.post("/{employee_id}/send-invite", response_model=SendInviteResponse)
@limiter.limit("10/minute")
async def send_employee_invite(
    request: Request,
    employee_id: UUID,
    current_user: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: EmployeeService = Depends(_get_service),
):
    """Send a portal invite link. Returns invite_url for HR to copy and share.
    Also works as a first-send — allowed for not_registered and invited states.
    """
    auth_header = request.headers.get("Authorization", "")
    inviter_jwt = auth_header.removeprefix("Bearer ").strip()
    return await service.send_invite(employee_id, inviter_jwt=inviter_jwt)


# ──────────── POST /employees/{id}/resend-invite ────────────
@router.post("/{employee_id}/resend-invite", response_model=SendInviteResponse)
@limiter.limit("10/minute")
async def resend_employee_invite(
    request: Request,
    employee_id: UUID,
    current_user: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: EmployeeService = Depends(_get_service),
):
    """Resend invite — generates a new token. Old token remains valid until it expires."""
    auth_header = request.headers.get("Authorization", "")
    inviter_jwt = auth_header.removeprefix("Bearer ").strip()
    return await service.send_invite(employee_id, inviter_jwt=inviter_jwt)


# ──────────── POST /employees/{id}/revoke-invite ────────────
@router.post("/{employee_id}/revoke-invite")
@limiter.limit("10/minute")
async def revoke_employee_invite(
    request: Request,
    employee_id: UUID,
    current_user: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: EmployeeService = Depends(_get_service),
):
    """Clear invite state — employee returns to not_registered.
    Does not invalidate the token in auth-service (no revoke API there).
    If employee uses the old link, link_account will fail gracefully.
    """
    return await service.revoke_invite(employee_id)


# ──────────── POST /employees/{id}/disable-account ────────────
@router.post("/{employee_id}/disable-account", response_model=EmployeeResponse)
@limiter.limit("10/minute")
async def disable_employee_account(
    request: Request,
    employee_id: UUID,
    current_user: TokenPayload = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR)),
    service: EmployeeService = Depends(_get_service),
):
    """Disable employee's auth account (sets is_active=False) and mark as suspended."""
    return await service.disable_account(employee_id)


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
