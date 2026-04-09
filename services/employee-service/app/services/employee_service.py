import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import AccountStatus
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
            user_id=data.user_id,  # None when creating without an auth account
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
                    "user_id": str(employee.user_id) if employee.user_id else None,
                    "email": employee.email,
                    "first_name": employee.first_name,
                    "last_name": employee.last_name,
                },
            )

        logger.info(
            f"Employee created: {employee.id}",
            extra={"user_id": str(employee.user_id) if employee.user_id else None, "service_task": "employee_create"},
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
        account_status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[list[Employee], int]:
        """List employees with pagination and filters."""
        return await self.repo.get_all(
            skip=skip,
            limit=limit,
            department_id=department_id,
            employment_status=employment_status,
            account_status=account_status,
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
                    "user_id": str(employee.user_id) if employee.user_id else None,
                    "updated_fields": list(update_data.keys()),
                },
            )

        logger.info(
            f"Employee updated: {employee.id}",
            extra={"user_id": str(employee.user_id) if employee.user_id else None, "service_task": "employee_update"},
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
                    "user_id": str(employee.user_id) if employee.user_id else None,
                    "email": employee.email,
                },
            )

        logger.info(
            f"Employee deactivated: {employee.id}",
            extra={"user_id": str(employee.user_id) if employee.user_id else None, "service_task": "employee_deactivate"},
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

    # ──────────── INVITE FLOW ────────────

    async def send_invite(self, employee_id: UUID, inviter_jwt: str) -> dict:
        """Send (or resend) a portal invite for the given employee.

        Allowed states: not_registered, invited.
        Returns invite_url (full URL) — raw token is never exposed.
        """
        import httpx

        employee = await self.get_employee(employee_id)

        if employee.account_status == AccountStatus.ACTIVE.value:
            raise HTTPException(status.HTTP_409_CONFLICT, "Employee already has an active account")
        if employee.account_status == AccountStatus.SUSPENDED.value:
            raise HTTPException(status.HTTP_409_CONFLICT, "Account is suspended; enable it before sending an invite")

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{settings.AUTH_SERVICE_URL}/api/v1/auth/invite",
                json={"email": employee.email, "role": employee.role or "employee"},
                headers={"Authorization": f"Bearer {inviter_jwt}"},
            )

        if resp.status_code == status.HTTP_409_CONFLICT:
            raise HTTPException(status.HTTP_409_CONFLICT, "A user account already exists for this email")
        if not resp.is_success:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Auth service error: {resp.status_code}")

        invite = resp.json()
        token = invite.get("token", "")
        expires_at_str = str(invite.get("expires_at", ""))
        invite_url = f"{settings.EMPLOYEE_APP_URL}/?token={token}"

        try:
            expires_dt = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        except Exception:
            expires_dt = None

        await self.repo.update(employee, {
            "account_status": AccountStatus.INVITED.value,
            "invite_expires_at": expires_dt,
        })

        logger.info(f"AUDIT invite_sent employee_id={employee_id} email={employee.email}")
        return {
            "employee_id": str(employee.id),
            "email": employee.email,
            "invite_url": invite_url,
            "expires_at": expires_at_str,
            "account_status": AccountStatus.INVITED.value,
        }

    async def revoke_invite(self, employee_id: UUID) -> dict:
        """Clear invite state — employee returns to not_registered."""
        employee = await self.get_employee(employee_id)
        if employee.account_status not in (AccountStatus.INVITED.value, AccountStatus.NOT_REGISTERED.value):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "No pending invite to revoke")
        await self.repo.update(employee, {
            "account_status": AccountStatus.NOT_REGISTERED.value,
            "invite_expires_at": None,
        })
        logger.info(f"AUDIT invite_revoked employee_id={employee_id}")
        return {"employee_id": str(employee.id), "account_status": AccountStatus.NOT_REGISTERED.value}

    async def link_account(self, user_id: UUID, email: str, company_id: str) -> Employee:
        """Link an auth-service user account to an employee record after invite acceptance.

        Idempotent: same user calling again returns current state without error.
        """
        employee = await self.repo.get_by_email(email)
        if not employee:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No employee record found for this email")
        if str(employee.company_id) != company_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Tenant mismatch")
        if employee.email.lower() != email.lower():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email mismatch between token and employee record")
        if employee.account_status == AccountStatus.SUSPENDED.value:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is suspended")

        if employee.user_id:
            if str(employee.user_id) == str(user_id):
                # Idempotent retry (e.g. network failure on first attempt)
                return await self.repo.get_by_id(employee.id)
            raise HTTPException(status.HTTP_409_CONFLICT, "Account already linked to a different user")

        await self.repo.update(employee, {
            "user_id": user_id,
            "account_status": AccountStatus.ACTIVE.value,
            "invite_expires_at": None,
        })
        logger.info(f"AUDIT account_linked employee_id={employee.id} user_id={user_id}")
        return await self.repo.get_by_id(employee.id)

    async def disable_account(self, employee_id: UUID) -> Employee:
        """Disable an employee's auth account and set account_status to suspended."""
        import httpx

        employee = await self.get_employee(employee_id)
        if not employee.user_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Employee has no linked auth account")

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.patch(
                f"{settings.AUTH_SERVICE_URL}/api/v1/auth/users/{employee.user_id}/status",
                json={"is_active": False},
                headers={"X-Service-Token": settings.INTERNAL_SERVICE_TOKEN},
            )
        if not resp.is_success:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Auth service failed to disable account")

        await self.repo.update(employee, {"account_status": AccountStatus.SUSPENDED.value})
        logger.info(f"AUDIT account_disabled employee_id={employee_id} user_id={employee.user_id}")
        return await self.repo.get_by_id(employee_id)
