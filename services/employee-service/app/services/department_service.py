import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.repositories.department_repository import DepartmentRepository
from app.schemas.department import DepartmentCreate, DepartmentUpdate

logger = logging.getLogger(__name__)


class DepartmentService:
    """Business logic layer for department operations."""

    def __init__(self, db: AsyncSession):
        self.repo = DepartmentRepository(db)

    async def create_department(self, data: DepartmentCreate) -> Department:
        """Create a new department."""
        existing = await self.repo.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Department '{data.name}' already exists",
            )

        department = Department(
            name=data.name,
            description=data.description,
            manager_id=data.manager_id,
        )
        department = await self.repo.create(department)

        logger.info(
            f"Department created: {department.id} ({department.name})",
            extra={"service_task": "department_create"},
        )
        return department

    async def get_department(self, department_id: UUID) -> Department:
        """Get a department by ID. Raises 404 if not found."""
        department = await self.repo.get_by_id(department_id)
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department {department_id} not found",
            )
        return department

    async def list_departments(self, include_inactive: bool = False) -> tuple[list[Department], int]:
        """List all departments. By default only active ones."""
        return await self.repo.get_all(include_inactive=include_inactive)

    async def soft_delete_department(self, department_id: UUID) -> Department:
        """Soft delete a department by setting is_active = 0."""
        department = await self.get_department(department_id)
        department = await self.repo.update(department, {"is_active": 0})
        logger.info(
            f"Department soft-deleted: {department.id} ({department.name})",
            extra={"service_task": "department_soft_delete"},
        )
        return department

    async def update_department(self, department_id: UUID, data: DepartmentUpdate) -> Department:
        """Update a department."""
        department = await self.get_department(department_id)
        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No fields to update",
            )

        # Check for duplicate name if changing
        if "name" in update_data:
            existing = await self.repo.get_by_name(update_data["name"])
            if existing and existing.id != department_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Department '{update_data['name']}' already exists",
                )

        department = await self.repo.update(department, update_data)

        logger.info(
            f"Department updated: {department.id} ({department.name})",
            extra={"service_task": "department_update"},
        )
        return department
