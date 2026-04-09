from pydantic import BaseModel
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime, date


class ShiftRequestCreate(BaseModel):
    employee_id: UUID
    request_type: Literal["swap", "change", "leave"]
    from_date: date
    to_date: date
    requested_shift_type_id: Optional[UUID] = None
    reason: Optional[str] = None


class ShiftRequestUpdate(BaseModel):
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    requested_shift_type_id: Optional[UUID] = None
    reason: Optional[str] = None


class ShiftRequestReview(BaseModel):
    status: Literal["approved", "rejected"]
    review_note: Optional[str] = None


class ShiftRequestResponse(BaseModel):
    id: UUID
    company_id: UUID
    employee_id: UUID
    request_type: str
    from_date: date
    to_date: date
    requested_shift_type_id: Optional[UUID] = None
    reason: Optional[str] = None
    status: str
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
