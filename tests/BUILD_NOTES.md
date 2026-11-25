# Build notes: uk-dbt-flight-policy (wave 3, 2026-11-24/25)

Built from `_template` with `instantiate.py` (slug `uk-dbt`, `--task-id book-uk-dbt-flight`, `--currency GBP`,
`--background 0`, `--scenarios 16`). Frozen handbook: `pilot_work/originals/uk-dbt/frozen/uk-dbt_policy.txt`,
2,854 words, 363 lines, sha256 `8af479aa...4e33` (raw PDF `8aa5889a...9774`). The size rule (EDGE_CASES 5.1) gives
24, but the wave 3b call (`pilot_work/originals/WAVE3B.md`) and the lead's brief set 16: every claimable trip is UK
to Japan or within Japan, so the route and duration space is narrow. The 24-mix scaled down is the template's
16-row: 3 easy, 4 boundary twins, 3 multi-rule, 2 hidden clause, 1 distractor, 1 refusal, 2 flags. Decisions were
taken without asking (the lead was away); each is recorded here.

## 1. What the handbook supports

Who books: the schedule binds the Supplier, which books its own travel and claims it from DBT (lines 10-15, 89-98,
235-238). BOOK is the ticket bought under the schedule; REFUSE means it pays for none.

| Lines | Clause | Operator / force | Used by |
|---|---|---|---|
| 119 | "book the lowest logical fare available" | expected (the default) | every booking |
| 51-52, 58, 95 | Contract Manager's written pre-approval before travel is reserved or purchased | mandatory | every trip record (form on file); osprey-cairn |
| 131-135 | class "Flying Time (per flight)": up to 5 h economy; over 5 h economy (but see below*); over 10 h business "subject to prior agreement with DBT Contract Manager" | strict "Over", per flight | alder-pennant, cobalt-weir, damson-ridge, elder-sound, heather-vane, linnet-brook, osprey-cairn, plover-reach |
| 137-145 | Director may allow the next higher class (never first) on five listed grounds | permissive, listed grounds | heather-vane, linnet-brook, plover-reach |
| 339-345 | the form records the class of travel and a justification for an upgrade | form fields | damson-ridge, elder-sound, osprey-cairn |
| 124-130, 65-68 | personal time: tell the Contract Manager; the Supplier covers extra cost "if earlier or later return flights are more expensive than" the business-only flights | strict "more expensive" | fennel-arch, garnet-mere |
| 146 | set dates only; "no open return tickets may be booked" | mandatory | juniper-loft |
| 147-152 | no air within the UK except to/from Scotland and NI, economy; "Domestic flights should only be taken when they are more economical than rail" | strict, directive | iris-tarn |
| 107-109 | no benefit from loyalty-scheme points on taxpayer-funded travel | mandatory | kestrel-moor |
| 20-24, 235-236 | claimable travel excludes "return journeys home at weekends during a continuous business location" | mandatory | nettle-fold |

Not used, because no booking decision turns on them: the three screenshot quotes (lines 120-123, Annex A; they go
with the pre-approval request, already signed in every case), the 5-day turnaround (lines 265-271), early booking
"where possible" (110-113, a distractor), taxis, rail class, insurance, passports, visas. No rule on several
travellers on one flight and none on overnight stops: those overlays are not required (`OVERLAY_MINIMUMS`). The
Osaka subsistence rate table (after line 114) is an image in the source: never tested.

## 2. World constraints and how they shaped the cases

- The shared world has Tokyo Haneda and Narita but **no Osaka airport** (KIX/ITM) and no other Japanese airport, and
  in the UK only LHR, LGW and EDI. So every trip flies UK-Tokyo (or back) and goes on to the Expo site in Osaka by
  rail, said in each purpose line; within-Japan flights cannot be tested. See section 7.
