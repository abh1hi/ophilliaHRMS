from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date, time


class ShiftScheduleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    shift_type_id: UUID
    clock_in_start_time: time
    clock_in_end_time: time
    clock_out_start_time: time
    clock_out_end_time: time
    auto_clock_out_enabled: bool = True
    auto_clock_out_time: time
    tasks_mandatory: bool = False
    allowed_clock_in_location_ids: List[UUID] = Field(default_factory=list)
    allowed_clock_out_location_ids: List[UUID] = Field(default_factory=list)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Schedule name must not be empty")
        return v.strip()

    @model_validator(mode="after")
    def validate_windows(self) -> "ShiftScheduleCreate":
        if self.clock_in_start_time >= self.clock_in_end_time:
            raise ValueError("clock_in_start_time must be before clock_in_end_time")
        if self.clock_out_start_time >= self.clock_out_end_time:
            raise ValueError("clock_out_start_time must be before clock_out_end_time")
        if not self.allowed_clock_in_location_ids:
            raise ValueError("At least one clock-in location is required")
        if not self.allowed_clock_out_location_ids:
            raise ValueError("At least one clock-out location is required")
        return self


class ShiftScheduleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    shift_type_id: Optional[UUID] = None
    clock_in_start_time: Optional[time] = None
    clock_in_end_time: Optional[time] = None
    clock_out_start_time: Optional[time] = None
    clock_out_end_time: Optional[time] = None
    auto_clock_out_enabled: Optional[bool] = None
    auto_clock_out_time: Optional[time] = None
    tasks_mandatory: Optional[bool] = None
    allowed_clock_in_location_ids: Optional[List[UUID]] = None
    allowed_clock_out_location_ids: Optional[List[UUID]] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: Optional[int] = None


class ShiftScheduleResponse(BaseModel):
    id: UUID
    company_id: UUID
    name: str
    description: Optional[str] = None
    shift_type_id: UUID
    clock_in_start_time: time
    clock_in_end_time: time
    clock_out_start_time: time
    clock_out_end_time: time
    auto_clock_out_enabled: bool
    auto_clock_out_time: time
    tasks_mandatory: bool
    allowed_clock_in_location_ids: List[UUID] = Field(default_factory=list)
    allowed_clock_out_location_ids: List[UUID] = Field(default_factory=list)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
