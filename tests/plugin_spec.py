"""The handbook-specific settings the template's acceptance tests read. Every other file in tests/ is the
template's and stays identical across plugins (see TEMPLATE_GUIDE.md)."""

from pathlib import Path

import contract

ROOT = Path(__file__).resolve().parents[1]

# Ids that are published or taken: a new plugin never reuses one (MASTER_PLAN section 4, "id check").
PUBLISHED_IDS = {
    "aiib-delegation-entitlement", "ec-mission-cabin-allowance", "ftr-city-pair-fare-selection",
    "gates-vendor-flight-ranking", "njc-cabin-meal-allowance", "sfc-travel-preapproval", "uc-g28-expense-audit",
    "un-staff-air-travel-audit", "vt-airfare-policy-booking", "wa-saam-travel-versioned-audit",
    "energy-corporate-flight-booking", "pharma-distributor-flight-booking", "shipping-company-flight-booking",
    "telecommunications-flight-booking", "preference-aware-flight-booking", "llm-context-compress",
    "weather-alert", "word-check", "arxiv-source",
}

# The frozen original's SHA256SUMS, when this checkout sits beside pilot_work/ (skipped elsewhere).
FROZEN_SHA256SUMS = ROOT.parents[1] / "pilot_work" / "originals" / "uk-dbt" / "frozen" / "SHA256SUMS"

# Scenario mix by primary category (EDGE_CASES.md section 5.2; the 16-scenario row).
MIX = {"easy": 3, "boundary_twin": 4, "multi_rule": 3, "hidden_clause": 2, "distractor": 1, "refusal": 1, "flag": 2}

# Overlay minimums (EDGE_CASES.md section 5.3) for the rules this handbook has. It has no rule on several
# travellers on one flight and none on overnight stops, so neither overlay is required.
OVERLAY_MINIMUMS = {
    "multi_leg": 3, "date_arithmetic": 2, "month_end": 1, "personal_travel": 1,
    "dearer_option": 2, "upgrade_not_taken": 2, "outside_air_section": 2,
}

# Words a scenario id may not contain beyond the template's universal list: this handbook's rule and role
# terms.
ID_FORBIDDEN_TERMS = {
    "expo", "osaka", "japan", "tokyo", "supplier", "contract", "manager", "director", "commercial", "personal",
    "leisure", "weekend", "home", "rail", "train", "domestic", "scotland", "open", "return", "loyalty", "points",
    "miles", "quote", "quotes", "screenshot", "class", "first", "premium", "business", "economy", "lowest",
    "logical", "fare", "taxi", "carbon", "green", "medical", "disability", "arrival", "seats", "authority",
    "form", "approval", "nonstop", "connection", "via",
}

# The handbook-specific enums whose member words a scenario id may not contain either.
ID_CATEGORY_ENUMS = [contract.TripKind, contract.SignOffSubject]

# How many scenarios a degenerate agent may pass: one that always holds the right offer for approval, and
# one that always books the cheapest seat (with the right section).
MAX_PASS_ALWAYS_FLAG = 1
MAX_PASS_ALWAYS_LOWEST = 6

# Hand-built duration cases beyond the automatic both-sides tests: (rule, outbound scheduled minutes per
# flight, layovers, expected True / False / None for unclear).
DURATION_CASES = [
    ("over-five", [300], [], False),  # "Up to 5 hours" is inclusive; "Over 5 hours" strict
    ("over-five", [301], [], True),
    ("over-five", [405, 590], [150], True),  # every flight over 5 hours
    ("over-five", [200, 200], [60], False),  # never added together
    ("over-five", [765, 240], [110], None),  # one flight over, one not: unclear
    ("over-ten", [600], [], False),
    ("over-ten", [601], [], True),
    ("over-ten", [405, 590], [150], False),  # flights add to 995 but each is 10 hours or less
    ("over-ten", [85, 825], [145], None),
    ("over-ten", [640, 610], [80], True),
]
