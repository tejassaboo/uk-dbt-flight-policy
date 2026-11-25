"""The answer key's rules for the Department for Business and Trade's Contract Schedule 31, Travel & Subsistence
Expenses Policy (supplier travel to and within Japan for Expo 2025), as exact integer code. Byte-identical in
src/plugin/rules.py and verifier/rules.py; it imports only modules a verifier may use.

Every rule cites the frozen handbook text (src/plugin/data/policy.txt) by line. Where the text leaves an
answer open, the rule returns FLAG_FOR_APPROVAL with the unclear words, and a scenario may depend on each
unclear phrase at most once (tests/test_scenarios.py). Combinations no scenario needs raise ValueError, so a
new scenario cannot fall silently into untested logic.

Who books. The handbook binds the Supplier: it books its own travel and claims it from DBT, and only what the
schedule allows is reimbursed (lines 10-15, 89-98, 235-238). "BOOK" here is the ticket the supplier buys under
the schedule; "REFUSE" means the schedule pays for no ticket at all for the request.

The duration hook. Lines 131-135 set the class "Flying Time (per flight)": "Up to 5 hours ... Economy";
"Over 5 hours ... Economy (but see below*)"; "Over 10 hours ... Business (subject to prior agreement with DBT
Contract Manager)". Both limits are strict ("Over") and measured on each flight's own scheduled minutes, never
on flights added together and never with ground time. An itinerary whose every flight is over a limit is over
it on every reading, and one whose every flight is at or under it is not. When one flight is over and another
is not, the world sells one cabin on every flight of the offer, and the table does not say how a per-flight
class applies to such a ticket: unclear (None).

The handbook does not say what a "flight" is on a connection. The one-way journey with a change of planes (the
offer, whose flights add to its flying time) is also a reading of "per flight" (EDGE_CASES 3.4: a measure not
defined for connections). Under it, a connection whose flights add to more than 10 hours is over the business
limit. A business request accepts the cheapest business fare of either reading (validation wave 4, 2026-11-25);
``over`` keeps the per-flight measure for every other rule.
"""

from contract import Approver, Cabin, Clause, Decision, ReasonCode, SignOffSubject, TripKind

from .world import airport

HANDBOOK = ("Department for Business and Trade, Contract Schedule 31, Travel & Subsistence Expenses Policy "
            "(supplier travel for Expo 2025, Japan)")

# Each closed-list section and the heading it names in the frozen text (tests check every heading is there).
CLAUSE_HEADINGS = {
    Clause.PURPOSE: "1. Purpose",
    Clause.SUPPORTING_EVIDENCE: "Supporting Evidence",
    Clause.EXPENSE_LIMITS: "Expense Limits",
    Clause.FOREIGN_CURRENCY: "Foreign Currency",
    Clause.VAT: "VAT",
    Clause.EXPENSE_PRE_APPROVAL: "Expense Pre-Approval",
    Clause.SCOPE: "2. Scope",
    Clause.DEFINITIONS: "3. Definitions",
    Clause.POLICY_STATEMENT: "4. Policy Statement",
    Clause.CLAIMING_REIMBURSEMENT: "Claiming Reimbursement:",
    Clause.AIR_TRAVEL: "Air Travel",
    Clause.RAIL_TRAVEL: "Rail Travel",
    Clause.SEA_TRAVEL: "Sea Travel",
    Clause.HOTEL_BOOKING: "Hotel Booking",
    Clause.TAXIS: "Taxis",
    Clause.PRIVATE_HIRE_VEHICLES: "Private & Hire Vehicles",
    Clause.MEAL_DRINK_ALLOWANCES: "Meal and Drink Allowances",
    Clause.INSURANCE: "Insurance",
    Clause.PASSPORTS: "Passports",
    Clause.VISAS: "Visas",
    Clause.VACCINATIONS: "Vaccinations",
    Clause.NON_REIMBURSABLE: "Non-Reimbursable Expenses",
    Clause.ROLES_RESPONSIBILITIES: "5. Roles and responsibilities",
    Clause.TRAINING: "6. Training",
    Clause.COMMUNICATION: "7. Communication and Implementation",
    Clause.MONITORING: "8. Monitoring",
    Clause.REVIEW: "9. Review",
    Clause.ANNEX_AUTHORISATION_PROCESS: "Annex A - Pre-Expense Authorisation Process",
    Clause.ANNEX_AUTHORISATION_FORM: "Annex B - Pre-Expense Authorisation Form",
}

