from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department


class DepartmentRepository:
    """Data access layer for departments — async CRUD."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, department: Department) -> Department:
        self.db.add(department)
        await self.db.commit()
        await self.db.refresh(department)
        return department

    async def get_by_id(self, department_id: UUID) -> Optional[Department]:
        result = await self.db.execute(
            select(Department).where(Department.id == department_id)
        )
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[Department]:
        result = await self.db.execute(
            select(Department).where(Department.name == name)
        )
        return result.scalars().first()

    async def get_all(self) -> tuple[List[Department], int]:
        """Return all departments with total count."""
        count_result = await self.db.execute(select(func.count(Department.id)))
        total = count_result.scalar() or 0

        result = await self.db.execute(
            select(Department).order_by(Department.name.asc())
        )
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
