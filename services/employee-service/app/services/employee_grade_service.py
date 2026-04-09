import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee_grade import EmployeeGrade
from app.repositories.employee_grade_repository import EmployeeGradeRepository
from app.schemas.employee_grade import EmployeeGradeCreate, EmployeeGradeUpdate

logger = logging.getLogger(__name__)


class EmployeeGradeService:
    def __init__(self, db: AsyncSession):
        self.repo = EmployeeGradeRepository(db)

    async def create(self, data: EmployeeGradeCreate) -> EmployeeGrade:
        if await self.repo.get_by_name(data.name):
            raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Employee grade '{data.name}' already exists")
        grade = await self.repo.create(EmployeeGrade(name=data.name))
        logger.info("EmployeeGrade created: %s", grade.id, extra={"service_task": "employee_grade_create"})
        return grade

    async def get(self, grade_id: UUID) -> EmployeeGrade:
        grade = await self.repo.get_by_id(grade_id)
        if not grade:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Employee grade {grade_id} not found")
        return grade

    async def list_all(self, include_inactive: bool = False):
        return await self.repo.get_all(include_inactive=include_inactive)

    async def update(self, grade_id: UUID, data: EmployeeGradeUpdate) -> EmployeeGrade:
        grade = await self.get(grade_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields to update")
        if "name" in update_data:
            existing = await self.repo.get_by_name(update_data["name"])
            if existing and existing.id != grade_id:
                raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Employee grade '{update_data['name']}' already exists")
        return await self.repo.update(grade, update_data)

    async def soft_delete(self, grade_id: UUID) -> EmployeeGrade:
        grade = await self.get(grade_id)
        return await self.repo.update(grade, {"is_active": 0})