# The handbook's duration thresholds (the per-handbook duration hook; tests/test_duration.py tests both
# sides of each). ">" is strict ("Over 5 hours", "Over 10 hours"); "Up to 5 hours" is the inclusive other side.
DURATION_RULES = (
    {"name": "over-five", "minutes": 300, "operator": ">", "lines": [132, 134],
     "quote": "Over 5 hours All journeys at public expense: Economy (but see below*)"},
    {"name": "over-ten", "minutes": 600, "operator": ">", "lines": [135, 135],
     "quote": "Over 10 hours All journeys at public expense: Business (subject to prior agreement with DBT Contract "
              "Manager)"},
)
LIMITS = {rule["name"]: rule["minutes"] for rule in DURATION_RULES}

# Handbook-specific conventions shown by booking_requirements, beyond the template's (none here).
CONVENTIONS = ()

# The unclear words of the one hold over the text: lines 131-134 give "Up to 5 hours" plain economy and mark only
# the "Over 5 hours" row "(but see below*)", while the footnote (lines 137-145) lets the Director allow the next
# higher class on grounds that include "short duty visits out and back in a working day".
SHORT_FLIGHT_PHRASE = "Over 5 hours All journeys at public expense: Economy (but see below*)"

# Who a hold over those words may name: the Director whose authority the footnote names, the Contract Manager
# who pre-approves the trip (lines 51-58), or nobody named to settle the text.
UNCLEAR_ROLES = [Approver.NOT_NAMED, Approver.DIRECTOR, Approver.CONTRACT_MANAGER]
# The hold also waits on a sign-off, so APPROVAL_REQUIRED may stand beside UNCLEAR_POLICY_TEXT.
UNCLEAR_REASONS = [ReasonCode.UNCLEAR_POLICY_TEXT, ReasonCode.APPROVAL_REQUIRED]

AIR = [Clause.AIR_TRAVEL, Clause.POLICY_STATEMENT]


def over(rule, offer):
    """True, False or None (unclear): whether every outbound flight of ``offer`` is over the handbook's ``rule``
    (over-five: more than 300 scheduled minutes; over-ten: more than 600), each flight on its own."""
    if rule not in LIMITS:
        raise ValueError(f"unknown duration rule {rule!r}")
    beyond = [segment.scheduled_minutes > LIMITS[rule] for segment in offer.segments]
    if all(beyond):
        return True
    if not any(beyond):
        return False
    return None


def by_value(items):
    return sorted(set(items), key=lambda item: item.value)


def answer(decision, offers, reasons, approvers, clauses, why, phrase=""):
    return {
        "decision": decision,
        "offer_ids": sorted(offer.offer_id for offer in offers),
        "cabins": by_value(offer.cabin for offer in offers) or [Cabin.NONE],
        "reason_codes": by_value(reasons),
        "approvers": by_value(approvers),
        "clauses": by_value(clauses),
        "unclear_phrase": phrase,
        "explanation": why,
    }


def cheapest(offers):
    if not offers:
        return []
    low = min(offer.fare_cents for offer in offers)
    return [offer for offer in offers if offer.fare_cents == low]


def in_cabin(offers, cabin):
    return [offer for offer in offers if offer.cabin == cabin]


def leaves(offer):
    """(origin code, local date) of an offer's first flight."""
    return offer.segments[0].origin, offer.segments[0].depart_local[:10]


