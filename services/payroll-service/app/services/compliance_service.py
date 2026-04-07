"""Statutory compliance service — ECR, ESIC, PT challan generation.

Generates EPFO/ESIC/PT return data for statutory filing.
"""
import logging
from decimal import Decimal
from datetime import date
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payroll import PayrollRun, Payslip, EmployeeSalary
from app.repositories.payroll_repository import PayrollRepository

logger = logging.getLogger(__name__)


class ComplianceService:
    """Service for generating statutory compliance documents."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PayrollRepository(db)

    async def generate_ecr_file(
        self,
        payroll_run_id: UUID,
    ) -> str:
        """Generate ECR (Electronic Challan cum Return) file for EPFO.

        ECR format (11 fields, #~# separator):
        UAN #~# Name #~# Gross Wages #~# EPF Wages #~# EPS Wages #~# EDLI Wages #~#
        EPF Contri #~# EPS Contri #~# EPF-EPS Diff #~# NCP Days #~# Refund of Advances

        Args:
            payroll_run_id: PayrollRun UUID

        Returns:
            ECR file content as string (can be saved as .txt or imported to EPFO portal)
        """
        run = await self.repo.get_payroll_run(payroll_run_id)
        if not run:
            raise ValueError(f"PayrollRun {payroll_run_id} not found")

        payslips = await self.repo.get_payslips_by_run(payroll_run_id)
        if not payslips:
            return ""  # Empty file

        ecr_lines = []

        for payslip in payslips:
            # Get employee for UAN (TODO: fetch from employee service)
            # For now, use employee_id as placeholder
            uan = str(payslip.employee_id)[:12].ljust(12, "0")
            name = f"Employee {payslip.employee_id}"  # TODO: Fetch actual name

            # EPF wage: min(basic, ₹15,000)
            epf_wage = min(payslip.basic, Decimal("15000"))
            # EPS wage: same as EPF wage for calculation
            eps_wage = epf_wage
            # EDLI wage: same as EPF wage
            edli_wage = epf_wage

            # Contributions
            epf_contrib = payslip.pf_deduction + payslip.employer_pf
            eps_contrib = payslip.employer_pf  # Employer EPS portion
            epf_eps_diff = payslip.pf_deduction - eps_contrib  # EPF-EPS difference

            # NCP (No Contribution Period) = LOP days
            ncp_days = payslip.lop_days

            # Refund of advances (TODO: integrate with loan service)
            refund_advances = Decimal("0.00")

            # Build ECR line
            ecr_line = (
                f"{uan}#~#{name}#~#{payslip.gross}#~#{epf_wage}#~#{eps_wage}#~#{edli_wage}#~#"
                f"{epf_contrib}#~#{eps_contrib}#~#{epf_eps_diff}#~#{ncp_days}#~#{refund_advances}"
            )
            ecr_lines.append(ecr_line)

        return "\n".join(ecr_lines)

    async def generate_esic_return(
        self,
        payroll_run_id: UUID,
    ) -> Dict[str, Any]:
        """Generate ESIC (Employee State Insurance) monthly return data.

        Returns structured JSON (not actual file, but data for return form).

        Args:
            payroll_run_id: PayrollRun UUID

        Returns:
            Dict with ESIC return summary and employee details
        """
        run = await self.repo.get_payroll_run(payroll_run_id)
        if not run:
            raise ValueError(f"PayrollRun {payroll_run_id} not found")

        payslips = await self.repo.get_payslips_by_run(payroll_run_id)

        total_esi_employee = Decimal("0.00")
        total_esi_employer = Decimal("0.00")
        employee_count = 0
        covered_employees = []

        for payslip in payslips:
            # Only employees with gross <= ₹21,000 are covered
            if payslip.gross <= Decimal("21000"):
                total_esi_employee += payslip.esi_deduction
                total_esi_employer += payslip.employer_esi
                employee_count += 1

                covered_employees.append({
                    "employee_id": str(payslip.employee_id),
                    "gross_wages": str(payslip.gross),
                    "esi_employee": str(payslip.esi_deduction),
                    "esi_employer": str(payslip.employer_esi),
                    "total_esi": str(payslip.esi_deduction + payslip.employer_esi),
                })

        total_esi_contribution = total_esi_employee + total_esi_employer

        return {
            "return_period": f"{run.period_start.year}-{run.period_start.month:02d}",
            "period_start": run.period_start.isoformat(),
            "period_end": run.period_end.isoformat(),
            "total_employees_covered": employee_count,
            "total_esi_employee_contribution": str(total_esi_employee),
            "total_esi_employer_contribution": str(total_esi_employer),
            "total_esi_contribution": str(total_esi_contribution),
            "employee_details": covered_employees,
        }

    async def generate_pt_challan(
        self,
        payroll_run_id: UUID,
        state_code: str,
    ) -> Dict[str, Any]:
        """Generate Professional Tax challan data per state.

        PT is collected monthly/half-yearly per state and deposited with state authorities.

        Args:
            payroll_run_id: PayrollRun UUID
            state_code: State code (e.g., "MH", "KA")

        Returns:
            Dict with PT summary and employee breakup
        """
        run = await self.repo.get_payroll_run(payroll_run_id)
        if not run:
            raise ValueError(f"PayrollRun {payroll_run_id} not found")

        payslips = await self.repo.get_payslips_by_run(payroll_run_id)

        total_pt = Decimal("0.00")
        employee_count = 0
        employee_details = []

        for payslip in payslips:
            if payslip.professional_tax > Decimal("0"):
                total_pt += payslip.professional_tax
                employee_count += 1
                employee_details.append({
                    "employee_id": str(payslip.employee_id),
                    "gross_wages": str(payslip.gross),
                    "pt_amount": str(payslip.professional_tax),
                })

        return {
            "state": state_code,
            "period": f"{run.period_start.year}-{run.period_start.month:02d}",
            "period_start": run.period_start.isoformat(),
            "period_end": run.period_end.isoformat(),
            "total_employees": employee_count,
            "total_pt_due": str(total_pt),
            "deposit_deadline": self._pt_deposit_deadline(run.period_end, state_code),
            "employee_details": employee_details,
        }

    async def generate_bank_advice(
        self,
        payroll_run_id: UUID,
    ) -> str:
        """Generate bank advice (salary transfer file) as CSV.

        Format: Employee ID, Name, Account, IFSC, Amount (for bank's salary bulk transfer)

        Args:
            payroll_run_id: PayrollRun UUID

        Returns:
            CSV content (can be imported to bank portal)
        """
        run = await self.repo.get_payroll_run(payroll_run_id)
        if not run:
            raise ValueError(f"PayrollRun {payroll_run_id} not found")

        payslips = await self.repo.get_payslips_by_run(payroll_run_id)
        if not payslips:
            return ""  # Empty file

        csv_lines = ["Employee ID,Name,Account Number,IFSC,Salary Amount"]

        for payslip in payslips:
            # TODO: Fetch employee bank details from employee service
            account_number = "XXXX"  # Placeholder
            ifsc = "XXXX0000001"  # Placeholder
            name = f"Employee {payslip.employee_id}"  # Placeholder

            csv_line = f"{payslip.employee_id},{name},{account_number},{ifsc},{payslip.net}"
            csv_lines.append(csv_line)

        return "\n".join(csv_lines)

    # ──────────────────────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _pt_deposit_deadline(period_end: date, state_code: str) -> str:
        """Calculate PT deposit deadline per state.

        Most states: 15th of next month
        Some states: Earlier deadline

        Args:
            period_end: End of payroll period
            state_code: State code

        Returns:
            ISO format date string
        """
        # Simplified: always 15th of next month
        if period_end.month == 12:
            deadline = date(period_end.year + 1, 1, 15)
        else:
            deadline = date(period_end.year, period_end.month + 1, 15)

        return deadline.isoformat()
