"""
Google Tasks ↔ HRMS sync (inbound: Google → HRMS).

Each Google Task list maps to a workspace (or floats without one).
Tasks are matched on google_task_id. Status mapping:
  Google "needsAction" → HRMS "todo"
  Google "completed"   → HRMS "done"
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from googleapiclient.discovery import build as _build_service
from googleapiclient.errors import HttpError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.task import CalendarTask
from app.models.google_integration import GoogleIntegration
from app.services.google_oauth_service import ensure_valid_credentials
from app.repositories.google_repository import (
    save_sync_log,
    mark_integration_error,
    mark_integration_success,
)

logger = logging.getLogger(__name__)

_STATUS_MAP = {"needsAction": "todo", "completed": "done"}
_PRIORITY_MAP = {"1": "urgent", "2": "high", "3": "medium", "4": "low"}


def _parse_google_dt(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


async def sync_tasks_for_integration(
    db: AsyncSession,
    integration: GoogleIntegration,
) -> dict:
    """Pull all task lists + tasks from Google Tasks API and upsert locally."""
    now = datetime.now(timezone.utc)
    if integration.next_sync_allowed_at and integration.next_sync_allowed_at > now:
        return {"synced": 0, "failed": 0}

    try:
        creds = await ensure_valid_credentials(db, integration)
    except Exception as exc:
        await mark_integration_error(db, integration)
        return {"synced": 0, "failed": 1}

    service = _build_service("tasks", "v1", credentials=creds, cache_discovery=False)
    company_id = str(integration.company_id)
    synced = failed = 0

    try:
        task_lists_resp = service.tasklists().list(maxResults=100).execute()
        task_lists = task_lists_resp.get("items", [])
    except HttpError as exc:
        logger.error(f"Failed to list Google task lists: {exc}")
        await mark_integration_error(db, integration)
        return {"synced": 0, "failed": 1}

    for tl in task_lists:
        tl_id = tl.get("id")

        try:
            tasks_resp = service.tasks().list(
                tasklist=tl_id,
                maxResults=100,
                showCompleted=True,
                showHidden=True,
            ).execute()
            items = tasks_resp.get("items", [])
        except HttpError as exc:
            logger.warning(f"Failed to list tasks for list {tl_id}: {exc}")
            failed += 1
            continue

        for g_task in items:
            try:
                await _upsert_task(db, g_task, tl_id, integration, company_id)
                synced += 1
            except Exception as exc:
                logger.warning(f"Failed to upsert task {g_task.get('id')}: {exc}")
                failed += 1

    await save_sync_log(
        db,
        employee_id=integration.employee_id,
        integration_id=integration.id,
        resource_type="calendar_task",
        local_resource_id=None,
        google_resource_id=None,
        sync_direction="inbound",
        sync_status="success" if failed == 0 else "partial",
        next_sync_token=None,
    )
    await mark_integration_success(db, integration)
    return {"synced": synced, "failed": failed}


async def _upsert_task(
    db: AsyncSession,
    g_task: dict,
    tasklist_id: str,
    integration: GoogleIntegration,
    company_id: str,
) -> None:
    google_task_id = g_task.get("id")
    if not google_task_id:
        return

    title = g_task.get("title", "(No title)")
    notes = g_task.get("notes")
    status = _STATUS_MAP.get(g_task.get("status", "needsAction"), "todo")
    due_date = _parse_google_dt(g_task.get("due"))
    completed_at = _parse_google_dt(g_task.get("completed"))
    deleted = g_task.get("deleted", False)

    result = await db.execute(
        select(CalendarTask).where(
            CalendarTask.google_task_id == google_task_id,
            CalendarTask.is_deleted == False,
        ).limit(1)
    )
    existing = result.scalars().first()

    if deleted:
        if existing:
            existing.is_deleted = True
            existing.deleted_at = datetime.now(timezone.utc)
            await db.flush()
        return

    if existing:
        existing.title = title
        existing.description = notes
        existing.status = status
        existing.due_date = due_date
        if completed_at:
            existing.completed_at = completed_at
        await db.flush()
    else:
        task = CalendarTask(
            company_id=company_id,
            title=title,
            description=notes,
            status=status,
            priority="medium",
            due_date=due_date,
            completed_at=completed_at,
            created_by=integration.employee_id,
            google_tasklist_id=tasklist_id,
            google_task_id=google_task_id,
            tags=[],
            attachments=[],
        )
        db.add(task)
        await db.flush()


async def push_task_to_google(
    db: AsyncSession,
    integration: GoogleIntegration,
    task: CalendarTask,
) -> Optional[str]:
    """
    Push a single local task to Google Tasks.
    Returns the Google task ID on success, None on failure.
    Used when a user creates a task in the HRMS and wants it mirrored.
    """
    try:
        creds = await ensure_valid_credentials(db, integration)
    except Exception:
        return None

    service = _build_service("tasks", "v1", credentials=creds, cache_discovery=False)

    # Use the task's stored tasklist ID or fall back to "@default"
    tasklist_id = task.google_tasklist_id or "@default"

    body: dict = {
        "title": task.title,
        "notes": task.description or "",
        "status": "completed" if task.status == "done" else "needsAction",
    }
    if task.due_date:
        body["due"] = task.due_date.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        created = service.tasks().insert(tasklist=tasklist_id, body=body).execute()
        return created.get("id")
    except HttpError as exc:
        logger.warning(f"Failed to push task {task.id} to Google: {exc}")
        return None


async def list_google_tasklists(integration: GoogleIntegration, db: AsyncSession) -> list:
    """Return a list of Google Task list metadata for the settings UI."""
    try:
        creds = await ensure_valid_credentials(db, integration)
        service = _build_service("tasks", "v1", credentials=creds, cache_discovery=False)
        resp = service.tasklists().list(maxResults=100).execute()
        return resp.get("items", [])
    except Exception as exc:
        logger.warning(f"Failed to list Google task lists: {exc}")
        return []
