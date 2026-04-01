from typing import Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user, require_role, TokenPayload
from app.api.v1.dependencies import get_db_with_tenant
from app.core.constants import UserRole
from app.services.attendance_service import AttendanceService, GeofenceService
from app.services.policy_service import PolicyService, PolicyTemplateService, PolicyExceptionService
from app.services.task_service import TaskService
from app.schemas.attendance import (
    ClockInRequest,
    ClockOutRequest,
    ManualAttendanceCreate,
    SchoolModeAttendanceCreate,
    AttendanceUpdate,
    AttendanceResponse,
    AttendanceListResponse,
    GeofenceCreate,
    GeofenceUpdate,
    GeofenceResponse,
    GeofenceListResponse,
    PolicyCreate,
    PolicyUpdate,
    PolicyResponse,
    PolicyListResponse,
    PolicyAuditLogListResponse,
    PolicyTemplateCreate,
    PolicyTemplateUpdate,
    PolicyTemplateResponse,
    PolicyTemplateListResponse,
    ApplyTemplateRequest,
    PolicyExceptionCreate,
    PolicyExceptionUpdate,
    PolicyExceptionResponse,
    PolicyExceptionListResponse,
    TaskCreate,
    TaskUpdate,
    TaskCompleteUpdate,
    TaskResponse,
    TaskListResponse,
    TaskAssignRequest,
    ProductivityReportResponse,
    AlertsResponse,
    BulkSchoolModeRequest,
    BulkSchoolModeResponse,
    BulkSchoolModeResult,
    TaskTemplateCreate,
    TaskTemplateUpdate,
    TaskTemplateResponse,
    TaskTemplateListResponse,
    AdminKPIResponse,
    AttendanceTrendResponse,
    DailyStatusBreakdown,
    PerformersResponse,
    TodayShiftsResponse,
)
from app.services.task_template_service import TaskTemplateService
from app.utils.pagination import PaginationParams
from app.core.rate_limit import limiter

router = APIRouter(prefix="/attendance", tags=["attendance"])


# ── Dependency helpers ───────────────────────────────────────────────────────

def _get_service(db: AsyncSession = Depends(get_db_with_tenant)) -> AttendanceService:
    return AttendanceService(db)


def _get_geofence_service(db: AsyncSession = Depends(get_db_with_tenant)) -> GeofenceService:
    return GeofenceService(db)


def _get_policy_service(db: AsyncSession = Depends(get_db_with_tenant)) -> PolicyService:
    return PolicyService(db)


def _get_policy_template_service(db: AsyncSession = Depends(get_db_with_tenant)) -> PolicyTemplateService:
    return PolicyTemplateService(db)


def _get_policy_exception_service(db: AsyncSession = Depends(get_db_with_tenant)) -> PolicyExceptionService:
    return PolicyExceptionService(db)


def _get_task_service(db: AsyncSession = Depends(get_db_with_tenant)) -> TaskService:
    return TaskService(db)


def _get_template_service(db: AsyncSession = Depends(get_db_with_tenant)) -> TaskTemplateService:
    return TaskTemplateService(db)


# ──────────────────── ATTENDANCE RECORDS ────────────────────

@router.post("/clock-in", response_model=AttendanceResponse, status_code=201)
@limiter.limit("5/minute")
async def clock_in(
    request: Request,
    data: ClockInRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: AttendanceService = Depends(_get_service),
):
    """Punch in for today. Validates geofence if required by policy.
    Saves GPS coordinates and optional human-readable location name.
    """
    return await service.clock_in(
        employee_id=UUID(current_user.sub),
        data=data,
    )


@router.post("/clock-out", response_model=AttendanceResponse)
@limiter.limit("5/minute")
async def clock_out(
    request: Request,
    data: ClockOutRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: AttendanceService = Depends(_get_service),
):
    """Punch out for today.
    Accepts day_rating (1-5) and optional inline task_completions list.
    Auto-computes work hours and overtime.
    """
    return await service.clock_out(
        employee_id=UUID(current_user.sub),
        data=data,
    )


