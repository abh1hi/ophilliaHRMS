"""India TDS (Tax Deducted at Source) calculation engine.

FY 2025-26: New regime with progressive slabs, 87A rebate, 4% cess.
Supports both old and new regimes (old regime implementation in Phase 2 extension).
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional


# ──────────────────────────────────────────────────────────────────────────
# TDS TAX SLABS — NEW REGIME (FY 2025-26)
# ──────────────────────────────────────────────────────────────────────────

TAX_SLABS_NEW_2025_26 = [
    (Decimal("400000"), Decimal("0.00")),      # 0% on first ₹4L
    (Decimal("800000"), Decimal("0.05")),      # 5% on ₹4L to ₹8L
    (Decimal("1200000"), Decimal("0.10")),     # 10% on ₹8L to ₹12L
    (Decimal("1600000"), Decimal("0.15")),     # 15% on ₹12L to ₹16L
    (Decimal("2000000"), Decimal("0.20")),     # 20% on ₹16L to ₹20L
    (Decimal("2400000"), Decimal("0.25")),     # 25% on ₹20L to ₹24L
    (Decimal("9999999999"), Decimal("0.30")),  # 30% above ₹24L
]

# TDS PARAMETERS — NEW REGIME
STANDARD_DEDUCTION_NEW = Decimal("75000")
REBATE_87A = Decimal("60000")  # Zero tax if taxable income ≤ ₹12L
REBATE_87A_INCOME_LIMIT = Decimal("1200000")
CESS_PERCENTAGE = Decimal("4.00")  # Health + education cess

# TDS PARAMETERS — OLD REGIME (stubbed for Phase 2 extension)
STANDARD_DEDUCTION_OLD = Decimal("50000")
REBATE_87A_OLD_LIMIT = Decimal("500000")


def compute_annual_tax_new_regime(taxable_income: Decimal) -> Decimal:
    """Compute annual tax in new regime with progressive slabs.

    Args:
        taxable_income: Income after standard deduction (₹75,000)

    Returns:
        Annual tax (before cess) with 87A rebate applied if eligible
    """
    if taxable_income <= Decimal("0"):
        return Decimal("0.00")

    # Apply progressive slabs
    tax = Decimal("0.00")
    previous_limit = Decimal("0.00")

    for slab_limit, slab_rate in TAX_SLABS_NEW_2025_26:
        if taxable_income <= previous_limit:
            break

        taxable_in_slab = min(taxable_income, slab_limit) - previous_limit
        tax += taxable_in_slab * slab_rate
        previous_limit = slab_limit

    tax = tax.quantize(Decimal("0.01"), ROUND_HALF_UP)

    # Apply 87A rebate: full rebate if taxable income ≤ ₹12L
    if taxable_income <= REBATE_87A_INCOME_LIMIT:
        return Decimal("0.00")

    return tax


def apply_cess(tax_amount: Decimal) -> Decimal:
    """Apply 4% health + education cess on tax.

    Args:
        tax_amount: Annual tax amount (before cess)

    Returns:
        Total tax with 4% cess included
    """
    cess = (tax_amount * CESS_PERCENTAGE / 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
    total_tax = (tax_amount + cess).quantize(Decimal("0.01"), ROUND_HALF_UP)
    return total_tax


def round_to_nearest_ten(amount: Decimal) -> Decimal:
    """CRITICAL FIX: Section 288B rounding.

    Indian Income Tax Act Section 288B mandates:
    Final tax payable shall be rounded off to the nearest multiple of ₹10.

    Examples:
    - ₹12,345.50 → ₹12,350
    - ₹12,344.50 → ₹12,340

    Args:
        amount: Tax amount (in paisa/paise)

    Returns:
        Tax rounded to nearest ₹10
    """
    if amount <= Decimal("0"):
        return Decimal("0.00")

    # Round to nearest 10: amount / 10 → round → amount * 10
    rounded = (amount / Decimal("10")).quantize(Decimal("1"), ROUND_HALF_UP) * Decimal("10")
    return rounded.quantize(Decimal("0.01"))


def compute_monthly_tds(
    monthly_gross: Decimal,
    ytd_gross: Decimal,
    ytd_tds: Decimal,
    current_month: int,
    fy_end_month: int = 3,  # March (FY ends 31-Mar)
    standard_deduction: Optional[Decimal] = None,
) -> Decimal:
    """Compute monthly TDS with year-to-date reconciliation.

    Strategy:
    1. Project annual gross: ytd_gross + monthly_gross * remaining_months
    2. Apply standard deduction, compute annual tax (new regime)
    3. Distribute remaining tax across remaining months
    4. On last month: pay exact remainder to avoid under/over-withholding

    Args:
        monthly_gross: Current month's gross salary
        ytd_gross: Year-to-date gross (accumulated, not including current month)
        ytd_tds: Year-to-date TDS already withheld
        current_month: Current month (1-12)
        fy_end_month: FY end month (default 3 for March)
        standard_deduction: Override for standard deduction (default ₹75K)

    Returns:
        Monthly TDS amount (rounded to nearest paisa, minimum ₹0)

    Example:
        Employee CTC ₹18,00,000 (₹15,000/month)
        April (month 1): ytd_gross=0, monthly=15,000 → TDS ≈ ₹1,125
        March (month 12): ytd_gross=165,000, monthly=15,000 → TDS adjusted for exact annual total
    """
    if standard_deduction is None:
        standard_deduction = STANDARD_DEDUCTION_NEW

    # Calculate remaining months in financial year
    if current_month <= fy_end_month:
        # We're in the last part of FY (e.g., Jan-Mar in FY 2025-26)
        remaining_months = fy_end_month - current_month + 1
    else:
        # We're in the first part of next FY (e.g., Apr-Dec in FY 2025-26)
        remaining_months = 12 - current_month + fy_end_month + 1

    # Ensure at least 1 month remaining
    remaining_months = max(1, remaining_months)

    # Project annual gross salary
    projected_annual_gross = ytd_gross + monthly_gross * Decimal(str(remaining_months))

    # Compute taxable income and annual tax
    taxable_income = max(Decimal("0"), projected_annual_gross - standard_deduction)
    annual_tax = compute_annual_tax_new_regime(taxable_income)
    annual_tax_with_cess = apply_cess(annual_tax)

    # CRITICAL FIX: Section 288B rounding (round to nearest ₹10)
    annual_tax_rounded = round_to_nearest_ten(annual_tax_with_cess)

    # Determine monthly TDS
    if remaining_months == 1:
        # Last month: pay exact remaining to avoid under/over-withholding
        monthly_tds = (annual_tax_rounded - ytd_tds).quantize(Decimal("0.01"), ROUND_HALF_UP)
    else:
        # Regular month: distribute remaining tax evenly
        remaining_tax = annual_tax_rounded - ytd_tds
        monthly_tds = (remaining_tax / Decimal(str(remaining_months))).quantize(Decimal("0.01"), ROUND_HALF_UP)

    # TDS cannot be negative
    return max(Decimal("0.00"), monthly_tds)


def compute_annual_tax_old_regime(
    taxable_income: Decimal,
    age_60_above: bool = False,
) -> Decimal:
    """Compute annual tax in old regime (Phase 2 extension).

    Placeholder for future implementation.
    Old regime has different slabs and exemptions (80C, 80D, etc).
    """
    raise NotImplementedError("Old regime tax calculation coming in Phase 2 extension")


# ──────────────────────────────────────────────────────────────────────────
# VALIDATION & DEBUGGING
# ──────────────────────────────────────────────────────────────────────────

def validate_tds_computation(
    monthly_gross: Decimal,
    ytd_gross: Decimal,
    ytd_tds: Decimal,
    current_month: int,
) -> Dict[str, any]:
    """Debug helper: return detailed breakdown of TDS computation.

    Returns dict with:
    - projected_annual_gross
    - taxable_income
    - annual_tax_before_cess
    - annual_tax_with_cess
    - remaining_tds_to_withhold
    - monthly_tds
    """
    remaining_months = max(1, 3 - current_month + 1) if current_month <= 3 else max(1, 15 - current_month)
    projected_annual_gross = ytd_gross + monthly_gross * Decimal(str(remaining_months))
    taxable_income = max(Decimal("0"), projected_annual_gross - STANDARD_DEDUCTION_NEW)
    annual_tax = compute_annual_tax_new_regime(taxable_income)
    annual_tax_with_cess = apply_cess(annual_tax)
    remaining_tds = (annual_tax_with_cess - ytd_tds).quantize(Decimal("0.01"), ROUND_HALF_UP)

    if remaining_months == 1:
        monthly_tds = remaining_tds
    else:
        monthly_tds = (remaining_tds / Decimal(str(remaining_months))).quantize(Decimal("0.01"), ROUND_HALF_UP)

    return {
        "projected_annual_gross": projected_annual_gross,
        "taxable_income": taxable_income,
        "annual_tax_before_cess": annual_tax,
        "annual_tax_with_cess": annual_tax_with_cess,
        "ytd_tds_so_far": ytd_tds,
        "remaining_tds_to_withhold": remaining_tds,
        "remaining_months": remaining_months,
        "monthly_tds": monthly_tds,
    }
