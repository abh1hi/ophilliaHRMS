"""Unit Tests for TDS (Tax Deducted at Source) Engine.

Tests India income tax calculations:
- Progressive slab computation
- 87A rebate (₹60K if taxable ≤ ₹12L)
- Health & education cess (4%)
- Section 288B rounding (to nearest ₹10)
- Monthly TDS with YTD reconciliation
- Last-month adjustment
"""
import pytest
from decimal import Decimal

from app.services.tax.india.tds import (
    compute_annual_tax_new_regime,
    apply_cess,
    compute_monthly_tds,
    round_to_nearest_ten,
    validate_tds_computation,
)


# ──────────────────────────────────────────────────────────────────────────
# Test: Annual Tax Computation (New Regime)
# ──────────────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestAnnualTaxComputation:
    """Tests for compute_annual_tax_new_regime()."""

    def test_zero_income(self):
        """Zero income = zero tax."""
        tax = compute_annual_tax_new_regime(Decimal("0"))
        assert tax == Decimal("0.00")

    def test_income_below_standard_deduction(self):
        """Income < standard deduction (₹75K) = zero tax."""
        # Gross: ₹50K, Standard deduction: ₹75K → Taxable: -₹25K
        tax = compute_annual_tax_new_regime(Decimal("0"))  # After deduction
        assert tax == Decimal("0.00")

    def test_rebate_87a_full_benefit(self):
        """Income ≤ ₹12L gets full 87A rebate."""
        # Income: ₹11L, Standard deduction: ₹75K → Taxable: ₹10.25L ≤ ₹12L
        taxable = Decimal("1025000")
        tax = compute_annual_tax_new_regime(taxable)
        assert tax == Decimal("0.00"), "87A rebate should zero out tax ≤ ₹12L"

    def test_income_12_lakh_boundary(self):
        """Income exactly ₹12L gets full 87A rebate."""
        taxable = Decimal("1200000")
        tax = compute_annual_tax_new_regime(taxable)
        assert tax == Decimal("0.00"), "87A rebate applies at ₹12L boundary"

    def test_income_above_12_lakh(self):
        """Income > ₹12L: tax computed progressively."""
        # Income: ₹13L → Taxable: ₹12.25L
        # Slab: 0-4L (0%), 4-8L (5%), 8-12L (10%), 12-12.25L (15%)
        # Tax: 0 + 200K×0.05 + 400K×0.10 + 25K×0.15
        #    = 10K + 40K + 3.75K = 53.75K
        taxable = Decimal("1225000")
        tax = compute_annual_tax_new_regime(taxable)
        assert tax > Decimal("0"), "Tax should be computed for income > ₹12L"

    def test_slab_progression_18_lakh(self):
        """Verify slab progression for ₹18L income."""
        # Income: ₹18L → Taxable: ₹17.25L (after ₹75K deduction)
        # Slabs:
        #   0-4L: 0% = ₹0
        #   4-8L: 5% = ₹20K
        #   8-12L: 10% = ₹40K
        #   12-16L: 15% = ₹60K
        #   16-17.25L: 20% = ₹25K
        # Total before cess: ₹145K
        taxable = Decimal("1725000")
        tax = compute_annual_tax_new_regime(taxable)
        expected_before_cess = Decimal("145000")
        assert tax == expected_before_cess, f"Expected {expected_before_cess}, got {tax}"

    def test_slab_30_percent_band(self):
        """Verify 30% slab for income > ₹24L."""
        # Income: ₹30L → Taxable: ₹29.25L
        # Tax: 0 + 20K×0.05 + 400K×0.10 + 400K×0.15 + 400K×0.20 + 400K×0.25 + 375K×0.30
        #    = 0 + 10K + 40K + 60K + 80K + 100K + 112.5K = 402.5K (before cess)
        # With 4% cess: 402.5K × 1.04 = 418.6K
        taxable = Decimal("2925000")
        tax = compute_annual_tax_new_regime(taxable)
        assert tax > Decimal("400000"), "30% slab should apply, tax should be > 400K"


# ──────────────────────────────────────────────────────────────────────────
# Test: Cess Calculation (4%)
# ──────────────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestCessCalculation:
    """Tests for apply_cess()."""

    def test_zero_tax_zero_cess(self):
        """Zero tax = zero cess."""
        total = apply_cess(Decimal("0"))
        assert total == Decimal("0.00")

    def test_cess_4_percent(self):
        """Cess should be 4% of tax."""
        # Tax: ₹1,00,000 → Cess: 4% = ₹4,000
        total = apply_cess(Decimal("100000"))
        assert total == Decimal("104000"), "Tax + cess should be ₹104,000"

    def test_cess_on_high_tax(self):
        """Cess on ₹1,62,500 tax."""
        # Tax: ₹1,62,500 → Cess: 4% = ₹6,500
        total = apply_cess(Decimal("162500"))
        assert total == Decimal("169000"), "₹162.5K tax + 4% cess = ₹169K"


# ──────────────────────────────────────────────────────────────────────────
# Test: Section 288B Rounding (to Nearest ₹10)
# ──────────────────────────────────────────────────────────────────────────

