from pydantic import BaseModel, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime, time

from app.core.constants import AttendanceStatus, AttendanceMethod


# ──────────── CLOCK IN ────────────
class ClockInRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None


# ──────────── CLOCK OUT ────────────
class ClockOutRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None


# ──────────── MANUAL ENTRY (Admin) ────────────
class ManualAttendanceCreate(BaseModel):
    employee_id: UUID
    date: date
    clock_in: datetime
    clock_out: Optional[datetime] = None
    status: AttendanceStatus = AttendanceStatus.PRESENT
    notes: Optional[str] = None


# ──────────── SCHOOL MODE ENTRY (Admin/HR) ────────────
class SchoolModeAttendanceCreate(BaseModel):
    employee_id: UUID
    status: AttendanceStatus = AttendanceStatus.PRESENT
    notes: Optional[str] = None


# ──────────── UPDATE (Admin correction) ────────────
class AttendanceUpdate(BaseModel):
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    status: Optional[AttendanceStatus] = None
    notes: Optional[str] = None


# ──────────── RESPONSE ────────────
class AttendanceResponse(BaseModel):
    id: UUID
    employee_id: UUID
    clock_in: datetime
    clock_out: Optional[datetime] = None
    clock_in_lat: Optional[float] = None
    clock_in_lng: Optional[float] = None
    clock_out_lat: Optional[float] = None
    clock_out_lng: Optional[float] = None
    work_hours: Optional[float] = None
    overtime_hours: float = 0.0
    status: str
    method: str
    notes: Optional[str] = None
    date: date
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ──────────── PAGINATED LIST ────────────
class AttendanceListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    records: List[AttendanceResponse]


# ──────────── GEOFENCE ────────────
class GeofenceCreate(BaseModel):
    name: str
    latitude: float
    longitude: float
    radius_meters: int = 200

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name must not be empty")
        return v.strip()

    @field_validator("radius_meters")
    @classmethod
    def radius_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Radius must be positive")
        return v


class GeofenceResponse(BaseModel):
    id: UUID
    name: str
    latitude: float
    longitude: float
    radius_meters: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GeofenceListResponse(BaseModel):
    total: int
    geofences: List[GeofenceResponse]


# ──────────── ATTENDANCE POLICY ────────────
class PolicyCreate(BaseModel):
    department_id: Optional[UUID] = None
    employee_id: Optional[UUID] = None
    method: AttendanceMethod = AttendanceMethod.MANUAL
    geofence_id: Optional[UUID] = None
    work_start_time: Optional[time] = None
    work_hours_per_day: float = 8.0


class PolicyResponse(BaseModel):
    id: UUID
    department_id: Optional[UUID] = None
    employee_id: Optional[UUID] = None
    method: str
    geofence_id: Optional[UUID] = None
    work_start_time: Optional[time] = None
    work_hours_per_day: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PolicyListResponse(BaseModel):
    total: int
    policies: List[PolicyResponse]
