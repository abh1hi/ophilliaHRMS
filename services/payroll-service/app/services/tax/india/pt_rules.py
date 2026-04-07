"""India Professional Tax (PT) Rules — State-wise calculations.

PT is a state-specific tax levied on employment income.
Rules vary by state: Maharashtra has monthly collection, Tamil Nadu has half-yearly, etc.
Female exemptions and February surcharge also vary by state.

All amounts in ₹, percentage in decimal form.
"""
from decimal import Decimal
from typing import Dict, Optional, Tuple


# ──────────────────────────────────────────────────────────────────────────
# STATE-WISE PT RULES (FY 2025-26)
# ──────────────────────────────────────────────────────────────────────────

PT_RULES = {
    # MAHARASHTRA: Monthly collection, February surcharge ₹100, female ≤ ₹25K exempt
    "MH": {
        "type": "monthly",
        "slabs": [
            (Decimal("7500"), Decimal("0")),        # Nil up to ₹7,500
            (Decimal("10000"), Decimal("175")),     # ₹175 from ₹7,501 to ₹10,000
            (Decimal("999999999"), Decimal("200")), # ₹200 above ₹10,000
        ],
        "february_extra": Decimal("100"),
        "female_exemption_limit": Decimal("25000"),
    },

    # KARNATAKA: Monthly collection, February surcharge ₹100
    "KA": {
        "type": "monthly",
        "slabs": [
            (Decimal("24999"), Decimal("0")),       # Nil up to ₹24,999
            (Decimal("999999999"), Decimal("200")), # ₹200 from ₹25,000 onwards
        ],
        "february_extra": Decimal("100"),
        "female_exemption_limit": None,
    },

    # TAMIL NADU: Half-yearly collection (Apr-Sep, Oct-Mar)
    "TN": {
        "type": "half_yearly",
        "slabs": [
            (Decimal("21000"), Decimal("0")),
            (Decimal("30000"), Decimal("600")),
            (Decimal("45000"), Decimal("1410")),
            (Decimal("60000"), Decimal("3060")),
            (Decimal("75000"), Decimal("4560")),
            (Decimal("999999999"), Decimal("6570")),
        ],
        "february_extra": None,
        "female_exemption_limit": None,
    },

    # ANDHRA PRADESH: Monthly collection
    "AP": {
        "type": "monthly",
        "slabs": [
            (Decimal("15000"), Decimal("0")),
            (Decimal("20000"), Decimal("150")),
            (Decimal("999999999"), Decimal("200")),
        ],
        "february_extra": None,
        "female_exemption_limit": None,
    },

    # WEST BENGAL: Monthly collection
    "WB": {
        "type": "monthly",
        "slabs": [
            (Decimal("10000"), Decimal("0")),
            (Decimal("15000"), Decimal("110")),
            (Decimal("25000"), Decimal("130")),
            (Decimal("40000"), Decimal("150")),
            (Decimal("999999999"), Decimal("200")),
        ],
        "february_extra": None,
        "female_exemption_limit": None,
    },

    # DELHI (NCT): No PT
    "DL": None,

    # TELANGANA: Monthly collection
    "TS": {
        "type": "monthly",
        "slabs": [
            (Decimal("15000"), Decimal("0")),
            (Decimal("20000"), Decimal("150")),
            (Decimal("999999999"), Decimal("200")),
        ],
        "february_extra": None,
        "female_exemption_limit": None,
    },

    # UTTAR PRADESH: Monthly collection
    "UP": {
        "type": "monthly",
        "slabs": [
            (Decimal("15000"), Decimal("0")),
            (Decimal("20000"), Decimal("150")),
            (Decimal("999999999"), Decimal("200")),
        ],
        "february_extra": None,
        "female_exemption_limit": None,
    },

    # PUNJAB: Monthly collection
    "PB": {
        "type": "monthly",
        "slabs": [
            (Decimal("20000"), Decimal("0")),
            (Decimal("25000"), Decimal("150")),
            (Decimal("999999999"), Decimal("200")),
        ],
        "february_extra": None,
        "female_exemption_limit": None,
    },

    # HARYANA: Monthly collection
    "HR": {
        "type": "monthly",
        "slabs": [
            (Decimal("15000"), Decimal("0")),
            (Decimal("20000"), Decimal("150")),
            (Decimal("999999999"), Decimal("200")),
        ],
        "february_extra": None,
        "female_exemption_limit": None,
    },

    # RAJASTHAN: Monthly collection
    "RJ": {
        "type": "monthly",
        "slabs": [
            (Decimal("15000"), Decimal("0")),
            (Decimal("20000"), Decimal("150")),
            (Decimal("999999999"), Decimal("200")),
        ],
        "february_extra": None,
        "female_exemption_limit": None,
    },

    # MADHYA PRADESH: Monthly collection
    "MP": {
        "type": "monthly",
        "slabs": [
            (Decimal("15000"), Decimal("0")),
            (Decimal("20000"), Decimal("150")),
            (Decimal("999999999"), Decimal("200")),
        ],
        "february_extra": None,
        "female_exemption_limit": None,
    },

    # BIHAR: Monthly collection (no PT)
    "BR": None,

    # ODISHA: Monthly collection (no PT in many cases)
    "OD": {
        "type": "monthly",
        "slabs": [
            (Decimal("10000"), Decimal("0")),
            (Decimal("15000"), Decimal("50")),
            (Decimal("20000"), Decimal("100")),
            (Decimal("999999999"), Decimal("200")),
        ],
        "february_extra": None,
        "female_exemption_limit": None,
    },

    # ASSAM: Monthly collection
    "AS": {
        "type": "monthly",
        "slabs": [
            (Decimal("15000"), Decimal("0")),
            (Decimal("20000"), Decimal("150")),
            (Decimal("999999999"), Decimal("200")),
        ],
        "february_extra": None,
        "female_exemption_limit": None,
    },

    # KERALA: Monthly collection
    "KL": {
        "type": "monthly",
        "slabs": [
            (Decimal("15000"), Decimal("0")),
            (Decimal("20000"), Decimal("150")),
            (Decimal("999999999"), Decimal("200")),
        ],
        "february_extra": None,
        "female_exemption_limit": None,
    },

    # Gujarat: Monthly collection
    "GJ": {
        "type": "monthly",
        "slabs": [
            (Decimal("15000"), Decimal("0")),
            (Decimal("20000"), Decimal("150")),
            (Decimal("999999999"), Decimal("200")),
        ],
        "february_extra": None,
        "female_exemption_limit": None,
    },
}


