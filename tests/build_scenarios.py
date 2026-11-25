"""Writes the DBT supplier-travel scenario JSON files (an authoring aid, not a test; the JSON files are the truth).

    uv run python tests/build_scenarios.py

Expected answers are hand-written here; tests/test_scenarios.py checks them against rules.solve. Fares are in
pence (handbook.json currency GBP).
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

POLICY = (ROOT / "src/plugin/data/policy.txt").read_text(encoding="utf-8").split("\n")
OUT = ROOT / "src/plugin/data/scenarios"


def norm(text):
    return " ".join(text.split())


def keep(a, b, quote, why):
    text = norm(" ".join(POLICY[a - 1:b]))
    quote = text if quote is None else quote
    assert norm(quote) in text, (a, b, quote, text)
    return {"lines": [a, b], "sha256": hashlib.sha256(text.encode()).hexdigest(), "quote": quote, "why": why}


def aside(a, b, quote, why):
    text = norm(" ".join(POLICY[a - 1:b]))
    assert norm(quote) in text, (a, b, quote, text)
    return {"lines": [a, b], "quote": quote, "why": why}


# ----- clauses the answers rest on -----
LOWEST = keep(119, 119, None, "the default: the lowest logical fare")
TABLE = keep(131, 135, None, "the class of travel per flight: economy up to and over 5 hours, business over 10 hours "
             "with the Contract Manager's prior agreement")
FIRST_BAR = keep(137, 138, None, "the Director may allow the next higher class, but not first class")
NO_SEATS = keep(142, 143, None, "a listed ground: no seats in the lower class and the date cannot change")
WORK_ON_ARRIVAL = keep(144, 144, None, "a listed ground: work immediately on arrival")
SHORT_VISIT = keep(140, 141, None, "a listed ground that implies short flights: out and back in a working day")
OPEN = keep(146, 146, None, "set dates only; no open return tickets")
UK_AIR = keep(147, 149, None, "no air within the UK except to/from Scotland and Northern Ireland, in economy")
RAIL = keep(151, 152, "Domestic flights should only be taken when they are more economical than rail.",
            "a domestic flight only when more economical than rail")
LOYALTY = keep(107, 109, "Suppliers must not derive a benefit by transacting the points or other rewards from loyalty "
               "schemes (e.g., air miles) during contract delivery activities paid for by the UK taxpayer.",
               "no benefit from loyalty-scheme points on taxpayer-funded travel")
PERSONAL_AIR = keep(124, 130, None, "personal time: tell the Contract Manager; the Supplier covers any extra fare over "
                    "the flights purely for business")
PERSONAL_PRE = keep(65, 68, None, "personal time: the Contract Manager is informed and the Supplier covers extra costs")
PRE_APPROVAL = keep(51, 52, None, "all claims need the Contract Manager's prior written pre-approval")
NO_PURCHASE = keep(58, 58, None, "no travel reserved or purchased without the Contract Manager's written pre-approval")
WEEKEND = keep(20, 24, None, "claimable travel excludes return journeys home at weekends during a continuous business "
               "location")
OFFICIAL = keep(10, 15, "Suppliers can only claim for official travel to and from Expo 2025 in Japan and within Japan.",
                "only official travel to, from and within Japan is claimable")
OUTSIDE = keep(235, 236, None, "expenses outside the areas specified are not reimbursed")
FORM_CLASS = keep(339, 345, None, "the pre-expense authorisation form records the class of travel and the business "
                  "justification for an upgrade")

# ----- nearby clauses that must not change the answer -----
EARLY = aside(110, 113, "It is expected that Suppliers make early bookings, where possible, booking well in advance to "
              "minimise costs", "booking early is 'where possible', not a ban on a late booking")
TURNAROUND = aside(270, 271, "allowing 5 days for turnaround by the Contract Manager",
                   "the 5 days are for the form's turnaround, already done here")
TAXI = aside(171, 175, "Use of taxis is expected only where there is a clear value for money or business justification",
             "a taxi rule, not a flight rule")
QUOTES = aside(120, 123, "Suppliers must obtain three quotes for all air travel",
               "the quotes go with the pre-approval request, which is already signed")
RAIL_CLASS = aside(154, 155, "For rail travel the Supplier should travel standard class",
                   "the train's class, not the flight's")
UK_ECONOMY = aside(148, 149, "Air travel in the UK must be by economy class.",
                   "the UK cabin rule; the flight booked here is the international one")
INSURANCE = aside(211, 213, "Suppliers must arrange and pay for their own travel insurance.",
                  "insurance is the Supplier's own cost, not part of the fare")
PUBLIC = aside(103, 104, "It is DBT's preference that public transport is utilised where possible in the first",
               "public transport for ground travel; a scheduled flight is not ruled out by it")

# ----- builders -----

SUPPLIER = "Kinsale Exhibition Builders Ltd"


def trip(**fields):
    base = {
        "traveller_name": "", "traveller_title": "", "supplier": SUPPLIER, "origin": "", "destination": "",
        "travel_date": "", "booking_date": "", "purpose": "", "trip_kind": "EXPO_SITE_WORK",
        "requested_cabin": "ECONOMY", "chosen_airline": "", "wants_open_return": False, "date_can_move": False,
        "leisure_days": 0, "work_only_date": "", "leisure_notified": False, "rail_option": "", "rail_fare_cents": 0,
        "rail_to_airport": "", "sign_offs": [],
    }
    unknown = set(fields) - set(base)
    assert not unknown, unknown
    base.update(fields)
    return base


def form(cabin, given_on, name="Helen Achterberg", grounds=""):
    """The DBT Contract Manager's signed Pre-Expense Authorisation Form for the trip."""
    return {"role": "CONTRACT_MANAGER", "name": name, "subject": "PRE_EXPENSE_AUTHORISATION", "cabin": cabin,
            "grounds": grounds, "given_on": given_on}


