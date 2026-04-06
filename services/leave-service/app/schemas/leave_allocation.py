from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel


class LeaveAllocationCreate(BaseModel):
    employee_id: UUID
    leave_type_id: UUID
    leave_period_id: Optional[UUID] = None
    from_date: date
    to_date: date
    new_leaves_allocated: float
    carry_forward_days: float = 0
    add_unused_from_previous: bool = False  # if True, fetch prior period balance and add


class LeaveAllocationUpdate(BaseModel):
    new_leaves_allocated: Optional[float] = None
    carry_forward_days: Optional[float] = None
    status: Optional[str] = None


class LeaveAllocationResponse(BaseModel):
    id: UUID
    company_id: UUID
    employee_id: UUID
    leave_type_id: UUID
    assignment_id: Optional[UUID] = None
    leave_period_id: Optional[UUID] = None
    from_date: date
    to_date: date
    new_leaves_allocated: float
    carry_forward_days: float
    total_leaves_allocated: float
    used_leaves: float
    leaves_pending_approval: float
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeaveAllocationListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    allocations: List[LeaveAllocationResponse]


# ── Leave Adjustment ─────────────────────────────────────────────────────────

class LeaveAdjustmentCreate(BaseModel):
    allocation_id: UUID
    adjustment_type: str  # "allocate" | "reduce"
    adjustment_days: float
    reason: Optional[str] = None


class LeaveAdjustmentResponse(BaseModel):
    id: UUID
    company_id: UUID
    employee_id: UUID
    allocation_id: UUID
    adjustment_type: str
    adjustment_days: float
    reason: Optional[str] = None
    adjusted_by: UUID
    adjustment_date: date
    created_at: datetime

    model_config = {"from_attributes": True}
