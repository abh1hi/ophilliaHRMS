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
    """Other services push leave/shift/holiday events into calendar."""
    from app.db.session import AsyncSessionLocal
    from app.services.event_service import create_event
    from uuid import uuid4

    async with AsyncSessionLocal() as db:
        db.info["company_id"] = str(data.calendar_id)  # company_id set by caller in payload
        # For inject, we use a system user ID
        event = await create_event(db, data, uuid4(), str(data.calendar_id))
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
