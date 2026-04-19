"""Pydantic schemas for overtime policies, overtime requests, and holiday calendars."""
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, Literal, List
from uuid import UUID
from datetime import date, datetime


# ─────────────────────────── OvertimePolicy ───────────────────────────

class OvertimePolicyCreate(BaseModel):
    employee_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    location_id: Optional[UUID] = None

    jurisdiction: Literal["INDIA", "EU", "CUSTOM"] = "CUSTOM"
    compliance_profile: Optional[str] = None

    daily_ot_threshold_hours: float = 8.0
    weekly_ot_threshold_hours: float = 40.0
    max_daily_hours: float = 12.0

    daily_ot_multiplier: float = 1.5
    weekly_ot_multiplier: float = 1.5
    weekend_multiplier: float = 1.5
    holiday_multiplier: float = 2.0

    prefer_comp_off: bool = False
    comp_off_ratio: float = 1.0

    @model_validator(mode="after")
    def single_scope(self) -> "OvertimePolicyCreate":
        scopes = [self.employee_id, self.department_id, self.location_id]
        if sum(s is not None for s in scopes) > 1:
            raise ValueError("Set at most one of employee_id, department_id, location_id")
        return self


class OvertimePolicyUpdate(BaseModel):
    daily_ot_threshold_hours: Optional[float] = None
    weekly_ot_threshold_hours: Optional[float] = None
    max_daily_hours: Optional[float] = None
    daily_ot_multiplier: Optional[float] = None
    weekly_ot_multiplier: Optional[float] = None
    weekend_multiplier: Optional[float] = None
    holiday_multiplier: Optional[float] = None
    prefer_comp_off: Optional[bool] = None
    comp_off_ratio: Optional[float] = None
    jurisdiction: Optional[Literal["INDIA", "EU", "CUSTOM"]] = None
    compliance_profile: Optional[str] = None
    is_active: Optional[bool] = None


class OvertimePolicyResponse(BaseModel):
    id: UUID
    company_id: UUID
    employee_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    jurisdiction: str
    compliance_profile: Optional[str] = None
    daily_ot_threshold_hours: float
    weekly_ot_threshold_hours: float
    max_daily_hours: float
    daily_ot_multiplier: float
    weekly_ot_multiplier: float
    weekend_multiplier: float
    holiday_multiplier: float
    prefer_comp_off: bool
    comp_off_ratio: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OvertimeTemplateCreate(BaseModel):
    template_key: Literal["INDIA_FACTORIES_ACT", "EU_WTD_48H"]


# ─────────────────────────── OvertimePolicyAudit ───────────────────────────

class OvertimePolicyAuditResponse(BaseModel):
    id: UUID
    policy_id: UUID
    action: str
    changed_by: UUID
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────── OvertimeRequest ───────────────────────────

class OvertimeRequestCreate(BaseModel):
    date: date
    requested_hours: float
    reason: str

    @field_validator("requested_hours")
    @classmethod
    def positive_hours(cls, v: float) -> float:
        if v <= 0 or v > 12:
            raise ValueError("requested_hours must be between 0.5 and 12")
        return round(v * 2) / 2  # round to nearest 0.5

    @field_validator("reason")
    @classmethod
    def reason_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("reason must not be empty")
        return v.strip()


class OvertimeRequestReview(BaseModel):
    status: Literal["approved", "rejected"]
    review_note: Optional[str] = None


class OvertimeRequestResponse(BaseModel):
    id: UUID
    company_id: UUID
    employee_id: UUID
    date: date
    requested_hours: float
    reason: str
    status: str
    reviewed_by: Optional[UUID] = None
    review_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────── HolidayCalendar ───────────────────────────

class HolidayCalendarCreate(BaseModel):
    name: str
    year: int
    location_id: Optional[UUID] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Calendar name must not be empty")
        return v.strip()

    @field_validator("year")
    @classmethod
    def valid_year(cls, v: int) -> int:
        if v < 2000 or v > 2100:
            raise ValueError("year must be between 2000 and 2100")
        return v


class HolidayCalendarUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class HolidayCreate(BaseModel):
    name: str
    date: date
    holiday_type: Literal["public", "optional", "restricted"] = "public"

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Holiday name must not be empty")
        return v.strip()


class HolidayResponse(BaseModel):
    id: UUID
    calendar_id: UUID
    name: str
    date: date
    holiday_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class HolidayCalendarResponse(BaseModel):
    id: UUID
    company_id: UUID
    location_id: Optional[UUID] = None
    name: str
    year: int
    is_active: bool
    holidays: List[HolidayResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