@router.get("/me/today", response_model=Optional[AttendanceResponse])
async def get_my_today(
    current_user: TokenPayload = Depends(get_current_user),
    service: AttendanceService = Depends(_get_service),
):
    """Get today's attendance record (with tasks) for the authenticated user."""
    record = await service.get_today_record(UUID(current_user.sub))
    if not record:
        return None
    return record


@router.get("/me/today/shifts", response_model=TodayShiftsResponse)
async def get_my_today_shifts(
    current_user: TokenPayload = Depends(get_current_user),
    service: AttendanceService = Depends(_get_service),
):
    """Get all shift records for today with shift metadata (max shifts, can start new)."""
    return await service.get_today_shifts(UUID(current_user.sub))


@router.get("/me", response_model=AttendanceListResponse)
async def get_my_records(
    pagination: PaginationParams = Depends(),
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    current_user: TokenPayload = Depends(get_current_user),
    service: AttendanceService = Depends(_get_service),
):
    """Get authenticated user's attendance history (paginated)."""
    records, total = await service.get_my_records(
        employee_id=UUID(current_user.sub),
        skip=pagination.skip,
        limit=pagination.limit,
        date_from=date_from,
        date_to=date_to,
    )
    return AttendanceListResponse(
        total=total, skip=pagination.skip, limit=pagination.limit, records=records
    )


@router.get("", response_model=AttendanceListResponse)
async def list_all_attendance(
    pagination: PaginationParams = Depends(),
    employee_id: Optional[UUID] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    status: Optional[str] = Query(None, description="Filter: present, late, half_day, absent"),
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.MANAGER)
    ),
    service: AttendanceService = Depends(_get_service),
):
    """List all attendance records (admin view). Paginated with filters."""
    records, total = await service.list_all(
        skip=pagination.skip,
        limit=pagination.limit,
        employee_id=employee_id,
        date_from=date_from,
        date_to=date_to,
        status=status,
    )
    return AttendanceListResponse(
        total=total, skip=pagination.skip, limit=pagination.limit, records=records
    )


@router.post("/manual", response_model=AttendanceResponse, status_code=201)
async def manual_entry(
    data: ManualAttendanceCreate,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: AttendanceService = Depends(_get_service),
):
    """Create a manual/backdated attendance entry. HR/Super Admin only."""
    return await service.manual_entry(data, created_by=current_user.sub)


@router.post("/school-mode", response_model=AttendanceResponse, status_code=201)
async def school_mode_entry(
    data: SchoolModeAttendanceCreate,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: AttendanceService = Depends(_get_service),
):
    """Mark an employee's attendance on their behalf. HR/Super Admin only."""
    return await service.mark_school_mode_attendance(data, created_by=current_user.sub)


# ──────────── POST /attendance/school-mode/bulk ────────────
@router.post("/school-mode/bulk", response_model=BulkSchoolModeResponse)
async def bulk_school_mode_entry(
    data: BulkSchoolModeRequest,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: AttendanceService = Depends(_get_service),
):
    """Mark attendance for multiple employees at once. HR/Super Admin only.
    Partial failures do not roll back successful rows.
    """
    results = []
    for idx, item in enumerate(data.items):
        try:
            entry = SchoolModeAttendanceCreate(
                employee_id=item.employee_id,
                status=item.status,
                notes=item.notes,
            )
            await service.mark_school_mode_attendance(entry, created_by=current_user.sub)
            results.append(BulkSchoolModeResult(
                index=idx, employee_id=item.employee_id, success=True
            ))
        except Exception as e:
            error_msg = e.detail if hasattr(e, "detail") else str(e)
            results.append(BulkSchoolModeResult(
                index=idx, employee_id=item.employee_id, success=False, error=error_msg
            ))
    succeeded = sum(1 for r in results if r.success)
    return BulkSchoolModeResponse(
        total=len(results), succeeded=succeeded, failed=len(results) - succeeded, results=results,
    )


# ──────────────────── TASKS ────────────────────

