from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession

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
        self,
        employee_id: UUID,
        department_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
    ) -> Optional[AttendancePolicy]:
        """Resolve policy via single-query cascade: employee → location → department → global.

        Uses one OR query ordered by scope priority; resolves in-memory.
        This avoids N sequential DB round-trips per clock-in.
        """
        candidates = await self.get_all_for_scopes(employee_id, location_id, department_id)
        return candidates[0] if candidates else None

    async def get_all_for_scopes(
        self,
        employee_id: UUID,
        location_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
    ) -> List[AttendancePolicy]:
        """Return all matching scope candidates ordered by priority (most specific first).

        Single DB query using OR scope filters + CASE WHEN ordering.
        Python caller iterates from most→least specific for field-level merge.
        """
        scope_filters = [AttendancePolicy.employee_id == employee_id]

        if location_id:
            scope_filters.append(
                and_(
                    AttendancePolicy.location_id == location_id,
                    AttendancePolicy.employee_id.is_(None),
                )
            )
        if department_id:
            scope_filters.append(
                and_(
                    AttendancePolicy.department_id == department_id,
                    AttendancePolicy.employee_id.is_(None),
                    AttendancePolicy.location_id.is_(None),
                )
            )
        scope_filters.append(
            and_(
                AttendancePolicy.employee_id.is_(None),
                AttendancePolicy.location_id.is_(None),
                AttendancePolicy.department_id.is_(None),
            )
        )

        priority = case(
            (AttendancePolicy.employee_id == employee_id, 1),
            (AttendancePolicy.location_id == location_id, 2) if location_id else (False, 5),
            (AttendancePolicy.department_id == department_id, 3) if department_id else (False, 5),
            else_=4,
        )

        result = await self.db.execute(
            self._scoped(select(AttendancePolicy))
            .where(or_(*scope_filters))
            .order_by(priority)
        )
        return list(result.scalars().all())

    async def update(self, policy: AttendancePolicy, updates: dict) -> AttendancePolicy:
        for key, value in updates.items():
            setattr(policy, key, value)
        await self.db.commit()
        await self.db.refresh(policy)
        return policy

    async def delete(self, policy: AttendancePolicy) -> None:
        await self.db.delete(policy)
        await self.db.commit()

    async def get_conflicting_policy(
        self,
        scope_type: str,
        scope_id: Optional[UUID] = None,
        exclude_id: Optional[UUID] = None,
    ) -> Optional[AttendancePolicy]:
        """Find an existing policy with the same scope to detect conflicts.

        scope_type: "employee" | "location" | "department" | "global"
        scope_id:   employee_id, location_id, or department_id (None for global)
        exclude_id: policy to exclude from the check (used on updates)
        """
        if scope_type == "employee":
            q = self._scoped(select(AttendancePolicy)).where(
                AttendancePolicy.employee_id == scope_id
            )
        elif scope_type == "location":
            q = self._scoped(select(AttendancePolicy)).where(
                and_(
                    AttendancePolicy.location_id == scope_id,
                    AttendancePolicy.employee_id.is_(None),
                )
            )
        elif scope_type == "department":
            q = self._scoped(select(AttendancePolicy)).where(
                and_(
                    AttendancePolicy.department_id == scope_id,
                    AttendancePolicy.employee_id.is_(None),
                    AttendancePolicy.location_id.is_(None),
                )
            )
        else:  # global
            q = self._scoped(select(AttendancePolicy)).where(
                and_(
                    AttendancePolicy.employee_id.is_(None),
                    AttendancePolicy.location_id.is_(None),
                    AttendancePolicy.department_id.is_(None),
                )
            )
        if exclude_id:
            q = q.where(AttendancePolicy.id != exclude_id)
        result = await self.db.execute(q.limit(1))
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> tuple[List[AttendancePolicy], int]:
        count_result = await self.db.execute(self._scoped(select(func.count(AttendancePolicy.id))))
        total = count_result.scalar() or 0
        result = await self.db.execute(
            self._scoped(select(AttendancePolicy)).order_by(AttendancePolicy.created_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total
