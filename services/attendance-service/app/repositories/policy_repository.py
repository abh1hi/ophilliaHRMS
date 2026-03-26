from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.attendance_policy import AttendancePolicy


class PolicyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant dependency")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(AttendancePolicy.company_id == self._company_id)

    async def create(self, policy: AttendancePolicy) -> AttendancePolicy:
        policy.company_id = self._company_id
        self.db.add(policy)
        await self.db.commit()
        await self.db.refresh(policy)
        return policy

    async def get_by_id(self, policy_id: UUID) -> Optional[AttendancePolicy]:
        result = await self.db.execute(
            self._scoped(select(AttendancePolicy)).where(AttendancePolicy.id == policy_id)
        )
        return result.scalars().first()

    async def get_for_employee(
        self, employee_id: UUID, department_id: Optional[UUID] = None
    ) -> Optional[AttendancePolicy]:
        """Resolve policy: employee-level > department-level > None (default).

        Args:
            employee_id: Auth-service user_id or employee service employee_id.
            department_id: Employee's department_id for fallback lookup.
        """
        # 1. Try employee-level policy
        result = await self.db.execute(
            self._scoped(select(AttendancePolicy)).where(AttendancePolicy.employee_id == employee_id)
        )
        policy = result.scalars().first()
        if policy:
            return policy

        # 2. Try department-level policy
        if department_id:
            result = await self.db.execute(
                self._scoped(select(AttendancePolicy)).where(
                    AttendancePolicy.department_id == department_id
                )
            )
            policy = result.scalars().first()
            if policy:
                return policy

        # 3. Try company-wide policy (no employee or department)
        result = await self.db.execute(
            self._scoped(select(AttendancePolicy)).where(
                and_(
                    AttendancePolicy.employee_id.is_(None),
                    AttendancePolicy.department_id.is_(None),
                )
            )
        )
        policy = result.scalars().first()
        if policy:
            return policy

        # 4. No policy found — caller should use global default
        return None

    async def update(self, policy: AttendancePolicy, updates: dict) -> AttendancePolicy:
        for key, value in updates.items():
            setattr(policy, key, value)
        await self.db.commit()
        await self.db.refresh(policy)
        return policy

    async def delete(self, policy: AttendancePolicy) -> None:
        await self.db.delete(policy)
        await self.db.commit()

    async def get_all(self, skip: int = 0, limit: int = 100) -> tuple[List[AttendancePolicy], int]:
        count_result = await self.db.execute(self._scoped(select(func.count(AttendancePolicy.id))))
        total = count_result.scalar() or 0
        result = await self.db.execute(
            self._scoped(select(AttendancePolicy)).order_by(AttendancePolicy.created_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total
