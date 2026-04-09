from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel


class LeaveLedgerEntryResponse(BaseModel):
    id: UUID
    company_id: UUID
    employee_id: UUID
    leave_type_id: UUID
    from_date: date
    to_date: date
    leaves: float
    transaction_type: str
    transaction_name: Optional[str] = None
    is_carry_forward: int
    is_expired: int
    is_lwp: int
    holiday_list_id: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LeaveLedgerListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    entries: List[LeaveLedgerEntryResponse]
