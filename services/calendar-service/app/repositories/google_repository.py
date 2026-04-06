from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.google_integration import GoogleIntegration
from app.models.sync_log import SyncLog


async def get_integration(db: AsyncSession, employee_id: UUID, company_id: str) -> Optional[GoogleIntegration]:
    result = await db.execute(
        select(GoogleIntegration).where(
            GoogleIntegration.employee_id == employee_id,
            GoogleIntegration.company_id == company_id,
            GoogleIntegration.is_deleted == False,
        )
    )
    return result.scalars().first()


async def list_active_integrations(db: AsyncSession) -> List[GoogleIntegration]:
    result = await db.execute(
        select(GoogleIntegration).where(
            GoogleIntegration.status == "active",
            GoogleIntegration.is_deleted == False,
        )
    )
    return result.scalars().all()


async def get_last_sync_token(db: AsyncSession, integration_id: UUID) -> Optional[str]:
    result = await db.execute(
        select(SyncLog.next_sync_token).where(
            SyncLog.integration_id == integration_id,
            SyncLog.next_sync_token != None,
        ).order_by(SyncLog.synced_at.desc()).limit(1)
    )
    row = result.first()
    return row[0] if row else None
