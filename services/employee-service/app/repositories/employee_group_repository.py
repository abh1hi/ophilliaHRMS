from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee_group import EmployeeGroup, employee_group_members


class EmployeeGroupRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(EmployeeGroup.company_id == self._company_id)

    async def create(self, group: EmployeeGroup) -> EmployeeGroup:
        group.company_id = self._company_id
        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def get_by_id(self, group_id: UUID) -> Optional[EmployeeGroup]:
        result = await self.db.execute(
            self._scoped(select(EmployeeGroup).where(EmployeeGroup.id == group_id))
            .options(selectinload(EmployeeGroup.members))
        )
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[EmployeeGroup]:
        result = await self.db.execute(self._scoped(select(EmployeeGroup).where(EmployeeGroup.name == name)))
        return result.scalars().first()

    async def get_all(self, include_inactive: bool = False) -> tuple[List[EmployeeGroup], int]:
        base = self._scoped(select(func.count(EmployeeGroup.id)))
        query = self._scoped(select(EmployeeGroup).order_by(EmployeeGroup.name.asc()))
        if not include_inactive:
            base = base.where(EmployeeGroup.is_active == 1)
            query = query.where(EmployeeGroup.is_active == 1)
        total = (await self.db.execute(base)).scalar() or 0
        items = (await self.db.execute(query)).scalars().all()
        return list(items), total

    async def update(self, group: EmployeeGroup, data: dict) -> EmployeeGroup:
        for k, v in data.items():
            if v is not None:
                setattr(group, k, v)
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def add_member(self, group_id: UUID, employee_id: UUID) -> None:
        await self.db.execute(
            insert(employee_group_members).values(
                group_id=group_id,
                employee_id=employee_id,
                company_id=self._company_id,
            ).on_conflict_do_nothing()
        )
        await self.db.commit()

    async def remove_member(self, group_id: UUID, employee_id: UUID) -> None:
        await self.db.execute(
            delete(employee_group_members).where(
                employee_group_members.c.group_id == group_id,
                employee_group_members.c.employee_id == employee_id,
            )
        )
        await self.db.commit()
