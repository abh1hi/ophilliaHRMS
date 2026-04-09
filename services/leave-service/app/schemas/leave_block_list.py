from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel


class LeaveBlockListDateCreate(BaseModel):
    block_date: date
    reason: Optional[str] = None


class LeaveBlockListAllowedCreate(BaseModel):
    approver_employee_id: UUID


class LeaveBlockListDateResponse(BaseModel):
    id: UUID
    block_list_id: UUID
    block_date: date
    reason: Optional[str] = None

    model_config = {"from_attributes": True}


class LeaveBlockListAllowedResponse(BaseModel):
    id: UUID
    block_list_id: UUID
    approver_employee_id: UUID

    model_config = {"from_attributes": True}


class LeaveBlockListCreate(BaseModel):
    name: str
    applies_to_company: int = 0
    dates: List[LeaveBlockListDateCreate] = []
    allowed_users: List[LeaveBlockListAllowedCreate] = []


class LeaveBlockListUpdate(BaseModel):
    name: Optional[str] = None
    applies_to_company: Optional[int] = None
    is_active: Optional[int] = None


class LeaveBlockListResponse(BaseModel):
    id: UUID
    company_id: UUID
    name: str
    applies_to_company: int
    is_active: int
    dates: List[LeaveBlockListDateResponse] = []
    allowed_users: List[LeaveBlockListAllowedResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