- Dates are in 2025 (the Expo ran April-October 2025); the world has no clock and accepts them.
- **No minute twins on the 5 h / 10 h bands.** On UK-Japan routes every nonstop is 13-15 hours and every connection
  either mixes bands (London-Hong Kong 765 + Hong Kong-Haneda 240) or has two flights between 5 and 10 hours (via
  Doha or Dubai). A one-minute twin needs a nonstop near 300 or 600 minutes, which no UK-Japan route has; a
  connection with one flight at 600/605 lands in the mixed case, which is unclear (see `rules.over`). Instead:
  - `damson-ridge`/`elder-sound` test the per-flight measurement: business agreed, a cheap Qatar business fare via
    Doha (405 + 590 minutes, 995 in all) and dearer nonstop business (825-830). One fact differs: nonstop business on
    sale (book JAL business, the dearer fare) or sold out (business not allowed on the Doha flights: book economy).
  - `fennel-arch`/`garnet-mere` are a true numeric boundary on the personal-time rule: Monday's lowest fare equal to
    Friday's (not "more expensive": book Monday) or 4.00 more (book Friday). This also covers month end (30 May to
    2 June) and date arithmetic.
  - `tests/test_duration.py` and `DURATION_CASES` cover 300/301 and 600/601 on both rules, connections included.

## 3. Unclear points and how they are handled

- **The asterisk's reach** (`plover-reach`, flag). Only the "Over 5 hours" row carries "(but see below*)"; the "Up to
  5 hours" row is plain economy; yet the footnote's grounds include "short duty visits out and back in a working
  day", which are short flights. With a Director's note for premium economy (work on arrival) on a London-Hong
  Kong-Haneda ticket (765 + 240 minutes), one reading keeps the short flight in economy (book economy), the other
  lets the note cover the journey (book premium economy). Hold either; reasons UNCLEAR_POLICY_TEXT or
  APPROVAL_REQUIRED (lesson 2); approvers NOT_NAMED, DIRECTOR, CONTRACT_MANAGER. Twins: `linnet-brook` (both flights
  over 5 h: premium economy) and `bramble-coil` (economy).
- **Mixed-band connections in general** (`rules.over` returns None). A business fare on a mixed connection raises
  ValueError: no scenario depends on it. `elder-sound`'s Doha business is not mixed (both flights at or under 10 h).
- **Approval required** (`osprey-cairn`): business on a 820-830-minute nonstop needs the Contract Manager's prior
  agreement; the form names economy and the traveller would rather wait. Hold JAL business for CONTRACT_MANAGER
  only. Twins `damson-ridge` (agreed: book business) and `elder-sound` (economy).
