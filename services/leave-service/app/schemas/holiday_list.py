from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel


class HolidayListEntryCreate(BaseModel):
    date: date
    description: Optional[str] = None


class HolidayListEntryResponse(BaseModel):
    id: UUID
    holiday_list_id: UUID
    date: date
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class HolidayListCreate(BaseModel):
    name: str
    from_date: date
    to_date: date
    description: Optional[str] = None
    entries: List[HolidayListEntryCreate] = []


class HolidayListUpdate(BaseModel):
    name: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    description: Optional[str] = None
    is_active: Optional[int] = None


class HolidayListResponse(BaseModel):
    id: UUID
    company_id: UUID
    name: str
    from_date: date
    to_date: date
    description: Optional[str] = None
    is_active: int
    entries: List[HolidayListEntryResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Holiday List Assignment ──────────────────────────────────────────────────

class HolidayListAssignmentCreate(BaseModel):
    applicable_for: str  # "company" | "employee"
    employee_id: Optional[UUID] = None
    holiday_list_id: UUID
    assignment_from: date


class HolidayListAssignmentResponse(BaseModel):
    id: UUID
    company_id: UUID
    applicable_for: str
    employee_id: Optional[UUID] = None
    holiday_list_id: UUID
    assignment_from: date
    created_at: datetime

    model_config = {"from_attributes": True}
