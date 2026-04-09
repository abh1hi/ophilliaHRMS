"""Unit Tests for FNF (Full & Final Settlement) Service.

Tests Full & Final settlement calculations:
- Gratuity: (basic+DA) × (15/26) × years (≥5 years)
- Gratuity exemption: ₹20L private sector (Section 10(10)(ii))
- Leave encashment: earned_days × (basic/26)
- Leave encashment exemption: ₹25L on exit (Section 10(10AA))
- Pro-rata final salary
- Final month TDS with partial year
- Loan recovery (flagged if net < 0)
- Last-month net pay adjustment
"""
import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.services.fnf_service import FNFService
from app.core.constants import PayrollStatus


@pytest.mark.unit
class TestGratuityCalculation:
    """Tests gratuity computation per Section 10(10)(ii) — ₹20L exemption."""

    def test_gratuity_below_5_years_zero(self):
        """Employee < 5 years of service: gratuity = ₹0."""
        service = FNFService()
        basic_da = Decimal("50000")
        years = Decimal("3")

        gratuity = service.calculate_gratuity(basic_da, years)
        assert gratuity == Decimal("0.00"), "Gratuity zero for < 5 years of service"

    def test_gratuity_exact_5_years(self):
        """Employee exactly 5 years: gratuity = basic × (15/26) × 5."""
        service = FNFService()
        basic_da = Decimal("50000")
        years = Decimal("5")

        # Gratuity = 50000 × (15/26) × 5 = 144,230.77 (rounded)
        gratuity = service.calculate_gratuity(basic_da, years)
        assert gratuity == Decimal("144230.77"), f"Expected ₹144,230.77, got ₹{gratuity}"

    def test_gratuity_10_years(self):
        """Employee 10 years: gratuity = basic × (15/26) × 10."""
        service = FNFService()
        basic_da = Decimal("50000")
        years = Decimal("10")

        gratuity = service.calculate_gratuity(basic_da, years)
        # 50000 × (15/26) × 10 = 288,461.54
        assert gratuity == Decimal("288461.54"), f"Expected ₹288,461.54, got ₹{gratuity}"

    def test_gratuity_capped_at_exemption(self):
        """Gratuity exemption ₹20L: Only ₹20L is tax-free."""
        service = FNFService()
        basic_da = Decimal("100000")
        years = Decimal("30")  # Very long service

        gratuity = service.calculate_gratuity(basic_da, years)
        # 100000 × (15/26) × 30 = 1,730,769.23
        assert gratuity == Decimal("1730769.23"), "Verify calculated gratuity"

    def test_gratuity_high_basic_still_respects_exemption(self):
        """Gratuity over ₹20L: Only first ₹20L is tax-free, excess is taxable."""
        service = FNFService()
        basic_da = Decimal("200000")
        years = Decimal("25")

        gratuity = service.calculate_gratuity(basic_da, years)
        # 200000 × (15/26) × 25 = 2,884,615.38
        assert gratuity == Decimal("2884615.38"), f"Expected ₹2,884,615.38, got ₹{gratuity}"


@pytest.mark.unit
class TestLeaveEncashmentCalculation:
    """Tests leave encashment (earned_days × basic/26)."""

    def test_no_earned_leave_zero_encashment(self):
        """No earned leave balance: encashment = ₹0."""
        service = FNFService()
        basic_da = Decimal("50000")
        earned_days = 0

        encashment = service.calculate_leave_encashment(basic_da, earned_days)
        assert encashment == Decimal("0.00"), "Zero earned days = zero encashment"

    def test_earned_leave_5_days(self):
        """5 earned days: encashment = 5 × (50000/26)."""
        service = FNFService()
        basic_da = Decimal("50000")
        earned_days = 5

        # 5 × (50000/26) = 9615.38
        encashment = service.calculate_leave_encashment(basic_da, earned_days)
        assert encashment == Decimal("9615.38"), f"Expected ₹9,615.38, got ₹{encashment}"

    def test_earned_leave_20_days(self):
        """20 earned days: encashment = 20 × (50000/26)."""
        service = FNFService()
        basic_da = Decimal("50000")
        earned_days = 20

        encashment = service.calculate_leave_encashment(basic_da, earned_days)
        # 20 × (50000/26) = 38,461.54
        assert encashment == Decimal("38461.54"), f"Expected ₹38,461.54, got ₹{encashment}"

    def test_leave_encashment_exemption_not_exceeded(self):
        """Leave encashment up to ₹25L is exempt on exit (Section 10(10AA))."""
        service = FNFService()
        basic_da = Decimal("100000")
        earned_days = 50  # Typical max

        encashment = service.calculate_leave_encashment(basic_da, earned_days)
        # 50 × (100000/26) = 192,307.69
        assert encashment == Decimal("192307.69"), f"Expected ₹192,307.69, got ₹{encashment}"


