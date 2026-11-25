# Validation notes: uk-dbt-flight-policy (wave 4, 2026-11-25)

The first paid validation of this plugin, judged to the method of
`efficient_corporate_travel_agent/pilot/ladder/runs/validation_w2_2026-11-25/VALIDATION.md` (APPROVER_REVIEW Q1-Q3,
approver rule 4', the declined-request reason rule). Line numbers are lines of `src/plugin/data/policy.txt`.

## What ran

- Arm `full`, once per scenario: 16 runs at head 0fd7599. DeepSeek V4 Flash (`deepseek/deepseek-v4-flash-0731`),
  Nebius fp8 pinned, temperature 0, max_steps 6, max_tokens 8192, `token_limit` 262144, `hosted_token_limit` 65536.
- Results: `efficient_corporate_travel_agent/pilot/ladder/runs/validation_w4_2026-11-25/` (`analysis.json`, key
  `uk-dbt-flight-policy@w4`; run folders `uk-dbt-flight-policy@w4/val_full/<scenario>/r1/`; event streams in
  `.events/`).
- **12/16 valid (75.0%), easy 3/3**, mean field score 0.875, billed $0.0202 ($0.00126 per run), 4.1 model calls per run,
  no hosted-cap overrun, no errors.

## Every failure, classified

| scenario | category | submitted vs key | class | evidence |
|---|---|---|---|---|
| damson-ridge | boundary_twin | Qatar business KPE2-ZE7W (2,680.00) via Doha, LONG_FLIGHT_APPROVED; key JAL business HTV2-MB8E (4,058.00) | **scenario defect: the measure is undefined for a connection** | It quoted the table and read the one-way journey as the flight: "The LHR-HND flight is over 10 hours (~13.75 hours) ... Among the business offers, the lowest logical fare is Qatar Airways at £2,680". Line 132 says only "Flying Time (per flight)"; nothing says whether a connection is one flight or two. The listing gives the offer `flying_minutes: 995`. On that reading the Qatar fare is the lowest logical business fare (line 119) under the form naming business (line 135). The fleet's own rule treats this wording as open: EDGE_CASES 3.4 (TT's "scheduled time of the flight" is "not defined for a connection": keep qualifying cases on nonstops or make every reading agree) and TEMPLATE_GUIDE (the duration hook: "a connection under a per-flight rule" is a real gap). The key's per-segment reading is also defensible. |
| elder-sound | boundary_twin | Qatar business 2M38-4QVV, LONG_FLIGHT_APPROVED; key Qatar economy 4R5Y-R9FR, UPGRADE_NOT_ELIGIBLE or LONG_FLIGHT_CONDITION_NOT_MET | **scenario defect (same)** | "The flight is over 10 hours (LHR to HND is ~13-14 hours). So Business is permitted ... The only business offer with seats available is Qatar Airways". It is the twin's reading applied to the same record. The pair differs only in whether the nonstop business seats are on sale, so both twins turn on the open word. No reading makes them agree: every London-Tokyo connection adds to more than 600 minutes. |
| garnet-mere | boundary_twin | **no submission**: `max_steps_reached` at step 6 (TaskNotSubmitted); key Friday ANA KJNR-X2TZ, PERSONAL_TIME_EXTRA_COST or PERSONAL_TRAVEL_NOT_COVERED | model slip (tool-call repetition) | Not tokens, not an error. The six calls were get_trip, search 2 June, the **same** search again, and again, then search 30 May, and the **same** search again. Steps 2 and 3 repeat the reasoning word for word ("So we need to search flights HND to LHR on 2025-06-02. Let me search."), and so do steps 5 and 6. By step 5 it had every fare and had set up the right test ("is the Monday flight more expensive than the flight that would have been taken purely for business"). Usage: 52,657 tokens in total, largest call 11,273 prompt tokens and 472 completion, against caps of 65,536 hosted, 262,144 and 8,192. The task needs 4 steps (README: 3 or 4 of 6). The twin fennel-arch, on the same request and searches, submitted in 4 and passed. The tool outputs were the same each time and complete. |
| plover-reach | flag | BOOK Cathay premium economy X6TJ-WJ72, NEXT_CLASS_UP_AUTHORISED, DIRECTOR; key FLAG (either fare) | model slip | "The flight is over 10 hours (flying minutes 1005 = ~16.75 hours) ... So book X6TJ-WJ72 in PREMIUM_ECONOMY". It never looked at the 240-minute Hong Kong-Haneda flight, so it never weighed line 133 (plain economy, no asterisk) against the footnote's short-visit ground (lines 140-141). It took one reading as settled, which is the fleet's usual flag slip. The connection reading above also leads to premium economy, but the strict per-flight reading still gives economy on the short flight. The readings disagree, so the hold stays right. |

The twin pair failing together pointed to the record, and it was the record. Three of three runs that met a
connection treated it as one flight (damson-ridge, elder-sound, plover-reach).

## Fix (no id, request, trip, world or category changed)

- `rules.py` (both copies byte-identical): a business request accepts the cheapest business fare under either
  reading of "per flight": per segment, as before, or the one-way journey with its flights added (`journey_over`,
  never ground time). The module docstring records the open word. `over()` is unchanged for every other rule.
- Keys changed, from regenerated JSON (`uv run python tests/build_scenarios.py`; only these two files differ, and only
  in `expected` and `design_notes`):
  - damson-ridge: offers `jl-business` and `doha-business`, BUSINESS, the same two reason codes.
  - elder-sound: offers `doha-economy` and `doha-business`; the cabin follows the offer. Reasons UPGRADE_NOT_ELIGIBLE,
    LONG_FLIGHT_CONDITION_NOT_MET, LONG_FLIGHT_APPROVED or INTERNATIONAL_LONG_FLIGHT.
- README rows updated. Nothing was widened for a slip: garnet-mere and plover-reach keep their keys.
- Q2: the always-cheapest agent books Qatar economy with LOWEST_FARE. It fails both twins, as before: in damson-ridge
  the cabin is wrong, and in elder-sound LOWEST_FARE is not accepted. It still passes 6/16 (37.5%) and the always-flag
  agent 1/16. The twins still separate an agent: in damson-ridge economy is wrong, and in elder-sound the sold-out
  nonstop cannot be booked.
- Q3: both accepted Qatar fares are on a ticket the text allows on one of its readings. Every other key is unchanged.

## Re-score of the stored paid answers at the new head (no paid call)

`scratchpad/uk-dbt-validation/rs.py`: **14/16 (87.5%), easy 3/3**. damson-ridge and elder-sound now pass. garnet-mere
(no submission) and plover-reach (slip) still fail. No request changed since the run.

## Re-runs

- **Required: none.** No scenario's request, trip record or listing changed, so every stored answer re-scores.
- Optional, variance only (about $0.004): garnet-mere, to see whether the repeated-call loop recurs. damson-ridge and
  elder-sound would confirm the fix. If a re-run of plover-reach books again, it is the same slip class. Do not
  convert it: the text has two open readings.

## Checks at the new head

```
uv run pytest -q                       162 passed
uv run ruff check .                    All checks passed!
uv lock --check                        Resolved 42 packages
python3 ../_template/check_shared.py . : ok
rules.py copies                        identical
stock_verify.py (nanoagent venv)       16 scenarios, 0 failures
stock nanoagent plugin inspect .       exit 0
```

## Verdict

**Pass after fix.** 12/16 valid, easy 3/3. The twin pair was a scenario defect, now fixed. Re-scored: 14/16 = 87.5%.
The two remaining failures are model slips: a repeated-call loop that ran out of steps, and a flag answered as a
booking.