def director(cabin, grounds, given_on, name="Rupert Osei"):
    return {"role": "DIRECTOR", "name": name, "subject": "HIGHER_CABIN", "cabin": cabin, "grounds": grounds,
            "given_on": given_on}


def offer(slot, flight, cabin, pence, seats=True, refundable=False):
    data = {"slot": slot, "flight": flight, "cabin": cabin, "fare_cents": pence}
    if not seats:
        data["seats"] = False
    if refundable:
        data["refundable"] = True
    return data


def expected(decision, slots, cabins, reasons, approvers, clauses, phrase=""):
    return {"decision": decision, "offer_slots": slots, "cabins": cabins, "reason_codes": sorted(reasons),
            "approvers": sorted(approvers), "clauses": sorted(clauses), "unclear_phrase": phrase}


def search(name, origin, destination, date, flights, offers):
    # handbook.json background_offers is 0 and every search sets 0: the pinned offers are the whole listing, so no
    # background routing can change an answer, and a search the case does not pin lists nothing.
    return {"name": name, "origin": origin, "destination": destination, "date": date, "return_date": "",
            "background": 0, "flights": flights, "offers": offers}


S = []


def scenario(id, category, overlays, request, trip_, searches, exp, must_keep, notes, twin_of="", twin_fact="",
             flag_twins=(), ambiguity="none", distractors=()):
    S.append({
        "id": id, "category": category, "overlays": list(overlays), "twin_of": twin_of, "twin_fact": twin_fact,
        "flag_twins": list(flag_twins), "ambiguity_note": ambiguity, "request": request, "trip": trip_,
        "world": {"searches": list(searches)}, "expected": exp, "must_keep": list(must_keep),
        "distractors": list(distractors), "design_notes": notes,
    })


AIR = ["AIR_TRAVEL", "POLICY_STATEMENT"]
ON_FILE = ["CONTRACT_MANAGER", "NONE"]
LEISURE_CLAUSES = [*AIR, "EXPENSE_PRE_APPROVAL", "PURPOSE"]
UNCLEAR_ROLES = ["CONTRACT_MANAGER", "DIRECTOR", "NOT_NAMED"]
UNCLEAR_REASONS = ["APPROVAL_REQUIRED", "UNCLEAR_POLICY_TEXT"]

# London Heathrow to Tokyo Haneda nonstops (eastbound scheduled minutes).
NONSTOPS = {
    "ba": {"carrier": "BA", "depart": "09:25", "minutes": [820]},
    "nh": {"carrier": "NH", "depart": "11:40", "minutes": [825]},
    "jl": {"carrier": "JL", "depart": "19:25", "minutes": [830]},
}
# Haneda to Heathrow nonstops (westbound).
HOMEWARD = {
    "jl": {"carrier": "JL", "depart": "10:15", "minutes": [885]},
    "nh": {"carrier": "NH", "depart": "11:50", "minutes": [880]},
    "ba": {"carrier": "BA", "depart": "13:05", "minutes": [890]},
}

# ===== easy (3) =====

scenario(
    "alder-pennant", "easy", ["upgrade_not_taken"],
    "Heathrow to Tokyo Haneda on 8 April for the pavilion fit-out meetings, please. My form was signed for business, "
    "but economy is fine for me: the cheapest seat you can get.",
    trip(traveller_name="Maeve Lindqvist", traveller_title="Fit-out Project Manager", origin="LHR", destination="HND",
         travel_date="2025-04-08", booking_date="2025-03-17",
         purpose="Pavilion fit-out progress meetings with the Expo site team in Osaka from 10 April (onward by rail "
                 "from Tokyo)",
         sign_offs=[form("BUSINESS", "2025-03-12", grounds="Overnight long-haul flight before a full working day")]),
    [search("main", "LHR", "HND", "2025-04-08", NONSTOPS, [
        offer("ba-economy", "ba", "ECONOMY", 72400, seats=False),
        offer("ba-business", "ba", "BUSINESS", 389000),
        offer("nh-economy", "nh", "ECONOMY", 75850),
        offer("nh-business", "nh", "BUSINESS", 402000),
        offer("jl-economy", "jl", "ECONOMY", 78900),
        offer("jl-business", "jl", "BUSINESS", 395500),
    ])],
    expected("BOOK", ["nh-economy"], ["ECONOMY"], ["COST_SAVINGS", "LOWEST_FARE"], ON_FILE, AIR),
    [LOWEST, TABLE, NO_PURCHASE],
    "Nonstops of 820-830 minutes are over 10 hours, so business is the class with the Contract Manager's agreement "
    "(line 135), which the form gives; the traveller asks for the cheapest economy, which is permitted. The cheapest "
    "fare (BA at 724.00) is sold out, so the lowest logical fare is ANA at 758.50 (line 119).",
    distractors=[QUOTES])