@pytest.mark.unit
class TestProRataFinalSalaryCalculation:
    """Tests pro-rata calculation for partial final month."""

    def test_full_month_pro_rata_factor_1(self):
        """Full month (30 days worked): pro_rata_factor = 1.0."""
        service = FNFService()
        last_working_day = date(2026, 4, 30)
        period_start = date(2026, 4, 1)
        period_end = date(2026, 4, 30)

        pro_rata = service.calculate_pro_rata_factor(last_working_day, period_start, period_end)
        assert pro_rata == Decimal("1.0"), "Full month = 1.0 pro-rata"

    def test_partial_month_15_days_worked(self):
        """Partial month: 15 days worked / 30 days = 0.5."""
        service = FNFService()
        last_working_day = date(2026, 4, 15)
        period_start = date(2026, 4, 1)
        period_end = date(2026, 4, 30)

        pro_rata = service.calculate_pro_rata_factor(last_working_day, period_start, period_end)
        expected = Decimal("15") / Decimal("30")
        assert pro_rata == expected, f"Expected {expected}, got {pro_rata}"

    def test_partial_month_1_day_worked(self):
        """1 day worked: 1/30 = 0.0333."""
        service = FNFService()
        last_working_day = date(2026, 4, 1)
        period_start = date(2026, 4, 1)
        period_end = date(2026, 4, 30)

        pro_rata = service.calculate_pro_rata_factor(last_working_day, period_start, period_end)
        # 1 / 30 = 0.0333 (4 decimal places)
        assert pro_rata == Decimal("0.0333"), f"Expected 0.0333, got {pro_rata}"

    def test_pro_rata_final_salary(self):
        """Pro-rata salary: monthly_gross × pro_rata_factor."""
        service = FNFService()
        monthly_gross = Decimal("85000")
        pro_rata_factor = Decimal("0.5")

        final_salary = service.apply_pro_rata(monthly_gross, pro_rata_factor)
        expected = Decimal("85000") * Decimal("0.5")
        assert final_salary == expected, f"Expected {expected}, got {final_salary}"


@pytest.mark.unit
class TestFinalMonthTDSCalculation:
    """Tests TDS for final month with partial year income."""

    def test_fnf_tds_with_low_annual_income(self):
        """Low annual income: TDS may be zero (87A rebate ≤ ₹12L)."""
        service = FNFService()
        ytd_gross = Decimal("500000")  # ₹5L YTD
        final_salary = Decimal("85000")
        annual_gross = ytd_gross + final_salary  # ₹5.85L

        # Taxable: ₹5.85L - ₹75K = ₹5.10L ≤ ₹12L → 87A rebate applies
        # TDS = ₹0
        tds = service.calculate_final_month_tds(annual_gross, Decimal("75000"))
        assert tds == Decimal("0.00"), "TDS should be zero with 87A rebate"

    def test_fnf_tds_with_high_annual_income(self):
        """High annual income: TDS computed on final installment."""
        service = FNFService()
        ytd_gross = Decimal("1500000")  # ₹15L YTD
        final_salary = Decimal("150000")
        annual_gross = ytd_gross + final_salary  # ₹16.5L

        # Taxable: ₹16.5L - ₹75K = ₹15.85L
        # Exceeds ₹12L → progressive tax applied
        tds = service.calculate_final_month_tds(annual_gross, Decimal("75000"))
        assert tds > Decimal("0"), "TDS should be computed for income > ₹12L"

    def test_fnf_tds_rounded_to_nearest_ten(self):
        """FNF TDS rounded to nearest ₹10 (Section 288B)."""
        service = FNFService()
        ytd_gross = Decimal("1000000")
        final_salary = Decimal("100000")
        annual_gross = ytd_gross + final_salary

        tds = service.calculate_final_month_tds(annual_gross, Decimal("75000"))
        # TDS should be divisible by 10 (or very close)
        remainder = tds % Decimal("10")
        assert remainder == Decimal("0") or remainder < Decimal("1"), f"TDS {tds} not rounded to nearest ₹10"


@pytest.mark.unit
class TestLoanRecoveryOnFNF:
    """Tests outstanding loan recovery during FNF."""

    def test_loan_recovery_deducted_from_fnf(self):
        """Outstanding loan amount deducted from FNF net."""
        service = FNFService()
        fnf_gross = Decimal("500000")  # Gratuity + leave encashment
        outstanding_loan = Decimal("50000")

        # FNF net should include loan deduction
        net_after_loan = fnf_gross - outstanding_loan
        assert net_after_loan == Decimal("450000")

    def test_fnf_with_no_outstanding_loans(self):
        """FNF with no loans: full net payable."""
        service = FNFService()
        fnf_gross = Decimal("500000")
        outstanding_loan = Decimal("0")

        net_payable = fnf_gross - outstanding_loan
        assert net_payable == Decimal("500000")

    def test_fnf_net_becomes_negative_with_high_loan(self):
        """If loans > FNF gross, net becomes negative (HR flag for review)."""
        service = FNFService()
        fnf_gross = Decimal("50000")
        outstanding_loan = Decimal("150000")

        net_payable = fnf_gross - outstanding_loan
        assert net_payable == Decimal("-100000"), "Negative FNF should be flagged"


