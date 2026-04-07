"""Helper module — Integrate adjustments into payroll computation.

Shows how PayrollAdjustment records (bonus, arrears, reimbursements, loan EMI)
are included in payroll runs and affect gross/net calculation.
"""
from decimal import Decimal
from typing import List, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payroll import PayrollAdjustment, PayrollRun
from app.core.constants import AdjustmentDirection


async def calculate_adjustments_for_employee(
    db: AsyncSession,
    payroll_run_id: UUID,
    employee_id: UUID,
) -> Dict[str, Any]:
    """Calculate total adjustments for an employee in a payroll run.

    Args:
        db: Database session
        payroll_run_id: PayrollRun UUID
        employee_id: Employee UUID

    Returns:
        Dict with:
        - adjustments: List of adjustment details
        - total_credits: Sum of CREDIT adjustments (added to gross)
        - total_debits: Sum of DEBIT adjustments (deducted from gross)
        - net_adjustment: Credits - Debits
        - taxable_total: Sum of taxable adjustments
    """
    # TODO: Query adjustments from database
    # for now, return template
    return {
        "adjustments": [],
        "total_credits": Decimal("0.00"),
        "total_debits": Decimal("0.00"),
        "net_adjustment": Decimal("0.00"),
        "taxable_total": Decimal("0.00"),
    }


def apply_adjustments_to_payslip(
    base_gross: Decimal,
    adjustments: List[PayrollAdjustment],
) -> Dict[str, Decimal]:
    """Apply adjustments to base gross salary.

    Adjustments modify gross salary:
    - CREDIT adjustments add to gross (bonus, reimbursement, arrears)
    - DEBIT adjustments subtract from gross (loan EMI, advance recovery)

    Args:
        base_gross: Base gross salary before adjustments
        adjustments: List of PayrollAdjustment records

    Returns:
        Dict with:
        - gross_before_adj: Original gross
        - total_credits: Sum of credit adjustments
        - total_debits: Sum of debit adjustments
        - adjusted_gross: New gross after adjustments
        - adjustment_breakdown: Per-type breakdown
    """
    total_credits = Decimal("0.00")
    total_debits = Decimal("0.00")
    adjustment_breakdown = {}

    for adj in adjustments:
        adj_type = adj.adjustment_type
        if adj_type not in adjustment_breakdown:
            adjustment_breakdown[adj_type] = Decimal("0.00")

        if adj.direction == AdjustmentDirection.CREDIT.value:
            total_credits += adj.amount
            adjustment_breakdown[adj_type] += adj.amount
        else:
            total_debits += adj.amount
            adjustment_breakdown[adj_type] -= adj.amount

    adjusted_gross = base_gross + total_credits - total_debits

    return {
        "gross_before_adj": base_gross,
        "total_credits": total_credits,
        "total_debits": total_debits,
        "adjusted_gross": adjusted_gross,
        "adjustment_breakdown": adjustment_breakdown,
    }


def separate_taxable_nontaxable(
    adjustments: List[PayrollAdjustment],
) -> Dict[str, Decimal]:
    """Separate adjustments into taxable and non-taxable components.

    Used for TDS calculation: only taxable adjustments contribute to
    gross income for tax purposes.

    Args:
        adjustments: List of PayrollAdjustment records

    Returns:
        Dict with:
        - taxable_amount: Sum of taxable adjustments
        - nontaxable_amount: Sum of non-taxable adjustments
        - taxable_details: List of taxable adjustment types
        - nontaxable_details: List of non-taxable adjustment types
    """
    taxable_amount = Decimal("0.00")
    nontaxable_amount = Decimal("0.00")
    taxable_details = []
    nontaxable_details = []

    for adj in adjustments:
        if adj.taxable:
            if adj.direction == AdjustmentDirection.CREDIT.value:
                taxable_amount += adj.amount
                taxable_details.append({
                    "type": adj.adjustment_type,
                    "amount": str(adj.amount),
                })
        else:
            if adj.direction == AdjustmentDirection.CREDIT.value:
                nontaxable_amount += adj.amount
                nontaxable_details.append({
                    "type": adj.adjustment_type,
                    "amount": str(adj.amount),
                })

    return {
        "taxable_amount": taxable_amount,
        "nontaxable_amount": nontaxable_amount,
        "taxable_details": taxable_details,
        "nontaxable_details": nontaxable_details,
    }


# ──────────────────────────────────────────────────────────────────
# EXAMPLE USAGE
# ──────────────────────────────────────────────────────────────────

"""
Example 1: Bonus in Regular Payroll

Base salary: ₹1,00,000/month
Bonus added: ₹25,000 (taxable)
Adjusted gross: ₹1,00,000 + ₹25,000 = ₹1,25,000

This ₹1,25,000 is used for:
- PF calculation: min(basic, ₹15K) × 12% (basic unaffected by bonus)
- ESI calculation: ₹1,25,000 × 0.75% (if <= ₹21K)
- PT calculation: ₹1,25,000 for state-wise slabs
- TDS calculation: ₹1,25,000 contributes to YTD gross

---

Example 2: Reimbursement (Non-taxable)

Base salary: ₹1,00,000/month
Travel reimbursement: ₹5,000 (non-taxable)
Adjusted gross: ₹1,00,000 + ₹5,000 = ₹1,05,000

For TDS/tax purposes:
- Taxable gross: ₹1,00,000 (excludes ₹5,000 reimbursement)
- Net gross: ₹1,05,000 (for net salary calculation)

---

Example 3: Loan EMI Deduction

Base salary: ₹1,00,000/month
Active loan EMI: ₹3,000/month (debit adjustment)
Adjusted gross: ₹1,00,000 - ₹3,000 = ₹97,000

Loan managed separately:
- Outstanding balance reduced by ₹3,000
- Closed when outstanding becomes ₹0
- Can be recovered in FNF if employee leaves

---

Example 4: Salary Revision Arrears

Old CTC: ₹12,00,000 (₹1,00,000/month)
New CTC: ₹15,00,000 (₹1,25,000/month)
Revision effective: April 15, 2025

Arrears computed for April 1-14:
- Days worked at old rate: 14 days
- Daily increase: (₹1,25,000 - ₹1,00,000) / 30 = ₹833.33/day
- Arrear amount: ₹833.33 × 14 = ₹11,666.62
- Added as ARREARS adjustment (taxable) in April payslip

---

Example 5: Off-cycle Bonus Run

Date: Mid-April 2025
Reason: Performance bonus distribution
Run type: BONUS (allows multiple runs for same period)

Employees get bonus via payroll:
1. Create PayrollRun with run_type="BONUS"
2. Add bonus adjustments for each employee
3. Compute/process like regular payroll
4. Separate from April regular salary

Key difference: Same period, different run_type allows multiple runs
(due to updated unique constraint in Phase 1A migration)
"""