scenario(
    "bramble-coil", "easy", ["multi_leg"],
    "I need to get from Heathrow to Tokyo Narita on 12 May for meetings with the other suppliers on the UK pavilion. "
    "Economy, and I don't mind changing planes if it's cheaper.",
    trip(traveller_name="Oliver Szabo", traveller_title="AV Systems Engineer", origin="LHR", destination="NRT",
         travel_date="2025-05-12", booking_date="2025-04-14", trip_kind="SUPPLIER_MEETINGS",
         purpose="Coordination meetings with other suppliers contracted for the UK pavilion, from 14 May",
         sign_offs=[form("ECONOMY", "2025-04-09")]),
    [search("main", "LHR", "NRT", "2025-05-12", {
        "dubai": {"carrier": "EK", "via": ["DXB"], "depart": "08:30", "minutes": [415, 580], "layovers": [125]},
        "jl": {"carrier": "JL", "depart": "13:00", "minutes": [830]},
        "nh": {"carrier": "NH", "depart": "19:00", "minutes": [825]},
    }, [
        offer("dubai-economy", "dubai", "ECONOMY", 61200),
        offer("jl-economy", "jl", "ECONOMY", 74300),
        offer("nh-economy", "nh", "ECONOMY", 71900),
    ])],
    expected("BOOK", ["dubai-economy"], ["ECONOMY"], ["LOWEST_FARE"], ON_FILE, AIR),
    [LOWEST, TABLE, NO_PURCHASE],
    "Economy on every flight (lines 133-134), and the traveller accepts a connection: the Emirates fare via Dubai at "
    "612.00 is the lowest logical fare (line 119).")

scenario(
    "cobalt-weir", "easy", ["upgrade_not_taken"],
    "Flying home from Tokyo Narita to Heathrow on Wednesday 16 July once the partner sessions finish. Economy is plenty, "
    "keep the cost down.",
    trip(traveller_name="Priya Natarajan", traveller_title="Partnerships Lead", origin="NRT", destination="LHR",
         travel_date="2025-07-16", booking_date="2025-06-30", trip_kind="STAKEHOLDER_MEETINGS",
         purpose="End of a two-week programme of stakeholder sessions at the Expo; flying back to London",
         sign_offs=[form("BUSINESS", "2025-06-24", grounds="Long-haul flights both ways")]),
    [search("main", "NRT", "LHR", "2025-07-16", {
        "nh": {"carrier": "NH", "depart": "10:30", "minutes": [875]},
        "jl": {"carrier": "JL", "depart": "11:05", "minutes": [880]},
        "ba": {"carrier": "BA", "depart": "12:15", "minutes": [890]},
    }, [
        offer("nh-economy", "nh", "ECONOMY", 70100),
        offer("jl-economy", "jl", "ECONOMY", 69800),
        offer("jl-business", "jl", "BUSINESS", 412000),
        offer("ba-economy", "ba", "ECONOMY", 68400),
        offer("ba-business", "ba", "BUSINESS", 398000),
    ])],
    expected("BOOK", ["ba-economy"], ["ECONOMY"], ["COST_SAVINGS", "LOWEST_FARE"], ON_FILE, AIR),
    [LOWEST, TABLE, NO_PURCHASE],
    "The flight home is over 10 hours and the form names business, but the traveller asks for economy: the lowest "
    "logical fare, BA at 684.00 (line 119). A mid-week flight at the end of the programme, not a weekend trip home.")

# ===== boundary twins (4) =====

DOHA_FLIGHTS = {
    "doha": {"carrier": "QR", "via": ["DOH"], "depart": "08:20", "minutes": [405, 590], "layovers": [150]},
    "ba": {"carrier": "BA", "depart": "12:35", "minutes": [825]},
    "jl": {"carrier": "JL", "depart": "19:25", "minutes": [830]},
}


def doha_offers(nonstop_business_seats):
    return [
        offer("doha-economy", "doha", "ECONOMY", 63800),
        offer("doha-business", "doha", "BUSINESS", 268000),
        offer("ba-economy", "ba", "ECONOMY", 76200),
        offer("ba-business", "ba", "BUSINESS", 412500, seats=nonstop_business_seats),
        offer("jl-economy", "jl", "ECONOMY", 74900),
        offer("jl-business", "jl", "BUSINESS", 405800, seats=nonstop_business_seats),
    ]


DOHA_REQUEST = ("Heathrow to Haneda on 3 September for the UK national day programme. Business class please, my form "
                "covers it. If business isn't allowed on what's left, book economy; I have to be at the national day "
                "events in Osaka, which start on 6 September.")


