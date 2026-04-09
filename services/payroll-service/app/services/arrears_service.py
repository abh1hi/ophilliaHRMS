"""Arrears service — Salary revision backpay calculation.

When an employee's salary is revised mid-year, arrears are calculated
for the period between the revision date and the previous salary structure.
"""
import logging
from decimal import Decimal
from datetime import date
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payroll import EmployeeSalary, Payslip
from app.repositories.payroll_repository import PayrollRepository

logger = logging.getLogger(__name__)


class ArrearsService:
    """Service for computing salary revision arrears."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PayrollRepository(db)

    async def compute_arrears_for_employee(
        self,
        employee_id: UUID,
        company_id: UUID,
        old_ctc: Decimal,
        new_ctc: Decimal,
        revision_effective_from: date,
        current_date: date,
    ) -> Dict[str, Any]:
        """Compute arrears due to salary revision.

        When salary is revised on a date, backpay is calculated for the period
        between that date and the previous salary assignment date.

        Example:
        - Old CTC: ₹12,00,000 (₹1,00,000/month)
        - New CTC: ₹15,00,000 (₹1,25,000/month)
        - Revision date: April 15, 2025
        - Arrear: (₹1,25,000 - ₹1,00,000) × days_worked_at_old_rate / calendar_days

        Args:
            employee_id: Employee UUID
            company_id: Company UUID
            old_ctc: Previous annual CTC
            new_ctc: New annual CTC
            revision_effective_from: Date revision takes effect
            current_date: Today's date (for arrear period calculation)

        Returns:
            Dict with:
            - arrear_amount: Total arrears owed
            - arrear_from_date: Start of arrear period
            - arrear_to_date: End of arrear period
            - old_monthly: Old monthly gross
            - new_monthly: New monthly gross
            - period_months: List of {month, arrear} breakdown
            - status: "OK" | "NO_BACKPAY" | "ERROR"
        """
        old_monthly = (old_ctc / 12).quantize(Decimal("0.01"))
        new_monthly = (new_ctc / 12).quantize(Decimal("0.01"))
        monthly_difference = new_monthly - old_monthly

        if monthly_difference <= Decimal("0"):
            return {
                "arrear_amount": Decimal("0.00"),
                "status": "NO_BACKPAY",
                "reason": "New CTC is not higher than old CTC",
            }

        # Find payslips between last salary change and revision_effective_from
        # For simplicity: calculate from start of month containing revision_effective_from
        arrear_from_date = date(revision_effective_from.year, revision_effective_from.month, 1)

        try:
            # Get all payslips for this employee in the arrear period
            payslips = await self.repo.get_payslips_by_employee(employee_id)

            total_arrears = Decimal("0.00")
            period_months = []

            for payslip in payslips:
                # Only include payslips between arrear_from_date and revision_effective_from
                if payslip.period_start >= arrear_from_date and payslip.period_start < revision_effective_from:
                    # Arrear = (new_monthly - old_monthly) × (working_days / calendar_days)
                    # For simplicity: use full month if revision hasn't taken effect yet
                    arrear_this_month = monthly_difference
                    total_arrears += arrear_this_month
                    period_months.append({
                        "month": payslip.period_start.strftime("%Y-%m"),
                        "arrear_amount": str(arrear_this_month),
                    })

            return {
                "arrear_amount": total_arrears,
                "arrear_from_date": arrear_from_date.isoformat(),
                "arrear_to_date": (revision_effective_from - date(revision_effective_from.year, revision_effective_from.month, 1)).isoformat(),
                "old_monthly": str(old_monthly),
                "new_monthly": str(new_monthly),
                "monthly_difference": str(monthly_difference),
                "period_months": period_months,
                "status": "OK",
            }

        except Exception as e:
            logger.exception(f"Arrears computation failed for {employee_id}")
            return {
                "arrear_amount": Decimal("0.00"),
                "status": "ERROR",
                "reason": str(e)[:100],
            }

    async def list_salary_revisions_for_employee(
        self,
        employee_id: UUID,
    ) -> List[Dict[str, Any]]:
        """List all salary revisions (changes) for an employee.

        Returns list of salary assignments in reverse chronological order.

        Args:
            employee_id: Employee UUID

        Returns:
            List of salary revisions with dates and amounts
        """
        salary_history = await self.repo.get_employee_salary_history(employee_id)

        revisions = []
        for i, salary in enumerate(salary_history):
            next_salary = salary_history[i + 1] if i + 1 < len(salary_history) else None

            revisions.append({
                "salary_id": str(salary.id),
                "ctc": str(salary.ctc),
                "effective_from": salary.effective_from.isoformat(),
                "effective_to": salary.effective_to.isoformat() if salary.effective_to else None,
                "previous_ctc": str(next_salary.ctc) if next_salary else None,
                "status": "active" if salary.is_active else "inactive",
            })

        return revisions

    def calculate_pro_rata_arrears(
        self,
        monthly_difference: Decimal,
        days_in_arrear_period: int,
        total_days_in_month: int = 30,
    ) -> Decimal:
        """Calculate pro-rata arrears for partial month.

        Args:
            monthly_difference: New monthly - Old monthly
            days_in_arrear_period: Number of days arrear applies to
            total_days_in_month: Calendar days in month (default 30)

        Returns:
            Pro-rata arrear amount
        """
        daily_rate = monthly_difference / Decimal(str(total_days_in_month))
        return (daily_rate * Decimal(str(days_in_arrear_period))).quantize(Decimal("0.01"))
