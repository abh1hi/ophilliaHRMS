from typing import Any
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import require_roles
from app.schemas.class_ import ClassCreate, ClassUpdate, ClassResponse, ClassListResponse
from app.services.class_service import ClassService

router = APIRouter()


@router.post(
    "/",
    response_model=ClassResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(["Admin"]))],
)
async def create_class(
    class_in: ClassCreate, db: AsyncSession = Depends(get_db)
) -> Any:
    """Create new class/grade. Allowed: Admin."""
    service = ClassService(db)
    return await service.create_class(class_in)


@router.get("/", response_model=ClassListResponse)
async def list_classes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    academic_year: str | None = Query(None),
    grade_level: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    # Ensure user is logged in (token valid)
    _user=Depends(require_roles(["Admin", "HR", "Teacher"])),
) -> Any:
    """List classes. Allowed: Admin, HR, Teacher."""
    service = ClassService(db)
    items, total = await service.list_classes(
        page, page_size, academic_year, grade_level
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


@router.get("/{class_id}", response_model=ClassResponse)
async def get_class(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_roles(["Admin", "HR", "Teacher"])),
) -> Any:
    """Get class details. Allowed: Admin, HR, Teacher."""
    service = ClassService(db)
    return await service.get_class(class_id)


@router.put(
    "/{class_id}",
    response_model=ClassResponse,
    dependencies=[Depends(require_roles(["Admin"]))],
)
async def update_class(
    class_id: uuid.UUID, class_in: ClassUpdate, db: AsyncSession = Depends(get_db)
) -> Any:
    """Update class info. Allowed: Admin."""
    service = ClassService(db)
    return await service.update_class(class_id, class_in)


@router.delete(
    "/{class_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(["Admin"]))],
)
async def delete_class(
    class_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> None:
    """Delete class completely. Allowed: Admin."""
    service = ClassService(db)
    await service.delete_class(class_id)
