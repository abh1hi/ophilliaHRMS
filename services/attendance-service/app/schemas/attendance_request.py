from typing import Optional, List
from uuid import UUID
from datetime import date, datetime

from pydantic import BaseModel
from typing import Literal


class AttendanceRequestCreate(BaseModel):
    employee_id: UUID
    from_date: date
    to_date: date
    reason: Literal["on_site_duty", "work_from_home", "other"]
    explanation: Optional[str] = None
    include_holidays: int = 0
    half_day: int = 0
    half_day_date: Optional[date] = None


class AttendanceRequestReview(BaseModel):
    status: Literal["approved", "rejected"]
    review_note: Optional[str] = None


class AttendanceRequestResponse(BaseModel):
    id: UUID
    company_id: UUID
    employee_id: UUID
    from_date: date
    to_date: date
    reason: str
    explanation: Optional[str] = None
    include_holidays: int
    half_day: int
    half_day_date: Optional[date] = None
    status: str
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AttendanceRequestListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    requests: List[AttendanceRequestResponse]
