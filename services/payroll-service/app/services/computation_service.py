"""Payroll computation service — DRAFT → REVIEW phase.

Computes payslips for preview without committing to database.
Collects validation errors/warnings to display in preview.
"""
import logging
from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Dict, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import LOPFetchStatus
from app.models.payroll import PayrollRun, Payslip, EmployeeSalary, SalaryStructure
from app.repositories.payroll_repository import PayrollRepository
from app.services.calculators.india_calculator import IndiaSalaryCalculator
from app.services.attendance_integration import (
    fetch_lop_summary,
    pro_rata_factor,
    lop_deduction,
    calendar_days_in_period,
)

logger = logging.getLogger(__name__)


class ComputationService:
    """Service for computing payslips in preview mode (not committed)."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PayrollRepository(db)
        self.calculator = IndiaSalaryCalculator(state_code="MH", tax_regime="new")

    async def compute_payroll_preview(
        self,
        run: PayrollRun,
    ) -> Tuple[List[Dict], List[str], List[str]]:
        """Compute payslips for preview without persisting.

        Args:
            run: PayrollRun to compute

        Returns:
            Tuple of (payslips_data, errors, warnings)
            - payslips_data: List of computed payslip dicts (not persisted)
            - errors: List of blocking validation errors
            - warnings: List of non-blocking warnings
        """
        errors: List[str] = []
        warnings: List[str] = []
        payslips_data: List[Dict] = []

        try:
            # Get all active employee salaries
            active_salaries = await self.repo.list_active_salaries()

            if not active_salaries:
                errors.append("No active employee salaries found")
                return payslips_data, errors, warnings

            company_id = self.db.info.get("company_id")

            for emp_salary in active_salaries:
                # Fetch salary structure
                structure = await self.repo.get_salary_structure(emp_salary.salary_structure_id)
                if not structure:
                    errors.append(
                        f"Salary structure {emp_salary.salary_structure_id} not found for employee {emp_salary.employee_id}"
                    )
                    continue

                if structure.is_active == 0:
                    warnings.append(
                        f"Employee {emp_salary.employee_id} uses inactive structure: {structure.name}"
                    )

                # ── Compute salary
                try:
                    payslip_dict = await self._compute_single_payslip(
                        emp_salary, structure, run, company_id
                    )
                    payslips_data.append(payslip_dict)

                    # Validate computed values
                    if payslip_dict["net"] < Decimal("0"):
                        warnings.append(
                            f"Employee {emp_salary.employee_id} has negative net pay: ₹{payslip_dict['net']}"
                        )

                except Exception as e:
                    errors.append(
                        f"Computation failed for employee {emp_salary.employee_id}: {str(e)[:100]}"
                    )
                    logger.exception(
                        f"Payslip computation error for {emp_salary.employee_id}",
                        extra={"run_id": str(run.id)},
                    )

        except Exception as e:
            errors.append(f"Payroll computation failed: {str(e)[:200]}")
            logger.exception(
                f"Payroll computation error",
                extra={"run_id": str(run.id)},
            )

        return payslips_data, errors, warnings

    async def _compute_single_payslip(
        self,
        emp_salary: EmployeeSalary,
        structure: SalaryStructure,
        run: PayrollRun,
        company_id: UUID,
    ) -> Dict:
        """Compute salary for single employee.

        Returns:
            Dict with all payslip fields (not persisted)
        """
        # Base salary calculation
        breakdown = self.calculator.calculate(
            ctc=Decimal(str(emp_salary.ctc)),
            basic_pct=Decimal(str(structure.basic_pct)),
            hra_pct=Decimal(str(structure.hra_pct)),
            allowances_pct=Decimal(str(structure.allowances_pct)),
            pf_pct=Decimal(str(structure.pf_pct)),
            esi_pct=Decimal(str(structure.esi_pct)),
            professional_tax=Decimal(str(structure.professional_tax)),
        )

        # Pro-ration
        prf = pro_rata_factor(emp_salary.effective_from, run.period_start, run.period_end)
        prorated_basic = breakdown.basic * prf
        prorated_hra = breakdown.hra * prf
        prorated_allowances = breakdown.allowances * prf
        prorated_gross = prorated_basic + prorated_hra + prorated_allowances

        # LOP integration
        lop_days = 0
        lop_fetch_status = LOPFetchStatus.OK.value
        if company_id:
            lop_days, fetch_status, _detail = await fetch_lop_summary(
                employee_id=str(emp_salary.employee_id),
                period_start=run.period_start,
                period_end=run.period_end,
                company_id=company_id,
            )
            if fetch_status != "OK":
                lop_fetch_status = LOPFetchStatus.UNAVAILABLE.value

        # LOP deduction
        period_days = calendar_days_in_period(run.period_start, run.period_end)
        lop_amount = lop_deduction(prorated_gross, lop_days, period_days, method="CALENDAR")
        net_gross = prorated_gross - lop_amount

        # Statutory deductions
        pf_employee = self.calculator.calculate_pf(prorated_basic, Decimal("12"))
        esi_employee = self.calculator.calculate_esi(net_gross, Decimal("0.75"))
        pt_employee = self.calculator.calculate_professional_tax(
            Decimal("0"),
            gross=net_gross,
            month=run.period_start.month,
            gender="M",
        )
        tds_employee = Decimal("0.00")
        lwf_employee = Decimal("0.00")

        # Employer contributions
        pf_employer = self.calculator.calculate_employer_pf(prorated_basic)
        esi_employer = self.calculator.calculate_employer_esi(net_gross)

        # Totals
        total_employee_deductions = pf_employee + esi_employee + pt_employee + tds_employee + lwf_employee
        net_salary = net_gross - total_employee_deductions

        return {
            "id": None,  # Will be assigned on persist
            "payroll_run_id": run.id,
            "employee_id": emp_salary.employee_id,
            "ctc": breakdown.ctc,
            "basic": prorated_basic,
            "hra": prorated_hra,
            "allowances": prorated_allowances,
            "pf_deduction": pf_employee,
            "esi_deduction": esi_employee,
            "professional_tax": pt_employee,
            "tds_deduction": tds_employee,
            "lwf_employee": lwf_employee,
            "other_deductions": Decimal("0.00"),
            "gross": net_gross,
            "total_deductions": total_employee_deductions,
            "net": net_salary,
            "employer_pf": pf_employer,
            "employer_esi": esi_employer,
            "employer_lwf": Decimal("0.00"),
            "lop_days": lop_days,
            "lop_amount": lop_amount,
            "lop_fetch_status": lop_fetch_status,
            "pro_rata_factor": prf,
            "tax_regime": "new",
            "period_start": run.period_start,
            "period_end": run.period_end,
        }