def doha_trip(name, title):
    return trip(traveller_name=name, traveller_title=title, origin="LHR", destination="HND",
                travel_date="2025-09-03", booking_date="2025-08-11", requested_cabin="BUSINESS",
                purpose="UK national day programme at the Expo site, Osaka, from 6 September (onward by rail from Tokyo)",
                sign_offs=[form("BUSINESS", "2025-08-06", grounds="Overnight long-haul flight before event duty")])


scenario(
    "damson-ridge", "boundary_twin", ["multi_leg", "dearer_option"],
    DOHA_REQUEST, doha_trip("Callum Rees", "Events Production Manager"),
    [search("main", "LHR", "HND", "2025-09-03", DOHA_FLIGHTS, doha_offers(True))],
    expected("BOOK", ["jl-business"], ["BUSINESS"], ["INTERNATIONAL_LONG_FLIGHT", "LONG_FLIGHT_APPROVED"], ON_FILE, AIR),
    [TABLE, FORM_CLASS, LOWEST],
    "Per flight (line 132): the nonstops (825, 830 minutes) are over 10 hours, so business with the Contract Manager's "
    "prior agreement (line 135), which the signed form naming business gives. The Qatar business fare is cheaper "
    "(2,680.00) but its flights are 405 and 590 minutes, each 10 hours or less, where the class is economy (lines "
    "133-134). The lowest logical business fare is JAL at 4,058.00.",
    twin_of="elder-sound", twin_fact="nonstop business seats on sale or sold out")

scenario(
    "elder-sound", "boundary_twin", ["multi_leg"],
    DOHA_REQUEST, doha_trip("Freya Holloway", "Events Production Manager"),
    [search("main", "LHR", "HND", "2025-09-03", DOHA_FLIGHTS, doha_offers(False))],
    expected("BOOK", ["doha-economy"], ["ECONOMY"], ["LONG_FLIGHT_CONDITION_NOT_MET", "UPGRADE_NOT_ELIGIBLE"], ON_FILE,
             AIR),
    [TABLE, LOWEST, FORM_CLASS],
    "The nonstop business seats are sold out. The only business fare left is the Qatar connection, whose flights (405 "
    "and 590 minutes) are each 10 hours or less: economy is the class on both (lines 132-134), and flying time is per "
    "flight, never added up. So business is not allowed, and the traveller asked for economy then: the lowest logical "
    "fare is the Qatar economy fare at 638.00 (line 119).",
    twin_of="damson-ridge", twin_fact="nonstop business seats on sale or sold out")

LEISURE_REQUEST = ("My work at the Expo wraps up on Friday 30 May, but I'd like to stay on in Japan over the weekend "
                   "and fly Haneda to Heathrow on Monday 2 June instead. The contract manager knows. If the extra days "
                   "mean the Monday flight can't all go on the contract, book me whichever flight home it does cover. "
                   "Economy.")


def leisure_trip(name):
    return trip(traveller_name=name, traveller_title="Structural Engineer", origin="HND", destination="LHR",
                travel_date="2025-06-02", booking_date="2025-05-06", trip_kind="EXPO_SITE_WORK",
                purpose="Flying home after a pavilion structural inspection; the work ends on Friday 30 May",
                leisure_days=3, work_only_date="2025-05-30", leisure_notified=True,
                sign_offs=[form("ECONOMY", "2025-04-29")])


def leisure_searches(monday_jl):
    return [
        search("monday", "HND", "LHR", "2025-06-02", HOMEWARD, [
            offer("mon-jl-economy", "jl", "ECONOMY", monday_jl),
            offer("mon-nh-economy", "nh", "ECONOMY", 66800),
            offer("mon-ba-economy", "ba", "ECONOMY", 67450),
        ]),
        search("friday", "HND", "LHR", "2025-05-30", HOMEWARD, [
            offer("fri-jl-economy", "jl", "ECONOMY", 66300),
            offer("fri-nh-economy", "nh", "ECONOMY", 65120),
            offer("fri-ba-economy", "ba", "ECONOMY", 68900),
        ]),
    ]


scenario(
    "fennel-arch", "boundary_twin", ["personal_travel", "date_arithmetic", "month_end"],
    LEISURE_REQUEST, leisure_trip("Tomasz Brennan"), leisure_searches(65120),
    expected("BOOK", ["mon-jl-economy"], ["ECONOMY"], ["LOWEST_FARE", "PERSONAL_TIME_NO_EXTRA_COST"], ON_FILE,
             LEISURE_CLAUSES),
    [PERSONAL_AIR, PERSONAL_PRE, LOWEST],
    "Lines 124-130: the Supplier covers extra cost only 'if earlier or later return flights are more expensive than "
    "flights that would have been taken purely for the purposes of the business trip'. The lowest Monday fare (JAL, "
    "651.20) equals the lowest Friday fare (ANA, 651.20): not more expensive, so the leisure days add nothing and the "
    "Monday flight is booked. The Contract Manager has been told (lines 65-66).",
    twin_of="garnet-mere", twin_fact="Monday's lowest fare 65120 or 65520 pence against Friday's 65120")