def notes(trip, subject, roles):
    return [record for record in trip.sign_offs if record.subject == subject and record.role in roles]


def pre_approval(trip):
    """Lines 51-52, 58 and 95: every trip needs the DBT Contract Manager's written pre-approval (the Pre-Expense
    Authorisation Form, Annex A and B) before travel is reserved or purchased. The form names the class of travel."""
    forms = notes(trip, SignOffSubject.PRE_EXPENSE_AUTHORISATION, [Approver.CONTRACT_MANAGER])
    if len(forms) > 1:
        raise ValueError("several pre-expense authorisation forms are not modelled")
    return forms[0] if forms else None


def higher_cabin(trip):
    found = notes(trip, SignOffSubject.HIGHER_CABIN, [Approver.DIRECTOR])
    if len(found) > 1:
        raise ValueError("several Director's notes are not modelled")
    return found[0] if found else None


# SYNC_NOTES 4': a BOOK whose needed sign-off is already on file accepts that role and NONE. Every booking here
# relies on the Contract Manager's pre-approval on file (lines 51-52, 58).
ON_FILE = [Approver.CONTRACT_MANAGER, Approver.NONE]


def lowest_economy(seated):
    lowest = cheapest(in_cabin(seated, Cabin.ECONOMY))
    if not lowest:
        raise ValueError("no economy offer can be bought")
    if any(offer.refundable for offer in lowest):
        raise ValueError("a refundable fare that is the lowest is not modelled")
    return lowest


def solve(trip, offers, hidden):
    """The answer key for one trip and the offers of its pinned searches: the decision, and every accepted
    offer id, cabin, reason, approver and section. ``hidden`` (answer_key_inputs) is unused by this handbook."""
    if hidden:
        raise ValueError("this handbook's scenarios carry no answer_key_inputs")
    if any(offer.return_segments for offer in offers):
        raise ValueError("round-trip fares are not modelled: every case buys a one-way ticket")
    seated = [offer for offer in offers if offer.seats_available]
    if trip.trip_kind == TripKind.HOME_VISIT:
        return home_visit(trip)
    if trip.trip_kind == TripKind.SIGHTSEEING:
        raise ValueError("a sightseeing trip is not modelled")
    form = pre_approval(trip)
    if form is None:
        raise ValueError("a trip without the Contract Manager's pre-approval is not modelled")
    if trip.leisure_days:
        return leisure(trip, seated)
    if trip.rail_option:
        return rail(trip, seated)
    on_trip = [offer for offer in seated if leaves(offer) == (trip.origin.code, trip.travel_date)]
    if len(on_trip) != len(seated):
        raise ValueError("offers off the trip's own route and date are only modelled for leisure days and rail")
    if trip.wants_open_return:
        return open_return(trip, on_trip)
    if trip.chosen_airline:
        return airline_choice(trip, on_trip)
    if trip.requested_cabin == Cabin.FIRST:
        return first(trip, on_trip, form)
    if trip.requested_cabin == Cabin.BUSINESS:
        return business(trip, on_trip, form)
    if trip.requested_cabin == Cabin.PREMIUM_ECONOMY:
        return premium(trip, on_trip, ReasonCode.NEXT_CLASS_UP_AUTHORISED)
    return economy(trip, on_trip, form)


def home_visit(trip):
    """Lines 20-24: claimable official travel must not include 'return journeys home at weekends during a
    continuous business location'; lines 235-236: expenses outside the areas specified are not reimbursed."""
    return answer(Decision.REFUSE, [], [ReasonCode.WEEKEND_TRAVEL_HOME, ReasonCode.OUTSIDE_POLICY_SCOPE,
                                        ReasonCode.PERSONAL_TRAVEL_NOT_COVERED],
                  [Approver.NONE, *(record.role for record in trip.sign_offs)],
                  [Clause.PURPOSE, Clause.NON_REIMBURSABLE],
                  "Lines 20-24: travel the Supplier may claim must not include return journeys home at weekends "
                  "during a continuous business location; the traveller is mid-way through a continuous stay in "
                  "Japan and asks to fly home for the weekend. Lines 235-236: nothing outside the schedule is "
                  "reimbursed, so no ticket is bought under it. The pre-approval on file covers the stay, not this "
                  "journey.")