@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def add_task(
    data: TaskCreate,
    record_id: UUID = Query(..., description="The attendance record to attach this task to"),
    current_user: TokenPayload = Depends(get_current_user),
    service: TaskService = Depends(_get_task_service),
):
    """Add a daily task to today's attendance record.

    - Employees add tasks to their own record.
    - Managers / Admins can attach tasks to any employee's record (pass record_id + data).
    """
    employee_uuid = UUID(current_user.sub)
    assigned_by: Optional[UUID] = None

    if current_user.role in (UserRole.HR.value, UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.MANAGER.value):
        # HR/Admin/Manager can assign tasks; the task employee_id is inferred from the record
        assigned_by = employee_uuid

    task = await service.add_task(
        record_id=record_id,
        employee_id=employee_uuid,
        data=data,
        assigned_by=assigned_by,
    )

    # Trigger state transition: PUNCHED_IN → ACTIVE after first task is added
    att_service = AttendanceService(service.task_repo.db)
    await att_service.update_state(record_id, employee_uuid)

    return task


@router.get("/tasks/today", response_model=TaskListResponse)
async def get_today_tasks(
    current_user: TokenPayload = Depends(get_current_user),
    attendance_service: AttendanceService = Depends(_get_service),
    task_service: TaskService = Depends(_get_task_service),
):
    """Get all tasks for the authenticated employee's today's record."""
    record = await attendance_service.get_today_record(UUID(current_user.sub))
    if not record:
        return TaskListResponse(total=0, tasks=[])
    tasks = await task_service.list_tasks_for_record(record.id)
    return TaskListResponse(total=len(tasks), tasks=tasks)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    service: TaskService = Depends(_get_task_service),
):
    """Edit a task's pre-completion details (title, description, expenses)."""
    return await service.update_task(
        task_id=task_id,
        employee_id=UUID(current_user.sub),
        data=data,
    )


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: TaskService = Depends(_get_task_service),
):
    """Delete a task.  Employees can only delete their own tasks."""
    await service.delete_task(
        task_id=task_id,
        employee_id=UUID(current_user.sub),
    )


@router.patch("/tasks/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: UUID,
    data: TaskCompleteUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    service: TaskService = Depends(_get_task_service),
):
    """Mark a task's completion at punch-out.
    Sets status (completed / partially_completed / not_completed), notes, actual expenses.
    """
    return await service.complete_task(
        task_id=task_id,
        employee_id=UUID(current_user.sub),
        data=data,
    )


@router.post("/tasks/assign", response_model=TaskResponse, status_code=201)
async def assign_task_to_employee(
    data: TaskAssignRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: TaskService = Depends(_get_task_service),
):
    """Assign a task to another employee's today attendance record.

    Any authenticated user (employee, manager, super admin) can assign tasks
    to a colleague who is already clocked in today.
    """
    return await service.assign_task_to_employee(
        data=data,
        assigned_by=UUID(current_user.sub),
    )


# ──────────────────── REPORTS ────────────────────

@router.get("/reports/productivity", response_model=ProductivityReportResponse)
async def productivity_report(
    year: int = Query(..., description="Year, e.g. 2026"),
    month: int = Query(..., ge=1, le=12, description="Month 1–12"),
    employee_id: Optional[UUID] = Query(None, description="Filter to single employee"),
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.MANAGER)
    ),
    service: AttendanceService = Depends(_get_service),
):
    """Monthly task productivity report per employee.
    Shows task completion rates, daily ratings, and expenses.
    HR / Manager / Super Admin only.
    """
    return await service.get_productivity_report(year=year, month=month, employee_id=employee_id)


# ──────────────────── ALERTS ────────────────────

@router.get("/alerts", response_model=AlertsResponse)
async def get_alerts(
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.MANAGER)
    ),
    service: AttendanceService = Depends(_get_service),
):
    """Today's attendance alerts: late punch-ins and employees who haven't punched out.
    HR / Manager / Super Admin only.
    """
    return await service.get_alerts()


# ──────────────────── GEOFENCES ────────────────────

@router.post("/geofences", response_model=GeofenceResponse, status_code=201)
async def create_geofence(
    data: GeofenceCreate,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: GeofenceService = Depends(_get_geofence_service),
):
    """Create a new geofence location (e.g. office). HR/Super Admin only."""
    return await service.create_geofence(data)


