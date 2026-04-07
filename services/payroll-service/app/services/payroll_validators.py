"""Payroll validation and exception reporting.

Used during payroll run COMPUTE phase to surface issues before approval.
Validation results are stored in payroll_run.exception_report (JSONB).
"""
from decimal import Decimal
from datetime import date
from typing import Dict, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.payroll_repository import PayrollRepository


class ValidationResult:
    """Structured validation report with errors and warnings."""

    def __init__(self):
        self.errors: List[str] = []  # Block REVIEW transition
        self.warnings: List[str] = []  # Allow REVIEW, show in preview

    def add_error(self, msg: str):
        """Add blocking validation error."""
        self.errors.append(msg)

    def add_warning(self, msg: str):
        """Add non-blocking warning."""
        self.warnings.append(msg)

    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0

    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "is_valid": self.is_valid(),
        }


async def validate_payroll_period(
    db: AsyncSession,
    period_start: date,
    period_end: date,
    company_id: UUID,
) -> ValidationResult:
    """Validate payroll period before processing.

    Checks:
    - Period dates are valid (start < end)
    - No existing completed run for this period
    """
    result = ValidationResult()

    if period_start >= period_end:
        result.add_error(f"Invalid period: {period_start} >= {period_end}")

    repo = PayrollRepository(db)
    # TODO: Check for existing runs in this period
    # existing = await repo.get_payroll_run_by_period(period_start, period_end, company_id)

    return result


async def validate_employee_salary_data(
    db: AsyncSession,
    employee_id: UUID,
    company_id: UUID,
) -> ValidationResult:
    """Validate employee salary assignment.

    Checks:
    - Employee has active salary structure assigned
    - CTC is positive
    - Structure exists and is active
    """
    result = ValidationResult()
    repo = PayrollRepository(db)

    salary = await repo.get_active_salary(employee_id)
    if not salary:
        result.add_error(f"Employee {employee_id} has no active salary structure")
        return result

    if salary.ctc <= Decimal("0"):
        result.add_error(f"Employee {employee_id} has invalid CTC: {salary.ctc}")

    structure = await repo.get_salary_structure(salary.salary_structure_id)
    if not structure:
        result.add_error(f"Salary structure {salary.salary_structure_id} not found")
    elif structure.is_active == 0:
        result.add_warning(f"Salary structure {structure.name} is inactive")

    return result


def validate_payroll_calculations(
    gross: Decimal,
    net: Decimal,
    total_deductions: Decimal,
    lop_fetch_status: str,
) -> ValidationResult:
    """Validate computed salary components.

    Checks:
    - Gross >= 0
    - Deductions <= Gross
    - Net >= 0 (warn if negative)
    - LOP fetch status is valid
    """
    result = ValidationResult()

    if gross < Decimal("0"):
        result.add_error(f"Gross cannot be negative: {gross}")

    if total_deductions > gross:
        result.add_error(f"Total deductions ({total_deductions}) exceed gross ({gross})")

    if net < Decimal("0"):
        result.add_warning(
            f"Net pay is negative: {net} (deductions > gross; may need manual review)"
        )

    valid_statuses = {"OK", "UNAVAILABLE", "SKIPPED"}
    if lop_fetch_status not in valid_statuses:
        result.add_error(f"Invalid LOP fetch status: {lop_fetch_status}")

    return result


def validate_pro_rata(
    pro_rata_factor: Decimal,
) -> ValidationResult:
    """Validate pro-rata factor.

    Checks:
    - Factor is between 0 and 1
    """
    result = ValidationResult()

    if pro_rata_factor < Decimal("0") or pro_rata_factor > Decimal("1"):
        result.add_error(f"Pro-rata factor out of range: {pro_rata_factor}")

    return result
