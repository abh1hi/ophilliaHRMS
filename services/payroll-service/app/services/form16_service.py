"""Form 16 (Income Tax Certificate) generation service.

Form 16 is issued by employer to employee showing salary income,
TDS deducted, and other tax-related information for a financial year.

Structure:
- Part A: Employee details, employer details, period
- Part B: Salary breakup, deductions, TDS month-wise
"""
import logging
from decimal import Decimal
from datetime import date
from typing import Dict, Any, Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payroll import EmployeeSalary, EmployeeTaxProfile, EmployeeYTD
from app.repositories.payroll_repository import PayrollRepository

logger = logging.getLogger(__name__)


class Form16Service:
    """Service for generating Form 16 income tax certificates."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PayrollRepository(db)

    async def generate_form16(
        self,
        employee_id: UUID,
        company_id: UUID,
        financial_year: int,
    ) -> Dict[str, Any]:
        """Generate Form 16 (Part A + Part B) for an employee in a financial year.

        Financial year in India: April 1 - March 31
        FY 2025-26: April 1, 2025 - March 31, 2026

        Args:
            employee_id: Employee UUID
            company_id: Company UUID
            financial_year: FY year (e.g., 2026 = FY 2025-26)

        Returns:
            Dict with Form 16 Part A and Part B data
        """
        # Fetch YTD for the financial year
        ytd = await self.repo.get_employee_ytd(employee_id, financial_year)
        if not ytd:
            raise ValueError(
                f"No YTD data found for employee {employee_id} in FY {financial_year}"
            )

        # Fetch tax profile
        tax_profile = await self.repo.get_employee_ytd(employee_id, financial_year)
        # TODO: Fetch actual tax profile from db

        # Build Part A (Deductor/Employer details, Deductee/Employee details)
        part_a = await self._build_part_a(company_id, employee_id, financial_year)

        # Build Part B (Income, deductions, TDS details)
        part_b = await self._build_part_b(employee_id, company_id, financial_year, ytd)

        return {
            "form_16": {
                "financial_year": f"FY {financial_year - 1}-{financial_year}",
                "financial_year_start": f"{financial_year - 1}-04-01",
                "financial_year_end": f"{financial_year}-03-31",
                "part_a": part_a,
                "part_b": part_b,
            }
        }

    async def _build_part_a(
        self,
        company_id: UUID,
        employee_id: UUID,
        financial_year: int,
    ) -> Dict[str, Any]:
        """Build Form 16 Part A: Employer and employee details.

        Args:
            company_id: Company UUID
            employee_id: Employee UUID
            financial_year: FY year

        Returns:
            Part A dict with employer/employee info
        """
        # TODO: Fetch actual company and employee data from respective services
        return {
            "deductor_details": {
                "name": "Company Name",
                "pan": "XXXXXXXXX",
                "address": "Company Address",
                "email": "company@example.com",
            },
            "deductee_details": {
                "name": f"Employee {employee_id}",
                "pan": "XXXXXXXXX",
                "aadhaar": "XXXX XXXX XXXX XXXX",
                "address": "Employee Address",
                "email": "employee@example.com",
                "phone": "9999999999",
            },
            "financial_year": f"FY {financial_year - 1}-{financial_year}",
            "assessment_year": f"AY {financial_year}-{financial_year + 1}",
        }

    async def _build_part_b(
        self,
        employee_id: UUID,
        company_id: UUID,
        financial_year: int,
        ytd: EmployeeYTD,
    ) -> Dict[str, Any]:
        """Build Form 16 Part B: Income and deductions.

        Args:
            employee_id: Employee UUID
            company_id: Company UUID
            financial_year: FY year
            ytd: EmployeeYTD record

        Returns:
            Part B dict with income breakup and TDS
        """
        # Salaries (Section 15)
        gross_salary = ytd.ytd_gross
        basic = ytd.ytd_basic
        hra = ytd.ytd_hra  # TODO: Fetch from payslips

        # Standard deduction (new regime FY 2025-26)
        standard_deduction = Decimal("75000")
        taxable_income = max(Decimal("0"), gross_salary - standard_deduction)

        # Deductions
        pf_employee = ytd.ytd_pf_employee
        esi_employee = ytd.ytd_esi_employee
        pt = ytd.ytd_professional_tax
        tds_deducted = ytd.ytd_tds

        # Net tax liability (before rebates)
        # Simplified: would use full slab calculation in production
        tax_before_rebate = self._calculate_tax_liability(taxable_income)

        # 87A rebate
        rebate_87a = self._calculate_rebate_87a(taxable_income)
        tax_after_rebate = max(Decimal("0"), tax_before_rebate - rebate_87a)

        # Cess 4%
        cess = (tax_after_rebate * Decimal("4") / 100).quantize(Decimal("0.01"))
        total_tax_liability = tax_after_rebate + cess

        return {
            "salaries": {
                "gross_salary": str(gross_salary),
                "basic": str(basic),
                "hra": str(hra),
                "allowances": str(gross_salary - basic - hra),
            },
            "deductions": {
                "section_80_c": "0",  # TODO: From tax profile
                "section_80_d": "0",  # TODO: From tax profile
                "standard_deduction": str(standard_deduction),
                "taxable_income": str(taxable_income),
            },
            "tax_calculation": {
                "tax_before_rebate": str(tax_before_rebate),
                "rebate_87a": str(rebate_87a),
                "tax_after_rebate": str(tax_after_rebate),
                "cess_4_percent": str(cess),
                "total_tax_liability": str(total_tax_liability),
            },
            "tds_deducted": {
                "monthly_tds": str(tds_deducted),
                "surcharge": "0",
                "cess": str(cess),
                "total_tds_deposited": str(tds_deducted),
            },
            "employee_deductions": {
                "pf": str(pf_employee),
                "esi": str(esi_employee),
                "pt": str(pt),
            },
            "tds_reconciliation": {
                "total_tax_liability": str(total_tax_liability),
                "tds_deducted": str(tds_deducted),
                "balance_due": str(max(Decimal("0"), total_tax_liability - tds_deducted)),
                "refund_due": str(max(Decimal("0"), tds_deducted - total_tax_liability)),
            },
        }

    @staticmethod
    def _calculate_tax_liability(taxable_income: Decimal) -> Decimal:
        """Calculate tax liability using new regime slabs (FY 2025-26).

        Args:
            taxable_income: Taxable income after standard deduction

        Returns:
            Annual tax amount
        """
        # New regime slabs
        slabs = [
            (400_000, Decimal("0.00")),
            (800_000, Decimal("0.05")),
            (1_200_000, Decimal("0.10")),
            (1_600_000, Decimal("0.15")),
            (2_000_000, Decimal("0.20")),
            (2_400_000, Decimal("0.25")),
            (float("inf"), Decimal("0.30")),
        ]

        tax = Decimal("0.00")
        previous_limit = Decimal("0")

        for slab_limit, slab_rate in slabs:
            if taxable_income <= previous_limit:
                break
            taxable_in_slab = min(taxable_income, Decimal(str(slab_limit))) - previous_limit
            tax += taxable_in_slab * slab_rate
            previous_limit = Decimal(str(slab_limit))

        return tax.quantize(Decimal("0.01"))

    @staticmethod
    def _calculate_rebate_87a(taxable_income: Decimal) -> Decimal:
        """Calculate 87A rebate (new regime FY 2025-26).

        Full rebate if taxable income <= ₹12L.

        Args:
            taxable_income: Taxable income after deductions

        Returns:
            Rebate amount (₹0 if income > ₹12L)
        """
        if taxable_income <= Decimal("1200000"):
            return Form16Service._calculate_tax_liability(taxable_income)
        return Decimal("0.00")
