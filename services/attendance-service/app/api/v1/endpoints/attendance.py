from typing import Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user, require_role, TokenPayload
from app.core.constants import UserRole
from app.services.attendance_service import AttendanceService, GeofenceService, PolicyService
from app.schemas.attendance import (
    ClockInRequest,
    ClockOutRequest,
    ManualAttendanceCreate,
    AttendanceUpdate,
    AttendanceResponse,
    AttendanceListResponse,
    GeofenceCreate,
    GeofenceResponse,
    GeofenceListResponse,
    PolicyCreate,
    PolicyResponse,
    PolicyListResponse,
)
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/attendance", tags=["attendance"])


def _get_service(db: AsyncSession = Depends(get_db)) -> AttendanceService:
    return AttendanceService(db)


def _get_geofence_service(db: AsyncSession = Depends(get_db)) -> GeofenceService:
    return GeofenceService(db)


def _get_policy_service(db: AsyncSession = Depends(get_db)) -> PolicyService:
    return PolicyService(db)


# ──────────────────── ATTENDANCE RECORDS ────────────────────

@router.post("/clock-in", response_model=AttendanceResponse, status_code=201)
async def clock_in(
    data: ClockInRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: AttendanceService = Depends(_get_service),
):
    """Clock in for today. Validates geofence if required by policy."""
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
    """Clock out for today. Auto-computes work hours and overtime."""
    return await service.clock_out(
        employee_id=UUID(current_user.sub),
        data=data,
    )


@router.get("/me/today", response_model=Optional[AttendanceResponse])
async def get_my_today(
    current_user: TokenPayload = Depends(get_current_user),
    service: AttendanceService = Depends(_get_service),
):
    """Get today's attendance record for the authenticated user."""
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