@router.get("/geofences", response_model=GeofenceListResponse)
async def list_geofences(
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = Query(False, description="Include soft-deleted geofences"),
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: GeofenceService = Depends(_get_geofence_service),
):
    """List geofence locations. By default only active ones."""
    geofences, total = await service.list_geofences(skip=skip, limit=limit, include_inactive=include_inactive)
    return GeofenceListResponse(total=total, geofences=geofences)


@router.patch("/geofences/{geofence_id}", response_model=GeofenceResponse)
async def update_geofence(
    geofence_id: UUID,
    data: GeofenceUpdate,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: GeofenceService = Depends(_get_geofence_service),
):
    """Update a geofence's name, coordinates, or radius. HR/Super Admin only."""
    return await service.update_geofence(geofence_id, data)


@router.delete("/geofences/{geofence_id}", response_model=GeofenceResponse)
async def delete_geofence(
    geofence_id: UUID,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: GeofenceService = Depends(_get_geofence_service),
):
    """Soft-delete a geofence (set is_active = false). HR/Super Admin only."""
    return await service.soft_delete_geofence(geofence_id)


# ──────────────────── ATTENDANCE POLICIES ────────────────────

@router.post("/policies", response_model=PolicyResponse, status_code=201)
async def create_policy(
    data: PolicyCreate,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: PolicyService = Depends(_get_policy_service),
):
    """Assign attendance method (manual/geofence/both) to dept or employee.
    Returns 409 if a policy for the same scope already exists.
    """
    return await service.create_policy(data, changed_by=UUID(current_user.sub))


@router.get("/policies", response_model=PolicyListResponse)
async def list_policies(
    skip: int = 0,
    limit: int = 100,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: PolicyService = Depends(_get_policy_service),
):
    """List all attendance policies."""
    policies, total = await service.list_policies(skip=skip, limit=limit)
    return PolicyListResponse(total=total, policies=policies)


@router.patch("/policies/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: UUID,
    data: PolicyUpdate,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: PolicyService = Depends(_get_policy_service),
):
    """Update an attendance policy's method, times, or scope. HR/Super Admin only."""
    return await service.update_policy(policy_id, data, changed_by=UUID(current_user.sub))


@router.delete("/policies/{policy_id}", status_code=204)
async def delete_policy(
    policy_id: UUID,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: PolicyService = Depends(_get_policy_service),
):
    """Hard-delete an attendance policy (config, not data). HR/Super Admin only."""
    await service.delete_policy(policy_id, changed_by=UUID(current_user.sub))


@router.get("/policies/{policy_id}/audit-log", response_model=PolicyAuditLogListResponse)
async def get_policy_audit_log(
    policy_id: UUID,
    skip: int = 0,
    limit: int = 50,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: PolicyService = Depends(_get_policy_service),
):
    """Full audit trail for a specific policy (creates, updates, deletes)."""
    logs, total = await service.get_audit_log(policy_id, skip=skip, limit=limit)
    return PolicyAuditLogListResponse(total=total, items=logs)


# ──────────────────── POLICY TEMPLATES ────────────────────

@router.post("/policy-templates", response_model=PolicyTemplateResponse, status_code=201)
async def create_policy_template(
    data: PolicyTemplateCreate,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: PolicyTemplateService = Depends(_get_policy_template_service),
):
    """Create a reusable policy template. HR/Admin only."""
    return await service.create_template(data, changed_by=UUID(current_user.sub))


@router.get("/policy-templates", response_model=PolicyTemplateListResponse)
async def list_policy_templates(
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = False,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: PolicyTemplateService = Depends(_get_policy_template_service),
):
    """List all active policy templates."""
    templates, total = await service.list_templates(
        skip=skip, limit=limit, include_inactive=include_inactive
    )
    return PolicyTemplateListResponse(total=total, templates=templates)


@router.patch("/policy-templates/{template_id}", response_model=PolicyTemplateResponse)
async def update_policy_template(
    template_id: UUID,
    data: PolicyTemplateUpdate,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: PolicyTemplateService = Depends(_get_policy_template_service),
):
    """Update a policy template. HR/Admin only."""
    return await service.update_template(template_id, data)


