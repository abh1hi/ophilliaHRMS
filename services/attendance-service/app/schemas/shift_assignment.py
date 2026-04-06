from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime, date


class ShiftAssignmentCreate(BaseModel):
    employee_id: UUID
    shift_type_id: Optional[UUID] = None
    shift_location_id: Optional[UUID] = None
    effective_from: date
    effective_to: Optional[date] = None
    notes: Optional[str] = None


class ShiftAssignmentUpdate(BaseModel):
    shift_type_id: Optional[UUID] = None
    shift_location_id: Optional[UUID] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    notes: Optional[str] = None
    is_active: Optional[int] = None


class ShiftAssignmentResponse(BaseModel):
    id: UUID
    company_id: UUID
    employee_id: UUID
    shift_type_id: Optional[UUID] = None
    shift_location_id: Optional[UUID] = None
    effective_from: date
    effective_to: Optional[date] = None
    is_active: int
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
