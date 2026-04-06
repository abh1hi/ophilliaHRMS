"""Audit trail service — writes immutable CalendarAuditLog entries."""
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar_audit_log import CalendarAuditLog


async def record(
    db: AsyncSession,
    company_id: str,
    actor_id: UUID,
    actor_role: str,
    resource_type: str,
    resource_id: UUID,
    action: str,
    before_state: Optional[Any] = None,
    after_state: Optional[Any] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """Write one audit log entry. Call this after every mutating operation."""
    log = CalendarAuditLog(
        company_id=company_id,
        actor_id=actor_id,
        actor_role=actor_role,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        before_state=before_state,
        after_state=after_state,
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log)
    # Don't commit here — let the caller's transaction handle it,
    # or call db.flush() so the log is included in the same commit.
    await db.flush()
