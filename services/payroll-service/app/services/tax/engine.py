"""Tax calculation engine dispatcher.

Routes to country/region-specific tax calculators.
Currently: India (new regime)
"""
from decimal import Decimal
from typing import Dict, Optional

from app.services.calculators.india_calculator import IndiaSalaryCalculator


class TaxEngine:
    """Main tax calculation engine with regional dispatch."""

    def __init__(self, country: str = "IN", state_code: str = "MH", tax_regime: str = "new"):
        """Initialize tax engine.

        Args:
            country: Country code (e.g., "IN" for India)
            state_code: State code for India (e.g., "MH", "KA")
            tax_regime: Tax regime ("old" or "new", default "new")
        """
        self.country = country
        self.state_code = state_code
        self.tax_regime = tax_regime

        # Instantiate country-specific calculator
        if country == "IN":
            self.calculator = IndiaSalaryCalculator(state_code=state_code, tax_regime=tax_regime)
        else:
            raise ValueError(f"Unsupported country: {country}")

    def compute_payroll(
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
        gender: str = "M",
    ) -> Dict:
        """Compute full payroll with TDS, PT, PF, ESI.

        Args:
            ctc: Annual CTC
            basic_pct: Basic as % of CTC
            hra_pct: HRA as % of CTC
            allowances_pct: Allowances as % of CTC
            pf_pct: PF percentage (statutory for India)
            esi_pct: ESI percentage (statutory for India)
            professional_tax: PT flat amount (ignored; state-wise slabs used)
            ytd_gross: Year-to-date gross (for TDS)
            ytd_tds: Year-to-date TDS (for TDS)
            current_month: Current month (1-12)
            gender: "M" or "F" for gender-specific exemptions

        Returns:
            Dict with earnings, deductions, employer contributions, net
        """
        return self.calculator.calculate_with_tds(
            ctc=ctc,
            basic_pct=basic_pct,
            hra_pct=hra_pct,
            allowances_pct=allowances_pct,
            pf_pct=pf_pct,
            esi_pct=esi_pct,
            professional_tax=professional_tax,
            ytd_gross=ytd_gross,
            ytd_tds=ytd_tds,
            current_month=current_month,
            month_for_pt=current_month,
            gender=gender,
        )


def get_tax_engine(country: str = "IN", state_code: str = "MH", tax_regime: str = "new") -> TaxEngine:
    """Factory function to get tax engine for a region.

    Args:
        country: Country code (default "IN")
        state_code: State code (default "MH")
        tax_regime: Tax regime (default "new")

    Returns:
        Configured TaxEngine instance
    """
    return TaxEngine(country=country, state_code=state_code, tax_regime=tax_regime)
