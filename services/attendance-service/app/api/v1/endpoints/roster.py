from typing import Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, TokenPayload, get_db_with_tenant
from app.core.responses import ok
from app.repositories.shift_schedule_assignment_repository import ShiftScheduleAssignmentRepository
from app.schemas.shift_schedule_assignment import ShiftScheduleAssignmentResponse

router = APIRouter(prefix="/roster", tags=["roster"])


@router.get("")
async def get_roster(
    from_date: date = Query(...),
    to_date: date = Query(...),
    employee_id: Optional[UUID] = Query(None),
    _: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    repo = ShiftScheduleAssignmentRepository(db)
    assignments = await repo.get_all_for_date_range(from_date, to_date, employee_id=employee_id)
    data = [ShiftScheduleAssignmentResponse.model_validate(a).model_dump(mode="json") for a in assignments]
    return ok(data, meta={"from_date": str(from_date), "to_date": str(to_date), "count": len(data)})
