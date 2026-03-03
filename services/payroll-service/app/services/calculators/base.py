"""Base salary calculator — strategy pattern for region-specific payroll logic.

Subclass and override methods to implement country-specific calculations:
- PF rules (India: 12% of basic, capped at ₹15,000 basic)
- ESI rules (India: 0.75% employee contribution if gross < ₹21,000)
- Professional tax (varies by Indian state)
- Tax brackets (country-specific)

Default implementation = India standard.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class SalaryBreakdown:
    """Immutable salary breakdown — snapshot at time of calculation."""
    ctc: Decimal
    basic: Decimal
    hra: Decimal
    allowances: Decimal
    pf_deduction: Decimal
    esi_deduction: Decimal
    professional_tax: Decimal
    other_deductions: Decimal
    gross: Decimal
    total_deductions: Decimal
    net: Decimal


class BaseSalaryCalculator:
    """Strategy base class. Override methods to swap region-specific logic."""

    def calculate(
        self,
        ctc: Decimal,
        basic_pct: Decimal,
        hra_pct: Decimal,
        allowances_pct: Decimal,
        pf_pct: Decimal,
        esi_pct: Decimal,
        professional_tax: Decimal,
    ) -> SalaryBreakdown:
        """Calculate monthly salary breakdown from annual CTC and structure percentages."""
        monthly_ctc = (ctc / 12).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        basic = (monthly_ctc * basic_pct / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        hra = (monthly_ctc * hra_pct / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        allowances = (monthly_ctc * allowances_pct / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        gross = basic + hra + allowances

        pf = self.calculate_pf(basic, pf_pct)
        esi = self.calculate_esi(gross, esi_pct)
        pt = self.calculate_professional_tax(professional_tax)

        total_deductions = pf + esi + pt
        net = gross - total_deductions

        return SalaryBreakdown(
            ctc=ctc,
            basic=basic,
            hra=hra,
            allowances=allowances,
            pf_deduction=pf,
            esi_deduction=esi,
            professional_tax=pt,
            other_deductions=Decimal("0.00"),
            gross=gross,
            total_deductions=total_deductions,
            net=net,
        )

    def calculate_pf(self, basic: Decimal, pf_pct: Decimal) -> Decimal:
        """PF: percentage of basic (India: capped at basic ≤ ₹15,000)."""
        capped_basic = min(basic, Decimal("15000.00"))
        return (capped_basic * pf_pct / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_esi(self, gross: Decimal, esi_pct: Decimal) -> Decimal:
        """ESI: applicable only if gross ≤ ₹21,000/month (India rule)."""
        if gross > Decimal("21000.00"):
            return Decimal("0.00")
        return (gross * esi_pct / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_professional_tax(self, pt_amount: Decimal) -> Decimal:
        """Professional tax: flat per-state amount (capped at ₹2,500/year = ~₹200/month)."""
        return pt_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