def economy(trip, on_trip, form):
    """An economy request: the lowest logical fare (line 119). When economy is sold out on every flight, the
    Director's authority for the next higher class (lines 137-143: 'when bookings are not available in the lower
    class and the timing or date of the journey cannot be changed') is what allows premium economy."""
    if not in_cabin(on_trip, Cabin.ECONOMY):
        if trip.date_can_move:
            raise ValueError("sold-out economy on a date that could move is not modelled")
        return premium(trip, on_trip, ReasonCode.NO_ECONOMY_SEATS_URGENT)
    lowest = lowest_economy(on_trip)
    reasons, why = [ReasonCode.LOWEST_FARE], "Line 119: Suppliers are expected to book the lowest logical fare available"
    if form.cabin == Cabin.BUSINESS and all(over("over-ten", offer) is True for offer in lowest):
        # The form allows business on a flight over 10 hours; economy instead is a saving the request chose.
        reasons.append(ReasonCode.COST_SAVINGS)
        why += ("; the pre-approval names business and the flight is over 10 hours (line 135), but the traveller asks "
                "for economy, which the class table permits")
    return answer(Decision.BOOK, lowest, reasons, ON_FILE, AIR, why + ".")


def business_offers(on_trip):
    """Business offers whose every flight is over 10 hours (line 135), checked for offers a reading could add."""
    offered = in_cabin(on_trip, Cabin.BUSINESS)
    qualifying = cheapest([offer for offer in offered if over("over-ten", offer) is True])
    if any(over("over-ten", offer) is None for offer in offered):
        raise ValueError("a business fare on a flight mix across 10 hours is not modelled")
    return qualifying


def journey_over(rule, offer):
    """The other reading of 'Flying Time (per flight)' (line 132) on a connection: the one-way journey is the
    flight, and its flights' scheduled minutes are added (never ground time)."""
    return sum(segment.scheduled_minutes for segment in offer.segments) > LIMITS[rule]


LONG_FLIGHT = [ReasonCode.LONG_FLIGHT_APPROVED, ReasonCode.INTERNATIONAL_LONG_FLIGHT]


