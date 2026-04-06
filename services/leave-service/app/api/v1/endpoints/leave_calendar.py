from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Annotated, List
from datetime import date, timedelta
from pydantic import BaseModel

from app.api.v1.dependencies import require_role, TokenPayload, get_db_with_tenant
from app.core.constants import UserRole, LeaveStatus
from app.models.leave import LeaveRequest
from app.schemas.response import APIResponse

router = APIRouter()

DB = Annotated[AsyncSession, Depends(get_db_with_tenant)]
CalendarUser = Annotated[TokenPayload, Depends(
    require_role(UserRole.HR, UserRole.MANAGER, UserRole.SUPER_ADMIN, UserRole.ADMIN)
)]


class CalendarDateResponse(BaseModel):
    date: date
    staff_on_leave: int
    staff_available: int
    leaves: List[dict]


@router.get("/", response_model=APIResponse[List[CalendarDateResponse]])
async def get_leave_calendar(
    start_date: date,
    end_date: date,
    *,
    db: DB,
    current_user: CalendarUser,
):
    company_id = db.info.get("company_id")
    query = (
        select(LeaveRequest)
        .options(selectinload(LeaveRequest.leave_type))
        .filter(
            LeaveRequest.company_id == company_id,
            LeaveRequest.status == LeaveStatus.APPROVED.value,
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date,
        )
    )
    result = await db.execute(query)
    leaves = result.scalars().all()

    calendar_data: dict = {}
    current_dt = start_date
    while current_dt <= end_date:
        calendar_data[current_dt] = []
        current_dt += timedelta(days=1)

    for leave in leaves:
        d = leave.start_date
        while d <= leave.end_date:
            if start_date <= d <= end_date:
                calendar_data[d].append({
                    "employee_id": str(leave.employee_id),
                    "leave_type": leave.leave_type.name,
                    "duration_type": leave.duration_type,
                })
            d += timedelta(days=1)

    response_data = [
        CalendarDateResponse(
            date=d,
            staff_on_leave=len(daily_leaves),
            staff_available=0,
            leaves=daily_leaves,
        )
        for d, daily_leaves in calendar_data.items()
    ]
    return APIResponse(success=True, data=response_data)
