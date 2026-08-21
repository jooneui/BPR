---
stage: 3-execute
artifact: phase-1-handoff
project: near-recurrent-explorer
phase: P1 — RDP_v JS port
status: complete
created-at: 2026-08-20
authors: [Sonnet5CC]
reads:
  - stage-2-plan-Sonnet5CC.md (P1 specification)
  - traffic_utils/segmentation.py::rdp_v (algorithm source)
  - traffic_utils/recurrent.py::classify_facet_rdpv, prepare_peak_table,
    _dedup_multiple_peaks (algorithm source)
  - references/bpr_calibration_reference_C3a.csv
siblings:
  - stage-3-phase-0-Sonnet5CC.md (amended by this phase — see its amendment note)
next-stage: Stage 3 Phase 2 — BPR calibration JS port
---

# Stage 3 Phase 1 — RDP_v JS port

## Headline

`src/rdpv.js` ports the modified-RDP near-recurrent classification exactly. All 11
eligible station-periods across all 9 stations match the confirmed Python reference
exactly on retained-segment count, verified in Node against real exported data — not
eyeballed. Getting there required finding and fixing three real, independent bugs, none
of which were visible from reading the algorithm alone; each was only findable by
actually running the port against real numbers and diffing where it diverged.

## Deliverables

- `src/rdpv.js` — `rdpVertical` (the modified-RDP recursion), `dedupMultiplePeaks`,
  `classifyFacetRdpv`, `computeWeekNums`
- `src/test_rdpv.js` — parity test harness (Node), checks all 11 eligible
  station-periods against `references/bpr_calibration_reference_C3a.csv`