scenario(
    "garnet-mere", "boundary_twin", ["personal_travel", "date_arithmetic", "month_end"],
    LEISURE_REQUEST, leisure_trip("Ines Kowalczyk"), leisure_searches(65520),
    expected("BOOK", ["fri-nh-economy"], ["ECONOMY"], ["PERSONAL_TIME_EXTRA_COST", "PERSONAL_TRAVEL_NOT_COVERED"],
             ON_FILE, LEISURE_CLAUSES),
    [PERSONAL_AIR, PERSONAL_PRE, LOWEST],
    "The lowest Monday fare (JAL, 655.20) is 4.00 more than the lowest Friday fare (ANA, 651.20), so the later flight "
    "is 'more expensive than flights that would have been taken purely for the purposes of the business trip' (lines "
    "124-130) and the extra would be the Supplier's. The traveller asked, in that case, for the flight home the "
    "contract covers: ANA on Friday 30 May, the lowest logical fare that day (line 119).",
    twin_of="fennel-arch", twin_fact="Monday's lowest fare 65120 or 65520 pence against Friday's 65120")

# ===== multi-rule (3) =====

scenario(
    "heather-vane", "multi_rule", ["dearer_option"],
    "Heathrow to Haneda on 18 June, please. The Department's director for the pavilion programme has signed off first class because I go straight into the "
    "pavilion handover when I land. If first isn't allowed, book what the policy does allow; I have to be at the "
    "handover.",
    trip(traveller_name="Adaeze Okafor", traveller_title="Commissioning Director", origin="LHR", destination="HND",
         travel_date="2025-06-18", booking_date="2025-05-26", requested_cabin="FIRST",
         purpose="Pavilion handover to the Department at the Expo site, Osaka, on arrival (onward by rail from Tokyo)",
         sign_offs=[form("BUSINESS", "2025-05-20", grounds="Overnight long-haul flight before the handover"),
                    director("FIRST", "Required to work immediately on arrival at the handover", "2025-05-21")]),
    [search("main", "LHR", "HND", "2025-06-18", {
        "ba": {"carrier": "BA", "depart": "09:25", "minutes": [820]},
        "jl": {"carrier": "JL", "depart": "11:40", "minutes": [830]},
    }, [
        offer("ba-economy", "ba", "ECONOMY", 74800),
        offer("ba-business", "ba", "BUSINESS", 398000),
        offer("ba-first", "ba", "FIRST", 795000),
        offer("jl-economy", "jl", "ECONOMY", 73600),
        offer("jl-business", "jl", "BUSINESS", 389500),
        offer("jl-first", "jl", "FIRST", 768000),
    ])],
    expected("BOOK", ["jl-business"], ["BUSINESS"], ["FIRST_CLASS_NOT_PERMITTED", "UPGRADE_NOT_ELIGIBLE"], ON_FILE, AIR),
    [FIRST_BAR, TABLE, WORK_ON_ARRIVAL, LOWEST],
    "Lines 137-138: the Director may allow 'the next higher class (but not first class)', so the Director's note for "
    "first is of no effect (its giver is not accepted as the approver). The flights are over 10 hours and the form "
    "names business (line 135), so business is what the policy allows: the lowest logical business fare, JAL at "
    "3,895.00.")

scenario(
    "iris-tarn", "multi_rule", ["multi_leg"],
    "I'm based in Edinburgh. I'd like to fly Edinburgh to Tokyo Haneda on 23 April, changing at Heathrow. If the "
    "policy wants me on the train down to London instead, book the flight from Heathrow.",
    trip(traveller_name="Euan MacLeod", traveller_title="Lighting Designer", origin="EDI", destination="HND",
         travel_date="2025-04-23", booking_date="2025-03-31",
         purpose="Pavilion lighting installation at the Expo site, Osaka (onward by rail from Tokyo)",
         rail_option=("Edinburgh to London King's Cross by train on the morning of 23 April, then the Heathrow Express; "
                      "it reaches Heathrow by 12:45, before every afternoon and evening departure from there"),
         rail_fare_cents=9850, rail_to_airport="LHR", sign_offs=[form("ECONOMY", "2025-03-26")]),
    [search("edinburgh", "EDI", "HND", "2025-04-23", {
        "via-london": {"carrier": "BA", "via": ["LHR"], "depart": "09:40", "minutes": [85, 825], "layovers": [145]},
        "via-london-late": {"carrier": "BA", "via": ["LHR"], "depart": "15:30", "minutes": [85, 830], "layovers": [130]},
    }, [
        offer("edi-early-economy", "via-london", "ECONOMY", 98400),
        offer("edi-late-economy", "via-london-late", "ECONOMY", 101200),
    ]),
     search("heathrow", "LHR", "HND", "2025-04-23", {
         "ba": {"carrier": "BA", "depart": "13:30", "minutes": [825]},
         "jl": {"carrier": "JL", "depart": "15:20", "minutes": [830]},
         "ba-late": {"carrier": "BA", "depart": "19:20", "minutes": [830]},
     }, [
         offer("lhr-ba-economy", "ba", "ECONOMY", 74100),
         offer("lhr-jl-economy", "jl", "ECONOMY", 72900),
         offer("lhr-ba-late-economy", "ba-late", "ECONOMY", 76300),
     ])],
    expected("BOOK", ["lhr-jl-economy"], ["ECONOMY"], ["COST_SAVINGS", "RAIL_PREFERRED"], ON_FILE, AIR),
    [UK_AIR, RAIL, LOWEST],
    "Air from Scotland is the exception to no air within the UK (lines 147-148), but 'Domestic flights should only be "
    "taken when they are more economical than rail' (lines 151-152). The through fare from Edinburgh is 984.00; the "
    "train (98.50) plus the lowest Heathrow fare (JAL, 729.00) is 827.50, and even with the same BA flight from "
    "Heathrow (741.00) it is 839.50. The flight to London is not more economical than rail, so the traveller goes by "
    "train and the ticket is the lowest logical fare from Heathrow.",
    distractors=[RAIL_CLASS, UK_ECONOMY])

