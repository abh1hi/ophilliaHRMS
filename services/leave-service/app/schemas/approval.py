from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.core.constants import LeaveStatus, ApprovalLevel

class LeaveApprovalBase(BaseModel):
    leave_request_id: UUID
    approver_id: UUID
    level: ApprovalLevel
    status: LeaveStatus
    remarks: Optional[str] = Field(None, max_length=1000)

class LeaveApprovalCreate(LeaveApprovalBase):
    pass

class LeaveApprovalUpdate(BaseModel):
    status: LeaveStatus
    remarks: Optional[str] = Field(None, max_length=1000)

class LeaveApprovalResponse(LeaveApprovalBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