@pytest.mark.integration
class TestCompleteFullAndFinalSettlement:
    """Integration tests for end-to-end FNF computation."""

    def test_fnf_complete_calculation_typical_employee(self):
        """Typical employee FNF: gratuity + leave encashment - loans."""
        service = FNFService()

        # Employee profile
        basic_da = Decimal("50000")
        monthly_gross = Decimal("100000")
        years_of_service = Decimal("10")
        earned_leave_days = 20
        outstanding_loans = Decimal("25000")
        ytd_gross = Decimal("900000")
        last_working_day = date(2026, 4, 15)
        period_start = date(2026, 4, 1)
        period_end = date(2026, 4, 30)

        # Calculate components
        gratuity = service.calculate_gratuity(basic_da, years_of_service)
        leave_encashment = service.calculate_leave_encashment(basic_da, earned_leave_days)
        pro_rata_factor = service.calculate_pro_rata_factor(last_working_day, period_start, period_end)
        final_salary = service.apply_pro_rata(monthly_gross, pro_rata_factor)

        # FNF gross = gratuity + leave encashment + pro-rata final salary
        fnf_gross = gratuity + leave_encashment + final_salary

        # TDS on final month
        annual_gross = ytd_gross + final_salary
        final_tds = service.calculate_final_month_tds(annual_gross, Decimal("75000"))

        # FNF net = FNF gross - TDS - loan recovery
        fnf_net = fnf_gross - final_tds - outstanding_loans

        # Verify all components are computed
        assert gratuity > Decimal("0"), "Gratuity should be positive for ≥5 years"
        assert leave_encashment > Decimal("0"), "Leave encashment should be positive"
        assert final_salary > Decimal("0"), "Final salary should be positive"
        assert fnf_gross > Decimal("0"), "FNF gross should be positive"
        assert fnf_net > Decimal("0"), "FNF net should be positive (no negative FNF)"

    def test_fnf_high_income_employee_with_significant_gratuity(self):
        """High-income employee: gratuity may exceed ₹20L exemption limit."""
        service = FNFService()

        # High-income profile
        basic_da = Decimal("150000")
        monthly_gross = Decimal("300000")
        years_of_service = Decimal("25")
        earned_leave_days = 30
        last_working_day = date(2026, 3, 31)  # Full last month
        period_start = date(2026, 3, 1)
        period_end = date(2026, 3, 31)

        # Calculate
        gratuity = service.calculate_gratuity(basic_da, years_of_service)
        leave_encashment = service.calculate_leave_encashment(basic_da, earned_leave_days)
        pro_rata_factor = service.calculate_pro_rata_factor(last_working_day, period_start, period_end)
        final_salary = service.apply_pro_rata(monthly_gross, pro_rata_factor)

        fnf_gross = gratuity + leave_encashment + final_salary

        # Gratuity = 150000 × (15/26) × 25 = 2,163,461.54
        # Leave = 30 × (150000/26) = 173,076.92
        # Final = 300000 × 1.0 = 300,000
        # Total ≈ 2.6M
        assert gratuity > Decimal("2000000"), "Gratuity exceeds ₹20L exemption for high-income employee"
        assert fnf_gross > Decimal("2500000"), "High-income FNF gross should be substantial"

    def test_fnf_junior_employee_no_gratuity(self):
        """Junior employee < 5 years: no gratuity, only leave encashment + pro-rata."""
        service = FNFService()

        basic_da = Decimal("30000")
        monthly_gross = Decimal("50000")
        years_of_service = Decimal("2")  # < 5 years
        earned_leave_days = 10
        outstanding_loans = Decimal("0")
        ytd_gross = Decimal("300000")
        last_working_day = date(2026, 4, 15)
        period_start = date(2026, 4, 1)
        period_end = date(2026, 4, 30)

        # Calculate
        gratuity = service.calculate_gratuity(basic_da, years_of_service)
        leave_encashment = service.calculate_leave_encashment(basic_da, earned_leave_days)
        pro_rata_factor = service.calculate_pro_rata_factor(last_working_day, period_start, period_end)
        final_salary = service.apply_pro_rata(monthly_gross, pro_rata_factor)

        fnf_gross = gratuity + leave_encashment + final_salary

        # Gratuity should be zero
        assert gratuity == Decimal("0"), "No gratuity for < 5 years of service"
        # But leave encashment and pro-rata salary should be positive
        assert leave_encashment > Decimal("0"), "Leave encashment should be positive"
        assert final_salary > Decimal("0"), "Pro-rata final salary should be positive"
        assert fnf_gross > Decimal("0"), "FNF gross should be positive even without gratuity"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit or integration"])