scenario(
    "juniper-loft", "multi_rule", [],
    "Please get me an open return from Heathrow to Haneda, flying out on 6 August. I don't know yet when the pavilion "
    "work will let me come home. If an open ticket isn't allowed, just book the flight out.",
    trip(traveller_name="Hamish Doyle", traveller_title="Site Operations Coordinator", origin="LHR", destination="HND",
         travel_date="2025-08-06", booking_date="2025-07-14", wants_open_return=True,
         purpose="Pavilion operations support at the Expo site, Osaka; the end date is not yet set",
         sign_offs=[form("ECONOMY", "2025-07-09")]),
    [search("main", "LHR", "HND", "2025-08-06", NONSTOPS, [
        offer("ba-economy", "ba", "ECONOMY", 76800),
        offer("nh-economy", "nh", "ECONOMY", 74200),
        offer("jl-economy", "jl", "ECONOMY", 75500),
        offer("jl-flex-economy", "jl", "ECONOMY", 99800, refundable=True),
    ])],
    expected("BOOK", ["nh-economy"], ["ECONOMY"], ["OPEN_TICKET_NOT_ALLOWED"], ON_FILE, AIR),
    [OPEN, LOWEST],
    "Line 146: 'All flights must be booked at set dates, no open return tickets may be booked.' So only the flight out "
    "on its set date is bought, at the lowest logical fare (ANA, 742.00; line 119); the flight home is booked once its "
    "date is set. The outbound date is fixed, so the dearer refundable fare is not needed.",
    distractors=[EARLY])

# ===== hidden clause (2) =====

scenario(
    "kestrel-moor", "hidden_clause", ["outside_air_section"],
    "Heathrow to Haneda on 21 May for the stakeholder round tables. Please put me on Japan Airlines, I'm close to the "
    "next status tier on their frequent flyer scheme. If that isn't allowed, book what the policy allows; I need to be "
    "at the round tables.",
    trip(traveller_name="Gareth Pryce", traveller_title="Stakeholder Engagement Manager", origin="LHR",
         destination="HND", travel_date="2025-05-21", booking_date="2025-04-28", trip_kind="STAKEHOLDER_MEETINGS",
         chosen_airline="Japan Airlines", purpose="Stakeholder round tables for the UK pavilion programme, from 23 May",
         sign_offs=[form("ECONOMY", "2025-04-23")]),
    [search("main", "LHR", "HND", "2025-05-21", NONSTOPS, [
        offer("ba-economy", "ba", "ECONOMY", 75900),
        offer("nh-economy", "nh", "ECONOMY", 74200),
        offer("jl-economy", "jl", "ECONOMY", 78700),
    ])],
    expected("BOOK", ["nh-economy"], ["ECONOMY"], ["LOWEST_FARE", "LOYALTY_PROGRAM_PREFERENCE"], ON_FILE,
             [*AIR, "CLAIMING_REIMBURSEMENT"]),
    [LOYALTY, LOWEST],
    "Lines 107-109 (under Claiming Reimbursement, away from Air Travel): Suppliers must not derive a benefit from "
    "loyalty-scheme points or rewards on taxpayer-funded travel; line 119: the lowest logical fare. JAL costs 787.00 "
    "against ANA's 742.00, so ANA.")

