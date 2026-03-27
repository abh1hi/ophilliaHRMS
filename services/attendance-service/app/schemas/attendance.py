from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime, time
from decimal import Decimal

from app.core.constants import AttendanceStatus, AttendanceMethod


# ──────────── TASK SCHEMAS ────────────

class TaskCreate(BaseModel):
    title: str
    details: Optional[str] = None
    estimated_finish_time: Optional[str] = None   # e.g. "6:30 PM"
    expected_expenses: Optional[Decimal] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Task title must not be empty")
        return v.strip()


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    details: Optional[str] = None
    estimated_finish_time: Optional[str] = None
    expected_expenses: Optional[Decimal] = None


class TaskCompleteUpdate(BaseModel):
    """Payload sent at punch-out time to mark each task's outcome."""
    status: str  # completed | partially_completed | not_completed
    completion_notes: Optional[str] = None
    actual_expenses: Optional[Decimal] = None

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        allowed = {"completed", "partially_completed", "not_completed"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class TaskResponse(BaseModel):
    id: UUID
    attendance_record_id: UUID
    employee_id: UUID
    company_id: Optional[UUID] = None
    assigned_by: Optional[UUID] = None
    title: str
    details: Optional[str] = None
    estimated_finish_time: Optional[str] = None
    expected_expenses: Optional[Decimal] = None
    status: str
    completion_notes: Optional[str] = None
    actual_expenses: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    total: int
    tasks: List[TaskResponse]


# ──────────── CLOCK IN ────────────
class ClockInRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None   # human-readable (village/town)
    notes: Optional[str] = None
    device_info: Optional[str] = None     # e.g. "iPhone 14 / Chrome 120"
    network_info: Optional[str] = None    # e.g. "WiFi / 4G"


# ──────────── CLOCK OUT ────────────
class TaskCompletionItem(BaseModel):
    """Inline task completion — used inside ClockOutRequest."""
    task_id: UUID
    status: str  # completed | partially_completed | not_completed
    completion_notes: Optional[str] = None
    actual_expenses: Optional[Decimal] = None

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        allowed = {"completed", "partially_completed", "not_completed"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class ClockOutRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None   # human-readable (village/town)
    notes: Optional[str] = None
    day_rating: Optional[int] = None      # 1-5 stars
    rating_comment: Optional[str] = None  # mandatory if rating <= 2
    task_completions: Optional[List[TaskCompletionItem]] = None

    @field_validator("day_rating")
    @classmethod
    def valid_rating(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v not in range(1, 6):
            raise ValueError("day_rating must be between 1 and 5")
        return v

    @model_validator(mode="after")
    def rating_comment_required_for_low_rating(self):
        if self.day_rating is not None and self.day_rating <= 2:
            if not self.rating_comment or not self.rating_comment.strip():
                raise ValueError("rating_comment is required when day_rating is 2 or below")
        return self


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
    company_id: Optional[UUID] = None
    clock_in: datetime
    clock_out: Optional[datetime] = None
    clock_in_lat: Optional[float] = None
    clock_in_lng: Optional[float] = None
    clock_out_lat: Optional[float] = None
    clock_out_lng: Optional[float] = None
    clock_in_location_name: Optional[str] = None
    clock_out_location_name: Optional[str] = None
    work_hours: Optional[float] = None
    overtime_hours: float = 0.0
    day_rating: Optional[int] = None
    rating_comment: Optional[str] = None
    state: str = "punched_in"
    productivity_score: Optional[float] = None
    device_info: Optional[str] = None
    network_info: Optional[str] = None
    shift_number: int = 1
    version: int = 1
    status: str
    method: str
    notes: Optional[str] = None
    date: date
    tasks: List[TaskResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ──────────── TODAY'S SHIFTS ────────────
class TodayShiftsResponse(BaseModel):
    shifts: List[AttendanceResponse]
    shift_count: int
    max_shifts: int
    can_start_new_shift: bool


# ──────────── PAGINATED LIST ────────────
class AttendanceListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    records: List[AttendanceResponse]


# ──────────── TASK ASSIGN (any user → any employee's today record) ────────────
class TaskAssignRequest(BaseModel):
    """Any authenticated user can assign a task to another employee's today record."""
    target_employee_id: UUID
    title: str
    details: Optional[str] = None
    estimated_finish_time: Optional[str] = None
    expected_expenses: Optional[Decimal] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Task title must not be empty")
        return v.strip()


# ──────────── PRODUCTIVITY REPORT ────────────
class ProductivityReportItem(BaseModel):
    employee_id: UUID
    company_id: Optional[UUID] = None
    month: int
    year: int
    total_days: int
    present_days: int
    late_days: int
    half_days: int
    total_tasks: int
    completed_tasks: int
    partial_tasks: int
    not_completed_tasks: int
    pending_tasks: int
    completion_rate: float
    avg_rating: Optional[float] = None
    total_expected_expenses: Optional[Decimal] = None
    total_actual_expenses: Optional[Decimal] = None

    model_config = {"from_attributes": True}


class ProductivityReportResponse(BaseModel):
    month: int
    year: int
    items: List[ProductivityReportItem]


# ──────────── ALERTS ────────────
class MissedPunchOutItem(BaseModel):
    employee_id: UUID
    company_id: Optional[UUID] = None
    record_id: UUID
    clock_in: datetime
    clock_in_location_name: Optional[str] = None

    model_config = {"from_attributes": True}


class AlertsResponse(BaseModel):
    date: date
    late_count: int
    missed_punch_out_count: int
    missed_punch_outs: List[MissedPunchOutItem]


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


class GeofenceUpdate(BaseModel):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_meters: Optional[int] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Name must not be empty")
        return v.strip() if v else v

    @field_validator("radius_meters")
    @classmethod
    def radius_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("Radius must be positive")
        return v


class GeofenceResponse(BaseModel):
    id: UUID
    company_id: Optional[UUID] = None
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
    auto_close_time: Optional[time] = None
    task_planning_grace_minutes: float = 30.0
    allow_night_shift: str = "false"
    max_shifts_per_day: float = 2


class PolicyUpdate(BaseModel):
    department_id: Optional[UUID] = None
    employee_id: Optional[UUID] = None
    method: Optional[AttendanceMethod] = None
    geofence_id: Optional[UUID] = None
    work_start_time: Optional[time] = None
    work_hours_per_day: Optional[float] = None
    auto_close_time: Optional[time] = None
    task_planning_grace_minutes: Optional[float] = None
    allow_night_shift: Optional[str] = None
    max_shifts_per_day: Optional[float] = None


class PolicyResponse(BaseModel):
    id: UUID
    company_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    employee_id: Optional[UUID] = None
    method: str
    geofence_id: Optional[UUID] = None
    work_start_time: Optional[time] = None
    work_hours_per_day: float
    auto_close_time: Optional[time] = None
    task_planning_grace_minutes: float = 30.0
    allow_night_shift: str = "false"
    max_shifts_per_day: float = 2
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PolicyListResponse(BaseModel):
    total: int
    policies: List[PolicyResponse]


# ──────────── BULK SCHOOL-MODE ATTENDANCE ────────────
class BulkSchoolModeItem(BaseModel):
    employee_id: UUID
    status: AttendanceStatus = AttendanceStatus.PRESENT
    notes: Optional[str] = None


class BulkSchoolModeRequest(BaseModel):
    items: List[BulkSchoolModeItem]


class BulkSchoolModeResult(BaseModel):
    index: int
    employee_id: UUID
    success: bool
    error: Optional[str] = None


class BulkSchoolModeResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: List[BulkSchoolModeResult]


# ──────────── TASK TEMPLATES ────────────
class TaskTemplateCreate(BaseModel):
    title: str
    details: Optional[str] = None
    estimated_finish_time: Optional[str] = None
    expected_expenses: Optional[Decimal] = None
    is_shared: bool = False

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Template title must not be empty")
        return v.strip()


class TaskTemplateUpdate(BaseModel):
    title: Optional[str] = None
    details: Optional[str] = None
    estimated_finish_time: Optional[str] = None
    expected_expenses: Optional[Decimal] = None
    is_shared: Optional[bool] = None


class TaskTemplateResponse(BaseModel):
    id: UUID
    company_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    title: str
    details: Optional[str] = None
    estimated_finish_time: Optional[str] = None
    expected_expenses: Optional[Decimal] = None
    is_shared: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskTemplateListResponse(BaseModel):
    total: int
    templates: List[TaskTemplateResponse]


# ──────────── ADMIN KPI DASHBOARD ────────────
class AdminKPIResponse(BaseModel):
    """Top-level KPI summary for admin dashboard."""
    date: date
    total_employees_present: int
    late_checkins: int
    absent_employees: int
    missed_punchouts: int
    auto_closed_count: int
    avg_working_hours: Optional[float] = None
    total_tasks_today: int
    completed_tasks_today: int
    task_completion_rate: Optional[float] = None


class DailyStatusBreakdown(BaseModel):
    """For pie chart: daily attendance status distribution."""
    date: date
    present: int
    late: int
    half_day: int
    absent: int
    auto_closed: int


class AttendanceTrendItem(BaseModel):
    """For line chart: attendance trend over time."""
    date: date
    present: int
    late: int
    absent: int
    half_day: int
    auto_closed: int
    avg_hours: Optional[float] = None


class AttendanceTrendResponse(BaseModel):
    items: List[AttendanceTrendItem]


class EmployeeProductivitySummary(BaseModel):
    """For top/low performers."""
    employee_id: UUID
    total_tasks: int
    completed_tasks: int
    completion_rate: float
    avg_rating: Optional[float] = None
    productivity_score: Optional[float] = None


class PerformersResponse(BaseModel):
    top_performers: List[EmployeeProductivitySummary]
    low_performers: List[EmployeeProductivitySummary]
