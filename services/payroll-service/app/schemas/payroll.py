from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal

from app.core.constants import PayrollStatus


# ── Salary Structure Schemas ─────────────────────────────────────────────────
class SalaryStructureCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    basic_pct: Decimal = Field(50.0, ge=0, le=100)
    hra_pct: Decimal = Field(20.0, ge=0, le=100)
    allowances_pct: Decimal = Field(15.0, ge=0, le=100)
    pf_pct: Decimal = Field(12.0, ge=0, le=100)
    esi_pct: Decimal = Field(1.75, ge=0, le=100)
    professional_tax: Decimal = Field(200.0, ge=0)


class SalaryStructureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    company_id: UUID
    name: str
    description: Optional[str] = None
    basic_pct: Decimal
    hra_pct: Decimal
    allowances_pct: Decimal
    pf_pct: Decimal
    esi_pct: Decimal
    professional_tax: Decimal
    is_active: int
    created_at: datetime
    updated_at: datetime


# ── Employee Salary Schemas ──────────────────────────────────────────────────
class EmployeeSalaryCreate(BaseModel):
    employee_id: UUID
    salary_structure_id: UUID
    ctc: Decimal = Field(..., gt=0)
    effective_from: date


class EmployeeSalaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    company_id: UUID
    employee_id: UUID
    salary_structure_id: UUID
    ctc: Decimal
    effective_from: date
    effective_to: Optional[date] = None
    is_active: int
    created_at: datetime
    updated_at: datetime


# ── Payroll Run Schemas ──────────────────────────────────────────────────────
class PayrollRunCreate(BaseModel):
    period_start: date
    period_end: date


class PayrollRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    company_id: UUID
    period_start: date
    period_end: date
    status: PayrollStatus
    total_employees: int
    total_gross: Decimal
    total_net: Decimal
    total_deductions: Decimal
    processed_by: Optional[UUID] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ── Payslip Schemas ──────────────────────────────────────────────────────────
class PayslipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    company_id: UUID
    payroll_run_id: UUID
    employee_id: UUID
    ctc: Decimal
    basic: Decimal
    hra: Decimal
    allowances: Decimal
    pf_deduction: Decimal
    esi_deduction: Decimal
    professional_tax: Decimal
    other_deductions: Decimal
    gross: Decimal
    total_deductions: Decimal
    net: Decimal
    period_start: date
    period_end: date
    created_at: datetime
