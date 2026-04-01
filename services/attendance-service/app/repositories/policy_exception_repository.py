from typing import List, Optional
from uuid import UUID
from datetime import date

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy_exception import PolicyException


class PolicyExceptionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant dependency")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(PolicyException.company_id == self._company_id)

    async def create(self, exception: PolicyException) -> PolicyException:
        exception.company_id = self._company_id
        self.db.add(exception)
        await self.db.commit()
        await self.db.refresh(exception)
        return exception

    async def get_by_id(self, exception_id: UUID) -> Optional[PolicyException]:
        result = await self.db.execute(
            self._scoped(
                select(PolicyException).where(PolicyException.id == exception_id)
            )
        )
        return result.scalars().first()

    async def get_active_for_employee(
        self, employee_id: UUID, target_date: date
    ) -> Optional[PolicyException]:
        """Return the active exception covering target_date for an employee, if any."""
        result = await self.db.execute(
            self._scoped(
                select(PolicyException).where(
                    and_(
                        PolicyException.employee_id == employee_id,
                        PolicyException.is_active == True,
                        PolicyException.from_date <= target_date,
                        or_(
                            PolicyException.to_date.is_(None),
                            PolicyException.to_date >= target_date,
                        ),
                    )
                )
            ).order_by(PolicyException.created_at.desc()).limit(1)
        )
        return result.scalars().first()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        employee_id: Optional[UUID] = None,
        include_inactive: bool = False,
    ) -> tuple[List[PolicyException], int]:
        q = self._scoped(select(PolicyException))
        if employee_id:
            q = q.where(PolicyException.employee_id == employee_id)
        if not include_inactive:
            q = q.where(PolicyException.is_active == True)

        count_result = await self.db.execute(
            select(func.count()).select_from(q.subquery())
        )
        total = count_result.scalar() or 0
        result = await self.db.execute(
            q.order_by(PolicyException.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def update(self, exception: PolicyException, updates: dict) -> PolicyException:
        for key, value in updates.items():
            setattr(exception, key, value)
        await self.db.commit()
        await self.db.refresh(exception)
        return exception

    async def delete(self, exception: PolicyException) -> None:
        await self.db.delete(exception)
        await self.db.commit()
