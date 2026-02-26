from typing import Any
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import require_roles
from app.schemas.guardian import GuardianCreate, GuardianUpdate, GuardianResponse
from app.services.guardian_service import GuardianService

router = APIRouter()


@router.post(
    "/",
    response_model=GuardianResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(["Admin", "HR"]))],
)
async def create_guardian(
    guardian_in: GuardianCreate, db: AsyncSession = Depends(get_db)
) -> Any:
    """Add guardian. Allowed: Admin, HR."""
    service = GuardianService(db)
    return await service.create_guardian(guardian_in)


@router.get(
    "/{guardian_id}",
    response_model=GuardianResponse,
    dependencies=[Depends(require_roles(["Admin", "HR"]))],
)
async def get_guardian(
    guardian_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> Any:
    """Get guardian. Allowed: Admin, HR."""
    service = GuardianService(db)
    return await service.get_guardian(guardian_id)


@router.get(
    "/student/{student_id}",
    response_model=list[GuardianResponse],
    dependencies=[Depends(require_roles(["Admin", "HR"]))],
)
async def list_guardians_for_student(
    student_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> Any:
    """Get all guardians for a specific student. Allowed: Admin, HR."""
    service = GuardianService(db)
    return await service.list_student_guardians(student_id)


@router.put(
    "/{guardian_id}",
    response_model=GuardianResponse,
    dependencies=[Depends(require_roles(["Admin", "HR"]))],
)
async def update_guardian(
    guardian_id: uuid.UUID,
    guardian_in: GuardianUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update guardian info. Allowed: Admin, HR."""
    service = GuardianService(db)
    return await service.update_guardian(guardian_id, guardian_in)


@router.delete(
    "/{guardian_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(["Admin"]))],
)
async def delete_guardian(
    guardian_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> None:
    """Remove guardian. Allowed: Admin."""
    service = GuardianService(db)
    await service.delete_guardian(guardian_id)
