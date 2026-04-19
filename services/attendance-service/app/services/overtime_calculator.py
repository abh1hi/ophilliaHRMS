"""Overtime calculator: derive work hours, OT pay hours, and half-day status."""
from datetime import datetime


class OvertimeCalculator:
    """Computes work hours and overtime for a completed clock-in/out session.

    Stateless — no DB or config required.

    Holiday logic: on a public holiday every hour worked attracts the
    holiday_multiplier (e.g. 2.0×) — threshold is effectively zero.
    Regular OT: hours beyond daily_ot_threshold × daily_ot_multiplier.
    """

    def compute(
        self,
        clock_in: datetime,
        clock_out: datetime,
        work_hours_per_day: float,
        daily_ot_threshold: float = 8.0,
        daily_ot_multiplier: float = 1.0,
        is_holiday: bool = False,
        holiday_multiplier: float = 2.0,
    ) -> tuple[float, float, str]:
        """Return (total_hours, ot_pay_hours, status_update).

        total_hours:    raw hours worked (stored on the record)
        ot_pay_hours:   overtime pay-equivalent hours (after multiplier)
        status_update:  'half_day' when total_hours < half of expected day,
                        'holiday' when clocked in on a public holiday,
                        '' otherwise
        """
        delta = clock_out - clock_in
        total_hours = round(delta.total_seconds() / 3600, 2)

        if is_holiday:
            ot_pay_hours = round(total_hours * holiday_multiplier, 2)
            status_update = "holiday"
        else:
            raw_ot = max(0.0, total_hours - daily_ot_threshold)
            ot_pay_hours = round(raw_ot * daily_ot_multiplier, 2)
            status_update = "half_day" if total_hours < (work_hours_per_day / 2) else ""

        return total_hours, ot_pay_hours, status_update
