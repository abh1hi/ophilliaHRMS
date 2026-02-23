from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.employee import Employee


class EmployeeRepository:
    """Data access layer for employees — async CRUD."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, employee: Employee) -> Employee:
        self.db.add(employee)
        await self.db.commit()
        await self.db.refresh(employee)
        return employee

    async def get_by_id(self, employee_id: UUID) -> Optional[Employee]:
        result = await self.db.execute(
            select(Employee).where(Employee.id == employee_id)
        )
        return result.scalars().first()

    async def get_by_user_id(self, user_id: UUID) -> Optional[Employee]:
        result = await self.db.execute(
            select(Employee).where(Employee.user_id == user_id)
        )
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[Employee]:
        result = await self.db.execute(
            select(Employee).where(Employee.email == email)
        )
        return result.scalars().first()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        department_id: Optional[UUID] = None,
        employment_status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Employee], int]:
        """Return paginated employees with optional filters."""
        query = select(Employee)
        count_query = select(func.count(Employee.id))

        if department_id:
            query = query.where(Employee.department_id == department_id)
            count_query = count_query.where(Employee.department_id == department_id)

        if employment_status:
            query = query.where(Employee.employment_status == employment_status)
            count_query = count_query.where(Employee.employment_status == employment_status)

        if search:
            search_pattern = f"%{search}%"
            search_filter = (
                Employee.first_name.ilike(search_pattern)
                | Employee.last_name.ilike(search_pattern)
                | Employee.email.ilike(search_pattern)
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        # Total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginated results
        query = query.order_by(Employee.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        employees = result.scalars().all()

        return list(employees), total

    async def update(self, employee: Employee, update_data: dict) -> Employee:
        for field, value in update_data.items():
            if value is not None:
                setattr(employee, field, value)
        await self.db.commit()
        await self.db.refresh(employee)
        return employee

    async def deactivate(self, employee: Employee) -> Employee:
        employee.employment_status = "terminated"
        await self.db.commit()
        await self.db.refresh(employee)
        return employee
