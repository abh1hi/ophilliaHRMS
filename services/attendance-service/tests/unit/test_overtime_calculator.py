"""Unit tests for OvertimeCalculator — thresholds, multipliers, half-day detection."""
import pytest
from datetime import datetime, timezone, timedelta

from app.services.overtime_calculator import OvertimeCalculator


@pytest.fixture
def calc():
    return OvertimeCalculator()


def _session(hours: float):
    """Return (clock_in, clock_out) for a session of given duration."""
    clock_in = datetime(2026, 4, 1, 9, 0, 0, tzinfo=timezone.utc)
    clock_out = clock_in + timedelta(hours=hours)
    return clock_in, clock_out


class TestNoOvertime:
    def test_exactly_at_threshold_no_ot(self, calc):
        ci, co = _session(8.0)
        total, ot, status = calc.compute(ci, co, 8.0, daily_ot_threshold=8.0)
        assert total == pytest.approx(8.0)
        assert ot == pytest.approx(0.0)
        assert status == ""

    def test_under_threshold_no_ot(self, calc):
        ci, co = _session(7.5)
        _, ot, _ = calc.compute(ci, co, 8.0, daily_ot_threshold=8.0)
        assert ot == pytest.approx(0.0)


class TestOvertimeWithMultipliers:
    def test_default_multiplier_one(self, calc):
        """Default multiplier=1.0: OT hours = raw excess."""
        ci, co = _session(10.0)
        _, ot, _ = calc.compute(ci, co, 8.0, daily_ot_threshold=8.0, daily_ot_multiplier=1.0)
        assert ot == pytest.approx(2.0)

    def test_india_factories_act_double_time(self, calc):
        """India: 2.0× multiplier, threshold = 9h."""
        ci, co = _session(11.0)
        _, ot, _ = calc.compute(ci, co, 9.0, daily_ot_threshold=9.0, daily_ot_multiplier=2.0)
        assert ot == pytest.approx(4.0)  # (11 - 9) × 2.0

    def test_eu_wtd_multiplier(self, calc):
        """EU: 1.25× daily multiplier, threshold = 10h."""
        ci, co = _session(12.0)
        _, ot, _ = calc.compute(ci, co, 8.0, daily_ot_threshold=10.0, daily_ot_multiplier=1.25)
        assert ot == pytest.approx(2.5)  # (12 - 10) × 1.25

    def test_ot_rounded_to_two_decimals(self, calc):
        ci, co = _session(9.333)
        _, ot, _ = calc.compute(ci, co, 8.0, daily_ot_threshold=8.0, daily_ot_multiplier=1.5)
        assert ot == round((9.333 - 8.0) * 1.5, 2)


class TestStatusUpdate:
    def test_half_day_when_under_half_expected(self, calc):
        ci, co = _session(3.9)
        _, _, status = calc.compute(ci, co, work_hours_per_day=8.0)
        assert status == "half_day"

    def test_no_status_update_for_full_day(self, calc):
        ci, co = _session(8.0)
        _, _, status = calc.compute(ci, co, work_hours_per_day=8.0)
        assert status == ""

    def test_no_status_update_for_ot_day(self, calc):
        ci, co = _session(10.0)
        _, _, status = calc.compute(ci, co, work_hours_per_day=8.0)
        assert status == ""

    def test_total_hours_returned_correctly(self, calc):
        ci, co = _session(6.5)
        total, _, _ = calc.compute(ci, co, work_hours_per_day=8.0)
        assert total == pytest.approx(6.5)


class TestHolidayWork:
    def test_holiday_all_hours_attract_multiplier(self, calc):
        """On a holiday every hour is paid at holiday_multiplier — threshold is zero."""
        ci, co = _session(8.0)
        total, ot_pay, status = calc.compute(
            ci, co, work_hours_per_day=8.0,
            is_holiday=True, holiday_multiplier=2.0,
        )
        assert total == pytest.approx(8.0)
        assert ot_pay == pytest.approx(16.0)
        assert status == "holiday"

    def test_holiday_status_overrides_half_day(self, calc):
        """Holiday status takes precedence even for a short session."""
        ci, co = _session(3.0)
        _, _, status = calc.compute(
            ci, co, work_hours_per_day=8.0,
            is_holiday=True, holiday_multiplier=2.0,
        )
        assert status == "holiday"

    def test_non_holiday_not_marked_holiday(self, calc):
        ci, co = _session(9.0)
        _, _, status = calc.compute(
            ci, co, work_hours_per_day=8.0,
            daily_ot_threshold=8.0, is_holiday=False,
        )
        assert status != "holiday"


class TestShiftAwareThreshold:
    def test_shift_threshold_overrides_default(self, calc):
        """12h night shift: OT kicks in after 12h, not 8h."""
        ci, co = _session(13.0)
        _, ot, _ = calc.compute(
            ci, co, work_hours_per_day=12.0,
            daily_ot_threshold=12.0, daily_ot_multiplier=1.5,
        )
        assert ot == pytest.approx(1.5)  # (13 - 12) × 1.5