def compute_professional_tax(
    gross_salary: Decimal,
    state_code: str,
    month: int,  # 1-12
    gender: str = "M",  # M / F
) -> Tuple[Decimal, str]:
    """Compute monthly Professional Tax (PT) for given state and salary.

    Args:
        gross_salary: Monthly gross salary (earnings, not CTC)
        state_code: Two-letter state code (e.g., "MH", "KA", "TN")
        month: Month number (1=Jan, 2=Feb, ..., 12=Dec)
        gender: "M" (male) or "F" (female) for exemption eligibility

    Returns:
        Tuple of (pt_amount, reason)
        reason = "OK" | "NO_PT" | "FEMALE_EXEMPT" | "UNKNOWN_STATE"
    """
    # Handle unknown or no-PT states
    if state_code not in PT_RULES:
        return Decimal("0.00"), "UNKNOWN_STATE"

    rules = PT_RULES[state_code]
    if rules is None:
        return Decimal("0.00"), "NO_PT"

    # Check female exemption (if applicable for state & gross <= limit)
    female_limit = rules.get("female_exemption_limit")
    if gender == "F" and female_limit and gross_salary <= female_limit:
        return Decimal("0.00"), "FEMALE_EXEMPT"

    # Apply slabs
    pt_amount = Decimal("0.00")
    for slab_limit, slab_amount in rules["slabs"]:
        if gross_salary <= slab_limit:
            pt_amount = slab_amount
            break

    # Add February surcharge if applicable
    if month == 2 and rules.get("february_extra"):
        pt_amount += rules["february_extra"]

    return pt_amount.quantize(Decimal("0.01")), "OK"


def get_pt_collection_schedule(state_code: str) -> Optional[str]:
    """Get PT collection schedule for a state.

    Returns:
        "monthly" | "half_yearly" | "quarterly" | "annual" | None
    """
    rules = PT_RULES.get(state_code)
    if rules is None:
        return None
    return rules.get("type")


def get_pt_annual_cap(state_code: str) -> Decimal:
    """Get annual PT cap for a state (default ₹2,500 across India).

    Returns:
        Annual PT cap in ₹
    """
    rules = PT_RULES.get(state_code)
    if rules is None:
        return Decimal("0.00")

    # Default cap: ₹2,500 per year
    # For half-yearly states like TN, cap per collection period would be ₹1,250
    if rules.get("type") == "half_yearly":
        return Decimal("1250.00")  # Per half-year (April-Sep, Oct-Mar)

    return Decimal("2500.00")  # Per financial year


# ──────────────────────────────────────────────────────────────────────────
# DEBUGGING & VALIDATION
# ──────────────────────────────────────────────────────────────────────────

def list_all_states() -> Dict[str, str]:
    """List all supported states with their PT status.

    Returns:
        Dict mapping state_code -> description
    """
    descriptions = {
        "MH": "Maharashtra (Monthly, Female exempt ≤₹25K)",
        "KA": "Karnataka (Monthly)",
        "TN": "Tamil Nadu (Half-yearly)",
        "AP": "Andhra Pradesh (Monthly)",
        "WB": "West Bengal (Monthly)",
        "DL": "Delhi NCT (No PT)",
        "TS": "Telangana (Monthly)",
        "UP": "Uttar Pradesh (Monthly)",
        "PB": "Punjab (Monthly)",
        "HR": "Haryana (Monthly)",
        "RJ": "Rajasthan (Monthly)",
        "MP": "Madhya Pradesh (Monthly)",
        "BR": "Bihar (No PT)",
        "OD": "Odisha (Monthly)",
        "AS": "Assam (Monthly)",
        "KL": "Kerala (Monthly)",
        "GJ": "Gujarat (Monthly)",
    }
    return descriptions