@router.delete("/policy-templates/{template_id}", response_model=PolicyTemplateResponse)
async def delete_policy_template(
    template_id: UUID,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: PolicyTemplateService = Depends(_get_policy_template_service),
):
    """Soft-delete a policy template (sets is_active=False). HR/Admin only."""
    return await service.delete_template(template_id)


@router.post("/departments/{dept_id}/apply-policy-template", response_model=PolicyResponse, status_code=201)
async def apply_policy_template_to_department(
    dept_id: UUID,
    data: ApplyTemplateRequest,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: PolicyTemplateService = Depends(_get_policy_template_service),
):
    """Stamp a new AttendancePolicy from a template onto a department.
    Returns 409 if the department already has a policy.
    """
    return await service.apply_template_to_department(
        dept_id=dept_id,
        template_id=data.template_id,
        changed_by=UUID(current_user.sub),
    )


# ──────────────────── POLICY EXCEPTIONS ────────────────────

@router.post("/policy-exceptions", response_model=PolicyExceptionResponse, status_code=201)
async def create_policy_exception(
    data: PolicyExceptionCreate,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: PolicyExceptionService = Depends(_get_policy_exception_service),
):
    """Create a temporary policy override for an employee (e.g. medical, WFH). HR/Admin only."""
    return await service.create_exception(data, approved_by=UUID(current_user.sub))


@router.get("/policy-exceptions", response_model=PolicyExceptionListResponse)
async def list_policy_exceptions(
    skip: int = 0,
    limit: int = 100,
    employee_id: Optional[UUID] = Query(None, description="Filter by employee"),
    include_inactive: bool = Query(False, description="Include deactivated exceptions"),
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: PolicyExceptionService = Depends(_get_policy_exception_service),
):
    """List all policy exceptions. HR/Admin only."""
    items, total = await service.list_exceptions(
        skip=skip, limit=limit, employee_id=employee_id, include_inactive=include_inactive
    )
    return PolicyExceptionListResponse(total=total, items=items)


@router.get("/policy-exceptions/{exception_id}", response_model=PolicyExceptionResponse)
async def get_policy_exception(
    exception_id: UUID,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: PolicyExceptionService = Depends(_get_policy_exception_service),
):
    """Get a specific policy exception by ID. HR/Admin only."""
    return await service.get_exception(exception_id)


@router.patch("/policy-exceptions/{exception_id}", response_model=PolicyExceptionResponse)
async def update_policy_exception(
    exception_id: UUID,
    data: PolicyExceptionUpdate,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: PolicyExceptionService = Depends(_get_policy_exception_service),
):
    """Update a policy exception (e.g. extend to_date). HR/Admin only."""
    return await service.update_exception(exception_id, data)


@router.delete("/policy-exceptions/{exception_id}", status_code=204)
async def delete_policy_exception(
    exception_id: UUID,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: PolicyExceptionService = Depends(_get_policy_exception_service),
):
    """Hard-delete a policy exception. HR/Admin only."""
    await service.delete_exception(exception_id)


# ──────────────────── TASK TEMPLATES ────────────────────

@router.post("/templates", response_model=TaskTemplateResponse, status_code=201)
async def create_template(
    data: TaskTemplateCreate,
    current_user: TokenPayload = Depends(get_current_user),
    service: TaskTemplateService = Depends(_get_template_service),
):
    """Create a task template. Employees create personal templates; admins can create shared ones."""
    is_admin = current_user.role in (UserRole.HR.value, UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)
    if data.is_shared and not is_admin:
        data.is_shared = False  # Only admins can create shared templates
    return await service.create_template(data, created_by=UUID(current_user.sub))


@router.get("/templates", response_model=TaskTemplateListResponse)
async def list_templates(
    skip: int = 0,
    limit: int = 50,
    current_user: TokenPayload = Depends(get_current_user),
    service: TaskTemplateService = Depends(_get_template_service),
):
    """List task templates visible to the current user (personal + shared)."""
    templates, total = await service.list_templates(UUID(current_user.sub), skip, limit)
    return TaskTemplateListResponse(total=total, templates=templates)


