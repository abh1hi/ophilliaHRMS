from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department


class DepartmentRepository:
    """Data access layer for departments — async CRUD with tenant isolation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        """Extract the tenant company_id set by get_db_with_tenant dependency."""
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant dependency")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        """Apply tenant filter to a query."""
        return stmt.where(Department.company_id == self._company_id)

    async def create(self, department: Department) -> Department:
        department.company_id = self._company_id
        self.db.add(department)
        await self.db.commit()
        await self.db.refresh(department)
        return department

    async def get_by_id(self, department_id: UUID) -> Optional[Department]:
        result = await self.db.execute(
            self._scoped(select(Department).where(Department.id == department_id))
        )
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[Department]:
        result = await self.db.execute(
            self._scoped(select(Department).where(Department.name == name))
        )
        return result.scalars().first()

    async def get_all(self, include_inactive: bool = False) -> tuple[List[Department], int]:
        """Return all departments with total count, scoped to tenant."""
        base = self._scoped(select(func.count(Department.id)))
        if not include_inactive:
            base = base.where(Department.is_active == 1)
        count_result = await self.db.execute(base)
        total = count_result.scalar() or 0

        query = self._scoped(select(Department).order_by(Department.name.asc()))
        if not include_inactive:
            query = query.where(Department.is_active == 1)
        result = await self.db.execute(query)
        departments = result.scalars().all()

        return list(departments), total

    async def update(self, department: Department, update_data: dict) -> Department:
        for field, value in update_data.items():
            if value is not None:
                setattr(department, field, value)
        await self.db.commit()
        await self.db.refresh(department)
        return department

    async def delete(self, department: Department) -> None:
        await self.db.delete(department)
        await self.db.commit()
