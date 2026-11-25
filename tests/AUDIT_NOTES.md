# Audit notes: uk-dbt-flight-policy (2026-11-25)

This file is under tests/ because stock `nanoagent plugin inspect` rejects extra files at the plugin root.

This is an independent audit of the build at b15f9c8, done to `pilot_work/tier_plan/build/WAVE3_AUDIT_BRIEF.md`. I
re-derived every answer from the frozen handbook (`src/plugin/data/policy.txt`, 363 lines) and the tool outputs the
agent sees (`get_trip` and every pinned `search_flights` listing, arrival times included), then compared each with
every accept set. The standard was WAVE3_BUILD_BRIEF.md (all 12 lessons), MASTER_PLAN section 4, EDGE_CASES
sections 1-3 and 5, and the worked audits (fedex-office, goodman-networks, hillrom, georgia-sao).

**Verdict: pass after fixes.** The key was right on all 14 non-flag scenarios and both flags are sound. The fixes
are in task instructions, request and trip-record wording, and one accept set. No decision, offer, fare, flight or
offer id changed.

## 1. Dates: what "today" is (the priority check)

The handbook covers only "official travel to and from Expo 2025 in Japan" (line 10), so the trips must fall in
2025, inside or just before the Expo (13 April to 13 October 2025). Every other plugin dates its trips in late 2026
or 2027; this one is the only plugin whose dates lie before the real date of the paid runs.

What the agent sees:

- The NanoAgent harness injects no current date into the system prompt (grepped `nanoagent/src`: no `today`
  formatting into prompts), so the agent's only "today" is what the case gives it.
- The trip record's `booking_date` is described as "Today in this world" in `contract.Trip`, and the convention
  "The trip record's booking_date is today in this world" is listed by `booking_requirements`. **But the booking
  task's tools are only `get_trip` and `search_flights`**: the agent never sees that convention, and the field
  descriptions sit in the output schema, which the model is not shown. So the agent saw a bare
  `booking_date: 2025-03-17`. A careful model with a 2026 sense of the date might then call the travel date past
  or Expo 2025 over, and REFUSE: a mass false-failure risk across all 16 cases.

Checked for every scenario: every sign-off's `given_on` comes before `booking_date`, and `booking_date` comes before
every pinned search date (travel date and the Friday alternative). All dates are on or before the Expo's close.
`alder-pennant` (8 April, fit-out meetings) and `linnet-brook` (10 April, opening rehearsal) come before the
13 April opening, which fits what each trip is for. `osprey-cairn` (1 October, "closing fortnight") is 12 days
before the close. The weekdays in the requests are right (Friday 30 May, Monday 2 June, Friday 13 June,
Wednesday 9 and 16 July, Friday 4 July 2025). The shared world handles the dates: `search_slots` measures every
search from `booking_date` (0 to 330 days ahead), every pinned search resolves, and a search dated before the
booking date is rejected. There is no wall clock anywhere.

**Fix:** the task instructions' conventions line now ends "The trip record's booking_date is today, the day the
ticket is bought." That puts "today" in front of the agent in every case, so every travel date reads as future and
the Expo as running. I kept the 2025 dates because moving them to 2026/2027 would put the trips outside "Expo 2025"
(line 10), which would make REFUSE defensible everywhere.

## 2. Defects found and fixed

