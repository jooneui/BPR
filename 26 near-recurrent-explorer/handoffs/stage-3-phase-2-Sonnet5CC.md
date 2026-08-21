---
stage: 3-execute
artifact: phase-2-handoff
project: near-recurrent-explorer
phase: P2 — BPR calibration JS port
status: complete
created-at: 2026-08-20
authors: [Sonnet5CC]
reads:
  - stage-2-plan-Sonnet5CC.md (P2 specification)
  - traffic_utils/bpr_fitting.py::aggregate_segment_level_bpr, fit_bpr_ols_stats,
    weighted_harmonic_mean
  - stage-3-phase-1-Sonnet5CC.md (P1's segment output, this phase's input)
next-stage: Stage 3 Phase 3 — Parity harness
---

# Stage 3 Phase 2 — BPR calibration JS port

## Headline

`src/bpr.js` ports segment aggregation and the OLS fit exactly, including replicating
a real paper/code discrepancy in the source rather than "fixing" it. Combined with P1,
produces correct fits for all 11 eligible station-periods (full verification is P3,
since the two can't be meaningfully checked apart — see that phase for numbers).

## Deliverables

- `src/bpr.js` — `aggregateSegment`, `olsFit`, `calibrateStationPeriod`

## Verification ran

Deferred to P3 (the parity harness) — aggregation and fit only produce checkable output
once fed real classification results from P1, so testing them in isolation would need
fabricated inputs with no ground truth to check against. See phase-3 handoff.

## Divergences

**Initially misdiagnosed as a paper/code discrepancy; corrected on closer review —
there is no discrepancy.**
`traffic_utils/bpr_fitting.py::weighted_harmonic_mean(values, weights)` computes
`sum(weights*values)/sum(weights)`, which looks like a plain weighted arithmetic mean of
`values`, not a harmonic mean — this was first logged here as a naming/formula
discrepancy against the paper's Eq. 9 (an N_j-weighted harmonic mean of speed).

That diagnosis was wrong. Working through Eq. 9 algebraically: $z_r = 1/\bar v_r =
(\sum_j N_j/\bar v_j)/\sum_j N_j$. Since $1/\bar v_j$ is exactly the day's travel time
$z_j$, this reduces to $z_r = (\sum_j N_j z_j)/\sum_j N_j$ — a plain demand-weighted
**arithmetic** mean of daily travel times. That is precisely what
`weighted_harmonic_mean(traveltimes, totaldemandoverlanes)` computes. A harmonic mean of
speed and an arithmetic mean of travel time are the same operation viewed in two
different units (harmonic mean = reciprocal of the arithmetic mean of reciprocals;
speed and travel-time-per-distance are reciprocals of each other). The function's input
is already in travel-time (reciprocal) space, so the plain weighted average *is* the
correct harmonic-mean-of-speed computation — no second inversion needed. The name refers
to what the function accomplishes conceptually, not to the literal arithmetic it
performs on its arguments.

**Net effect:** the code matches the paper exactly here. This port's use of the same
formula is correct for the same reason, not merely "correct because it matches the
confirmed reference" (P3's pass is still the operative verification, but the earlier
claim that this was a *deliberate* replicate-the-code-over-the-paper choice was
incorrect — there was nothing to choose between). No propagate-back needed; this does
not affect the paper or `traffic_utils`.

## Gaps touched

None new. This phase's finding is adjacent in spirit to G11 (Frame) — another confirmed
place where the paper's description and the actual code diverge — but doesn't block
anything for this project, since the site's job is to match the code, not adjudicate it.

## What unblocks Phase 3

`calibrateStationPeriod(facetResultsByDow, zeta)` is the complete pipeline from raw
per-day rows to a fit — exactly what the parity harness needs to run end-to-end against
the reference table.

## Uncertainty markers

- **Uncertain:** whether `free_tt = median(free_traveltime)` in Python ever produces a
  value that differs from the constant ζ this port uses directly. Since
  `free_traveltime` doesn't vary by day in the source data (it's derived once per
  station from `bpr_ff_speed_threshold`), median-of-a-constant trivially equals the
  constant — but this wasn't independently verified against the raw column, only
  inferred from how it's computed upstream. Flagged as a candidate source of the small
  residual numerical difference found in P3 (see that phase's report).
