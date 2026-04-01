from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy_template import PolicyTemplate


class PolicyTemplateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant dependency")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(PolicyTemplate.company_id == self._company_id)

    async def create(self, template: PolicyTemplate) -> PolicyTemplate:
        template.company_id = self._company_id
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def get_by_id(self, template_id: UUID) -> Optional[PolicyTemplate]:
        result = await self.db.execute(
            self._scoped(
                select(PolicyTemplate).where(PolicyTemplate.id == template_id)
            )
        )
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[PolicyTemplate]:
        result = await self.db.execute(
            self._scoped(
                select(PolicyTemplate).where(
                    and_(PolicyTemplate.name == name, PolicyTemplate.is_active == True)
                )
            )
        )
        return result.scalars().first()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> tuple[List[PolicyTemplate], int]:
        q = self._scoped(select(PolicyTemplate))
        if not include_inactive:
            q = q.where(PolicyTemplate.is_active == True)

        count_result = await self.db.execute(
            select(func.count()).select_from(q.subquery())
        )
        total = count_result.scalar() or 0
        result = await self.db.execute(
            q.order_by(PolicyTemplate.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def update(self, template: PolicyTemplate, updates: dict) -> PolicyTemplate:
        for key, value in updates.items():
            setattr(template, key, value)
        await self.db.commit()
        await self.db.refresh(template)
        return template
