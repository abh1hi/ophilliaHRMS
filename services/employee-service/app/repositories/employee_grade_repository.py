from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee_grade import EmployeeGrade


class EmployeeGradeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _company_id(self) -> UUID:
        cid = self.db.info.get("company_id")
        if not cid:
            raise RuntimeError("company_id not set on session — use get_db_with_tenant")
        return UUID(cid) if isinstance(cid, str) else cid

    def _scoped(self, stmt):
        return stmt.where(EmployeeGrade.company_id == self._company_id)

    async def create(self, grade: EmployeeGrade) -> EmployeeGrade:
        grade.company_id = self._company_id
        self.db.add(grade)
        await self.db.commit()
        await self.db.refresh(grade)
        return grade

    async def get_by_id(self, grade_id: UUID) -> Optional[EmployeeGrade]:
        result = await self.db.execute(self._scoped(select(EmployeeGrade).where(EmployeeGrade.id == grade_id)))
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[EmployeeGrade]:
        result = await self.db.execute(self._scoped(select(EmployeeGrade).where(EmployeeGrade.name == name)))
        return result.scalars().first()

    async def get_all(self, include_inactive: bool = False) -> tuple[List[EmployeeGrade], int]:
        base = self._scoped(select(func.count(EmployeeGrade.id)))
        query = self._scoped(select(EmployeeGrade).order_by(EmployeeGrade.name.asc()))
        if not include_inactive:
            base = base.where(EmployeeGrade.is_active == 1)
            query = query.where(EmployeeGrade.is_active == 1)
        total = (await self.db.execute(base)).scalar() or 0
        items = (await self.db.execute(query)).scalars().all()
        return list(items), total

    async def update(self, grade: EmployeeGrade, data: dict) -> EmployeeGrade:
        for k, v in data.items():
            if v is not None:
                setattr(grade, k, v)
        await self.db.commit()
        await self.db.refresh(grade)
        return grade