| # | Scenario(s) | Class | Defect | Fix |
|---|---|---|---|---|
| 1 | all 16 | hidden "today" (see section 1) | The agent was never told that `booking_date` is today, and the dates are in 2025. | Added the sentence above to the `book-uk-dbt-flight` instructions (nanoagent.yaml). |
| 2 | linnet-brook, plover-reach, heather-vane | ambiguous signer | "My director has signed off ...", said by a Supplier's employee, reads as the Supplier's own director. The footnote needs "the DBT Director for the relevant business area" (line 137). In `linnet-brook` a careful agent could then judge the note invalid and, with economy sold out, FLAG or REFUSE instead of the keyed BOOK. | Each request now says "The Department's director for the pavilion programme has ..." (a fact about who signed, not the rule's wording). |
| 3 | heather-vane | inconsistent record | The request says "I go straight into the pavilion handover when I land", but the purpose said "the day after landing". | The purpose is now "... on arrival (onward by rail from Tokyo)". No answer turns on it (the note for first is void). |
| 4 | damson-ridge/elder-sound (both twins, identically), linnet-brook, kestrel-moor, marram-spit, osprey-cairn, alder-pennant, bramble-coil | arrival with no deadline (lesson 4, preventive) | "I have to be at the national day events" with no date, where the keyed JAL business lands at 18:15 against BA's 11:20. Likewise the rehearsal (EK 13:25 against QR 12:25), the round tables, the maintenance shift (JAL 18:15 against BA 08:05), the closing programme (held JAL 18:15 against BA 08:05), the fit-out and supplier meetings. | Each purpose names a start date two or more days after landing ("from 6 September", "on 12 April", "from 23 May", "from 12 July", "from 3 October", "from 10 April", "from 14 May"). The twins' requests both add "which start on 6 September"; linnet-brook's adds "on 12 April". |
| 5 | linnet-brook | accept set (lesson 5) | The premium economy is booked because it is allowed. PREMIUM_ECONOMY_ALLOWED is the natural code for that, and it was rejected. | Added to the accept set (rules.py, both copies byte-identical, and the README). |

## 3. Re-derivation, scenario by scenario

| Scenario | My answer from the text and the offers | Key | Agrees |
|---|---|---|---|
| alder-pennant | 820-830-minute nonstops; the form allows business, but the traveller asks for the cheapest economy. BA economy is sold out, so ANA economy 758.50. CM/NONE | same | yes |
| bramble-coil | economy on every flight (415 and 580 minutes); the traveller accepts a connection; EK 612.00 (it lands 20 minutes after JAL's nonstop, with meetings from 14 May) | same | yes |
| cobalt-weir | homeward, over 10 hours, the form allows business, the traveller asks for economy: BA 684.00 | same | yes |
| damson-ridge | per flight (line 132): QR's 405 and 590 minutes are each 10 hours or less, so its business is not allowed; nonstop business with the form: JAL 4,058.00 < BA 4,125.00 | same | yes |
| elder-sound | nonstop business sold out; QR business not allowed; the request's fallback is economy: QR 638.00. It lands at 12:25, before JAL, so it is a logical fare | same | yes |
| fennel-arch | Monday's lowest 651.20 is not "more expensive" than Friday's lowest 651.20; CM told: Monday JAL | same | yes |
| garnet-mere | Monday's lowest 655.20 is more than 651.20, so the extra would be the Supplier's; the traveller asked for the covered flight: Friday ANA | same | yes |
| heather-vane | "(but not first class)" (line 138) voids the note; the flights are over 10 hours and the form names business: JAL business 3,895.00 | same | yes |
| iris-tarn | the Scotland exception allows air, but line 152: through fare 984.00 against rail 98.50 + JAL 729.00 = 827.50, so rail and then JAL from Heathrow | same | yes |
| juniper-loft | line 146: no open return; the outbound date is set: ANA 742.00 non-refundable | same | yes |
| kestrel-moor | JAL 787.00 against ANA 742.00; lines 107-109 rule out the loyalty benefit and line 119 gives ANA anyway | same | yes |
| linnet-brook | economy sold out, the date fixed, every flight 405-595 minutes (the asterisked row); the DBT director's note: EK PE 1,268.00 | same | yes |
| marram-spit | early booking is "where possible" (lines 110-113); the form is signed; JAL 799.00 | same | yes |
| nettle-fold | a weekend trip home during a continuous posting (line 22): REFUSE | same | yes |
| osprey-cairn | business over 10 hours needs the CM's prior agreement; the form names economy and the traveller would rather wait: hold JAL business for the CONTRACT_MANAGER | same | yes |
| plover-reach | flag (see section 4) | FLAG, either fare | yes |

Always-cheapest agent: 6 of 16 (alder-pennant, bramble-coil, cobalt-weir, fennel-arch, kestrel-moor, marram-spit),
37.5%, unchanged. Always-flag: 1 (plover-reach).

## 4. The builder's unsure points, settled

- **plover-reach: is the asterisk's reach really unclear? Yes, keep the flag.** Lines 131-135 set the class
  "per flight", and only the "Over 5 hours" row carries "(but see below*)". Read literally, the 240-minute
  Hong Kong-Haneda flight is in the plain-economy row, so premium economy on it is not allowed and the request's
  fallback books economy. But the footnote's second ground, "short duty visits out and back in a working day"
  (lines 140-141), can only describe short flights: a London day trip out and back is flights of well under
  5 hours. That ground would be empty if the footnote reached only flights over 5 hours, so it implies the footnote
  reaches the short row too. Then the Director's note (work on arrival, line 144) covers the whole ticket and
  premium economy is booked. The rows also say "All journeys", while the header says "per flight". Both readings
  rest on the words, not on a misreading, and the case accepts both held fares, APPROVAL_REQUIRED or
  UNCLEAR_POLICY_TEXT, and DIRECTOR, CONTRACT_MANAGER or NOT_NAMED. The fix in section 2 #2 removes a second,
  unintended doubt (whose director signed).
- **iris-tarn: "Domestic flights should only be taken when they are more economical than rail", read as
  binding. Settled: the answer does not depend on it.** Section 4.11 opens softly ("Please have
  consideration"), but its last sentence is a plain directive ("should only"). If it were read as soft, line 119
  ("the lowest logical fare") still points the same way, because the through fare is 156.50 dearer than the
  train plus the Heathrow flight on either pricing (827.50 or 839.50 against 984.00). The request also states the
  fallback ("If the policy wants me on the train ... book the flight from Heathrow"). Every defensible reading books
  JAL from Heathrow.
- **heather-vane: the void Director's note. Settled: keep DIRECTOR out of the approvers.** Line 138 bars first
  class outright, so the note has no effect. The booking rests only on the Contract Manager's form naming
  business, the "prior agreement" of line 135. Under SYNC_NOTES 4' the approver is the sign-off the booking relies
  on: CONTRACT_MANAGER or NONE. Naming the Director would endorse an invalid sign-off, which is the template's
  invalid-sign-off exception.
- **No minute-level twins on the 5-hour and 10-hour bands. Justified.** The world has no Osaka or other
  Japanese airport besides HND and NRT, and in the UK only LHR, LGW and EDI. Every UK-Japan nonstop is 13-15 hours.
  A 300/301 twin needs a short flight, and the only one is the HKG-HND leg. That puts one side in `plover-reach`'s
  mixed-band case, which is a flag, so the pair would not be clear on both sides. A 600/601 twin on a connection
  has the same problem. Instead, the per-flight measure is twinned (`damson-ridge`/`elder-sound`), the
  personal-time rule has a true numeric twin (`fennel-arch`/`garnet-mere`: equal fares against 4.00 more), and
  `tests/test_duration.py` with `DURATION_CASES` covers 300/301 and 600/601 on both rules, connections included.
  The template change request in BUILD_NOTES section 7 (add KIX/ITM and more UK airports) would allow real band
  twins later.

## 5. Other checks

- Flags: 2 of 16 (12.5%). `osprey-cairn` is an approval hold (CONTRACT_MANAGER only, APPROVAL_REQUIRED or
  INTERNATIONAL_LONG_FLIGHT); its text is clear.
- Twins differ in one fact each: `damson-ridge`/`elder-sound` (whether nonstop business seats are on sale; the
  requests are identical) and `fennel-arch`/`garnet-mere` (Monday's JAL fare).
- No request carries rule wording or thresholds. The fallbacks (lesson 3) are present wherever the request names
  something the policy may forbid (heather-vane, kestrel-moor, juniper-loft, damson/elder, plover-reach, iris-tarn).
- The decline-reason sentence (lesson 12) is in the instructions. LOWEST_FARE is rejected on declined requests
  except `kestrel-moor`, where the lowest-fare rule itself is a ground for declining.
- Only named alternates are searched: the Friday date (`work_only_date`) and Heathrow (`rail_to_airport`).

## 6. Acceptance outputs (after the fixes)

```
$ uv run pytest -q
162 passed
$ uv run ruff check .
All checks passed!
$ uv lock --check
Resolved 42 packages
$ python3 ../_template/check_shared.py .
: ok
$ <nanoagent venv>/python ../_template/tools/stock_verify.py .
16 scenarios, 0 failures
$ <nanoagent venv>/nanoagent plugin inspect .
exit 0
```
