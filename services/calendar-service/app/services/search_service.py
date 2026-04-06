"""PostgreSQL tsvector full-text search across events, tasks, and comments."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, text


async def search(
    db: AsyncSession,
    company_id: str,
    q: str,
    search_type: Optional[str] = None,  # "events" | "tasks" | "comments" | None = all
    workspace_id: Optional[UUID] = None,
    fields: Optional[str] = None,  # sparse fieldset e.g. "id,title,start_time"
    limit: int = 20,
) -> dict:
    """Returns ranked FTS results grouped by type."""
    from app.models.calendar_event import CalendarEvent
    from app.models.task import CalendarTask
    from app.models.task_comment import TaskComment

    ts_query = func.plainto_tsquery("english", q)
    results = {"events": [], "tasks": [], "comments": []}

    if search_type in (None, "events"):
        q_stmt = (
            select(CalendarEvent)
            .where(
                CalendarEvent.company_id == company_id,
                CalendarEvent.is_deleted == False,
                CalendarEvent.search_vector.op("@@")(ts_query),
            )
            .order_by(func.ts_rank(CalendarEvent.search_vector, ts_query).desc())
            .limit(limit)
        )
        rows = (await db.execute(q_stmt)).scalars().all()
        results["events"] = _sparse(rows, fields, ["id", "title", "start_time", "end_time", "event_type", "calendar_id"])

    if search_type in (None, "tasks"):
        q_stmt = select(CalendarTask).where(
            CalendarTask.company_id == company_id,
            CalendarTask.is_deleted == False,
            CalendarTask.search_vector.op("@@")(ts_query),
        )
        if workspace_id:
            q_stmt = q_stmt.where(CalendarTask.workspace_id == workspace_id)
        q_stmt = q_stmt.order_by(func.ts_rank(CalendarTask.search_vector, ts_query).desc()).limit(limit)
        rows = (await db.execute(q_stmt)).scalars().all()
        results["tasks"] = _sparse(rows, fields, ["id", "title", "status", "priority", "workspace_id"])

    if search_type in (None, "comments"):
        q_stmt = (
            select(TaskComment)
            .where(
                TaskComment.company_id == company_id,
                TaskComment.is_deleted == False,
                TaskComment.search_vector.op("@@")(ts_query),
            )
            .order_by(func.ts_rank(TaskComment.search_vector, ts_query).desc())
            .limit(limit)
        )
        rows = (await db.execute(q_stmt)).scalars().all()
        results["comments"] = _sparse(rows, fields, ["id", "body", "task_id", "author_id"])

    return results


def _sparse(rows, fields_str: Optional[str], default_fields: list) -> list:
    """Return only the requested fields from each row."""
    wanted = set(fields_str.split(",")) if fields_str else set(default_fields)
    out = []
    for row in rows:
        obj = {}
        for f in wanted:
            if hasattr(row, f):
                val = getattr(row, f)
                obj[f] = str(val) if val is not None else None
        out.append(obj)
    return out
