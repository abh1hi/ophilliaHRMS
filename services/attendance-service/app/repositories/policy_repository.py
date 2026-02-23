from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.attendance_policy import AttendancePolicy


class PolicyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, policy: AttendancePolicy) -> AttendancePolicy:
        self.db.add(policy)
        await self.db.commit()
        await self.db.refresh(policy)
        return policy

    async def get_by_id(self, policy_id: UUID) -> Optional[AttendancePolicy]:
        result = await self.db.execute(
            select(AttendancePolicy).where(AttendancePolicy.id == policy_id)
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
            select(AttendancePolicy).where(AttendancePolicy.employee_id == employee_id)
        )
        policy = result.scalars().first()
        if policy:
            return policy

        # 2. Try department-level policy
        if department_id:
            result = await self.db.execute(
                select(AttendancePolicy).where(
                    AttendancePolicy.department_id == department_id
                )
            )
            policy = result.scalars().first()
            if policy:
                return policy

        # 3. No policy found — caller should use global default
        return None

    async def get_all(self) -> tuple[List[AttendancePolicy], int]:
        count_result = await self.db.execute(select(func.count(AttendancePolicy.id)))
        total = count_result.scalar() or 0
        result = await self.db.execute(
            select(AttendancePolicy).order_by(AttendancePolicy.created_at.desc())
        )
        return list(result.scalars().all()), total
