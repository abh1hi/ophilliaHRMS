from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID
from datetime import time, datetime


class ShiftTypeCreate(BaseModel):
    name: str
    start_time: time
    end_time: time
    work_hours_per_day: float = 8.0
    break_minutes: int = 0
    grace_period_minutes: int = 5
    color_code: Optional[str] = None
    description: Optional[str] = None
    is_night_shift: bool = False

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Shift name must not be empty")
        return v.strip()

    @field_validator("color_code")
    @classmethod
    def valid_hex_color(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not (len(v) == 7 and v.startswith("#")):
            raise ValueError("color_code must be a 7-character hex string, e.g. #6366f1")
        return v


class ShiftTypeUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    work_hours_per_day: Optional[float] = None
    break_minutes: Optional[int] = None
    grace_period_minutes: Optional[int] = None
    color_code: Optional[str] = None
    description: Optional[str] = None
    is_night_shift: Optional[bool] = None
    is_active: Optional[bool] = None


class ShiftTypeResponse(BaseModel):
    id: UUID
    company_id: UUID
    name: str
    start_time: time
    end_time: time
    work_hours_per_day: float
    break_minutes: int
    grace_period_minutes: int
    color_code: Optional[str] = None
    description: Optional[str] = None
    is_night_shift: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
