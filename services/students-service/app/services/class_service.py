from __future__ import annotations
import uuid
import logging
from typing import Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_ import Class
from app.schemas.class_ import ClassCreate, ClassUpdate
from app.repositories.class_repo import ClassRepository

logger = logging.getLogger(__name__)


class ClassService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = ClassRepository(db)

    async def create_class(self, class_in: ClassCreate) -> Class:
        new_class = Class(**class_in.model_dump())
        created = await self.repo.create(new_class)
        logger.info("Class created definition", extra={"class_id": str(created.id)})
        return created

    async def get_class(self, class_id: uuid.UUID) -> Class:
        class_obj = await self.repo.get_by_id(class_id)
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found."
            )
        return class_obj

    async def list_classes(
        self,
        page: int = 1,
        page_size: int = 20,
        academic_year: Optional[str] = None,
        grade_level: Optional[int] = None,
    ) -> tuple[Sequence[Class], int]:
        return await self.repo.list_all(
            page=page,
            page_size=page_size,
            academic_year=academic_year,
            grade_level=grade_level
        )

    async def update_class(
        self, class_id: uuid.UUID, class_in: ClassUpdate
    ) -> Class:
        class_obj = await self.get_class(class_id)
        update_data = class_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(class_obj, field, value)
        
        updated = await self.repo.update(class_obj)
        logger.info("Class updated", extra={"class_id": str(updated.id)})
        return updated

    async def delete_class(self, class_id: uuid.UUID) -> None:
        class_obj = await self.get_class(class_id)
        await self.repo.delete(class_obj)
        logger.info("Class deleted", extra={"class_id": str(class_id)})
