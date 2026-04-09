from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel


class LeavePolicyItemCreate(BaseModel):
    leave_type_id: UUID
    annual_allocation: float


class LeavePolicyItemResponse(BaseModel):
    id: UUID
    policy_id: UUID
    leave_type_id: UUID
    annual_allocation: float

    model_config = {"from_attributes": True}


class LeavePolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    items: List[LeavePolicyItemCreate] = []


class LeavePolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[int] = None


class LeavePolicyResponse(BaseModel):
    id: UUID
    company_id: UUID
    name: str
    description: Optional[str] = None
    is_active: int
    items: List[LeavePolicyItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Leave Policy Assignment ──────────────────────────────────────────────────

class LeavePolicyAssignmentCreate(BaseModel):
    employee_id: UUID
    policy_id: UUID
    leave_period_id: Optional[UUID] = None
    assignment_based_on: str = "custom"  # "leave_period" | "joining_date" | "custom"
    effective_from: date
    effective_to: Optional[date] = None


class LeavePolicyAssignmentResponse(BaseModel):
    id: UUID
    company_id: UUID
    employee_id: UUID
    policy_id: UUID
    leave_period_id: Optional[UUID] = None
    assignment_based_on: str
    effective_from: date
    effective_to: Optional[date] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
