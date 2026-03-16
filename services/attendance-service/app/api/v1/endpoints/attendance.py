from typing import Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user, require_role, TokenPayload
from app.api.v1.dependencies import get_db_with_tenant
from app.core.constants import UserRole
from app.services.attendance_service import AttendanceService, GeofenceService, PolicyService
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
    GeofenceResponse,
    GeofenceListResponse,
    PolicyCreate,
    PolicyResponse,
    PolicyListResponse,
    TaskCreate,
    TaskUpdate,
    TaskCompleteUpdate,
    TaskResponse,
    TaskListResponse,
    TaskAssignRequest,
    ProductivityReportResponse,
    AlertsResponse,
)
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/attendance", tags=["attendance"])


# ── Dependency helpers ───────────────────────────────────────────────────────

def _get_service(db: AsyncSession = Depends(get_db_with_tenant)) -> AttendanceService:
    return AttendanceService(db)


def _get_geofence_service(db: AsyncSession = Depends(get_db_with_tenant)) -> GeofenceService:
    return GeofenceService(db)


def _get_policy_service(db: AsyncSession = Depends(get_db_with_tenant)) -> PolicyService:
    return PolicyService(db)


def _get_task_service(db: AsyncSession = Depends(get_db_with_tenant)) -> TaskService:
    return TaskService(db)


# ──────────────────── ATTENDANCE RECORDS ────────────────────

@router.post("/clock-in", response_model=AttendanceResponse, status_code=201)
async def clock_in(
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
async def clock_out(
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
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.MANAGER)
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


@router.get("/{record_id}", response_model=AttendanceResponse)
async def get_attendance_record(
    record_id: UUID,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN)
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
        require_role(UserRole.HR, UserRole.SUPER_ADMIN)
    ),
    service: AttendanceService = Depends(_get_service),
):
    """Manually correct an attendance record. HR/Super Admin only."""
    return await service.update_record(record_id, data)


@router.post("/manual", response_model=AttendanceResponse, status_code=201)
async def manual_entry(
    data: ManualAttendanceCreate,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN)
    ),
    service: AttendanceService = Depends(_get_service),
):
    """Create a manual/backdated attendance entry. HR/Super Admin only."""
    return await service.manual_entry(data, created_by=current_user.sub)


@router.post("/school-mode", response_model=AttendanceResponse, status_code=201)
async def school_mode_entry(
    data: SchoolModeAttendanceCreate,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN)
    ),
    service: AttendanceService = Depends(_get_service),
):
    """Mark an employee's attendance on their behalf. HR/Super Admin only."""
    return await service.mark_school_mode_attendance(data, created_by=current_user.sub)


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

    if current_user.role in (UserRole.HR.value, UserRole.SUPER_ADMIN.value, UserRole.MANAGER.value):
        # HR/Admin/Manager can assign tasks; the task employee_id is inferred from the record
        assigned_by = employee_uuid

    return await service.add_task(
        record_id=record_id,
        employee_id=employee_uuid,
        data=data,
        assigned_by=assigned_by,
    )


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
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.MANAGER)
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
        require_role(UserRole.HR, UserRole.SUPER_ADMIN, UserRole.MANAGER)
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
        require_role(UserRole.HR, UserRole.SUPER_ADMIN)
    ),
    service: GeofenceService = Depends(_get_geofence_service),
):
    """Create a new geofence location (e.g. office). HR/Super Admin only."""
    return await service.create_geofence(data)


@router.get("/geofences", response_model=GeofenceListResponse)
async def list_geofences(
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN)
    ),
    service: GeofenceService = Depends(_get_geofence_service),
):
    """List all active geofence locations."""
    geofences, total = await service.list_geofences()
    return GeofenceListResponse(total=total, geofences=geofences)


# ──────────────────── ATTENDANCE POLICIES ────────────────────

@router.post("/policies", response_model=PolicyResponse, status_code=201)
async def create_policy(
    data: PolicyCreate,
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN)
    ),
    service: PolicyService = Depends(_get_policy_service),
):
    """Assign attendance method (manual/geofence/both) to dept or employee."""
    return await service.create_policy(data)


@router.get("/policies", response_model=PolicyListResponse)
async def list_policies(
    current_user: TokenPayload = Depends(
        require_role(UserRole.HR, UserRole.SUPER_ADMIN)
    ),
    service: PolicyService = Depends(_get_policy_service),
):
    """List all attendance policies."""
    policies, total = await service.list_policies()
    return PolicyListResponse(total=total, policies=policies)
