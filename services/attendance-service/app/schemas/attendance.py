from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Any
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
    accuracy_meters: Optional[float] = None  # GPS accuracy radius from device (for smart geofence adjust)


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
    schedule_id: Optional[UUID] = None
    clock_in: datetime
    clock_out: Optional[datetime] = None
    scheduled_clock_in_at: Optional[datetime] = None
    scheduled_clock_out_at: Optional[datetime] = None
    auto_clock_out_at: Optional[datetime] = None
    tasks_mandatory_snapshot: bool = False
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
    tasks: List[TaskResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ──────────── TODAY'S SHIFTS ────────────
class TodayShiftsResponse(BaseModel):
    shifts: List[AttendanceResponse]
    shift_count: int
    max_shifts: int
    can_start_new_shift: bool


class ScheduleLocationResponse(BaseModel):
    id: UUID
    name: str
    latitude: float
    longitude: float
    radius_meters: int

    model_config = {"from_attributes": True}


class TodayScheduleResponse(BaseModel):
    schedule_id: UUID
    schedule_name: str
    shift_type_id: UUID
    shift_type_name: str
    date: date
    clock_in_start_time: time
    clock_in_end_time: time
    clock_out_start_time: time
    clock_out_end_time: time
    auto_clock_out_time: time
    tasks_mandatory: bool
    allowed_clock_in_locations: List[ScheduleLocationResponse]
    allowed_clock_out_locations: List[ScheduleLocationResponse]
    can_clock_in_now: bool
    can_clock_out_now: bool
    clock_in_status_reason: Optional[str] = None
    clock_out_status_reason: Optional[str] = None
    clock_in_status: Optional[str] = None    # ClockInStatus value for UI state machine
    is_off_day: bool = False                 # True if today is a scheduled off day
    shift_start_time: Optional[time] = None  # Shift type start time
    shift_end_time: Optional[time] = None    # Shift type end time
    grace_period_minutes: int = 0


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
    is_active: bool = True

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
    is_active: Optional[bool] = None

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
    location_id: Optional[UUID] = None
    method: AttendanceMethod = AttendanceMethod.MANUAL
    geofence_ids: List[UUID] = []
    work_start_time: Optional[time] = None
    work_hours_per_day: float = 8.0
    auto_close_time: Optional[time] = None
    task_planning_grace_minutes: float = 30.0
    allow_night_shift: bool = False
    max_shifts_per_day: float = 2
    late_grace_period_minutes: int = 0

    @model_validator(mode="after")
    def geofence_required_for_location_method(self) -> "PolicyCreate":
        if self.method in (AttendanceMethod.GEOFENCE, AttendanceMethod.BOTH) and not self.geofence_ids:
            raise ValueError("geofence_ids must contain at least one entry when method is 'geofence' or 'both'")
        return self


class PolicyUpdate(BaseModel):
    department_id: Optional[UUID] = None
    employee_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    method: Optional[AttendanceMethod] = None
    geofence_ids: Optional[List[UUID]] = None
    work_start_time: Optional[time] = None
    work_hours_per_day: Optional[float] = None
    auto_close_time: Optional[time] = None
    task_planning_grace_minutes: Optional[float] = None
    allow_night_shift: Optional[bool] = None
    max_shifts_per_day: Optional[float] = None
    late_grace_period_minutes: Optional[int] = None


class PolicyResponse(BaseModel):
    id: UUID
    company_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    employee_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    method: str
    work_start_time: Optional[time] = None
    work_hours_per_day: float
    auto_close_time: Optional[time] = None
    task_planning_grace_minutes: float = 30.0
    allow_night_shift: bool = False
    max_shifts_per_day: float = 2
    late_grace_period_minutes: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PolicyListResponse(BaseModel):
    total: int
    policies: List[PolicyResponse]


# ──────────── POLICY AUDIT LOG ────────────
class PolicyAuditLogResponse(BaseModel):
    id: UUID
    policy_id: UUID
    company_id: Optional[UUID] = None
    action: str
    changed_by: UUID
    timestamp: datetime
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None

    model_config = {"from_attributes": True}


class PolicyAuditLogListResponse(BaseModel):
    total: int
    items: List[PolicyAuditLogResponse]


# ──────────── POLICY TEMPLATES ────────────
class PolicyTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    method: AttendanceMethod = AttendanceMethod.MANUAL
    geofence_id: Optional[UUID] = None
    work_start_time: Optional[time] = None
    work_hours_per_day: float = 8.0
    auto_close_time: Optional[time] = None
    task_planning_grace_minutes: float = 30.0
    allow_night_shift: bool = False
    max_shifts_per_day: float = 2
    late_grace_period_minutes: int = 0

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Template name must not be empty")
        return v.strip()


class PolicyTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    method: Optional[AttendanceMethod] = None
    geofence_id: Optional[UUID] = None
    work_start_time: Optional[time] = None
    work_hours_per_day: Optional[float] = None
    auto_close_time: Optional[time] = None
    task_planning_grace_minutes: Optional[float] = None
    allow_night_shift: Optional[bool] = None
    max_shifts_per_day: Optional[float] = None
    late_grace_period_minutes: Optional[int] = None


class PolicyTemplateResponse(BaseModel):
    id: UUID
    company_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    method: str
    geofence_id: Optional[UUID] = None
    work_start_time: Optional[time] = None
    work_hours_per_day: float
    auto_close_time: Optional[time] = None
    task_planning_grace_minutes: float
    allow_night_shift: bool
    max_shifts_per_day: float
    late_grace_period_minutes: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PolicyTemplateListResponse(BaseModel):
    total: int
    templates: List[PolicyTemplateResponse]


class ApplyTemplateRequest(BaseModel):
    template_id: UUID


# ──────────── POLICY EXCEPTIONS ────────────
_VALID_REASON_CATEGORIES = {"medical_leave", "client_visit", "training", "custom"}
_VALID_OVERRIDE_METHODS = {"manual", "geofence", "both"}


class PolicyExceptionCreate(BaseModel):
    employee_id: UUID
    reason: str
    reason_category: Optional[str] = None
    from_date: date
    to_date: Optional[date] = None

    override_method: Optional[str] = None
    override_work_hours: Optional[float] = None
    override_work_start_time: Optional[time] = None
    override_late_grace_minutes: Optional[int] = None
    override_geofence_id: Optional[UUID] = None
    override_geofence_ids: Optional[List[UUID]] = None
    override_overtime_policy_id: Optional[UUID] = None

    @field_validator("reason")
    @classmethod
    def reason_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Reason must not be empty")
        return v.strip()

    @field_validator("override_method")
    @classmethod
    def valid_method(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _VALID_OVERRIDE_METHODS:
            raise ValueError("override_method must be manual, geofence, or both")
        return v

    @field_validator("reason_category")
    @classmethod
    def valid_reason_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _VALID_REASON_CATEGORIES:
            raise ValueError(f"reason_category must be one of: {sorted(_VALID_REASON_CATEGORIES)}")
        return v

    @model_validator(mode="after")
    def geofence_required_when_method_is_geofence(self) -> "PolicyExceptionCreate":
        if self.override_method in ("geofence", "both"):
            has_geofence = self.override_geofence_ids or self.override_geofence_id
            if not has_geofence:
                raise ValueError(
                    "override_geofence_ids (or override_geofence_id) is required "
                    "when override_method is 'geofence' or 'both'"
                )
        return self


class PolicyExceptionUpdate(BaseModel):
    reason: Optional[str] = None
    reason_category: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    override_method: Optional[str] = None
    override_work_hours: Optional[float] = None
    override_work_start_time: Optional[time] = None
    override_late_grace_minutes: Optional[int] = None
    override_geofence_id: Optional[UUID] = None
    override_geofence_ids: Optional[List[UUID]] = None
    override_overtime_policy_id: Optional[UUID] = None
    is_active: Optional[bool] = None

    @field_validator("override_method")
    @classmethod
    def valid_method(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _VALID_OVERRIDE_METHODS:
            raise ValueError("override_method must be manual, geofence, or both")
        return v

    @field_validator("reason_category")
    @classmethod
    def valid_reason_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _VALID_REASON_CATEGORIES:
            raise ValueError(f"reason_category must be one of: {sorted(_VALID_REASON_CATEGORIES)}")
        return v


class PolicyExceptionResponse(BaseModel):
    id: UUID
    company_id: Optional[UUID] = None
    employee_id: UUID
    reason: str
    reason_category: Optional[str] = None
    from_date: date
    to_date: Optional[date] = None
    override_method: Optional[str] = None
    override_work_hours: Optional[float] = None
    override_work_start_time: Optional[time] = None
    override_late_grace_minutes: Optional[int] = None
    override_geofence_id: Optional[UUID] = None
    override_geofence_ids: Optional[List[UUID]] = None
    override_overtime_policy_id: Optional[UUID] = None
    approved_by: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PolicyExceptionListResponse(BaseModel):
    total: int
    items: List[PolicyExceptionResponse]


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


# ─────────────────────────── GeofenceConsent ───────────────────────────

class GeofenceConsentResponse(BaseModel):
    id: UUID
    company_id: UUID
    employee_id: UUID
    consented: bool
    consent_given_at: Optional[datetime] = None
    consent_withdrawn_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GeofenceConsentStatusResponse(BaseModel):
    consented: bool
    consent_given_at: Optional[datetime] = None
    consent_withdrawn_at: Optional[datetime] = None


class GeofenceConsentListResponse(BaseModel):
    items: List[GeofenceConsentResponse]
    total: int
