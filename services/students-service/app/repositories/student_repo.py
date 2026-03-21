from __future__ import annotations
import uuid
from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student, StudentStatusEnum


class StudentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    @property
    def db(self) -> AsyncSession:
        return self._db

    def _get_company_id(self) -> uuid.UUID:
        raw = self._db.info.get("company_id")
        return uuid.UUID(raw) if isinstance(raw, str) else raw

    async def create(self, student: Student) -> Student:
        student.company_id = self._get_company_id()
        self._db.add(student)
        await self._db.flush()
        await self._db.refresh(student)
        return student

    async def get_by_id(self, student_id: uuid.UUID) -> Optional[Student]:
        company_id = self._get_company_id()
        result = await self._db.execute(
            select(Student).where(
                Student.id == student_id,
                Student.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_student_number(self, student_number: str) -> Optional[Student]:
        company_id = self._get_company_id()
        result = await self._db.execute(
            select(Student).where(
                Student.student_number == student_number,
                Student.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[StudentStatusEnum] = None,
        class_id: Optional[uuid.UUID] = None,
    ) -> tuple[Sequence[Student], int]:
        company_id = self._get_company_id()
        query = select(Student).where(Student.company_id == company_id)
        if status:
            query = query.where(Student.status == status)
        if class_id:
            query = query.where(Student.class_id == class_id)

        total_result = await self._db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = total_result.scalar_one()

        result = await self._db.execute(
            query.offset((page - 1) * page_size).limit(page_size)
        )
        return result.scalars().all(), total

    async def update(self, student: Student) -> Student:
        await self._db.flush()
        await self._db.refresh(student)
        return student

    async def delete(self, student: Student) -> None:
        await self._db.delete(student)
        await self._db.flush()
