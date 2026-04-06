from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.calendar import Calendar


async def get_calendar(db: AsyncSession, calendar_id: UUID, company_id: str) -> Optional[Calendar]:
    result = await db.execute(
        select(Calendar).where(
            Calendar.id == calendar_id,
            Calendar.company_id == company_id,
            Calendar.is_deleted == False,
        )
    )
    return result.scalars().first()


async def get_calendar_by_share_token(db: AsyncSession, token: str) -> Optional[Calendar]:
    result = await db.execute(
        select(Calendar).where(
            Calendar.public_share_token == token,
            Calendar.is_deleted == False,
        )
    )
    return result.scalars().first()


async def list_calendars(db: AsyncSession, company_id: str, workspace_id: Optional[UUID] = None) -> List[Calendar]:
    q = select(Calendar).where(Calendar.company_id == company_id, Calendar.is_deleted == False)
    if workspace_id:
        q = q.where(Calendar.workspace_id == workspace_id)
    result = await db.execute(q)
    return result.scalars().all()