def business(trip, on_trip, form):
    """A business request. Line 135: 'Over 10 hours ... Business (subject to prior agreement with DBT Contract
    Manager)', per flight (line 132). The agreement is the pre-approval form naming business (lines 339-345).
    A connection under 'per flight' is open (module docstring), so the cheapest business fare whose flights add
    to over 10 hours is accepted beside the per-flight answer."""
    if higher_cabin(trip):
        raise ValueError("a business request with a Director's note on file is not modelled")
    qualifying = business_offers(on_trip)
    journey = cheapest([offer for offer in in_cabin(on_trip, Cabin.BUSINESS) if journey_over("over-ten", offer)])
    if journey and form.cabin != Cabin.BUSINESS and journey != qualifying:
        raise ValueError("a connection's business fare without business agreed is not modelled")
    if not qualifying:
        if journey:
            return answer(Decision.BOOK, [*lowest_economy(on_trip), *journey],
                          [ReasonCode.UPGRADE_NOT_ELIGIBLE, ReasonCode.LONG_FLIGHT_CONDITION_NOT_MET, *LONG_FLIGHT],
                          ON_FILE, AIR,
                          "Lines 132-135: business is the class only for a flight over 10 hours. The business seats "
                          "still on sale are on a connection whose flights are each 10 hours or less, so per flight "
                          "business is not allowed and the traveller asked for economy then: the lowest logical fare "
                          "(line 119). The handbook does not say whether a connection is one flight; read as one, its "
                          "flying time is over 10 hours and the form naming business allows its business fare (line "
                          "135). Either is accepted.")
        return answer(Decision.BOOK, lowest_economy(on_trip),
                      [ReasonCode.UPGRADE_NOT_ELIGIBLE, ReasonCode.LONG_FLIGHT_CONDITION_NOT_MET], ON_FILE, AIR,
                      "Lines 132-135: business is the class only for a flight over 10 hours, counted per flight. The "
                      "business seats still on sale are on a connection whose flights are each 10 hours or less "
                      "(economy, lines 133-134), so business is not allowed; the traveller asked for economy then: the "
                      "lowest logical fare (line 119).")
    if form.cabin == Cabin.BUSINESS:
        if journey != qualifying:
            return answer(Decision.BOOK, [*qualifying, *journey], LONG_FLIGHT, ON_FILE, AIR,
                          "Line 135: the nonstop is over 10 hours, so business is the class, subject to the Contract "
                          "Manager's prior agreement, which the signed pre-approval form naming business gives. Per "
                          "flight, a cheaper business fare on a connection whose flights are each 10 hours or less is "
                          "not allowed (lines 132-134), so the lowest logical business fare is the nonstop (line 119). "
                          "The handbook does not say whether a connection is one flight; read as one, its flying time "
                          "is over 10 hours and its cheaper business fare is the lowest logical one. Either is accepted.")
        return answer(Decision.BOOK, qualifying, LONG_FLIGHT,
                      ON_FILE, AIR,
                      "Line 135: the nonstop is over 10 hours, so business is the class, subject to the Contract "
                      "Manager's prior agreement, which the signed pre-approval form naming business gives. The lowest "
                      "logical business fare (line 119).")
    if form.cabin != Cabin.ECONOMY:
        raise ValueError("a pre-approval naming another cabin is not modelled")
    return answer(Decision.FLAG_FOR_APPROVAL, qualifying, [ReasonCode.APPROVAL_REQUIRED,
                                                           ReasonCode.INTERNATIONAL_LONG_FLIGHT],
                  [Approver.CONTRACT_MANAGER], [*AIR, Clause.EXPENSE_PRE_APPROVAL],
                  "Line 135: the nonstop is over 10 hours, so business may be used, but only 'subject to prior "
                  "agreement with DBT Contract Manager'; the pre-approval on file names economy, and travel may not be "
                  "purchased without the Contract Manager's written pre-approval (line 58). The traveller would rather "
                  "wait for business: hold the lowest business fare for the Contract Manager.")


def first(trip, on_trip, form):
    """A first-class request. Line 138: the Director may allow 'the next higher class (but not first class)'; the
    class table never gives first (lines 132-135). A Director's note for first is therefore of no effect."""
    note = higher_cabin(trip)
    if note is None or note.cabin != Cabin.FIRST or form.cabin != Cabin.BUSINESS:
        raise ValueError("a first-class request is only modelled with a Director's note for first and business agreed")
    qualifying = business_offers(on_trip)
    if not qualifying:
        raise ValueError("a first-class request with no business fare over 10 hours is not modelled")
    # The Director's note is invalid for first, which is what the case tests, so DIRECTOR is not accepted.
    return answer(Decision.BOOK, qualifying, [ReasonCode.FIRST_CLASS_NOT_PERMITTED, ReasonCode.UPGRADE_NOT_ELIGIBLE],
                  ON_FILE, AIR,
                  "Lines 137-138: the Director may allow the next higher class, 'but not first class', so the note "
                  "for first has no effect. Line 135: the nonstop is over 10 hours and the pre-approval names business, "
                  "so business is what the policy allows: the lowest logical business fare (line 119).")


