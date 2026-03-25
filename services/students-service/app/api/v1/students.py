from typing import Any
import uuid

from fastapi import APIRouter, Depends, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.dependencies import get_current_user, get_db_with_tenant
from app.core.security import require_roles
from app.events.publisher import EventPublisher
from app.models.student import StudentStatusEnum
from app.schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentStatusUpdate,
    StudentResponse,
    StudentListResponse,
)
from app.services.student_service import StudentService

router = APIRouter()

def get_event_publisher(request: Request) -> EventPublisher:
    """Dependency to retrieve the global event publisher from app lifespan."""
    import main # Avoid circular import by accessing global late
    return main.event_publisher

@router.post(
    "/",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(["super_admin", "admin", "hr"]))],
)
async def create_student(
    student_in: StudentCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    publisher: EventPublisher = Depends(get_event_publisher),
) -> Any:
    """Enroll new student. Allowed: Admin, HR."""
    service = StudentService(db, publisher)
    return await service.create_student(student_in)


@router.get("/", response_model=StudentListResponse)
async def list_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: StudentStatusEnum | None = Query(None, alias="status"),
    class_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db_with_tenant),
    _user=Depends(require_roles(["super_admin", "admin", "hr", "manager"])),
) -> Any:
    """List students. Allowed: Admin, HR, Teacher."""
    # Note: publisher not needed for read
    service = StudentService(db, None)  # type: ignore
    items, total = await service.list_students(page, page_size, status_filter, class_id)
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    _user=Depends(require_roles(["super_admin", "admin", "hr", "manager"])),
) -> Any:
    """Get student profile. Allowed: Admin, HR, Teacher."""
    service = StudentService(db, None)  # type: ignore
    return await service.get_student(student_id)


@router.put(
    "/{student_id}",
    response_model=StudentResponse,
    dependencies=[Depends(require_roles(["super_admin", "admin", "hr"]))],
)
async def update_student(
    student_id: uuid.UUID,
    student_in: StudentUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    publisher: EventPublisher = Depends(get_event_publisher),
) -> Any:
    """Update general student info. Allowed: Admin, HR."""
    service = StudentService(db, publisher)
    return await service.update_student(student_id, student_in)


@router.patch(
    "/{student_id}/status",
    response_model=StudentResponse,
    dependencies=[Depends(require_roles(["super_admin", "admin"]))],
)
async def change_student_status(
    student_id: uuid.UUID,
    status_in: StudentStatusUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    publisher: EventPublisher = Depends(get_event_publisher),
) -> Any:
    """Change student enrollment status (emits event). Allowed: Admin."""
    service = StudentService(db, publisher)
    return await service.change_status(student_id, status_in.status)


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(["super_admin", "admin"]))],
)
async def delete_student(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    publisher: EventPublisher = Depends(get_event_publisher),
) -> None:
    """Hard delete student from DB. Allowed: Admin."""
    service = StudentService(db, publisher)
    await service.delete_student(student_id)
