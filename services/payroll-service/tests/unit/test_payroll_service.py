"""Unit tests for PayrollService and salary calculator."""
import pytest, uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.calculators.base import BaseSalaryCalculator, SalaryBreakdown
from app.services.payroll_service import PayrollService
from app.core.constants import PayrollStatus


def test_calculator_basic_breakdown():
    calc = BaseSalaryCalculator()
    result = calc.calculate(
        ctc=Decimal("1200000"), basic_pct=Decimal("50"), hra_pct=Decimal("20"),
        allowances_pct=Decimal("15"), pf_pct=Decimal("12"), esi_pct=Decimal("1.75"),
        professional_tax=Decimal("200"),
    )
    assert isinstance(result, SalaryBreakdown)
    monthly = Decimal("1200000") / 12
    assert result.basic == (monthly * 50 / 100).quantize(Decimal("0.01"))
    assert result.net == result.gross - result.total_deductions
    assert result.net > 0


def test_calculator_esi_not_applied_for_high_salary():
    calc = BaseSalaryCalculator()
    result = calc.calculate(
        ctc=Decimal("600000"), basic_pct=Decimal("50"), hra_pct=Decimal("20"),
        allowances_pct=Decimal("15"), pf_pct=Decimal("12"), esi_pct=Decimal("1.75"),
        professional_tax=Decimal("200"),
    )
    # gross > 21000 → ESI should be 0
    assert result.esi_deduction == Decimal("0.00")


def test_calculator_pf_capped_at_15000():
    calc = BaseSalaryCalculator()
    # high CTC → basic > 15000 → PF capped at 12% of 15000
    result = calc.calculate(
        ctc=Decimal("2400000"), basic_pct=Decimal("50"), hra_pct=Decimal("20"),
        allowances_pct=Decimal("15"), pf_pct=Decimal("12"), esi_pct=Decimal("0"),
        professional_tax=Decimal("200"),
    )
    expected_pf = (Decimal("15000") * 12 / 100).quantize(Decimal("0.01"))
    assert result.pf_deduction == expected_pf


@pytest.mark.asyncio
async def test_payroll_run_idempotency():
    """Duplicate payroll run for same period should raise ValueError."""
    from app.schemas.payroll import PayrollRunCreate
    from datetime import date

    db = AsyncMock()
    service = PayrollService(db)

    with patch.object(service.repo, "create_payroll_run", side_effect=Exception("uq_payroll_run_company_period")):
        with pytest.raises(ValueError, match="Payroll already exists"):
            await service.run_payroll(
                PayrollRunCreate(period_start=date(2026, 3, 1), period_end=date(2026, 3, 31)),
                processed_by=uuid.uuid4(),
            )
