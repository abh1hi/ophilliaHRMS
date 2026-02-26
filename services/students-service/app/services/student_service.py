from __future__ import annotations
import uuid
import logging
from typing import Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student, StudentStatusEnum
from app.schemas.student import StudentCreate, StudentUpdate
from app.repositories.student_repo import StudentRepository
from app.services.class_service import ClassService
from app.events.publisher import EventPublisher

logger = logging.getLogger(__name__)


class StudentService:
    def __init__(self, db: AsyncSession, event_publisher: EventPublisher) -> None:
        self.repo = StudentRepository(db)
        self.class_service = ClassService(db)
        self.event_publisher = event_publisher

    async def create_student(self, student_in: StudentCreate) -> Student:
        # Check student_number uniqueness
        existing = await self.repo.get_by_student_number(student_in.student_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Student number '{student_in.student_number}' already exists."
            )

        # Validate class_id if provided
        if student_in.class_id:
            await self.class_service.get_class(student_in.class_id)

        new_student = Student(**student_in.model_dump())
        created = await self.repo.create(new_student)

        logger.info("Student enrolled", extra={"student_id": str(created.id)})
        
        # Publish event
        company_id = self.repo.db.info.get("company_id")
        await self.event_publisher.publish(
            "student.enrolled",
            payload={
                "company_id": str(company_id) if company_id else None,
                "user_id": str(created.id), # Map to user_id for notification service
                "student_number": created.student_number,
                "first_name": created.first_name,
                "last_name": created.last_name,
            }
        )

        return created

    async def get_student(self, student_id: uuid.UUID) -> Student:
        student = await self.repo.get_by_id(student_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found."
            )
        return student

    async def list_students(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[StudentStatusEnum] = None,
        class_id: Optional[uuid.UUID] = None,
    ) -> tuple[Sequence[Student], int]:
        return await self.repo.list_all(
            page=page,
            page_size=page_size,
            status=status_filter,
            class_id=class_id,
        )

    async def update_student(self, student_id: uuid.UUID, student_in: StudentUpdate) -> Student:
        student = await self.get_student(student_id)

        if student_in.class_id and student_in.class_id != student.class_id:
            await self.class_service.get_class(student_in.class_id)

        update_data = student_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(student, field, value)

        updated = await self.repo.update(student)
        logger.info("Student updated", extra={"student_id": str(updated.id)})
        return updated

    async def change_status(self, student_id: uuid.UUID, new_status: StudentStatusEnum) -> Student:
        student = await self.get_student(student_id)
        old_status = student.status

        if old_status == new_status:
            return student

        student.status = new_status
        updated = await self.repo.update(student)

        logger.info(
            "Student status changed", 
            extra={
                "student_id": str(updated.id),
                "old_status": old_status.value,
                "new_status": new_status.value
            }
        )

        company_id = self.repo.db.info.get("company_id")
        
        await self.event_publisher.publish(
            "student.status_changed",
            payload={
                "company_id": str(company_id) if company_id else None,
                "student_id": str(updated.id),
                "student_number": updated.student_number,
                "old_status": old_status.value,
                "new_status": new_status.value,
            }
        )

        if new_status == StudentStatusEnum.graduated:
            await self.event_publisher.publish(
                "student.graduated",
                payload={"company_id": str(company_id) if company_id else None, "student_id": str(updated.id), "student_number": updated.student_number}
            )

        return updated

    async def delete_student(self, student_id: uuid.UUID) -> None:
        student = await self.get_student(student_id)
        await self.repo.delete(student)
        logger.info("Student deleted", extra={"student_id": str(student_id)})
