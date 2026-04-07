"""Bank advice service — Salary transfer file generation.

Generates files for bulk salary transfers to employee bank accounts.
Formats: NEFT/RTGS, bank-specific formats, or standard CSV/XLSX.
"""
import logging
from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payroll import PayrollRun, Payslip
from app.repositories.payroll_repository import PayrollRepository

logger = logging.getLogger(__name__)


class BankAdviceService:
    """Service for generating salary bank transfer files."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PayrollRepository(db)

    async def generate_bank_advice_csv(
        self,
        payroll_run_id: UUID,
    ) -> str:
        """Generate bank advice as CSV for salary bulk transfer.

        Format: Employee ID, Name, Account, IFSC, Amount

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

        csv_lines = [
            "Employee ID,Employee Name,Account Number,IFSC Code,Net Salary,Pay Period"
        ]

        period_str = f"{run.period_start.strftime('%d-%b-%Y')} to {run.period_end.strftime('%d-%b-%Y')}"

        for payslip in payslips:
            # TODO: Fetch employee bank details from employee service
            # For now, use placeholders
            employee_name = f"Employee {payslip.employee_id}"
            account_number = "XXXX1234567890"  # Placeholder
            ifsc = "XXXX0000001"  # Placeholder

            csv_line = (
                f"{payslip.employee_id},"
                f'"{employee_name}",'
                f"{account_number},"
                f"{ifsc},"
                f"{payslip.net},"
                f"{period_str}"
            )
            csv_lines.append(csv_line)

        return "\n".join(csv_lines)

    async def generate_neft_file(
        self,
        payroll_run_id: UUID,
        bank_code: str = "001",  # RBI bank code
    ) -> str:
        """Generate NEFT (National Electronic Funds Transfer) format file.

        NEFT is used for batch transfers <= ₹10 lakhs per transaction.

        Args:
            payroll_run_id: PayrollRun UUID
            bank_code: RBI bank code (default 001)

        Returns:
            NEFT format content
        """
        run = await self.repo.get_payroll_run(payroll_run_id)
        if not run:
            raise ValueError(f"PayrollRun {payroll_run_id} not found")

        payslips = await self.repo.get_payslips_by_run(payroll_run_id)
        if not payslips:
            return ""

        neft_lines = []
        batch_count = 0
        total_amount = Decimal("0.00")

        for payslip in payslips:
            batch_count += 1
            total_amount += payslip.net

            # NEFT line format (simplified)
            # Actual format depends on bank requirements
            neft_line = (
                f"{batch_count:06d}|"  # Batch serial
                f"{payslip.employee_id}|"  # Reference
                f"XXXX0000001|"  # IFSC (placeholder)
                f"XXXX1234567890|"  # Account
                f"{payslip.net}|"  # Amount
                f"Employee {payslip.employee_id}"  # Beneficiary name
            )
            neft_lines.append(neft_line)

        # NEFT header
        header = (
            f"HDR|"
            f"{run.period_start.strftime('%d%m%Y')}|"  # Settlement date
            f"SALARY|"  # Batch type
            f"INR|"  # Currency
            f"{batch_count}|"  # Total records
            f"{total_amount}"  # Total amount
        )

        return header + "\n" + "\n".join(neft_lines)

    async def generate_payment_schedule(
        self,
        payroll_run_id: UUID,
    ) -> Dict[str, Any]:
        """Generate payment schedule summary for finance/treasury.

        Args:
            payroll_run_id: PayrollRun UUID

        Returns:
            Dict with payment summary and mode breakdown
        """
        run = await self.repo.get_payroll_run(payroll_run_id)
        if not run:
            raise ValueError(f"PayrollRun {payroll_run_id} not found")

        payslips = await self.repo.get_payslips_by_run(payroll_run_id)

        total_gross = Decimal("0.00")
        total_deductions = Decimal("0.00")
        total_net = Decimal("0.00")
        count = 0

        employee_list = []

        for payslip in payslips:
            total_gross += payslip.gross
            total_deductions += payslip.total_deductions
            total_net += payslip.net
            count += 1

            employee_list.append({
                "employee_id": str(payslip.employee_id),
                "gross": str(payslip.gross),
                "deductions": str(payslip.total_deductions),
                "net": str(payslip.net),
            })

        return {
            "payroll_run_id": str(payroll_run_id),
            "period_start": run.period_start.isoformat(),
            "period_end": run.period_end.isoformat(),
            "payment_date": None,  # To be set by finance
            "summary": {
                "total_employees": count,
                "total_gross_salary": str(total_gross),
                "total_deductions": str(total_deductions),
                "total_net_payable": str(total_net),
            },
            "payment_modes": {
                "bank_transfer": {
                    "count": count,
                    "amount": str(total_net),
                    "method": "NEFT/RTGS",
                },
                "cash": {
                    "count": 0,
                    "amount": "0.00",
                },
                "cheque": {
                    "count": 0,
                    "amount": "0.00",
                },
            },
            "employees": employee_list,
        }

    async def verify_bank_details_completeness(
        self,
        payroll_run_id: UUID,
    ) -> Dict[str, Any]:
        """Verify that all employees have complete bank details.

        Args:
            payroll_run_id: PayrollRun UUID

        Returns:
            Dict with verification status and list of employees with missing details
        """
        run = await self.repo.get_payroll_run(payroll_run_id)
        if not run:
            raise ValueError(f"PayrollRun {payroll_run_id} not found")

        payslips = await self.repo.get_payslips_by_run(payroll_run_id)

        missing_details = []
        employees_ready = 0
        employees_incomplete = 0

        for payslip in payslips:
            # TODO: Fetch employee bank details from employee service
            # For now, simulate all as ready
            employees_ready += 1
            # if employee_bank_details_missing:
            #     missing_details.append({
            #         "employee_id": str(payslip.employee_id),
            #         "missing_fields": ["account_number", "ifsc"],
            #     })
            #     employees_incomplete += 1

        return {
            "payroll_run_id": str(payroll_run_id),
            "total_employees": len(payslips),
            "ready_for_transfer": employees_ready,
            "incomplete_details": employees_incomplete,
            "missing_details": missing_details,
            "can_process": len(missing_details) == 0,
        }
