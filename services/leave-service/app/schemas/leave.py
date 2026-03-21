from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime

from app.core.constants import LeaveStatus, DurationType


# Shared properties
class LeaveTypeBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    days_allowed: int = Field(..., ge=0)
    requires_approval: bool = True
    is_active: bool = True


class LeaveTypeCreate(LeaveTypeBase):
    pass


class LeaveTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    days_allowed: Optional[int] = Field(None, ge=0)
    requires_approval: Optional[bool] = None
    is_active: Optional[bool] = None


class LeaveTypeResponse(LeaveTypeBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: Optional[UUID] = None


class LeaveBalanceBase(BaseModel):
    employee_id: UUID
    leave_type_id: UUID
    total_days: int = Field(0, ge=0)
    used_days: int = Field(0, ge=0)
    pending_days: int = Field(0, ge=0)
    year: int


class LeaveBalanceCreate(LeaveBalanceBase):
    pass


class LeaveBalanceUpdate(BaseModel):
    total_days: Optional[int] = Field(None, ge=0)
    used_days: Optional[int] = Field(None, ge=0)
    pending_days: Optional[int] = Field(None, ge=0)


class LeaveBalanceResponse(LeaveBalanceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: Optional[UUID] = None
    leave_type: LeaveTypeResponse


class BulkLeaveBalanceItem(BaseModel):
    employee_id: UUID
    total_days: int = Field(..., ge=0)


class BulkLeaveBalanceRequest(BaseModel):
    leave_type_id: UUID
    year: int
    items: List[BulkLeaveBalanceItem]


class BulkLeaveBalanceResult(BaseModel):
    index: int
    employee_id: UUID
    success: bool
    error: Optional[str] = None


class BulkLeaveBalanceResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: List[BulkLeaveBalanceResult]


class LeaveRequestBase(BaseModel):
    leave_type_id: UUID
    start_date: date
    end_date: date
    duration_type: DurationType = Field(default=DurationType.FULL_DAY)
    is_emergency: bool = Field(default=False)
    reason: str = Field(..., min_length=10, max_length=1000, description="Detailed reason for the leave (min 10 chars)")
    supporting_document: Optional[str] = None

    @model_validator(mode='after')
    def validate_dates(self) -> 'LeaveRequestBase':
        if self.end_date < self.start_date:
            raise ValueError('end_date must be after or equal to start_date')
        if self.duration_type == DurationType.HALF_DAY and self.start_date != self.end_date:
            raise ValueError("Half day leave must have the same start and end date")
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
    company_id: Optional[UUID] = None
    total_days: int
    status: LeaveStatus
    approved_by_id: Optional[UUID] = None
    manager_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    leave_type: LeaveTypeResponse