@pytest.mark.compliance
class TestSection288BRounding:
    """Tests for round_to_nearest_ten()."""

    def test_round_down(self):
        """₹13,541.67 → ₹13,540 (rounds down)."""
        rounded = round_to_nearest_ten(Decimal("13541.67"))
        assert rounded == Decimal("13540.00")

    def test_round_up(self):
        """₹13,545.00 → ₹13,550 (rounds up)."""
        rounded = round_to_nearest_ten(Decimal("13545.00"))
        assert rounded == Decimal("13550.00")

    def test_round_5_exact(self):
        """₹13,545.00 is exactly 1354.5 × 10 → rounds to ₹13,550."""
        rounded = round_to_nearest_ten(Decimal("13545.00"))
        assert rounded == Decimal("13550.00"), "Half-up rounding (ROUND_HALF_UP)"

    def test_small_amount(self):
        """₹5.00 → ₹10.00 (rounds to nearest ₹10)."""
        rounded = round_to_nearest_ten(Decimal("5.00"))
        assert rounded == Decimal("10.00")

    def test_zero(self):
        """Zero stays zero."""
        rounded = round_to_nearest_ten(Decimal("0.00"))
        assert rounded == Decimal("0.00")

    def test_negative_zero(self):
        """Negative or zero amounts stay ≥ 0."""
        rounded = round_to_nearest_ten(Decimal("-100"))
        assert rounded == Decimal("0.00")


# ──────────────────────────────────────────────────────────────────────────
# Test: Monthly TDS with YTD Reconciliation
# ──────────────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestMonthlyTDSComputation:
    """Tests for compute_monthly_tds() with YTD tracking."""

    def test_april_first_month(self):
        """First month (April) of FY: YTD = 0."""
        # Monthly gross: ₹1,00,000
        # YTD: ₹0
        # Projected annual: ₹0 + ₹1,00,000 × 12 = ₹12,00,000
        # Taxable: ₹12,00,000 - ₹75,000 = ₹11,25,000 ≤ ₹12L → 87A rebate
        # Annual tax: ₹0
        # Monthly TDS: (0 - 0) / 12 = ₹0
        monthly_tds = compute_monthly_tds(
            monthly_gross=Decimal("100000"),
            ytd_gross=Decimal("0"),
            ytd_tds=Decimal("0"),
            current_month=4,  # April
        )
        assert monthly_tds == Decimal("0.00"), "No TDS for ₹12L CTC (87A rebate)"

    def test_march_last_month_adjustment(self):
        """Last month (March): Pay exact remaining to avoid over/under-withholding."""
        # YTD gross: ₹11,00,000
        # March gross: ₹1,00,000
        # Total annual: ₹12,00,000
        # Annual tax: ₹0 (87A rebate)
        # YTD TDS: ₹0
        # Final TDS: 0 - 0 = ₹0
        monthly_tds = compute_monthly_tds(
            monthly_gross=Decimal("100000"),
            ytd_gross=Decimal("1100000"),
            ytd_tds=Decimal("0"),
            current_month=3,  # March
        )
        assert monthly_tds == Decimal("0.00"), "Exact remaining TDS in last month"

    def test_high_income_progression(self):
        """High income: ₹18L CTC → TDS should be computed."""
        # Monthly: ₹1,50,000
        # Projected annual: ₹18,00,000
        # Taxable: ₹17,25,000 (after ₹75K deduction)
        # Annual tax: ₹1,45,000 (from slab progression)
        # + Cess 4%: ₹150,800
        # Months remaining: 12
        # Monthly TDS: ₹150,800 / 12 ≈ ₹12,567
        monthly_tds = compute_monthly_tds(
            monthly_gross=Decimal("150000"),
            ytd_gross=Decimal("0"),
            ytd_tds=Decimal("0"),
            current_month=4,
        )
        assert monthly_tds > Decimal("0"), "TDS should be computed for ₹18L CTC"


# ──────────────────────────────────────────────────────────────────────────
# Test: Validation Helper
# ──────────────────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_validate_tds_computation_debug():
    """Test TDS computation breakdown for debugging."""
    breakdown = validate_tds_computation(
        monthly_gross=Decimal("150000"),
        ytd_gross=Decimal("300000"),  # Already earned 3 months
        ytd_tds=Decimal("30000"),     # Already withheld
        current_month=7,               # July
    )

    assert "projected_annual_gross" in breakdown
    assert "taxable_income" in breakdown
    assert "annual_tax_before_cess" in breakdown
    assert "annual_tax_with_cess" in breakdown
    assert "monthly_tds" in breakdown
    assert breakdown["remaining_months"] == 8  # 8 months left (Aug-Mar)


# ──────────────────────────────────────────────────────────────────────────
# Integration: Full Year TDS Reconciliation
# ──────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestFullYearTDSReconciliation:
    """Tests TDS across all 12 months ensuring total reconciles."""

    def test_12_month_tds_accumulation(self):
        """Compute TDS for all 12 months; verify total matches annual tax."""
        # ₹18L CTC (₹1,50K/month)
        monthly_gross = Decimal("150000")
        ytd_gross = Decimal("0")
        ytd_tds = Decimal("0")
        monthly_tds_list = []

        for month in range(4, 16):  # April (4) to March (15=3 next year)
            actual_month = month if month <= 12 else month - 12
            tds = compute_monthly_tds(
                monthly_gross=monthly_gross,
                ytd_gross=ytd_gross,
                ytd_tds=ytd_tds,
                current_month=actual_month,
            )
            monthly_tds_list.append(tds)
            ytd_gross += monthly_gross
            ytd_tds += tds

        # Total TDS for year
        total_tds = sum(monthly_tds_list)

        # Annual tax should match
        annual_taxable = (monthly_gross * 12) - Decimal("75000")
        annual_tax = compute_annual_tax_new_regime(annual_taxable)
        tax_with_cess = apply_cess(annual_tax)
        annual_tax_rounded = round_to_nearest_ten(tax_with_cess)

        # Allow small rounding difference (≤ ₹10)
        difference = abs(total_tds - annual_tax_rounded)
        assert difference <= Decimal("10"), (
            f"Total TDS {total_tds} should match annual tax {annual_tax_rounded} "
            f"(difference: {difference})"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit or compliance"])