def premium(trip, on_trip, reason):
    """Premium economy under the Director's authority (lines 137-145), the next higher class above economy on
    flights over 5 hours (line 134). A flight of 5 hours or less is in the row with no asterisk (line 133)."""
    note = higher_cabin(trip)
    if note is None or note.cabin != Cabin.PREMIUM_ECONOMY:
        raise ValueError("premium economy without the Director's note for it is not modelled")
    offered = in_cabin(on_trip, Cabin.PREMIUM_ECONOMY)
    allowed = cheapest([offer for offer in offered if over("over-five", offer) is True])
    unclear = cheapest([offer for offer in offered if over("over-five", offer) is None])
    if allowed and unclear:
        raise ValueError("premium economy offers both allowed and unclear are not modelled")
    if allowed:
        return answer(Decision.BOOK, allowed, [reason, ReasonCode.NEXT_CLASS_UP_AUTHORISED, ReasonCode.PREMIUM_ECONOMY_ALLOWED],
                      [*ON_FILE, Approver.DIRECTOR], AIR,
                      "Lines 133-134 and 137-143: every flight is over 5 hours, where economy is the class 'but see "
                      "below*', and the Director's note on file allows the next higher class on one of the listed "
                      "grounds; economy is sold out and the date cannot move. The cheapest premium economy fare.")
    if not unclear:
        raise ValueError("a premium economy request with no premium economy offer is not modelled")
    if reason != ReasonCode.NEXT_CLASS_UP_AUTHORISED:
        raise ValueError("an unclear premium economy fare with economy sold out is not modelled")
    return answer(Decision.FLAG_FOR_APPROVAL, [*unclear, *lowest_economy(on_trip)], UNCLEAR_REASONS, UNCLEAR_ROLES,
                  AIR,
                  "Lines 132-134: one flight is over 5 hours and the other is 5 hours or less. Only the 'Over 5 hours' "
                  "row carries '(but see below*)', so the Director's next higher class may not reach the short flight; "
                  "yet the footnote's grounds include short duty visits out and back in a day, which are short flights. "
                  "The offer sells premium economy on both flights. Hold the premium economy fare (or the economy fare "
                  "of the stricter reading).", phrase=SHORT_FLIGHT_PHRASE)


def open_return(trip, on_trip):
    """Line 146: 'All flights must be booked at set dates, no open return tickets may be booked.'"""
    if trip.requested_cabin != Cabin.ECONOMY:
        raise ValueError("an open-return request outside economy is not modelled")
    return answer(Decision.BOOK, lowest_economy(on_trip), [ReasonCode.OPEN_TICKET_NOT_ALLOWED], ON_FILE, AIR,
                  "Line 146: flights are booked at set dates and no open return ticket may be booked, so only the "
                  "flight out on its set date is bought: the lowest logical fare (line 119). The return is booked "
                  "separately once its date is set.")


def airline_choice(trip, on_trip):
    """Line 119: the lowest logical fare; lines 107-109: no benefit from loyalty-scheme points or rewards."""
    lowest = lowest_economy(on_trip)
    if any(offer.carrier == trip.chosen_airline for offer in lowest):
        raise ValueError("a chosen airline at the lowest fare is not modelled")
    if not any(offer.carrier == trip.chosen_airline for offer in in_cabin(on_trip, Cabin.ECONOMY)):
        raise ValueError("a chosen airline with no offer is not modelled")
    # The airline is declined because it is dearer than the lowest logical fare, and for the points, so both codes.
    return answer(Decision.BOOK, lowest, [ReasonCode.LOWEST_FARE, ReasonCode.LOYALTY_PROGRAM_PREFERENCE], ON_FILE,
                  [*AIR, Clause.CLAIMING_REIMBURSEMENT],
                  "Line 119: the lowest logical fare; the chosen airline costs more. Lines 107-109: Suppliers must not "
                  "derive a benefit from loyalty-scheme points or rewards on travel paid for by the taxpayer, so the "
                  "status the traveller is after is no reason to pay more.")