@router.patch("/templates/{template_id}", response_model=TaskTemplateResponse)
async def update_template(
    template_id: UUID,
    data: TaskTemplateUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    service: TaskTemplateService = Depends(_get_template_service),
):
    """Update a task template. Only the creator or admin can update."""
    is_admin = current_user.role in (UserRole.HR.value, UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)
    return await service.update_template(template_id, data, UUID(current_user.sub), is_admin)


@router.delete("/templates/{template_id}", status_code=204)
async def delete_template(
    template_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: TaskTemplateService = Depends(_get_template_service),
):
    """Delete a task template. Only the creator or admin can delete."""
    is_admin = current_user.role in (UserRole.HR.value, UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)
    await service.delete_template(template_id, UUID(current_user.sub), is_admin)


# ──────────────────── ADMIN DASHBOARD / KPI ────────────────────

@router.get("/dashboard/kpi", response_model=AdminKPIResponse)
async def admin_kpi(
    target_date: Optional[date] = Query(None, description="Date for KPI (default: today)"),
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.MANAGER)
    ),
    service: AttendanceService = Depends(_get_service),
):
    """Top-level KPI summary: present, late, absent, missed punch-outs, avg hours, task metrics."""
    return await service.get_admin_kpi(target_date)


@router.get("/dashboard/trend", response_model=AttendanceTrendResponse)
async def attendance_trend(
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.MANAGER)
    ),
    service: AttendanceService = Depends(_get_service),
):
    """Attendance trend for the last N days (line chart data)."""
    return await service.get_attendance_trend(days)


@router.get("/dashboard/status-breakdown", response_model=DailyStatusBreakdown)
async def daily_status_breakdown(
    target_date: Optional[date] = Query(None, description="Date (default: today)"),
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.MANAGER)
    ),
    service: AttendanceService = Depends(_get_service),
):
    """Daily attendance status breakdown (pie chart data)."""
    return await service.get_daily_status_breakdown(target_date)


@router.get("/dashboard/performers", response_model=PerformersResponse)
async def performers(
    year: int = Query(..., description="Year"),
    month: int = Query(..., ge=1, le=12, description="Month 1-12"),
    limit: int = Query(5, ge=1, le=20, description="Number of top/low performers"),
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.MANAGER)
    ),
    service: AttendanceService = Depends(_get_service),
):
    """Top and low performers for a given month based on productivity score."""
    return await service.get_performers(year, month, limit)


# ──────────────────── EXPORT ────────────────────

@router.get("/export/csv")
@limiter.limit("5/minute")
async def export_attendance_csv(
    request: Request,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    employee_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: AttendanceService = Depends(_get_service),
):
    """Export attendance data as CSV. HR/Admin only."""
    import csv
    import io
    from starlette.responses import StreamingResponse

    records, _ = await service.list_all(
        skip=0, limit=10000,
        employee_id=employee_id,
        date_from=date_from,
        date_to=date_to,
        status=status_filter,
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Employee ID", "Date", "Clock In", "Clock Out", "Status", "State",
        "Work Hours", "Overtime Hours", "Day Rating", "Productivity Score",
        "Clock In Location", "Clock Out Location", "Shift", "Tasks Count",
    ])
    for r in records:
        writer.writerow([
            str(r.employee_id), str(r.date), str(r.clock_in), str(r.clock_out or ""),
            r.status, r.state, r.work_hours or "", r.overtime_hours,
            r.day_rating or "", r.productivity_score or "",
            r.clock_in_location_name or "", r.clock_out_location_name or "",
            r.shift_number, len(r.tasks) if r.tasks else 0,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance_export.csv"},
    )


# ──────────────────── SINGLE RECORD (must be last — wildcard catches all /{id}) ────────────────────

@router.get("/{record_id}", response_model=AttendanceResponse)
async def get_attendance_record(
    record_id: UUID,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: AttendanceService = Depends(_get_service),
):
    """Get a specific attendance record by ID."""
    return await service.get_record(record_id)


@router.patch("/{record_id}", response_model=AttendanceResponse)
async def update_attendance_record(
    record_id: UUID,
    data: AttendanceUpdate,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.ADMIN)
    ),
    service: AttendanceService = Depends(_get_service),
):
    """Manually correct an attendance record. HR/Super Admin only."""
    return await service.update_record(record_id, data)
