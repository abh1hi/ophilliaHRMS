from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy_audit_log import PolicyAuditLog


class PolicyAuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant dependency")
        return UUID(cid) if isinstance(cid, str) else cid

    async def create(self, log: PolicyAuditLog) -> PolicyAuditLog:
        log.company_id = self._company_id
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def get_by_policy(
        self,
        policy_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[PolicyAuditLog], int]:
        base = (
            select(PolicyAuditLog)
            .where(
                PolicyAuditLog.company_id == self._company_id,
                PolicyAuditLog.policy_id == policy_id,
            )
        )
        count_result = await self.db.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar() or 0
        result = await self.db.execute(
            base.order_by(PolicyAuditLog.timestamp.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total
