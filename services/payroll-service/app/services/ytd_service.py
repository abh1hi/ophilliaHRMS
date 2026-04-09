"""Year-To-Date (YTD) accumulation and management service.

YTD records are updated ONLY when payroll transitions from APPROVED → COMPLETED.
They are used for:
1. TDS calculation (distributed across remaining months)
2. Form 16 generation
3. Year-end reports and compliance filings

Financial year in India: April 1 - March 31
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payroll import EmployeeYTD, Payslip
from app.repositories import payroll_repository as repo


async def get_or_create_ytd(
    db: AsyncSession,
    employee_id: UUID,
    company_id: UUID,
    financial_year: int,
) -> EmployeeYTD:
    """Get existing YTD record or create a new one for the financial year.

    Args:
        db: Database session
        employee_id: Employee UUID
        company_id: Company UUID
        financial_year: Financial year (e.g., 2026 = FY 2025-26)

    Returns:
        EmployeeYTD record (new or existing)
    """
    ytd = await repo.get_employee_ytd(db, employee_id, company_id, financial_year)

    if ytd:
        return ytd

    # Create new YTD for this employee + FY
    ytd = EmployeeYTD(
        employee_id=employee_id,
        company_id=company_id,
        financial_year=financial_year,
        ytd_gross=Decimal("0.00"),
        ytd_basic=Decimal("0.00"),
        ytd_hra=Decimal("0.00"),
        ytd_taxable_income=Decimal("0.00"),
        ytd_pf_employee=Decimal("0.00"),
        ytd_esi_employee=Decimal("0.00"),
        ytd_professional_tax=Decimal("0.00"),
        ytd_lwf_employee=Decimal("0.00"),
        ytd_tds=Decimal("0.00"),
        ytd_pf_employer=Decimal("0.00"),
        ytd_esi_employer=Decimal("0.00"),
        ytd_lop_days=0,
        ytd_bonus=Decimal("0.00"),
        ytd_arrears=Decimal("0.00"),
    )
    db.add(ytd)
    await db.flush()
    return ytd


async def accumulate_payslip(
    db: AsyncSession,
    payslip: Payslip,
    ytd: EmployeeYTD,
) -> EmployeeYTD:
    """Accumulate payslip amounts into YTD record.

    Called ONLY during payroll PROCESS phase (APPROVED → COMPLETED).

    Args:
        db: Database session
        payslip: Completed payslip record
        ytd: YTD record to update

    Returns:
        Updated YTD record
    """
    # Accumulate income
    ytd.ytd_gross += payslip.gross
    ytd.ytd_basic += payslip.basic
    ytd.ytd_hra += payslip.hra

    # Accumulate employee deductions
    ytd.ytd_pf_employee += payslip.pf_deduction
    ytd.ytd_esi_employee += payslip.esi_deduction
    ytd.ytd_professional_tax += payslip.professional_tax
    ytd.ytd_lwf_employee += payslip.lwf_employee
    ytd.ytd_tds += payslip.tds_deduction

    # Accumulate employer contributions
    ytd.ytd_pf_employer += payslip.employer_pf
    ytd.ytd_esi_employer += payslip.employer_esi

    # Accumulate other metrics
    ytd.ytd_lop_days += payslip.lop_days

    # Update timestamp
    ytd.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.flush()
    return ytd


async def reset_ytd(
    db: AsyncSession,
    employee_id: UUID,
    company_id: UUID,
    financial_year: int,
) -> EmployeeYTD:
    """Reset YTD to zero (for salary revision or correction).

    Use case: Salary revised mid-year → recompute all past payslips with new structure.

    Args:
        db: Database session
        employee_id: Employee UUID
        company_id: Company UUID
        financial_year: Financial year to reset

    Returns:
        Reset YTD record
    """
    ytd = await get_or_create_ytd(db, employee_id, company_id, financial_year)

    ytd.ytd_gross = Decimal("0.00")
    ytd.ytd_basic = Decimal("0.00")
    ytd.ytd_hra = Decimal("0.00")
    ytd.ytd_taxable_income = Decimal("0.00")
    ytd.ytd_pf_employee = Decimal("0.00")
    ytd.ytd_esi_employee = Decimal("0.00")
    ytd.ytd_professional_tax = Decimal("0.00")
    ytd.ytd_lwf_employee = Decimal("0.00")
    ytd.ytd_tds = Decimal("0.00")
    ytd.ytd_pf_employer = Decimal("0.00")
    ytd.ytd_esi_employer = Decimal("0.00")
    ytd.ytd_lop_days = 0
    ytd.ytd_bonus = Decimal("0.00")
    ytd.ytd_arrears = Decimal("0.00")
    ytd.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.flush()
    return ytd


async def recalculate_ytd_from_payslips(
    db: AsyncSession,
    employee_id: UUID,
    company_id: UUID,
    financial_year: int,
    from_month: Optional[int] = None,
) -> EmployeeYTD:
    """Rebuild YTD by replaying all locked payslips in the financial year.

    Use case: Correction or audit — recompute YTD from raw payslip data.

    Args:
        db: Database session
        employee_id: Employee UUID
        company_id: Company UUID
        financial_year: Financial year to recalculate
        from_month: Only recompute from this month onwards (1-12, optional)

    Returns:
        Rebuilt YTD record
    """
    ytd = await reset_ytd(db, employee_id, company_id, financial_year)

    # Fetch all locked payslips for this employee in this FY
    payslips = await repo.get_payslips_by_employee_fy(
        db, employee_id, company_id, financial_year
    )

    # Replay each locked payslip
    for payslip in payslips:
        if payslip.locked_at is None:
            continue  # Skip unlocked payslips

        # Optional: skip until from_month
        if from_month and payslip.period_start.month < from_month:
            continue

        ytd = await accumulate_payslip(db, payslip, ytd)

    return ytd


async def get_ytd_summary(
    db: AsyncSession,
    employee_id: UUID,
    company_id: UUID,
    financial_year: int,
) -> dict:
    """Get YTD summary for reporting/debugging.

    Returns dict with all YTD fields plus computed metrics.
    """
    ytd = await get_or_create_ytd(db, employee_id, company_id, financial_year)

    return {
        "employee_id": str(employee_id),
        "financial_year": financial_year,
        "income": {
            "ytd_gross": str(ytd.ytd_gross),
            "ytd_basic": str(ytd.ytd_basic),
            "ytd_hra": str(ytd.ytd_hra),
        },
        "deductions": {
            "ytd_pf_employee": str(ytd.ytd_pf_employee),
            "ytd_esi_employee": str(ytd.ytd_esi_employee),
            "ytd_professional_tax": str(ytd.ytd_professional_tax),
            "ytd_lwf_employee": str(ytd.ytd_lwf_employee),
            "ytd_tds": str(ytd.ytd_tds),
        },
        "employer": {
            "ytd_pf_employer": str(ytd.ytd_pf_employer),
            "ytd_esi_employer": str(ytd.ytd_esi_employer),
        },
        "other": {
            "ytd_lop_days": ytd.ytd_lop_days,
            "ytd_bonus": str(ytd.ytd_bonus),
            "ytd_arrears": str(ytd.ytd_arrears),
        },
    }
