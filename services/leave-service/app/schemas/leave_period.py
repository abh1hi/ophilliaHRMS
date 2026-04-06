from typing import Optional
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel


class LeavePeriodCreate(BaseModel):
    name: str
    from_date: date
    to_date: date
    is_active: int = 1
    optional_holiday_list_id: Optional[UUID] = None


class LeavePeriodUpdate(BaseModel):
    name: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    is_active: Optional[int] = None
    optional_holiday_list_id: Optional[UUID] = None


class LeavePeriodResponse(BaseModel):
    id: UUID
    company_id: UUID
    name: str
    from_date: date
    to_date: date
    is_active: int
    optional_holiday_list_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
