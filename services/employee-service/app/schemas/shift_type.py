from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime, time


class ShiftTypeCreate(BaseModel):
    name: str
    start_time: time
    end_time: time
    break_minutes: int = 0
    grace_period_minutes: int = 5
    is_overnight: int = 0
    color_code: Optional[str] = None
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Shift type name must not be empty")
        return v.strip()


class ShiftTypeUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_minutes: Optional[int] = None
    grace_period_minutes: Optional[int] = None
    is_overnight: Optional[int] = None
    color_code: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[int] = None


class ShiftTypeResponse(BaseModel):
    id: UUID
    company_id: UUID
    name: str
    start_time: time
    end_time: time
    break_minutes: int
    work_hours: Optional[float] = None
    grace_period_minutes: int
    is_overnight: int
    color_code: Optional[str] = None
    description: Optional[str] = None
    is_active: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
