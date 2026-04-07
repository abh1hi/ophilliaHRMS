"""Soft integration with leave-service for LOP (Loss of Pay) data.

Fetches leave/LOP summary from leave-service via internal HTTP API.
On timeout/error: gracefully fallback to lop_days=0 with warning flag.
Never blocks payroll processing on leave-service availability.
"""
import logging
from decimal import Decimal
from datetime import date, datetime, timezone
from typing import Dict, Optional, Tuple

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Internal service token for inter-service auth
INTERNAL_TOKEN = settings.INTERNAL_SERVICE_TOKEN
LEAVE_SERVICE_BASE_URL = settings.LEAVE_SERVICE_URL

# ── Guard: External Service Timeout ──────────────────────────────────────
# Prevent payroll from hanging on leave-service unavailability.
# If leave-service doesn't respond within 2 seconds, gracefully fallback.
LEAVE_SERVICE_TIMEOUT = 2.0  # seconds


async def fetch_lop_summary(
    employee_id: str,
    period_start: date,
    period_end: date,
    company_id: str,
) -> Tuple[int, str, Optional[Dict]]:
    """Fetch LOP (Loss of Pay) summary from leave-service.

    Args:
        employee_id: Employee UUID as string
        period_start: Period start date
        period_end: Period end date
        company_id: Company UUID as string

    Returns:
        Tuple of (lop_days: int, status: str, detail: Optional[Dict])
        status = "OK" | "UNAVAILABLE" | "ERROR"
        detail = full response from leave-service (if OK)
    """
    try:
        url = f"{LEAVE_SERVICE_BASE_URL}/api/v1/internal/lop-summary"
        headers = {
            "x-internal-token": INTERNAL_TOKEN,
            "x-company-id": company_id,
        }
        params = {
            "employee_id": employee_id,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
        }

        async with httpx.AsyncClient(timeout=LEAVE_SERVICE_TIMEOUT) as client:
            resp = await client.get(url, headers=headers, params=params)

            if resp.status_code == 200:
                data = resp.json()
                lop_days = int(data.get("lop_days", 0))
                return lop_days, "OK", data

            elif resp.status_code == 404:
                # Employee not found or no leave data
                logger.warning(
                    f"LOP data not found for employee {employee_id} in period {period_start}-{period_end}",
                    extra={"service": "payroll", "integration": "leave-service"},
                )
                return 0, "OK", None

            else:
                logger.warning(
                    f"Leave-service returned {resp.status_code}: {resp.text[:200]}",
                    extra={"service": "payroll", "integration": "leave-service"},
                )
                return 0, "UNAVAILABLE", None

    except httpx.TimeoutException:
        logger.warning(
            f"Leave-service timeout (>{LEAVE_SERVICE_TIMEOUT}s) for employee {employee_id}",
            extra={"service": "payroll", "integration": "leave-service"},
        )
        return 0, "UNAVAILABLE", None

    except httpx.RequestError as e:
        logger.warning(
            f"Leave-service connection error: {str(e)[:100]}",
            extra={"service": "payroll", "integration": "leave-service"},
        )
        return 0, "UNAVAILABLE", None

    except Exception as e:
        logger.exception(
            f"Unexpected error fetching LOP data: {str(e)[:100]}",
            extra={"service": "payroll", "integration": "leave-service"},
        )
        return 0, "ERROR", None


def pro_rata_factor(
    effective_from: date,
    period_start: date,
    period_end: date,
) -> Decimal:
    """Calculate pro-rata factor for salary when employee joins mid-month.

    Pro-ration applies only if employee's effective_from date is AFTER period_start.

    Args:
        effective_from: Employee salary effective date (joining/revision date)
        period_start: Payroll period start
        period_end: Payroll period end

    Returns:
        Pro-rata factor (Decimal between 0.0000 and 1.0000)
        - 1.0000 if effective_from <= period_start (full month)
        - Decimal fraction if effective_from is within the period
        - Formula: days_worked / calendar_days_in_period

    Example:
        Employee joins on 20th of a 30-day month
        → pro_rata_factor = (30 - 20 + 1) / 30 = 0.3667
    """
    if effective_from <= period_start:
        return Decimal("1.0000")

    if effective_from > period_end:
        # Employee hasn't joined yet for this period
        return Decimal("0.0000")

    # Calculate calendar days in period
    calendar_days = (period_end - period_start).days + 1

    # Calculate working days (from effective_from to period_end, inclusive)
    working_days = (period_end - effective_from).days + 1

    factor = Decimal(str(working_days)) / Decimal(str(calendar_days))
    return factor.quantize(Decimal("0.0001"))


