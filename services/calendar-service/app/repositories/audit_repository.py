from uuid import UUID
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.calendar_audit_log import CalendarAuditLog


async def list_audit_logs(
    db: AsyncSession,
    company_id: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[UUID] = None,
    actor_id: Optional[UUID] = None,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[CalendarAuditLog]:
    q = select(CalendarAuditLog).where(CalendarAuditLog.company_id == company_id)
    if resource_type:
        q = q.where(CalendarAuditLog.resource_type == resource_type)
    if resource_id:
        q = q.where(CalendarAuditLog.resource_id == resource_id)
    if actor_id:
        q = q.where(CalendarAuditLog.actor_id == actor_id)
    if from_dt:
        q = q.where(CalendarAuditLog.created_at >= from_dt)
    if to_dt:
        q = q.where(CalendarAuditLog.created_at <= to_dt)
    result = await db.execute(q.order_by(CalendarAuditLog.created_at.desc()).offset(skip).limit(limit))
    return result.scalars().all()
