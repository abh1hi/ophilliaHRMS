from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel


class LeaveEncashmentCreate(BaseModel):
    employee_id: UUID
    leave_type_id: UUID
    leave_period_id: Optional[UUID] = None
    leave_allocation_id: Optional[UUID] = None
    encashment_date: Optional[date] = None
    encashment_amount: float = 0


class LeaveEncashmentResponse(BaseModel):
    id: UUID
    company_id: UUID
    employee_id: UUID
    leave_type_id: UUID
    leave_period_id: Optional[UUID] = None
    leave_allocation_id: Optional[UUID] = None
    leave_balance: float
    encashable_days: float
    encashment_amount: float
    encashment_date: Optional[date] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeaveEncashmentListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    encashments: List[LeaveEncashmentResponse]