def lop_deduction(
    monthly_gross: Decimal,
    lop_days: int,
    period_days: int,
    method: str = "CALENDAR",
) -> Decimal:
    """Calculate LOP (Loss of Pay) deduction amount.

    Args:
        monthly_gross: Gross salary for the month (after pro-ration if applicable)
        lop_days: Number of LOP days
        period_days: Calendar days in the period (typically 30 or 31)
        method: LOP calculation method
            - "CALENDAR": lop_amount = monthly_gross / period_days * lop_days
            - "WORKING": lop_amount = monthly_gross / working_days * lop_days
            - "FIXED_30": lop_amount = monthly_gross / 30 * lop_days

    Returns:
        LOP deduction amount (rounded to 2 decimals)

    Example:
        monthly_gross = ₹30,000, lop_days = 2, period_days = 30
        → lop_deduction = 30,000 / 30 * 2 = ₹2,000
    """
    if lop_days <= 0:
        return Decimal("0.00")

    if method == "CALENDAR":
        per_day = monthly_gross / Decimal(str(period_days))
    elif method == "WORKING":
        # Assume 26 working days in a month (52 weeks * 5 days / 12)
        per_day = monthly_gross / Decimal("26")
    elif method == "FIXED_30":
        per_day = monthly_gross / Decimal("30")
    else:
        raise ValueError(f"Unknown LOP method: {method}")

    deduction = per_day * Decimal(str(lop_days))
    return deduction.quantize(Decimal("0.01"))


def calendar_days_in_period(period_start: date, period_end: date) -> int:
    """Calculate number of calendar days in period (inclusive).

    Args:
        period_start: Start date
        period_end: End date

    Returns:
        Number of days (inclusive of both start and end)

    Example:
        April 1 - April 30 → 30 days
        April 1 - May 1 → 31 days
    """
    return (period_end - period_start).days + 1


def working_days_in_period(
    period_start: date,
    period_end: date,
    holidays: Optional[list] = None,
) -> int:
    """Calculate number of working days (Mon-Fri) in period.

    Args:
        period_start: Start date
        period_end: End date
        holidays: Optional list of holiday dates to exclude

    Returns:
        Number of working days (excluding Saturdays, Sundays, and holidays)

    Example:
        If April 2025 has 22 working days and 8 weekend days
        → returns 22
    """
    current = period_start
    working_days = 0
    holidays_set = set(holidays) if holidays else set()

    while current <= period_end:
        # Weekday: Monday=0, ..., Sunday=6
        if current.weekday() < 5 and current not in holidays_set:
            working_days += 1
        current = date(current.year, current.month, current.day + 1) if current.day < 31 else date(current.year, current.month + 1, 1)

    return working_days


# ──────────────────────────────────────────────────────────────────────
# VALIDATION & DEBUGGING
# ──────────────────────────────────────────────────────────────────────

def validate_pro_rata(
    effective_from: date,
    period_start: date,
    period_end: date,
    monthly_gross: Decimal,
) -> Dict:
    """Debug helper: validate pro-rata calculation.

    Returns dict with all intermediate values.
    """
    prf = pro_rata_factor(effective_from, period_start, period_end)
    prorated_gross = monthly_gross * prf

    return {
        "effective_from": effective_from.isoformat(),
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "calendar_days": calendar_days_in_period(period_start, period_end),
        "pro_rata_factor": str(prf),
        "original_gross": str(monthly_gross),
        "prorated_gross": str(prorated_gross),
    }


def validate_lop(
    monthly_gross: Decimal,
    lop_days: int,
    period_days: int,
    method: str = "CALENDAR",
) -> Dict:
    """Debug helper: validate LOP calculation.

    Returns dict with all intermediate values.
    """
    deduction = lop_deduction(monthly_gross, lop_days, period_days, method)
    net_after_lop = monthly_gross - deduction

    return {
        "monthly_gross": str(monthly_gross),
        "lop_days": lop_days,
        "period_days": period_days,
        "method": method,
        "per_day_rate": str(monthly_gross / Decimal(str(period_days))),
        "lop_deduction": str(deduction),
        "net_after_lop": str(net_after_lop),
    }
