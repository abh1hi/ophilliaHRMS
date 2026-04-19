from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.overtime_policy import OvertimePolicy, OvertimePolicyAudit


class OvertimePolicyRepository:
    """Data access for overtime_policies with scope-cascade lookup."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(OvertimePolicy.company_id == self._company_id)

    async def create(self, policy: OvertimePolicy) -> OvertimePolicy:
        policy.company_id = self._company_id
        self.db.add(policy)
        await self.db.flush()
        await self.db.refresh(policy)
        return policy

    async def get_by_id(self, policy_id: UUID) -> Optional[OvertimePolicy]:
        result = await self.db.execute(
            self._scoped(select(OvertimePolicy)).where(OvertimePolicy.id == policy_id)
        )
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> tuple[List[OvertimePolicy], int]:
        count = await self.db.execute(
            self._scoped(select(func.count(OvertimePolicy.id)))
        )
        total = count.scalar() or 0
        result = await self.db.execute(
            self._scoped(select(OvertimePolicy))
            .where(OvertimePolicy.is_active.is_(True))
            .order_by(OvertimePolicy.created_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_for_employee(
        self,
        employee_id: UUID,
        location_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
    ) -> Optional[OvertimePolicy]:
        """Cascade: employee → location → department → company-global."""
        scope_filters = [
            OvertimePolicy.employee_id == employee_id,
        ]
        if location_id:
            scope_filters.append(
                and_(OvertimePolicy.location_id == location_id, OvertimePolicy.employee_id.is_(None))
            )
        if department_id:
            scope_filters.append(
                and_(
                    OvertimePolicy.department_id == department_id,
                    OvertimePolicy.employee_id.is_(None),
                    OvertimePolicy.location_id.is_(None),
                )
            )
        scope_filters.append(
            and_(
                OvertimePolicy.employee_id.is_(None),
                OvertimePolicy.location_id.is_(None),
                OvertimePolicy.department_id.is_(None),
            )
        )
        priority = case(
            (OvertimePolicy.employee_id == employee_id, 1),
            (OvertimePolicy.location_id == location_id, 2) if location_id else (False, 5),
            (OvertimePolicy.department_id == department_id, 3) if department_id else (False, 5),
            else_=4,
        )
        result = await self.db.execute(
            self._scoped(select(OvertimePolicy))
            .where(and_(OvertimePolicy.is_active.is_(True), or_(*scope_filters)))
            .order_by(priority)
            .limit(1)
        )
        return result.scalars().first()

    async def update(self, policy: OvertimePolicy, updates: dict) -> OvertimePolicy:
        for key, value in updates.items():
            setattr(policy, key, value)
        await self.db.flush()
        await self.db.refresh(policy)
        return policy

    async def delete(self, policy: OvertimePolicy) -> None:
        await self.db.delete(policy)
        await self.db.flush()

    async def create_audit(self, audit: OvertimePolicyAudit) -> OvertimePolicyAudit:
        self.db.add(audit)
        await self.db.flush()
        return audit
