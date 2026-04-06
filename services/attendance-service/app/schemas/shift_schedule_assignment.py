from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class ShiftScheduleAssignmentCreate(BaseModel):
    schedule_id: UUID
    employee_id: UUID


class ShiftScheduleAssignmentResponse(BaseModel):
    id: UUID
    company_id: UUID
    schedule_id: UUID
    employee_id: UUID
    is_active: int
    created_at: datetime

    model_config = {"from_attributes": True}