scenario(
    "linnet-brook", "hidden_clause", ["multi_leg", "dearer_option"],
    "Heathrow to Haneda on 10 April. I have to be at the opening rehearsal on 12 April and the date can't move. Economy if there's "
    "anything left; the Department's director for the pavilion programme has already signed off premium economy if "
    "there isn't.",
    trip(traveller_name="Sofia Marchetti", traveller_title="Show Control Engineer", origin="LHR", destination="HND",
         travel_date="2025-04-10", booking_date="2025-03-24",
         purpose="Expo opening rehearsal at the UK pavilion, Osaka, on 12 April (onward by rail from Tokyo)",
         sign_offs=[form("ECONOMY", "2025-03-19"),
                    director("PREMIUM_ECONOMY", "Economy is sold out on every flight that day and the rehearsal date "
                             "cannot move", "2025-03-21")]),
    [search("main", "LHR", "HND", "2025-04-10", {
        "doha": {"carrier": "QR", "via": ["DOH"], "depart": "08:20", "minutes": [405, 590], "layovers": [150]},
        "dubai": {"carrier": "EK", "via": ["DXB"], "depart": "09:40", "minutes": [415, 580], "layovers": [130]},
        "doha-late": {"carrier": "QR", "via": ["DOH"], "depart": "15:45", "minutes": [405, 595], "layovers": [135]},
    }, [
        offer("doha-economy", "doha", "ECONOMY", 64800, seats=False),
        offer("doha-premium", "doha", "PREMIUM_ECONOMY", 128400),
        offer("dubai-economy", "dubai", "ECONOMY", 62900, seats=False),
        offer("dubai-premium", "dubai", "PREMIUM_ECONOMY", 126800),
        offer("doha-late-economy", "doha-late", "ECONOMY", 66100, seats=False),
        offer("doha-late-premium", "doha-late", "PREMIUM_ECONOMY", 131900),
    ])],
    expected("BOOK", ["dubai-premium"], ["PREMIUM_ECONOMY"], ["NEXT_CLASS_UP_AUTHORISED", "NO_ECONOMY_SEATS_URGENT", "PREMIUM_ECONOMY_ALLOWED"],
             [*ON_FILE, "DIRECTOR"], AIR),
    [TABLE, NO_SEATS, LOWEST],
    "Economy is sold out on every flight. Every flight is over 5 hours and at most 10 (405-595 minutes), where economy "
    "is the class 'but see below*' (line 134); the footnote (lines 137-143) lets the Director allow the next higher "
    "class 'when bookings are not available in the lower class and the timing or date of the journey cannot be "
    "changed', and that note is on file. The cheapest premium economy fare: Emirates at 1,268.00.")

# ===== distractor (1) =====

scenario(
    "marram-spit", "distractor", ["date_arithmetic"],
    "Short notice, sorry: the Expo team only confirmed my slot on Friday. Heathrow to Haneda on Wednesday 9 July, "
    "economy. I'll get a taxi to Heathrow.",
    trip(traveller_name="Lena Fischer", traveller_title="Exhibit Maintenance Technician", origin="LHR",
         destination="HND", travel_date="2025-07-09", booking_date="2025-07-07",
         purpose="Exhibit maintenance shift at the UK pavilion, Osaka, from 12 July (onward by rail from Tokyo)",
         sign_offs=[form("ECONOMY", "2025-07-04")]),
    [search("main", "LHR", "HND", "2025-07-09", NONSTOPS, [
        offer("ba-economy", "ba", "ECONOMY", 81500),
        offer("nh-economy", "nh", "ECONOMY", 84200),
        offer("jl-economy", "jl", "ECONOMY", 79900),
    ])],
    expected("BOOK", ["jl-economy"], ["ECONOMY"], ["LOWEST_FARE"], ON_FILE, AIR),
    [LOWEST, NO_PURCHASE],
    "The booking is two days before the flight. Early booking is expected 'where possible' (lines 110-113), and the "
    "5 days of lines 270-271 are the form's turnaround, already done (signed 4 July). The taxi is a ground-transport "
    "matter. The lowest logical fare: JAL at 799.00 (line 119).",
    distractors=[EARLY, TURNAROUND, TAXI])

# ===== refusal (1) =====

scenario(
    "nettle-fold", "refusal", ["personal_travel", "outside_air_section"],
    "I've been out at the Expo since early May and I'm here until the end of June. Could you book me Haneda to "
    "Heathrow on Friday 13 June so I can spend the weekend at home? Economy is fine.",
    trip(traveller_name="Rhys Abernethy", traveller_title="Pavilion Duty Manager", origin="HND", destination="LHR",
         travel_date="2025-06-13", booking_date="2025-05-27", trip_kind="HOME_VISIT",
         purpose="A weekend at home in London in the middle of a posting at the UK pavilion (5 May to 27 June)",
         sign_offs=[form("ECONOMY", "2025-04-22", grounds="The posting's flights out on 5 May and home on 27 June")]),
    [search("main", "HND", "LHR", "2025-06-13", HOMEWARD, [
        offer("jl-economy", "jl", "ECONOMY", 66400),
        offer("nh-economy", "nh", "ECONOMY", 67900),
        offer("ba-economy", "ba", "ECONOMY", 69100),
    ])],
    expected("REFUSE", [], ["NONE"], ["OUTSIDE_POLICY_SCOPE", "PERSONAL_TRAVEL_NOT_COVERED", "WEEKEND_TRAVEL_HOME"],
             ["CONTRACT_MANAGER", "NONE"], ["NON_REIMBURSABLE", "PURPOSE"]),
    [WEEKEND, OUTSIDE, OFFICIAL],
    "Lines 20-24: claimable official travel must not include 'return journeys home at weekends during a continuous "
    "business location'. The traveller is mid-posting and asks to fly home for the weekend; lines 235-236: what the "
    "schedule does not cover is not reimbursed. The form on file covers the posting's own flights, not this one, so "
    "NONE or CONTRACT_MANAGER (an unused sign-off on file).")

# ===== flag (2) =====

