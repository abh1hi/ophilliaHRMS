import logging
from typing import Optional, List
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.repositories.employee_repository import EmployeeRepository
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.events.publisher import EventPublisher

logger = logging.getLogger(__name__)


class EmployeeService:
    """Business logic layer for employee operations."""

    def __init__(self, db: AsyncSession, event_publisher: Optional[EventPublisher] = None):
        self.repo = EmployeeRepository(db)
        self.event_publisher = event_publisher

    async def create_employee(self, data: EmployeeCreate) -> Employee:
        """Create a new employee profile."""
        # Auto-generate user_id if not provided
        user_id = data.user_id or uuid4()

        # Check for duplicate email
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Employee with email {data.email} already exists",
            )

        # Check for duplicate user_id only if one was explicitly provided
        if data.user_id:
            existing_user = await self.repo.get_by_user_id(data.user_id)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Employee profile already exists for this user",
                )

        employee = Employee(
            user_id=user_id,
            # Personal
            first_name=data.first_name,
            last_name=data.last_name,
            gender=data.gender.value if data.gender else None,
            date_of_birth=data.date_of_birth,
            # Address
            door_no=data.door_no,
            street=data.street,
            village_town=data.village_town,
            pin_code=data.pin_code,
            # Contact
            phone=data.phone,
            phone_2=data.phone_2,
            personal_email=data.personal_email,
            email=data.email,
            # Government IDs
            driving_license_number=data.driving_license_number,
            aadhaar_number=data.aadhaar_number,
            uan_number=data.uan_number,
            esi_number=data.esi_number,
            pan_number=data.pan_number,
            # Banking
            bank_account_number=data.bank_account_number,
            bank_name=data.bank_name,
            bank_branch=data.bank_branch,
            ifsc_code=data.ifsc_code,
            # Emergency contact
            emergency_contact_name=data.emergency_contact_name,
            emergency_contact_number=data.emergency_contact_number,
            emergency_contact_relation=data.emergency_contact_relation,
            # Education
            highest_qualification=data.highest_qualification,
            year_of_passing=data.year_of_passing,
            percentage=data.percentage,
            institute_name=data.institute_name,
            # Work history
            last_firm_name=data.last_firm_name,
            years_of_experience=data.years_of_experience,
            last_designation=data.last_designation,
            last_drawn_salary=data.last_drawn_salary,
            reason_to_quit=data.reason_to_quit,
            referred_by=data.referred_by,
            # Health
            health_issues=data.health_issues,
            allergies=data.allergies,
            # Employee code
            employee_code=data.employee_code,
            # Job info
            date_joined=data.date_joined,
            department_id=data.department_id,
            designation=data.designation,
            project=data.project,
            joining_salary=data.joining_salary,
            role=data.role,
            # Files
            staff_photo_url=data.staff_photo_url,
            staff_documents_urls=data.staff_documents_urls,
        )
        employee = await self.repo.create(employee)

        # Publish event (non-blocking, graceful failure)
        if self.event_publisher:
            await self.event_publisher.publish(
                "employee.created",
                {
                    "employee_id": str(employee.id),
                    "company_id": str(employee.company_id),
                    "user_id": str(employee.user_id),
                    "email": employee.email,
                    "first_name": employee.first_name,
                    "last_name": employee.last_name,
                },
            )

        logger.info(
            f"Employee created: {employee.id}",
            extra={"user_id": str(employee.user_id), "service_task": "employee_create"},
        )
        return employee

    async def get_employee(self, employee_id: UUID) -> Employee:
        """Get an employee by ID. Raises 404 if not found."""
        employee = await self.repo.get_by_id(employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee {employee_id} not found",
            )
        return employee

    async def get_employee_by_user_id(self, user_id: UUID) -> Employee:
        """Get employee profile by auth-service user_id."""
        employee = await self.repo.get_by_user_id(user_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee profile not found for this user",
            )
        return employee

    async def list_employees(
        self,
        skip: int = 0,
        limit: int = 20,
        department_id: Optional[UUID] = None,
        employment_status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[list[Employee], int]:
        """List employees with pagination and filters."""
        return await self.repo.get_all(
            skip=skip,
            limit=limit,
            department_id=department_id,
            employment_status=employment_status,
            search=search,
        )

    async def update_employee(self, employee_id: UUID, data: EmployeeUpdate) -> Employee:
        """Update an employee's profile."""
        employee = await self.get_employee(employee_id)
        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No fields to update",
            )

        # Convert enum values to strings for DB storage
        if "gender" in update_data and update_data["gender"] is not None:
            update_data["gender"] = update_data["gender"].value
        if "employment_status" in update_data and update_data["employment_status"] is not None:
            update_data["employment_status"] = update_data["employment_status"].value

        employee = await self.repo.update(employee, update_data)

        # Publish event
        if self.event_publisher:
            await self.event_publisher.publish(
                "employee.updated",
                {
                    "employee_id": str(employee.id),
                    "user_id": str(employee.user_id),
                    "updated_fields": list(update_data.keys()),
                },
            )

        logger.info(
            f"Employee updated: {employee.id}",
            extra={"user_id": str(employee.user_id), "service_task": "employee_update"},
        )
        return employee

    async def deactivate_employee(self, employee_id: UUID) -> Employee:
        """Soft-deactivate (terminate) an employee."""
        employee = await self.get_employee(employee_id)
        employee = await self.repo.deactivate(employee)

        # Publish event
        if self.event_publisher:
            await self.event_publisher.publish(
                "employee.deactivated",
                {
                    "employee_id": str(employee.id),
                    "user_id": str(employee.user_id),
                    "email": employee.email,
                },
            )

        logger.info(
            f"Employee deactivated: {employee.id}",
            extra={"user_id": str(employee.user_id), "service_task": "employee_deactivate"},
        )
        return employee

    async def bulk_create_employees(self, employees_data: List[EmployeeCreate]) -> list[dict]:
        """Create multiple employees. Returns per-row result with success/error."""
        results = []
        for idx, data in enumerate(employees_data):
            try:
                employee = await self.create_employee(data)
                results.append({"index": idx, "success": True, "employee": employee, "error": None})
            except HTTPException as e:
                results.append({"index": idx, "success": False, "employee": None, "error": e.detail})
            except Exception as e:
                results.append({"index": idx, "success": False, "employee": None, "error": str(e)})
        return results
