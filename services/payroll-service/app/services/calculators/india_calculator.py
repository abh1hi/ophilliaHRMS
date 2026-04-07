"""India-specific salary calculator with TDS, PT, PF, ESI, LWF compliance."""
from decimal import Decimal
from typing import Optional

from app.services.calculators.base import BaseSalaryCalculator, SalaryBreakdown
from app.services.tax.india.tds import compute_monthly_tds
from app.services.tax.india.pt_rules import compute_professional_tax
from app.core.constants import (
    PF_WAGE_CEILING,
    PF_EMPLOYEE_PCT,
    PF_EMPLOYER_EPF_PCT,
    PF_EMPLOYER_EPS_PCT,
    PF_EMPLOYER_FIXED_PCT,
    PF_EMPLOYER_MAX_EPS,
    ESI_GROSS_CEILING,
    ESI_EMPLOYEE_PCT,
    ESI_EMPLOYER_PCT,
)


class IndiaSalaryCalculator(BaseSalaryCalculator):
    """Concrete calculator for India payroll with statutory compliance.

    Implements:
    - PF: 12% of basic (capped at ₹15,000)
    - ESI: 0.75% if gross ≤ ₹21,000
    - Professional Tax: State-wise slabs
    - TDS: Progressive slabs with 87A rebate (new regime)
    - LWF: State-wise rates (Phase 2 extension)

    Does NOT handle pro-ration or LOP here — those are applied in payroll_service layer.
    """

    def __init__(self, state_code: str = "MH", tax_regime: str = "new"):
        """Initialize India calculator with state and tax regime.

        Args:
            state_code: Two-letter state code (e.g., "MH", "KA", "DL")
            tax_regime: "old" or "new" (default "new")
        """
        self.state_code = state_code
        self.tax_regime = tax_regime

    def calculate_pf(self, basic: Decimal, pf_pct: Decimal) -> Decimal:
        """PF deduction: 12% of basic, capped at ₹15,000 basic.

        India statutory rule: Max wage subject to PF is ₹15,000/month.
        """
        capped_basic = min(basic, Decimal(str(PF_WAGE_CEILING)))
        pf = (capped_basic * PF_EMPLOYEE_PCT / 100).quantize(Decimal("0.01"))
        return pf

    def calculate_esi(self, gross: Decimal, esi_pct: Decimal) -> Decimal:
        """ESI deduction: 0.75% only if gross ≤ ₹21,000/month.

        India statutory rule: No ESI if gross > ₹21,000.
        """
        if gross > Decimal(str(ESI_GROSS_CEILING)):
            return Decimal("0.00")
        esi = (gross * ESI_EMPLOYEE_PCT / 100).quantize(Decimal("0.01"))
        return esi

    def calculate_professional_tax(self, pt_amount: Decimal, **kwargs) -> Decimal:
        """Professional Tax: State-wise, from pt_rules.py.

        Args:
            pt_amount: Ignored (kept for signature compatibility)
            **kwargs: Optional month, gender for state-specific rules

        Returns:
            Computed PT amount
        """
        # Extract optional parameters
        gross = kwargs.get("gross", Decimal("0.00"))
        month = kwargs.get("month", 1)
        gender = kwargs.get("gender", "M")

        pt, reason = compute_professional_tax(
            gross_salary=gross,
            state_code=self.state_code,
            month=month,
            gender=gender,
        )
        return pt

    def calculate_employer_pf(self, basic: Decimal) -> Decimal:
        """Employer PF contributions: EPF (3.67%) + EPS (8.33%, capped ₹1,250) + Fixed (1%).

        Wage ceiling: ₹15,000/month basic+DA.
        """
        capped_basic = min(basic, Decimal(str(PF_WAGE_CEILING)))

        # EPF: 3.67%
        epf = (capped_basic * PF_EMPLOYER_EPF_PCT / 100).quantize(Decimal("0.01"))

        # EPS: 8.33% but capped at ₹1,250
        eps_uncapped = (capped_basic * PF_EMPLOYER_EPS_PCT / 100).quantize(Decimal("0.01"))
        eps = min(eps_uncapped, Decimal(str(PF_EMPLOYER_MAX_EPS)))

        # Fixed: 1%
        fixed = (capped_basic * PF_EMPLOYER_FIXED_PCT / 100).quantize(Decimal("0.01"))

        total_pf = (epf + eps + fixed).quantize(Decimal("0.01"))
        return total_pf

    def calculate_employer_esi(self, gross: Decimal) -> Decimal:
        """Employer ESI: 3.25% if gross ≤ ₹21,000.

        India statutory rule: No ESI if gross > ₹21,000.
        """
        if gross > Decimal(str(ESI_GROSS_CEILING)):
            return Decimal("0.00")
        esi = (gross * ESI_EMPLOYER_PCT / 100).quantize(Decimal("0.01"))
        return esi

    def calculate_tds(
        self,
        monthly_gross: Decimal,
        ytd_gross: Decimal,
        ytd_tds: Decimal,
        current_month: int,
    ) -> Decimal:
        """TDS: Progressive slabs with 87A rebate (new regime only).

        Args:
            monthly_gross: Current month gross
            ytd_gross: Year-to-date gross (excluding current month)
            ytd_tds: Year-to-date TDS already withheld
            current_month: Current month (1-12)

        Returns:
            Monthly TDS amount
        """
        if self.tax_regime != "new":
            raise NotImplementedError("Old regime TDS in Phase 2 extension")

        tds = compute_monthly_tds(
            monthly_gross=monthly_gross,
            ytd_gross=ytd_gross,
            ytd_tds=ytd_tds,
            current_month=current_month,
            fy_end_month=3,  # March for Indian FY
        )
        return tds

    def calculate_lwf(
        self,
        gross: Decimal,
        state_code: Optional[str] = None,
        month: Optional[int] = None,
    ) -> Decimal:
        """Labour Welfare Fund (LWF): State-wise, half-yearly or monthly.

        Phase 2 extension: implement state-wise LWF rules.
        For now: return ₹0.
        """
        # Placeholder for Phase 2 extension
        return Decimal("0.00")

    def calculate_with_tds(
        self,
        ctc: Decimal,
        basic_pct: Decimal,
        hra_pct: Decimal,
        allowances_pct: Decimal,
        pf_pct: Decimal,
        esi_pct: Decimal,
        professional_tax: Decimal,
        ytd_gross: Decimal = Decimal("0.00"),
        ytd_tds: Decimal = Decimal("0.00"),
        current_month: int = 1,
        month_for_pt: int = 1,
        gender: str = "M",
    ) -> dict:
        """Calculate full salary breakdown including TDS.

        This is the main method for payroll processing.

        Args:
            ctc: Annual CTC
            basic_pct: Basic as % of CTC
            hra_pct: HRA as % of CTC
            allowances_pct: Allowances as % of CTC
            pf_pct: PF percentage (ignored; uses statutory ₹15K cap)
            esi_pct: ESI percentage (ignored; uses statutory ₹21K limit)
            professional_tax: Ignored; uses state-wise slabs
            ytd_gross: Year-to-date gross (for TDS calculation)
            ytd_tds: Year-to-date TDS (for TDS calculation)
            current_month: Current month (1-12)
            month_for_pt: Month for PT surcharge (default = current_month)
            gender: "M" or "F" for PT female exemption

        Returns:
            Dict with earnings, deductions, employer contributions
        """
        # Base calculation (earnings breakdown)
        base = self.calculate(ctc, basic_pct, hra_pct, allowances_pct, pf_pct, esi_pct, professional_tax)

        # Override with statutory deductions
        monthly_ctc = ctc / 12
        basic = (monthly_ctc * basic_pct / 100).quantize(Decimal("0.01"))
        gross = base.gross

        # Recalculate with India rules
        pf_employee = self.calculate_pf(basic, Decimal(str(PF_EMPLOYEE_PCT)))
        esi_employee = self.calculate_esi(gross, Decimal(str(ESI_EMPLOYEE_PCT)))
        pt_employee = self.calculate_professional_tax(
            professional_tax,
            gross=gross,
            month=month_for_pt,
            gender=gender,
        )
        tds = self.calculate_tds(gross, ytd_gross, ytd_tds, current_month)
        lwf = self.calculate_lwf(gross, self.state_code, current_month)

        # Employer contributions
        pf_employer = self.calculate_employer_pf(basic)
        esi_employer = self.calculate_employer_esi(gross)

        # Recalculate totals
        total_deductions = pf_employee + esi_employee + pt_employee + tds + lwf
        net_salary = gross - total_deductions

        return {
            "ctc": ctc,
            "monthly_ctc": monthly_ctc,
            "earnings": {
                "basic": base.basic,
                "hra": base.hra,
                "allowances": base.allowances,
                "gross": gross,
            },
            "employee_deductions": {
                "pf": pf_employee,
                "esi": esi_employee,
                "professional_tax": pt_employee,
                "tds": tds,
                "lwf": lwf,
                "total": total_deductions,
            },
            "employer_contributions": {
                "pf": pf_employer,
                "esi": esi_employer,
                "lwf": Decimal("0.00"),  # Placeholder
                "total": pf_employer + esi_employer,
            },
            "net_salary": net_salary,
            "ytd_before_tds": ytd_tds,
            "ytd_after_tds": ytd_tds + tds,
        }