def leisure(trip, seated):
    """Lines 65-67 and 124-130: personal time at the start or end of a business trip is told to the Contract
    Manager, and the Supplier covers the extra cost 'if earlier or later return flights are more expensive than
    flights that would have been taken purely for the purposes of the business trip' (strict: equal is not more)."""
    if not trip.leisure_notified or not trip.work_only_date or trip.requested_cabin != Cabin.ECONOMY:
        raise ValueError("leisure days are only modelled when notified, with a work-only date, in economy")
    later = lowest_economy([offer for offer in seated if leaves(offer) == (trip.origin.code, trip.travel_date)])
    plain = lowest_economy([offer for offer in seated if leaves(offer) == (trip.origin.code, trip.work_only_date)])
    clauses = [*AIR, Clause.EXPENSE_PRE_APPROVAL, Clause.PURPOSE]
    if later[0].fare_cents <= plain[0].fare_cents:
        return answer(Decision.BOOK, later, [ReasonCode.PERSONAL_TIME_NO_EXTRA_COST, ReasonCode.LOWEST_FARE], ON_FILE,
                      clauses,
                      "Lines 124-130: the later flight is not more expensive than the lowest fare on the day the work "
                      "ends, so the leisure days add no cost; the Contract Manager has been told (lines 65-66). Book the "
                      "lowest fare on the day the traveller asked for.")
    # The later flight costs more, so the contract does not cover it in full; the traveller asked, in that case,
    # for the flight home it does cover: the lowest fare on the work-only date (the request says so).
    return answer(Decision.BOOK, plain, [ReasonCode.PERSONAL_TIME_EXTRA_COST, ReasonCode.PERSONAL_TRAVEL_NOT_COVERED],
                  ON_FILE, clauses,
                  "Lines 124-130 and 66-67: the later flight is more expensive than the flight purely for the business "
                  "trip, so the leisure days add a cost the Supplier would have to cover; the traveller asked for the "
                  "flight the contract covers in that case: the lowest fare on the day the work ends.")


def rail(trip, seated):
    """Lines 147-152: air within the UK is not normally used, with an exception for travel to/from Scotland, and
    'Domestic flights should only be taken when they are more economical than rail' (strict)."""
    if trip.origin.country != "GB" or not trip.rail_to_airport or trip.requested_cabin != Cabin.ECONOMY:
        raise ValueError("a rail option is only modelled from a UK airport in economy")
    through_offers = [offer for offer in seated if leaves(offer) == (trip.origin.code, trip.travel_date)]
    if not all(airport(offer.segments[0].destination).country == "GB" for offer in through_offers):
        raise ValueError("a through fare whose first flight leaves the UK is not modelled")
    through = lowest_economy(through_offers)[0]
    onward = [offer for offer in seated if leaves(offer) == (trip.rail_to_airport, trip.travel_date)]
    by_rail = lowest_economy(onward)
    # Two ways to price the domestic flight: the whole through fare against rail plus the lowest onward fare, or
    # the through fare against rail plus the same onward flight bought alone. Only cases where both agree.
    same = [offer for offer in in_cabin(onward, Cabin.ECONOMY)
            if offer.segments[0].flight_number == through.segments[1].flight_number]
    tests = [through.fare_cents < by_rail[0].fare_cents + trip.rail_fare_cents]
    tests += [through.fare_cents < offer.fare_cents + trip.rail_fare_cents for offer in same]
    if any(tests):
        raise ValueError("a domestic flight more economical than rail on some reading is not modelled")
    return answer(Decision.BOOK, by_rail, [ReasonCode.RAIL_PREFERRED, ReasonCode.COST_SAVINGS], ON_FILE, AIR,
                  "Lines 147-152: air from Scotland is the exception to no air within the UK, but domestic flights "
                  "should only be taken when more economical than rail; the through fare from Edinburgh costs more "
                  "than the train to London plus the lowest fare from Heathrow, so the traveller goes by rail and the "
                  "ticket is the lowest logical fare from Heathrow (line 119).")
