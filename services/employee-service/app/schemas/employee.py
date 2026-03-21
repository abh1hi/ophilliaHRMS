from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal

from app.core.constants import EmploymentStatus, Gender


# ──────────── CREATE ────────────
class EmployeeCreate(BaseModel):
    user_id: UUID
    # Personal
    first_name: str
    last_name: str
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None

    # Address
    door_no: Optional[str] = None
    street: Optional[str] = None
    village_town: Optional[str] = None
    pin_code: Optional[str] = None

    # Contact
    phone: Optional[str] = None
    phone_2: Optional[str] = None
    personal_email: Optional[EmailStr] = None
    email: EmailStr                         # work / login email (required & unique)

    # Government IDs
    driving_license_number: Optional[str] = None
    aadhaar_number: Optional[str] = None
    uan_number: Optional[str] = None
    esi_number: Optional[str] = None
    pan_number: Optional[str] = None

    # Banking
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_branch: Optional[str] = None
    ifsc_code: Optional[str] = None

    # Emergency contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_number: Optional[str] = None
    emergency_contact_relation: Optional[str] = None

    # Education
    highest_qualification: Optional[str] = None
    year_of_passing: Optional[str] = None
    percentage: Optional[str] = None
    institute_name: Optional[str] = None

    # Work history
    last_firm_name: Optional[str] = None
    years_of_experience: Optional[str] = None
    last_designation: Optional[str] = None
    last_drawn_salary: Optional[Decimal] = None
    reason_to_quit: Optional[str] = None
    referred_by: Optional[str] = None

    # Health
    health_issues: Optional[str] = None
    allergies: Optional[str] = None

    # Job info
    date_joined: date
    department_id: Optional[UUID] = None
    designation: Optional[str] = None
    project: Optional[str] = None
    joining_salary: Optional[Decimal] = None
    role: Optional[str] = None

    # Files
    staff_photo_url: Optional[str] = None
    staff_documents_urls: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name must not be empty")
        return v.strip()

    @field_validator("aadhaar_number")
    @classmethod
    def aadhaar_must_be_12_digits(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v.isdigit() or len(v) != 12):
            raise ValueError("Aadhaar number must be exactly 12 digits")
        return v

    @field_validator("pan_number")
    @classmethod
    def pan_format(cls, v: Optional[str]) -> Optional[str]:
        import re
        if v is not None and not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", v.upper()):
            raise ValueError("PAN must follow the format: AAAAA9999A")
        return v.upper() if v else v


# ──────────── UPDATE ────────────
class EmployeeUpdate(BaseModel):
    # Personal
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None

    # Address
    door_no: Optional[str] = None
    street: Optional[str] = None
    village_town: Optional[str] = None
    pin_code: Optional[str] = None

    # Contact
    phone: Optional[str] = None
    phone_2: Optional[str] = None
    personal_email: Optional[EmailStr] = None

    # Government IDs
    driving_license_number: Optional[str] = None
    aadhaar_number: Optional[str] = None
    uan_number: Optional[str] = None
    esi_number: Optional[str] = None
    pan_number: Optional[str] = None

    # Banking
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_branch: Optional[str] = None
    ifsc_code: Optional[str] = None

    # Emergency contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_number: Optional[str] = None
    emergency_contact_relation: Optional[str] = None

    # Education
    highest_qualification: Optional[str] = None
    year_of_passing: Optional[str] = None
    percentage: Optional[str] = None
    institute_name: Optional[str] = None

    # Work history
    last_firm_name: Optional[str] = None
    years_of_experience: Optional[str] = None
    last_designation: Optional[str] = None
    last_drawn_salary: Optional[Decimal] = None
    reason_to_quit: Optional[str] = None
    referred_by: Optional[str] = None

    # Health
    health_issues: Optional[str] = None
    allergies: Optional[str] = None

    # Job info
    department_id: Optional[UUID] = None
    designation: Optional[str] = None
    employment_status: Optional[EmploymentStatus] = None
    project: Optional[str] = None
    joining_salary: Optional[Decimal] = None
    role: Optional[str] = None

    # Files
    staff_photo_url: Optional[str] = None
    staff_documents_urls: Optional[str] = None


# ──────────── RESPONSE ────────────
class EmployeeResponse(BaseModel):
    id: UUID
    company_id: UUID
    user_id: UUID

    # Personal
    first_name: str
    last_name: str
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None

    # Address
    door_no: Optional[str] = None
    street: Optional[str] = None
    village_town: Optional[str] = None
    pin_code: Optional[str] = None

    # Contact
    phone: Optional[str] = None
    phone_2: Optional[str] = None
    personal_email: Optional[str] = None
    email: str

    # Government IDs
    driving_license_number: Optional[str] = None
    aadhaar_number: Optional[str] = None
    uan_number: Optional[str] = None
    esi_number: Optional[str] = None
    pan_number: Optional[str] = None

    # Banking
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_branch: Optional[str] = None
    ifsc_code: Optional[str] = None

    # Emergency contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_number: Optional[str] = None
    emergency_contact_relation: Optional[str] = None

    # Education
    highest_qualification: Optional[str] = None
    year_of_passing: Optional[str] = None
    percentage: Optional[str] = None
    institute_name: Optional[str] = None

    # Work history
    last_firm_name: Optional[str] = None
    years_of_experience: Optional[str] = None
    last_designation: Optional[str] = None
    last_drawn_salary: Optional[Decimal] = None
    reason_to_quit: Optional[str] = None
    referred_by: Optional[str] = None

    # Health
    health_issues: Optional[str] = None
    allergies: Optional[str] = None

    # Job info
    date_joined: date
    department_id: Optional[UUID] = None
    designation: Optional[str] = None
    employment_status: str
    project: Optional[str] = None
    joining_salary: Optional[Decimal] = None
    role: Optional[str] = None

    # Files
    staff_photo_url: Optional[str] = None
    staff_documents_urls: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ──────────── PAGINATED LIST ────────────
class EmployeeListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    employees: List[EmployeeResponse]


# ──────────── BULK IMPORT ────────────
class BulkEmployeeResult(BaseModel):
    index: int
    success: bool
    employee: Optional[EmployeeResponse] = None
    error: Optional[str] = None


class BulkEmployeeResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: List[BulkEmployeeResult]
