from __future__ import annotations
import uuid
from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_ import Class


class ClassRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    @property
    def db(self) -> AsyncSession:
        return self._db

    def _get_company_id(self) -> uuid.UUID:
        raw = self._db.info.get("company_id")
        return uuid.UUID(raw) if isinstance(raw, str) else raw

    async def create(self, class_: Class) -> Class:
        class_.company_id = self._get_company_id()
        self._db.add(class_)
        await self._db.flush()
        await self._db.refresh(class_)
        return class_

    async def get_by_id(self, class_id: uuid.UUID) -> Optional[Class]:
        company_id = self._get_company_id()
        result = await self._db.execute(
            select(Class).where(
                Class.id == class_id,
                Class.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        academic_year: Optional[str] = None,
        grade_level: Optional[int] = None,
    ) -> tuple[Sequence[Class], int]:
        company_id = self._get_company_id()
        query = select(Class).where(Class.company_id == company_id)
        if academic_year:
            query = query.where(Class.academic_year == academic_year)
        if grade_level:
            query = query.where(Class.grade_level == grade_level)

        total_result = await self._db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = total_result.scalar_one()

        result = await self._db.execute(
            query.offset((page - 1) * page_size).limit(page_size)
        )
        return result.scalars().all(), total

    async def update(self, class_: Class) -> Class:
        await self._db.flush()
        await self._db.refresh(class_)
        return class_

    async def delete(self, class_: Class) -> None:
        await self._db.delete(class_)
        await self._db.flush()
