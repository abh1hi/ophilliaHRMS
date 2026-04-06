from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel


class CompensatoryLeaveRequestCreate(BaseModel):
    leave_type_id: UUID
    work_from_date: date
    work_end_date: date
    reason: Optional[str] = None


class CompensatoryLeaveReview(BaseModel):
    status: str  # "approved" | "rejected"
    review_note: Optional[str] = None


class CompensatoryLeaveRequestResponse(BaseModel):
    id: UUID
    company_id: UUID
    employee_id: UUID
    leave_type_id: UUID
    work_from_date: date
    work_end_date: date
    reason: Optional[str] = None
    status: str
    leave_allocation_id: Optional[UUID] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompensatoryLeaveListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    requests: List[CompensatoryLeaveRequestResponse]
