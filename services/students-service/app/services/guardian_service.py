from __future__ import annotations
import uuid
import logging
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guardian import Guardian
from app.schemas.guardian import GuardianCreate, GuardianUpdate
from app.repositories.guardian_repo import GuardianRepository
from app.repositories.student_repo import StudentRepository

logger = logging.getLogger(__name__)


class GuardianService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = GuardianRepository(db)
        self.student_repo = StudentRepository(db)

    async def create_guardian(self, guardian_in: GuardianCreate) -> Guardian:
        student = await self.student_repo.get_by_id(guardian_in.student_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {guardian_in.student_id} not found."
            )

        new_guardian = Guardian(**guardian_in.model_dump())
        created = await self.repo.create(new_guardian)
        logger.info(
            "Guardian created", 
            extra={"guardian_id": str(created.id), "student_id": str(created.student_id)}
        )
        return created

    async def get_guardian(self, guardian_id: uuid.UUID) -> Guardian:
        guardian = await self.repo.get_by_id(guardian_id)
        if not guardian:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guardian not found."
            )
        return guardian

    async def list_student_guardians(self, student_id: uuid.UUID) -> Sequence[Guardian]:
        student = await self.student_repo.get_by_id(student_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found."
            )
        return await self.repo.list_by_student(student_id)

    async def update_guardian(self, guardian_id: uuid.UUID, guardian_in: GuardianUpdate) -> Guardian:
        guardian = await self.get_guardian(guardian_id)
        update_data = guardian_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(guardian, field, value)

        updated = await self.repo.update(guardian)
        logger.info("Guardian updated", extra={"guardian_id": str(updated.id)})
        return updated

    async def delete_guardian(self, guardian_id: uuid.UUID) -> None:
        guardian = await self.get_guardian(guardian_id)
        await self.repo.delete(guardian)
        logger.info("Guardian deleted", extra={"guardian_id": str(guardian_id)})