- **Director's note for first** (`heather-vane`): line 138 "(but not first class)" makes it void; the note's giver
  is not accepted as approver (the template's invalid-sign-off exception). Business is what the agreed form allows.
- **"Domestic flights should only be taken when ... more economical than rail"** (`iris-tarn`): two ways to price the
  domestic flight (through fare against rail plus the lowest Heathrow fare, or against rail plus the same BA flight
  alone). The numbers agree on both (827.50 and 839.50 against 984.00); `rules.rail` raises if they ever split.
- **Personal time**: the text says "earlier or later return flights"; the cases use a later flight home, which is the
  plain case. The request says what to do when the later flight costs more ("book me whichever flight home it does
  cover"), so the alternative reading (book Monday, the Supplier pays the difference) is not open. The request does
  not state the comparison rule itself.

## 4. Choices made without asking

1. Every trip record holds the Contract Manager's signed Pre-Expense Authorisation Form (with the cabin entered on
   it), so every BOOK relies on a sign-off on file: approvers CONTRACT_MANAGER or NONE (SYNC_NOTES 4'). The form
   naming BUSINESS is the "prior agreement with DBT Contract Manager" of line 135.
2. `nettle-fold` (refusal): the form on file covers the posting's own flights and goes unused, so NONE or
   CONTRACT_MANAGER (4(b)). Reasons WEEKEND_TRAVEL_HOME (a handbook code here, a decoy elsewhere),
   OUTSIDE_POLICY_SCOPE, PERSONAL_TRAVEL_NOT_COVERED (lesson 5). WEEKEND_TRIP_NOT_EARNED, a decoy in other plugins,
   was left out of this list because a reader could pick it for this refusal.
3. Lesson 12: LOWEST_FARE is not accepted where the request is declined on another ground (`elder-sound`,
   `garnet-mere`, `heather-vane`, `iris-tarn`, `juniper-loft`, `linnet-brook`). It is accepted on `kestrel-moor`,
   where the airline is declined because it is dearer than the lowest logical fare (and for the points, line 107).
4. COST_SAVINGS is accepted beside LOWEST_FARE where a permitted business fare is not taken (`alder-pennant`,
   `cobalt-weir`) and beside RAIL_PREFERRED on `iris-tarn`.
5. `linnet-brook` and `plover-reach` (BOOK side) accept DIRECTOR too: the premium economy rests on the Director's
   note on file.
6. `juniper-loft` accepts only the non-refundable lowest fare: the outbound date is set (line 146), so the dearer
   refundable fare is not the lowest logical fare.
7. Background offers: 0 everywhere (handbook.json and every search), so the pinned offers are the whole listing.
8. Clauses: AIR_TRAVEL or POLICY_STATEMENT (Air Travel is a sub-heading of section 4) for air rules; plus
   EXPENSE_PRE_APPROVAL and PURPOSE for personal time (lines 65-68), CLAIMING_REIMBURSEMENT for loyalty (lines
   107-109 sit under it), EXPENSE_PRE_APPROVAL for the approval hold; PURPOSE or NON_REIMBURSABLE for the refusal.
9. Decoy reason codes (grepped: no subject in the text): NEXT_OF_KIN_TRAVEL, FLY_AMERICA_US_CARRIER_REQUIRED,
   OPEN_SKIES_AGREEMENT, CREATIVE_TICKETING, EXTENDED_TRAVEL_SAVINGS, DENIED_BOARDING_NOT_ALLOWED,
   CHANCELLOR_WRITTEN_AUTHORIZATION, DOUBLE_BOOKING_PROHIBITED, PRIVATE_AIRCRAFT_NOT_APPROVED,
   CANDIDATE_TRIP_NOT_COVERED, SAME_CLASS_AS_CUSTOMER, TRAVEL_PACKAGE_NOT_ITEMIZED. Approver decoys: LINE_MANAGER,
   FINANCE_DIRECTOR, PERMANENT_SECRETARY, TRAVEL_DESK. COMMERCIAL_MANAGER (Annex B, line 323) and HUMAN_RESOURCES
   (line 145) are roles the text names; no key uses them.
10. The task instructions add "and for any other airport or date the trip record gives as an alternative" to the
    search step, for the two cases with two pinned searches (lesson 8: only alternates the record names).

## 5. Mix, overlays and baselines

3 easy, 4 boundary_twin, 3 multi_rule, 2 hidden_clause, 1 distractor, 1 refusal, 2 flag (12.5%). Decisions: 13
BOOK (2 business, 1 premium economy, 10 economy), 1 REFUSE, 2 FLAG. Overlays: multi_leg 6, date_arithmetic 3
(month_end 2), personal_travel 3, dearer_option 4, upgrade_not_taken 2, outside_air_section 2. Degenerate agents:
always-flag passes 1 (`plover-reach`), always-cheapest passes 6 of 16 (37.5%: alder-pennant, bramble-coil,
cobalt-weir, fennel-arch, kestrel-moor, marram-spit), the limits in `plugin_spec.py`.

## 6. Independent blind read (non-flag scenarios)

Re-derived from the frozen text and the tool outputs only (`get_trip` plus every pinned `search_flights` listing,
dumped per scenario), not from rules.py, then compared with `expected`.

| Scenario | My reading from text + offers | Agrees |
|---|---|---|
| alder-pennant | 820-830-min nonstops, form names business, traveller wants cheapest economy; BA 724.00 sold out; ANA 758.50 | yes |
| bramble-coil | economy, connection welcome; EK via DXB (415 + 580) 612.00 lowest | yes |
| cobalt-weir | homeward 875-890 min, business permitted but economy chosen; BA 684.00 | yes |
| damson-ridge | per flight: QR business flights 405/590 are economy-band; nonstop business with form: JAL 4,058.00 < BA 4,125.00 | yes |
| elder-sound | nonstop business sold out; QR business not allowed per flight; economy: QR 638.00 lowest | yes |
| fennel-arch | Monday lowest 651.20 (JAL) = Friday lowest 651.20 (ANA): not more expensive, CM told: Monday JAL | yes |
| garnet-mere | Monday lowest 655.20 > Friday 651.20: extra not covered; traveller asked for the covered flight: Friday ANA | yes |
| heather-vane | first never (line 138); form names business, 820/830 min: JAL business 3,895.00 | yes |
| iris-tarn | Scotland exception, but through 984.00 > rail 98.50 + JAL 729.00 = 827.50 (and + BA 741.00 = 839.50): rail, JAL from LHR | yes |
| juniper-loft | no open returns: one-way out, lowest non-refundable ANA 742.00 | yes |
| kestrel-moor | JAL 787.00 dearer than ANA 742.00; points no reason: ANA | yes |
| linnet-brook | economy sold out, date fixed, Director's note for PE, every flight 405-595 min: cheapest PE EK 1,268.00 | yes |
| marram-spit | 2 days' notice is soft (lines 110-113); form signed 4 July; lowest JAL 799.00 | yes |
| nettle-fold | weekend journey home mid-posting: excluded (lines 20-24): refuse | yes |

14 of 14 non-flag scenarios agree. The read changed one request: the personal-time twins first said "if the Monday
flight costs more than the Friday one, book Friday", which states the comparison and makes the handbook moot; it now
says "if the extra days mean the Monday flight can't all go on the contract, book me whichever flight home it does
cover". No answer changed.

## 7. Template change requests

- **Add Japanese and more UK airports to the shared `world.py`:** KIX (Osaka Kansai, JP, +540) and ITM (Osaka
  Itami), plus CTS, FUK, OKA; MAN, GLA and BFS in the UK. With them this handbook could test its real destination
  (Osaka), within-Japan flights (lines 10-11 "and within Japan"), Northern Ireland (line 148) and UK domestic legs
  from more cities, and the short-flight band (Haneda-Osaka about 75 minutes). No new hubs are needed (JL and NH
  already hub at HND/NRT), so existing routes should not move; run `tools/world_diff.py`.
- Observation: the skeleton README and product.yaml carry Thornton text; rewritten here.

## 8. Hosted-cap estimate

Full-handbook prompt: 17,907 bytes, 2,854 words; about 3,800 tokens at 1.33 a word, about 5,400 on the
Thornton/NJC calibration (0.2 a character plus 1,800). A 3-call run is about 29,000 input tokens before the final
message (about 41,000 with it); the three 4-call cases (two searches) add about 6,000. Well under the 65,536 cap.

## 9. Acceptance outputs

```
$ uv run pytest -q
162 passed in 2.79s
$ uv run ruff check .
All checks passed!
$ uv lock --check
Resolved 42 packages in 6ms
$ python3 ../_template/check_shared.py .
: ok
$ nanoagent plugin inspect .
ok (exit 0)
$ nanoagent plugin pack . <scratchpad>/uk-dbt/uk-dbt-flight-policy.tar.gz
packed . into <scratchpad>/uk-dbt/uk-dbt-flight-policy.tar.gz (154991 bytes)
$ python ../_template/tools/stock_verify.py .  (nanoagent venv python)
alder-pennant        right=True score=1.00 identical=True wrong-decision-rejected=True
bramble-coil         right=True score=1.00 identical=True wrong-decision-rejected=True
cobalt-weir          right=True score=1.00 identical=True wrong-decision-rejected=True
damson-ridge         right=True score=1.00 identical=True wrong-decision-rejected=True
elder-sound          right=True score=1.00 identical=True wrong-decision-rejected=True
fennel-arch          right=True score=1.00 identical=True wrong-decision-rejected=True
garnet-mere          right=True score=1.00 identical=True wrong-decision-rejected=True
heather-vane         right=True score=1.00 identical=True wrong-decision-rejected=True
iris-tarn            right=True score=1.00 identical=True wrong-decision-rejected=True
juniper-loft         right=True score=1.00 identical=True wrong-decision-rejected=True
kestrel-moor         right=True score=1.00 identical=True wrong-decision-rejected=True
linnet-brook         right=True score=1.00 identical=True wrong-decision-rejected=True
marram-spit          right=True score=1.00 identical=True wrong-decision-rejected=True
nettle-fold          right=True score=1.00 identical=True wrong-decision-rejected=True
osprey-cairn         right=True score=1.00 identical=True wrong-decision-rejected=True
plover-reach         right=True score=1.00 identical=True wrong-decision-rejected=True
16 scenarios, 0 failures
```
