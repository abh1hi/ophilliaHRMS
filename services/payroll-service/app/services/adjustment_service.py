"""Payroll adjustment service — Variable pay, bonus, arrears, loans.

Manages one-time adjustments (bonus, reimbursement, loan recovery, etc.)
that are added/deducted from a specific payroll run.
"""
import logging
from decimal import Decimal
from datetime import date
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payroll import PayrollAdjustment, PayrollRun
from app.core.constants import AdjustmentType, AdjustmentDirection
from app.repositories.payroll_repository import PayrollRepository

logger = logging.getLogger(__name__)


class AdjustmentService:
    """Service for managing payroll adjustments."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PayrollRepository(db)

    async def create_adjustment(
        self,
        payroll_run_id: UUID,
        employee_id: UUID,
        adjustment_type: str,
        amount: Decimal,
        direction: str = AdjustmentDirection.CREDIT.value,
        taxable: bool = True,
        description: Optional[str] = None,
        period_ref_start: Optional[date] = None,
        period_ref_end: Optional[date] = None,
        created_by: UUID,
    ) -> PayrollAdjustment:
        """Create a payroll adjustment.

        Args:
            payroll_run_id: PayrollRun ID
            employee_id: Employee UUID
            adjustment_type: Type (e.g., "BONUS", "ARREARS")
            amount: Amount in rupees
            direction: CREDIT (adds to salary) or DEBIT (deducts)
            taxable: Whether adjustment is taxable (default True for most)
            description: Optional description
            period_ref_start: For arrears, start of period covered
            period_ref_end: For arrears, end of period covered
            created_by: User creating adjustment

        Returns:
            Created PayrollAdjustment record
        """
        company_id = self.db.info.get("company_id")

        adjustment = PayrollAdjustment(
            company_id=UUID(company_id) if isinstance(company_id, str) else company_id,
            payroll_run_id=payroll_run_id,
            employee_id=employee_id,
            adjustment_type=adjustment_type,
            amount=amount,
            direction=direction,
            taxable=taxable,
            description=description,
            period_ref_start=period_ref_start,
            period_ref_end=period_ref_end,
            created_by=created_by,
        )

        self.db.add(adjustment)
        await self.db.flush()

        logger.info(
            f"Adjustment created: {adjustment_type} ₹{amount} for emp {employee_id}",
            extra={
                "adjustment_type": adjustment_type,
                "employee_id": str(employee_id),
                "amount": str(amount),
            },
        )

        return adjustment

    async def create_bonus(
        self,
        payroll_run_id: UUID,
        employee_id: UUID,
        amount: Decimal,
        taxable: bool = True,
        description: Optional[str] = None,
        created_by: UUID = None,
    ) -> PayrollAdjustment:
        """Create a bonus adjustment.

        Args:
            payroll_run_id: PayrollRun ID
            employee_id: Employee UUID
            amount: Bonus amount
            taxable: Whether bonus is taxable (default True)
            description: Optional description
            created_by: User creating

        Returns:
            Created PayrollAdjustment
        """
        return await self.create_adjustment(
            payroll_run_id=payroll_run_id,
            employee_id=employee_id,
            adjustment_type=AdjustmentType.BONUS.value,
            amount=amount,
            direction=AdjustmentDirection.CREDIT.value,
            taxable=taxable,
            description=description or "Performance bonus",
            created_by=created_by,
        )

    async def create_statutory_bonus(
        self,
        payroll_run_id: UUID,
        employee_id: UUID,
        basic_da_capped: Decimal,  # min(basic+DA, ₹7,000) from salary structure
        created_by: UUID,
    ) -> PayrollAdjustment:
        """Create statutory bonus (8.33% of min(basic+DA, ₹7,000)).

        Bonus Act 1965: Employees earn ₹7,000+ basic+DA → eligible for 8.33% bonus.

        Args:
            payroll_run_id: PayrollRun ID
            employee_id: Employee UUID
            basic_da_capped: min(basic+DA, ₹7,000) from monthly salary
            created_by: User creating

        Returns:
            Created PayrollAdjustment
        """
        bonus_amount = (basic_da_capped * Decimal("8.33") / 100).quantize(Decimal("0.01"))

        return await self.create_adjustment(
            payroll_run_id=payroll_run_id,
            employee_id=employee_id,
            adjustment_type=AdjustmentType.STATUTORY_BONUS.value,
            amount=bonus_amount,
            direction=AdjustmentDirection.CREDIT.value,
            taxable=True,
            description=f"Statutory bonus (8.33% of ₹{basic_da_capped})",
            created_by=created_by,
        )

    async def create_reimbursement(
        self,
        payroll_run_id: UUID,
        employee_id: UUID,
        amount: Decimal,
        description: str,
        created_by: UUID,
    ) -> PayrollAdjustment:
        """Create a reimbursement (non-taxable).

        Reimbursements are typically non-taxable (travel, mobile, internet, etc).

        Args:
            payroll_run_id: PayrollRun ID
            employee_id: Employee UUID
            amount: Reimbursement amount
            description: Type of reimbursement (e.g., "Travel reimbursement")
            created_by: User creating

        Returns:
            Created PayrollAdjustment
        """
        return await self.create_adjustment(
            payroll_run_id=payroll_run_id,
            employee_id=employee_id,
            adjustment_type=AdjustmentType.REIMBURSEMENT.value,
            amount=amount,
            direction=AdjustmentDirection.CREDIT.value,
            taxable=False,
            description=description,
            created_by=created_by,
        )

    async def get_adjustments_for_run(
        self,
        payroll_run_id: UUID,
    ) -> List[PayrollAdjustment]:
        """Get all adjustments for a payroll run.

        Args:
            payroll_run_id: PayrollRun ID

        Returns:
            List of PayrollAdjustment records
        """
        # TODO: Implement query in repository
        # return await self.repo.get_adjustments_by_run(payroll_run_id)
        return []

    async def get_adjustments_for_employee_in_run(
        self,
        payroll_run_id: UUID,
        employee_id: UUID,
    ) -> List[PayrollAdjustment]:
        """Get all adjustments for an employee in a specific run.

        Args:
            payroll_run_id: PayrollRun ID
            employee_id: Employee UUID

        Returns:
            List of PayrollAdjustment records
        """
        # TODO: Implement query in repository
        return []

    async def calculate_adjustment_total(
        self,
        adjustments: List[PayrollAdjustment],
    ) -> Dict[str, Decimal]:
        """Calculate totals for adjustments.

        Args:
            adjustments: List of PayrollAdjustment records

        Returns:
            Dict with:
            - total_credits: Sum of CREDIT adjustments
            - total_debits: Sum of DEBIT adjustments
            - net_adjustment: Credits - Debits
            - taxable_amount: Sum of taxable adjustments
        """
        total_credits = Decimal("0.00")
        total_debits = Decimal("0.00")
        taxable_amount = Decimal("0.00")

        for adj in adjustments:
            if adj.direction == AdjustmentDirection.CREDIT.value:
                total_credits += adj.amount
            else:
                total_debits += adj.amount

            if adj.taxable:
                if adj.direction == AdjustmentDirection.CREDIT.value:
                    taxable_amount += adj.amount
                else:
                    taxable_amount -= adj.amount

        return {
            "total_credits": total_credits,
            "total_debits": total_debits,
            "net_adjustment": total_credits - total_debits,
            "taxable_amount": taxable_amount,
        }
