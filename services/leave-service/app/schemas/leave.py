from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime

from app.core.constants import LeaveStatus


# Shared properties
class LeaveTypeBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    days_allowed: int = Field(..., ge=0)
    requires_approval: bool = True
    is_active: bool = True


class LeaveTypeCreate(LeaveTypeBase):
    pass


class LeaveTypeUpdate(LeaveTypeBase):
    pass


class LeaveTypeResponse(LeaveTypeBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID


class LeaveBalanceBase(BaseModel):
    employee_id: UUID
    leave_type_id: UUID
    total_days: int = Field(0, ge=0)
    used_days: int = Field(0, ge=0)
    pending_days: int = Field(0, ge=0)
    year: int


class LeaveBalanceCreate(LeaveBalanceBase):
    pass


class LeaveBalanceResponse(LeaveBalanceBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    leave_type: LeaveTypeResponse


class LeaveRequestBase(BaseModel):
    leave_type_id: UUID
    start_date: date
    end_date: date
    reason: Optional[str] = None

    @model_validator(mode='after')
    def validate_dates(self) -> 'LeaveRequestBase':
        if self.end_date < self.start_date:
            raise ValueError('end_date must be after or equal to start_date')
        return self


class LeaveRequestCreate(LeaveRequestBase):
    employee_id: UUID


class LeaveRequestUpdate(BaseModel):
    status: LeaveStatus
    manager_notes: Optional[str] = None


class LeaveRequestResponse(LeaveRequestBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    employee_id: UUID
    total_days: int
    status: LeaveStatus
    approved_by_id: Optional[UUID] = None
    manager_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    leave_type: LeaveTypeResponse
