from pydantic import BaseModel, model_validator
from typing import Optional
from uuid import UUID
from datetime import datetime, date


class ShiftScheduleAssignmentCreate(BaseModel):
    schedule_id: UUID
    employee_id: UUID
    effective_from: date
    effective_to: Optional[date] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_dates(self) -> "ShiftScheduleAssignmentCreate":
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to must be on or after effective_from")
        return self


class ShiftScheduleAssignmentUpdate(BaseModel):
    schedule_id: Optional[UUID] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: Optional[int] = None
    notes: Optional[str] = None


class ShiftScheduleAssignmentResponse(BaseModel):
    id: UUID
    company_id: UUID
    schedule_id: UUID
    employee_id: UUID
    effective_from: date
    effective_to: Optional[date] = None
    is_active: int
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
