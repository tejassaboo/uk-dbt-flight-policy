# UK DBT Supplier Travel Flight Booking

The handbook is the UK Department for Business and Trade's *Contract Schedule 31: Travel & Subsistence Expenses
Policy* (supplier travel to and within Japan for Expo 2025, v1.0 June 2024), a public contract schedule bundled
verbatim for research. No affiliation with the Department. Its public URL is not yet confirmed (the pinned copy is
the raw PDF in `pilot_work/originals/`), so confirm it before publishing this plugin.

A `nanoagent.plugin/v0001` plugin. An agent handles one supplier traveller's flight request under the schedule: it
reads the trip record, searches a simulated flight world (fares in GBP pence) and submits **BOOK**, **REFUSE** or
**FLAG_FOR_APPROVAL** with the offer, cabin, reason, approver and handbook section. A deterministic Python
verifier, with no LLM, rebuilds the offers and the handbook's answer itself and checks every field.

## The handbook and the harness flag

The frozen text (`src/plugin/data/policy.txt`, 2,854 words, sha256 `8af479aa...4e33`) is never paraphrased, and
the task text restates no rule. Under stock NanoAgent the agent does not see it: the plugin then runs as the `off`
baseline. The `harness.policy` switch of the NanoAgent fork (github.com/tejassaboo/nanoagent, branch
`policy-switch`) adds it to the system prompt: `harness.policy: full` adds all of it, and the selection methods add
parts of it. These plugins are meant to run with `query: instructions+input`, so a selector sees the traveller's
request.

The schedule binds the Supplier, who books its own travel and claims it from the Department. "BOOK" is the ticket
bought under the schedule; "REFUSE" means the schedule pays for no ticket for the request. Every claimable trip is
UK to Japan or within Japan. The world has Tokyo (HND, NRT) but no Osaka airport, so trips fly to Tokyo and go on by
rail; the Osaka subsistence rate table is an image in the source and is never tested.

## Task

- **Input:** `TaskInput`: `scenario` (one of 16 case ids) and `request`, the traveller's own words.
- **Steps:** `get_trip`, then `search_flights` on the trip's route and date (and on an alternative airport or date
  the record gives: `fennel-arch`, `garnet-mere`, `iris-tarn`), then `submit` (3 or 4 of the 6 hosted steps).
