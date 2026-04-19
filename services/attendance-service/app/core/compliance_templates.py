"""Pre-built OvertimePolicy configuration dicts for India and EU jurisdictions.

These are pure data constants — no DB access, no logic.
Pass to OvertimeService.create_from_template() to seed a company's OT rules.
"""

INDIA_FACTORIES_ACT: dict = {
    "jurisdiction": "INDIA",
    "compliance_profile": "INDIA_FACTORIES_ACT",
    "daily_ot_threshold_hours": 9.0,
    "weekly_ot_threshold_hours": 48.0,
    "max_daily_hours": 12.0,
    "daily_ot_multiplier": 2.0,
    "weekly_ot_multiplier": 2.0,
    "weekend_multiplier": 2.0,
    "holiday_multiplier": 2.0,
    "prefer_comp_off": False,
    "comp_off_ratio": 1.0,
}

EU_WORKING_TIME_DIRECTIVE: dict = {
    "jurisdiction": "EU",
    "compliance_profile": "EU_WTD_48H",
    "daily_ot_threshold_hours": 10.0,
    "weekly_ot_threshold_hours": 48.0,
    "max_daily_hours": 13.0,
    "daily_ot_multiplier": 1.25,
    "weekly_ot_multiplier": 1.5,
    "weekend_multiplier": 1.5,
    "holiday_multiplier": 1.5,
    "prefer_comp_off": True,
    "comp_off_ratio": 1.5,
}

COMPLIANCE_TEMPLATES: dict[str, dict] = {
    "INDIA_FACTORIES_ACT": INDIA_FACTORIES_ACT,
    "EU_WTD_48H": EU_WORKING_TIME_DIRECTIVE,
}