- Amendments to `src/export_site_data.py` (see phase-0 handoff's amendment note)

## Verification ran

```
$ node test_rdpv.js
VDS          Period  N(JS)  N(ref)  match
SR91-EB      AM      19     19      OK
SR91-EB      PM      13     13      OK
SR91-WB      PM      21     21      OK
I5 SB-1      AM      17     17      OK
I5 SB-2      AM      32     32      OK
I5 SB-3      AM      29     29      OK
I5 NB-1      PM      21     21      OK
SR134 WB-1   AM      14     14      OK
SR134 WB-1   PM      27     27      OK
SR134 EB-1   PM      39     39      OK
SR134 EB-2   PM      10     10      OK

ALL MATCH
```

This checks the *aggregate* retained-segment count per station-period (summed across
all 7 day-of-week facets), which is what feeds P2's `N` directly. It does not yet check
individual segment week-ranges beyond what two hand-traced facets confirmed (below).

Additionally hand-verified, segment-by-segment, against Python's `meta['segments']`
output for two full facets (SR91-WB Tuesday PM and I5-SB-2 Thursday AM) — exact match
on every breakpoint position and every retained segment's week range, not just the
final count. Chose these two because they were the ones that initially disagreed.

## Divergences

Three real bugs, found in sequence, each only surfaced by actually running the port
against real data and tracing exact per-day-of-week disagreement — none were visible
from code review alone. All three ended up requiring changes to `export_site_data.py`
(P0), which is why P0's handoff carries an amendment note pointing back here.

**R2 — missing dedup step (constraint: C6, JS must not diverge from Python).**
First test run: every station showed identical AM/PM totals (undercounting relative to
reference by varying amounts). Root cause: the raw Stage-1 CSVs carry genuine
same-date duplicate `(date, period)` rows — 4917 of 11465 rows for VDS 1203506 alone
(~43%). `_dedup_multiple_peaks` exists in Python specifically for this and was
originally assumed (in the phase-1 spec, per Plan's uncertainty marker) "probably not
exercised" for these 9 stations. It's exercised heavily. Added `dedupMultiplePeaks` to
`rdpv.js`, matching Python's default branch (`drop_multiplecongestion_days=False`):
keep longest-duration peak per date, tie-break earliest start hour. This alone brought
7 of 11 station-periods to exact match.

**R2 — malformed time strings not excluded (constraint: C6).**
Of the 4 remaining mismatches, most improved after this fix: the raw data contains
time strings like `"24:00:00"` (three colon-separated parts, out-of-range hour) that
`time_to_fractional_hour` can't parse. Python's version returns NaN on the parse
failure, and that NaN is exactly what makes `prepare_peak_table` mark the row
`is_peak=-5` — non-qualifying, excluded from classification. The exporter used the same
parsing logic but never dropped the resulting nulls, so these rows survived as phantom
qualifying days. Found in every station except 1205572/1212611; as many as 156 rows for
VDS 761003. Fixed in the exporter (P0 amendment): drop rows where `start_h`/`end_h`
fails to parse, before export.

**R2 — rounding broke exact duration ties (constraint: C6, the subtlest of the three).**
One station (I5 SB-2, which has *zero* malformed-time rows — ruling out the second bug)
still disagreed after both fixes above, with byte-identical qualifying-week counts
between JS and Python but different retained-segment counts. Traced to date 2021-03-04
at VDS 1205572: two congested-period rows on the same date, `07:35–08:10` and
`10:55–11:30`, both **exactly 35 minutes** — a genuine tie on duration. Python's
tie-break (earliest start_hour) should be unambiguous, but the exporter's rounding
(originally 2 decimals, tried 6 next) perturbs the float64 bit pattern of `end_h -
start_h` enough that JS and Python land on different float64 comparisons for values
that are mathematically equal but reach that equality via different `h + m/60.0` paths.
Fixed by removing rounding on `start_h`/`end_h` entirely — `json.dump` serializes
Python floats with enough digits to round-trip to the identical float64 in JS's
`JSON.parse`, so the tie now resolves identically in both languages. This was the fix
that brought the last 4 mismatches to exact match, all at once.

**Cost of these three fixes:** `data/` grew from an initial (buggy) 1113 KB to a
correct 1553 KB — 51% over Plan's 1024 KB tripwire. Gzipped, 294.6 KB (was 274 KB) —
a 20 KB real-world difference, still comfortably inside the load-time constraint.
Explicitly not treated as a tripwire violation to apologize for: the alternative
(rounding for a smaller file) is a program that produces wrong answers.

## Gaps touched

None of Frame's original gaps directly, but this phase produced three new, real
findings about the source data (`traffic_utils`'s inputs, not its logic) that didn't
exist as gaps before because nobody had needed this level of numerical exactness from
the daily-peak CSVs before. Not filed as new formal gaps since all three are closed —
recorded here as the permanent trail per divergence-recording practice.

## What unblocks Phase 2

`classifyFacetRdpv`'s output segments (with `weeks`, `startHours`, `endHours` per
retained segment) are exactly the input P2's aggregation step needs to compute
`(N_r, z_r)` per retained interval. The verified retained-segment *counts* match: P2's
job is to confirm the aggregated *values* (`N`, `log α̃`, `β`, `R²`) also match, which
requires the actual `demand`/`speed` fields the classification step doesn't touch.

## Uncertainty markers

- **Confident:** all 11 eligible station-periods verified on aggregate count; 2 verified
  segment-by-segment in full detail. High confidence the port is correct.
- **Uncertain (U-P1-2, carried from Plan):** the week_num anchor date is computed from
  the earliest date across this station's *exported* (congested-day-only) rows, not the
  earliest date in the *full* raw file (which would include off-peak-only days, not
  exported per Frame's data contract). Not verified to matter — all 18 station-periods
  passed despite this — but not proven irrelevant either; flagged in case a future
  station or parameter setting exposes it.
- **Not implemented:** the `drop_multiplecongestion_days=True` branch of
  `_dedup_multiple_peaks` (irrelevant — MASTER_CONFIG uses `False`, and the port
  correctly implements only the branch actually used).
- **Methodological note worth keeping:** all three bugs were invisible from reading the
  algorithm description or the ported code — each required actually running the port
  against real numbers and tracing a real disagreement to its root cause. This is
  direct, concrete evidence for why `state-machine-runtime.md`'s "a rulebook alone
  isn't enough" argument (from our earlier conversation) generalizes past FASTRIC
  specifically: a correct-looking port of a correct-looking algorithm can still be
  wrong in ways only execution against real data surfaces.