scenario(
    "osprey-cairn", "flag", ["approval_required", "dearer_option"],
    "Heathrow to Haneda on 1 October for the closing-fortnight stakeholder programme. I'd like business class for this "
    "one, please; my form went in for economy. I'd rather wait for business than fly economy on this one.",
    trip(traveller_name="Bethan Hughes", traveller_title="Programme Director", origin="LHR", destination="HND",
         travel_date="2025-10-01", booking_date="2025-09-08", requested_cabin="BUSINESS",
         trip_kind="STAKEHOLDER_MEETINGS", purpose="Closing-fortnight stakeholder programme at the Expo, Osaka, from 3 October",
         sign_offs=[form("ECONOMY", "2025-09-03")]),
    [search("main", "LHR", "HND", "2025-10-01", NONSTOPS, [
        offer("ba-economy", "ba", "ECONOMY", 75600),
        offer("ba-business", "ba", "BUSINESS", 401000),
        offer("nh-economy", "nh", "ECONOMY", 76900),
        offer("nh-business", "nh", "BUSINESS", 408800),
        offer("jl-economy", "jl", "ECONOMY", 74300),
        offer("jl-business", "jl", "BUSINESS", 396500),
    ])],
    expected("FLAG_FOR_APPROVAL", ["jl-business"], ["BUSINESS"], ["APPROVAL_REQUIRED", "INTERNATIONAL_LONG_FLIGHT"],
             ["CONTRACT_MANAGER"], [*AIR, "EXPENSE_PRE_APPROVAL"]),
    [TABLE, NO_PURCHASE, FORM_CLASS],
    "The nonstops are over 10 hours, so business may be used 'subject to prior agreement with DBT Contract Manager' "
    "(line 135). The signed form names economy, and travel may not be purchased without the Contract Manager's written "
    "pre-approval (line 58). The traveller would rather wait for business: hold the lowest business fare (JAL, "
    "3,965.00) for the Contract Manager. Approval required, not 'no compliant offer'.",
    flag_twins=["damson-ridge", "elder-sound"],
    ambiguity="none: the Contract Manager's prior agreement to business is required and missing; the text is clear")

scenario(
    "plover-reach", "flag", ["multi_leg", "unclear_phrase"],
    "Heathrow to Haneda on 25 June; via Hong Kong is fine. The Department's director for the pavilion programme has "
    "approved premium economy because I go "
    "straight into the technical rehearsal when I land. If premium economy isn't allowed, book economy.",
    trip(traveller_name="Kenji Hartley", traveller_title="Technical Rehearsal Lead", origin="LHR", destination="HND",
         travel_date="2025-06-25", booking_date="2025-06-02", requested_cabin="PREMIUM_ECONOMY",
         purpose="Technical rehearsal at the UK pavilion, Osaka, on arrival (onward by rail from Tokyo)",
         sign_offs=[form("ECONOMY", "2025-05-28"),
                    director("PREMIUM_ECONOMY", "Required to work immediately on arrival at the technical rehearsal",
                             "2025-05-29")]),
    [search("main", "LHR", "HND", "2025-06-25", {
        "hongkong": {"carrier": "CX", "via": ["HKG"], "depart": "11:10", "minutes": [765, 240], "layovers": [110]},
        "hongkong-late": {"carrier": "CX", "via": ["HKG"], "depart": "18:25", "minutes": [770, 245], "layovers": [95]},
    }, [
        offer("hongkong-economy", "hongkong", "ECONOMY", 66200),
        offer("hongkong-premium", "hongkong", "PREMIUM_ECONOMY", 104800),
        offer("hongkong-late-economy", "hongkong-late", "ECONOMY", 67900),
        offer("hongkong-late-premium", "hongkong-late", "PREMIUM_ECONOMY", 108300),
    ])],
    expected("FLAG_FOR_APPROVAL", ["hongkong-economy", "hongkong-premium"], ["ECONOMY", "PREMIUM_ECONOMY"],
             UNCLEAR_REASONS, UNCLEAR_ROLES, AIR, phrase="Over 5 hours All journeys at public expense: Economy (but see "
             "below*)"),
    [TABLE, WORK_ON_ARRIVAL, SHORT_VISIT],
    "Each itinerary has a flight over 10 hours to Hong Kong (765 or 770 minutes) and one of 5 hours or less on to "
    "Haneda (240 or 245). The class is set per flight (line 132). The Director's note allows the next higher class for "
    "work on arrival (line 144), but only the 'Over 5 hours' row carries '(but see below*)' (line 134); the 'Up to 5 "
    "hours' row is plain economy (line 133). Yet the footnote's own grounds include 'short duty visits out and back in "
    "a working day' (lines 140-141), which are short flights, so it may reach them too. The offer sells premium economy "
    "on both flights. Hold the premium economy fare, or the economy fare of the stricter reading.",
    flag_twins=["linnet-brook", "bramble-coil"],
    ambiguity={"phrase": "Over 5 hours All journeys at public expense: Economy (but see below*)",
               "readings": [("the asterisk marks only the 'Over 5 hours' row, so the Hong Kong to Haneda flight of 5 "
                             "hours or less stays in economy and a premium economy ticket on it is not allowed: book "
                             "the Cathay economy fare"),
                            ("the footnote lets the Director allow the next higher class for the journey, short flights "
                             "included (its grounds name same-day visits): book the Cathay premium economy fare")]})


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.json"):
        old.unlink()
    for data in S:
        (OUT / f"{data['id']}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(S)} scenarios to {OUT}")


if __name__ == "__main__":
    main()
