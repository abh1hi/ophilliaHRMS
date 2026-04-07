"""Loan service — Salary advances and loan EMI management.

Tracks salary advances/loans with EMI deduction across payroll runs.
"""
import logging
from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payroll import PayrollLoan
from app.core.constants import LoanStatus

logger = logging.getLogger(__name__)


class LoanService:
    """Service for managing employee loans and advances."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_loan(
        self,
        employee_id: UUID,
        company_id: UUID,
        loan_type: str,
        principal: Decimal,
        emi_amount: Decimal,
        start_month: str,  # YYYY-MM format
        end_month: str,    # YYYY-MM format
    ) -> PayrollLoan:
        """Create a new loan/advance record.

        Args:
            employee_id: Employee UUID
            company_id: Company UUID
            loan_type: "ADVANCE" or "LOAN"
            principal: Principal amount borrowed
            emi_amount: Monthly EMI
            start_month: Start of deduction (YYYY-MM)
            end_month: End of deduction (YYYY-MM)

        Returns:
            Created PayrollLoan record
        """
        loan = PayrollLoan(
            company_id=company_id,
            employee_id=employee_id,
            loan_type=loan_type,
            principal=principal,
            outstanding=principal,  # Initially full principal
            emi_amount=emi_amount,
            start_month=start_month,
            end_month=end_month,
            status=LoanStatus.ACTIVE.value,
        )

        self.db.add(loan)
        await self.db.flush()

        logger.info(
            f"Loan created: {loan_type} ₹{principal} for emp {employee_id}",
            extra={
                "loan_type": loan_type,
                "principal": str(principal),
                "employee_id": str(employee_id),
            },
        )

        return loan

    async def deduct_emi(
        self,
        loan_id: UUID,
        emi_amount: Decimal,
    ) -> PayrollLoan:
        """Deduct EMI from outstanding balance.

        Called during payroll processing when this month's EMI is deducted.

        Args:
            loan_id: Loan record ID
            emi_amount: EMI amount to deduct

        Returns:
            Updated PayrollLoan record
        """
        # TODO: Implement query in repository
        # loan = await self.repo.get_loan(loan_id)
        # if not loan:
        #     raise ValueError(f"Loan {loan_id} not found")
        #
        # loan.outstanding -= emi_amount
        # if loan.outstanding <= Decimal("0"):
        #     loan.outstanding = Decimal("0")
        #     loan.status = LoanStatus.CLOSED.value
        #     loan.closed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        #
        # await self.db.flush()
        # return loan
        pass

    async def close_loan(
        self,
        loan_id: UUID,
        final_deduction: Optional[Decimal] = None,
    ) -> PayrollLoan:
        """Close a loan (mark as CLOSED).

        Used for:
        - Last EMI payment (outstanding becomes 0)
        - FNF settlement (employee leaves, loan closed)

        Args:
            loan_id: Loan record ID
            final_deduction: Optional final amount deducted

        Returns:
            Updated PayrollLoan record
        """
        # TODO: Implement
        pass

    async def get_active_loans_for_employee(
        self,
        employee_id: UUID,
        company_id: UUID,
    ) -> List[PayrollLoan]:
        """Get all active loans for an employee.

        Args:
            employee_id: Employee UUID
            company_id: Company UUID

        Returns:
            List of active PayrollLoan records
        """
        # TODO: Implement query in repository
        return []

    async def calculate_loan_summary(
        self,
        employee_id: UUID,
        company_id: UUID,
    ) -> Dict[str, Any]:
        """Calculate total loan balance and EMI.

        Args:
            employee_id: Employee UUID
            company_id: Company UUID

        Returns:
            Dict with:
            - total_outstanding: Sum of outstanding balances
            - total_emi: Sum of all monthly EMIs
            - active_loans_count: Number of active loans
            - loans: List of individual loan details
        """
        loans = await self.get_active_loans_for_employee(employee_id, company_id)

        total_outstanding = Decimal("0.00")
        total_emi = Decimal("0.00")

        loan_details = []
        for loan in loans:
            total_outstanding += loan.outstanding
            total_emi += loan.emi_amount

            loan_details.append({
                "loan_id": str(loan.id),
                "type": loan.loan_type,
                "principal": str(loan.principal),
                "outstanding": str(loan.outstanding),
                "emi_monthly": str(loan.emi_amount),
                "start_month": loan.start_month,
                "end_month": loan.end_month,
            })

        return {
            "total_outstanding": total_outstanding,
            "total_emi": total_emi,
            "active_loans_count": len(loans),
            "loans": loan_details,
        }

    async def is_loan_active_in_month(
        self,
        loan_id: UUID,
        year: int,
        month: int,
    ) -> bool:
        """Check if loan EMI should be deducted in a specific month.

        Args:
            loan_id: Loan record ID
            year: Year (YYYY)
            month: Month (1-12)

        Returns:
            True if loan is active and EMI should be deducted, False otherwise
        """
        # TODO: Implement
        # loan = await self.repo.get_loan(loan_id)
        # if not loan or loan.status != LoanStatus.ACTIVE.value:
        #     return False
        #
        # from_ym = loan.start_month  # YYYY-MM
        # to_ym = loan.end_month
        # current_ym = f"{year:04d}-{month:02d}"
        #
        # return from_ym <= current_ym <= to_ym
        pass