- **Output:** `BookingOutput`: `decision`, `offer_id` (empty when refusing), `cabin` (`NONE` when refusing),
  `reason_code`, `approver` and `clause`, each from a closed list. The reason list is shared by every handbook
  plugin and holds codes for rules this handbook lacks, plus decoy codes from other handbooks' rules. Every trip
  has the Contract Manager's signed pre-expense authorisation on file, so bookings accept `CONTRACT_MANAGER` or
  `NONE` (template SYNC_NOTES 4'); a hold awaiting a sign-off accepts only the awaited roles.
- **Success:** every field is one the answer key accepts. Score = fields right / 6.

| Scenario | Category | Expected decision (offer) | Reason | Approver | Clause cited (frozen lines) |
|---|---|---|---|---|---|
| `alder-pennant` | easy | BOOK (nh-economy, ECONOMY) | COST_SAVINGS or LOWEST_FARE | CONTRACT_MANAGER or NONE | AIR_TRAVEL or POLICY_STATEMENT (119; 131-135; 58) |
| `bramble-coil` | easy | BOOK (dubai-economy, ECONOMY) | LOWEST_FARE | CONTRACT_MANAGER or NONE | AIR_TRAVEL or POLICY_STATEMENT (119; 131-135; 58) |
| `cobalt-weir` | easy | BOOK (ba-economy, ECONOMY) | COST_SAVINGS or LOWEST_FARE | CONTRACT_MANAGER or NONE | AIR_TRAVEL or POLICY_STATEMENT (119; 131-135; 58) |
| `damson-ridge` | boundary_twin | BOOK (jl-business, BUSINESS) | INTERNATIONAL_LONG_FLIGHT or LONG_FLIGHT_APPROVED | CONTRACT_MANAGER or NONE | AIR_TRAVEL or POLICY_STATEMENT (131-135; 339-345; 119) |
| `elder-sound` | boundary_twin | BOOK (doha-economy, ECONOMY) | LONG_FLIGHT_CONDITION_NOT_MET or UPGRADE_NOT_ELIGIBLE | CONTRACT_MANAGER or NONE | AIR_TRAVEL or POLICY_STATEMENT (131-135; 119; 339-345) |
| `fennel-arch` | boundary_twin | BOOK (mon-jl-economy, ECONOMY) | LOWEST_FARE or PERSONAL_TIME_NO_EXTRA_COST | CONTRACT_MANAGER or NONE | AIR_TRAVEL or EXPENSE_PRE_APPROVAL or POLICY_STATEMENT or PURPOSE (124-130; 65-68; 119) |
| `garnet-mere` | boundary_twin | BOOK (fri-nh-economy, ECONOMY) | PERSONAL_TIME_EXTRA_COST or PERSONAL_TRAVEL_NOT_COVERED | CONTRACT_MANAGER or NONE | AIR_TRAVEL or EXPENSE_PRE_APPROVAL or POLICY_STATEMENT or PURPOSE (124-130; 65-68; 119) |
| `heather-vane` | multi_rule | BOOK (jl-business, BUSINESS) | FIRST_CLASS_NOT_PERMITTED or UPGRADE_NOT_ELIGIBLE | CONTRACT_MANAGER or NONE | AIR_TRAVEL or POLICY_STATEMENT (137-138; 131-135; 144; 119) |
| `iris-tarn` | multi_rule | BOOK (lhr-jl-economy, ECONOMY) | COST_SAVINGS or RAIL_PREFERRED | CONTRACT_MANAGER or NONE | AIR_TRAVEL or POLICY_STATEMENT (147-149; 151-152; 119) |
| `juniper-loft` | multi_rule | BOOK (nh-economy, ECONOMY) | OPEN_TICKET_NOT_ALLOWED | CONTRACT_MANAGER or NONE | AIR_TRAVEL or POLICY_STATEMENT (146; 119) |
| `kestrel-moor` | hidden_clause | BOOK (nh-economy, ECONOMY) | LOWEST_FARE or LOYALTY_PROGRAM_PREFERENCE | CONTRACT_MANAGER or NONE | AIR_TRAVEL or CLAIMING_REIMBURSEMENT or POLICY_STATEMENT (107-109; 119) |
| `linnet-brook` | hidden_clause | BOOK (dubai-premium, PREMIUM_ECONOMY) | NEXT_CLASS_UP_AUTHORISED or NO_ECONOMY_SEATS_URGENT or PREMIUM_ECONOMY_ALLOWED | CONTRACT_MANAGER or DIRECTOR or NONE | AIR_TRAVEL or POLICY_STATEMENT (131-135; 142-143; 119) |
| `marram-spit` | distractor | BOOK (jl-economy, ECONOMY) | LOWEST_FARE | CONTRACT_MANAGER or NONE | AIR_TRAVEL or POLICY_STATEMENT (119; 58) |
| `nettle-fold` | refusal | REFUSE (none, NONE) | OUTSIDE_POLICY_SCOPE or PERSONAL_TRAVEL_NOT_COVERED or WEEKEND_TRAVEL_HOME | CONTRACT_MANAGER or NONE | NON_REIMBURSABLE or PURPOSE (20-24; 235-236; 10-15) |
| `osprey-cairn` | flag | FLAG_FOR_APPROVAL (jl-business, BUSINESS) | APPROVAL_REQUIRED or INTERNATIONAL_LONG_FLIGHT | CONTRACT_MANAGER | AIR_TRAVEL or EXPENSE_PRE_APPROVAL or POLICY_STATEMENT (131-135; 58; 339-345) |
| `plover-reach` | flag | FLAG_FOR_APPROVAL (hongkong-economy, hongkong-premium, ECONOMY/PREMIUM_ECONOMY) | APPROVAL_REQUIRED or UNCLEAR_POLICY_TEXT | CONTRACT_MANAGER or DIRECTOR or NOT_NAMED | AIR_TRAVEL or POLICY_STATEMENT (131-135; 144; 140-141) |

Mix (EDGE_CASES.md 5.2, the 16-scenario row): 3 easy, 4 boundary twins, 3 multi-rule, 2 hidden clause, 1
distractor, 1 refusal, 2 flags (12.5%). `plover-reach` holds over the unclear words "Over 5 hours ... Economy (but
see below*)" (twins `linnet-brook` and `bramble-coil`); `osprey-cairn` is an approval-required hold (twins
`damson-ridge` and `elder-sound`), which is never the same as "no compliant offer".

## Tools

| Tool | Does | Code |
|---|---|---|
| `booking_requirements` | The trip record's fields, the world's conventions (local times, dates, fares, sold-out seats) and its airports | `src/plugin/guide.py` |
| `get_trip` | A case's request and trip record: traveller, route, dates, purpose, requested cabin, airline and ticket, leisure days, a train option, sign-offs | `src/plugin/tools.py` |
| `search_flights` | Every offer on a route and local date: the pinned scenario offers; a search the case does not pin lists nothing and says so | `src/plugin/world.py` |
| `solve_booking` | The answer key (`rules.solve`), the agent task's `reference`, never shown to the agent | `src/plugin/rules.py` |

| Task | Does | Runner |
|---|---|---|
| `book-uk-dbt-flight` | Handles one booking request | `agent`, with `get_trip` and `search_flights`; reference `solve_booking` |
| `booking-requirements` | Shows `booking_requirements` | `tool` |
| `search-flights` | Shows `search_flights` | `tool` |

## Layout

- `contract.py`: the template's shared contract plus this handbook's scenario ids, approvers, sections and trip record.
- `src/plugin/`: `world.py` (the simulated world: real airports and airline hubs, distance-based times
  and fares, hash-seeded background offers and opaque offer ids), `scenarios.py`, `guide.py`,
  `answer.py`, `tools.py`, `rules.py` (this handbook's rules, citing frozen lines), `__main__.py`.
- `src/plugin/data/`: `policy.txt` (frozen), `handbook.json`, `scenarios/*.json`.
- `verifier/`: byte-identical copies of `world.py`, `scenarios.py`, `guide.py`, `answer.py` and
  `rules.py`, plus `booking.py` (`verify_task`) and `tools.py` (`verify_input`, `verify_output`).
- `tests/`: the template's acceptance suite; `tests/plugin_spec.py` holds this handbook's settings,
  `tests/build_scenarios.py` writes the scenario JSON, and `tests/BUILD_NOTES.md` records the build.

## Develop and run

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv lock --check
# from a NanoAgent checkout:
nanoagent plugin inspect <this folder>
```

Offline: `hosts: []`, an empty `.env`, `write: []`, no clock (each case fixes its `booking_date`).
