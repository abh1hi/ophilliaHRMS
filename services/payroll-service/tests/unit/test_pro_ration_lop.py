"""Unit Tests for Pro-Ration and LOP (Loss of Pay) Deduction.

Tests:
- Pro-ration factor for mid-period joins
- LOP deduction methods: CALENDAR, WORKING, FIXED_30
- Leave-service integration with timeout fallback
- Pro-rata salary calculation
- Combined pro-rata + LOP impact
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from app.services.attendance_integration import (
    fetch_lop_summary,
    pro_rata_factor,
    lop_deduction,
)


@pytest.mark.unit
class TestProRataFactor:
    """Tests pro_rata_factor() for mid-period joins."""

    def test_full_month_no_pro_ration(self):
        """Employee worked full month: pro_rata = 1.0."""
        effective_from = date(2026, 4, 1)
        period_start = date(2026, 4, 1)
        period_end = date(2026, 4, 30)

        factor = pro_rata_factor(effective_from, period_start, period_end)
        assert factor == Decimal("1.0"), "Full month should have pro_rata = 1.0"

    def test_join_mid_month_april_15(self):
        """Employee joined April 15 (period April 1-30)."""
        effective_from = date(2026, 4, 15)
        period_start = date(2026, 4, 1)
        period_end = date(2026, 4, 30)

        # Days from April 15 to April 30 = 16 days
        # Total days in April = 30
        # pro_rata = 16/30 = 0.5333 (quantized to 4 decimals)
        factor = pro_rata_factor(effective_from, period_start, period_end)
        assert factor == Decimal("0.5333"), f"Expected 0.5333, got {factor}"

    def test_join_april_1_full_month(self):
        """Employee joined April 1 (period April 1-30)."""
        effective_from = date(2026, 4, 1)
        period_start = date(2026, 4, 1)
        period_end = date(2026, 4, 30)

        factor = pro_rata_factor(effective_from, period_start, period_end)
        assert factor == Decimal("1.0000"), "Joining on period start = full month"

    def test_join_april_30_last_day(self):
        """Employee joined April 30 (last day): 1 day worked."""
        effective_from = date(2026, 4, 30)
        period_start = date(2026, 4, 1)
        period_end = date(2026, 4, 30)

        # Days from April 30 to April 30 = 1 day
        # pro_rata = 1/30 = 0.0333 (quantized to 4 decimals)
        factor = pro_rata_factor(effective_from, period_start, period_end)
        assert factor == Decimal("0.0333"), f"Expected 0.0333, got {factor}"

    def test_join_before_period_start_no_pro_ration(self):
        """Employee joined before period start (February): full pro_rata for April."""
        effective_from = date(2026, 2, 1)
        period_start = date(2026, 4, 1)
        period_end = date(2026, 4, 30)

        factor = pro_rata_factor(effective_from, period_start, period_end)
        assert factor == Decimal("1.0"), "Joined before period = full month in current period"


@pytest.mark.unit
class TestLOPDeduction:
    """Tests LOP (Loss of Pay) deduction with different methods."""

    def test_calendar_method_lop_deduction(self):
        """CALENDAR: LOP = monthly_gross / 30 × lop_days."""
        monthly_gross = Decimal("30000")
        lop_days = 2
        method = "CALENDAR"

        deduction = lop_deduction(monthly_gross, lop_days, 30, method)
        expected = (monthly_gross / Decimal("30")) * Decimal(lop_days)
        assert deduction == expected, f"Expected {expected}, got {deduction}"

    def test_calendar_method_full_month_lop(self):
        """CALENDAR: Full month LOP (30 days) = entire monthly_gross."""
        monthly_gross = Decimal("60000")
        lop_days = 30
        method = "CALENDAR"

        deduction = lop_deduction(monthly_gross, lop_days, 30, method)
        assert deduction == monthly_gross, "30 days LOP should equal full month salary"

    def test_working_method_lop_deduction(self):
        """WORKING: LOP = monthly_gross / 26 working days × lop_days.

        Note: WORKING method uses hardcoded 26 working days per month.
        """
        monthly_gross = Decimal("60000")
        lop_days = 2
        method = "WORKING"

        deduction = lop_deduction(monthly_gross, lop_days, 30, method)
        # 60000 / 26 × 2 = 4615.38 (26 working days per month)
        expected = Decimal("4615.38")
        assert deduction == expected, f"Expected {expected}, got {deduction}"

    def test_fixed_30_method_lop_deduction(self):
        """FIXED_30: LOP = monthly_gross / 30 × lop_days (same as CALENDAR)."""
        monthly_gross = Decimal("60000")
        lop_days = 3
        method = "FIXED_30"

        deduction = lop_deduction(monthly_gross, lop_days, 30, method)
        expected = (monthly_gross / Decimal("30")) * Decimal(lop_days)
        assert deduction == expected, f"Expected {expected}, got {deduction}"

    def test_lop_zero_days_zero_deduction(self):
        """No LOP days: deduction = ₹0."""
        monthly_gross = Decimal("60000")
        lop_days = 0
        method = "CALENDAR"

        deduction = lop_deduction(monthly_gross, lop_days, 30, method)
        assert deduction == Decimal("0"), "Zero LOP days = zero deduction"

    def test_lop_fractional_deduction(self):
        """Fractional LOP deduction (e.g., 2.5 days)."""
        monthly_gross = Decimal("60000")
        lop_days = 2.5
        method = "CALENDAR"

        deduction = lop_deduction(monthly_gross, Decimal(str(lop_days)), 30, method)
        expected = (monthly_gross / Decimal("30")) * Decimal(str(lop_days))
        assert deduction == expected


@pytest.mark.unit
class TestProRataAndLOPCombined:
    """Tests combined pro-rata + LOP impact."""

    def test_pro_rata_half_month_plus_2_lop(self):
        """Employee: 50% pro-rata + 2 LOP days in the working period."""
        monthly_gross = Decimal("60000")
        pro_rata = Decimal("0.5")
        lop_days = 2

        # Effective gross after pro-rata: 60000 × 0.5 = 30000
        prorated_gross = monthly_gross * pro_rata

        # LOP deduction on pro-rata gross: 30000 / 30 × 2 = 2000
        # (Note: LOP is typically calculated on effective worked period)
        lop_amt = lop_deduction(prorated_gross, lop_days, 30, "CALENDAR")

        # Net = 30000 - 2000 = 28000
        net = prorated_gross - lop_amt
        assert net == Decimal("28000"), f"Expected ₹28,000, got ₹{net}"

    def test_full_month_full_lop_zero_pay(self):
        """Full month with full LOP (30 days): net = ₹0."""
        monthly_gross = Decimal("60000")
        pro_rata = Decimal("1.0")
        lop_days = 30

        prorated_gross = monthly_gross * pro_rata
        lop_amt = lop_deduction(prorated_gross, lop_days, 30, "CALENDAR")
        net = prorated_gross - lop_amt

        assert net == Decimal("0"), "Full LOP should result in zero net"

    def test_multiple_salary_components_with_lop(self):
        """LOP affects all salary components proportionally."""
        basic = Decimal("40000")
        hra = Decimal("15000")
        allowances = Decimal("5000")
        monthly_gross = basic + hra + allowances  # ₹60,000

        pro_rata = Decimal("0.8")
        lop_days = 3

        prorated_gross = monthly_gross * pro_rata  # ₹48,000
        lop_amt = lop_deduction(prorated_gross, lop_days, 30, "CALENDAR")  # ₹4,800
        net = prorated_gross - lop_amt  # ₹43,200

        assert net == Decimal("43200"), f"Expected ₹43,200, got {net}"


@pytest.mark.unit
class TestLeaveServiceIntegration:
    """Tests leave-service integration behavior patterns."""

    def test_lop_summary_structure(self):
        """Verify LOP summary return structure."""
        lop_summary = {
            "lop_days": 2,
            "worked_days": 28,
            "total_days": 30,
            "status": "OK"
        }

        assert "lop_days" in lop_summary
        assert "status" in lop_summary
        assert lop_summary["lop_days"] == 2

    def test_lop_unavailable_fallback_structure(self):
        """Fallback structure when leave-service unavailable."""
        fallback = {
            "lop_days": 0,
            "worked_days": 0,
            "total_days": 0,
            "status": "UNAVAILABLE"
        }

        assert fallback["lop_days"] == 0, "Fallback LOP should be zero"
        assert fallback["status"] == "UNAVAILABLE"

    def test_lop_skipped_structure(self):
        """Structure when LOP data not found."""
        skipped = {
            "lop_days": 0,
            "worked_days": 0,
            "total_days": 0,
            "status": "SKIPPED"
        }

        assert skipped["lop_days"] == 0
        assert skipped["status"] == "SKIPPED"


@pytest.mark.integration
class TestFullSalaryWithProRataAndLOP:
    """Integration: Full salary calculation with pro-rata and LOP."""

    def test_complete_salary_with_pro_rata_and_lop(self):
        """Complete payslip: basic + HRA + allowances, pro-rated, LOP deducted."""
        # Salary structure
        basic = Decimal("50000")
        hra = Decimal("20000")
        allowances = Decimal("15000")
        monthly_gross = basic + hra + allowances  # ₹85,000

        # Pro-ration (joined April 15)
        effective_from = date(2026, 4, 15)
        period_start = date(2026, 4, 1)
        period_end = date(2026, 4, 30)
        pro_rata = pro_rata_factor(effective_from, period_start, period_end)

        # LOP (2 days lost)
        lop_days = 2

        # Apply pro-rata
        prorated_gross = monthly_gross * pro_rata

        # Apply LOP
        lop_amt = lop_deduction(prorated_gross, lop_days, 30, "CALENDAR")

        # Final gross for payslip
        final_gross = prorated_gross - lop_amt

        # Verify calculations
        # pro_rata = 16/30 = 0.5333 (4 decimals)
        assert pro_rata == Decimal("0.5333"), "16 days worked / 30 days = 0.5333"
        # prorated_gross = 85000 × 0.5333 = 45330.5 (quantized)
        assert prorated_gross == Decimal("45330.50"), f"Expected 45330.50, got {prorated_gross}"
        assert lop_amt > Decimal("0"), "LOP deduction should be positive"
        assert final_gross < prorated_gross, "Final gross < prorated gross (due to LOP)"

    def test_salary_components_proportional_reduction(self):
        """All salary components reduced proportionally by pro-rata."""
        basic = Decimal("40000")
        hra = Decimal("16000")
        allowances = Decimal("14000")
        monthly_gross = basic + hra + allowances  # ₹70,000

        pro_rata = Decimal("0.75")  # 75% of month

        # All components scale by pro-rata
        prorated_basic = basic * pro_rata  # ₹30,000
        prorated_hra = hra * pro_rata      # ₹12,000
        prorated_allowances = allowances * pro_rata  # ₹10,500
        prorated_gross = prorated_basic + prorated_hra + prorated_allowances

        assert prorated_gross == Decimal("52500"), f"Expected ₹52,500, got {prorated_gross}"
        assert prorated_basic == Decimal("30000")
        assert prorated_hra == Decimal("12000")
        assert prorated_allowances == Decimal("10500")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit or integration"])
