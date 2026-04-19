"""Internal endpoints — authenticated via X-Internal-Token header only."""
from fastapi import APIRouter, Depends
from typing import List
from uuid import UUID
from datetime import datetime, timezone

from app.core.security import verify_internal_token
from app.core.responses import APIResponse
from app.schemas.calendar_event import EventCreate, CalendarEventResponse
from app.schemas.task import CalendarTaskResponse

router = APIRouter(dependencies=[Depends(verify_internal_token)])


@router.post("/events/inject", response_model=APIResponse[CalendarEventResponse], status_code=201)
async def inject_event(data: EventCreate):
    """Other services push leave/shift/holiday events into calendar.

    Requires explicit company_id in the payload — validated before setting tenant context.
    """
    from app.db.session import AsyncSessionLocal
    from app.services.event_service import create_event
    from app.models.calendar import Calendar
    from sqlalchemy.future import select
    from uuid import uuid4
    from fastapi import HTTPException

    if not getattr(data, "company_id", None):
        raise HTTPException(status_code=400, detail="company_id is required for event injection")

    async with AsyncSessionLocal() as db:
        # Verify the target calendar belongs to the stated company
        result = await db.execute(
            select(Calendar).where(
                Calendar.id == data.calendar_id,
                Calendar.company_id == data.company_id,
            )
        )
        if not result.scalars().first():
            raise HTTPException(status_code=403, detail="Calendar does not belong to stated company")

        db.info["company_id"] = str(data.company_id)
        event = await create_event(db, data, uuid4(), str(data.company_id))
    return APIResponse(success=True, data=event)


@router.get("/tasks/by-employee/{employee_id}", response_model=APIResponse[List[CalendarTaskResponse]])
async def tasks_by_employee(employee_id: UUID, company_id: str):
    """Fetch open tasks assigned to an employee — used by other services."""
    from app.db.session import AsyncSessionLocal
    from app.repositories.task_repository import list_tasks

    async with AsyncSessionLocal() as db:
        db.info["company_id"] = company_id
        tasks = await list_tasks(db, company_id, assignee_id=employee_id)
    return APIResponse(success=True, data=tasks)
