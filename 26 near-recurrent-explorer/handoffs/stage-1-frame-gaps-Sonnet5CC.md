---
stage: 1-frame
artifact: gaps
project: near-recurrent-explorer
status: draft
created-at: 2026-08-20
authors: [Sonnet5CC, jooneui]
reads:
  - stage-1-frame-problem-Sonnet5CC.md
  - stage-1-frame-architecture-Sonnet5CC.md
siblings:
  - stage-1-frame-problem-Sonnet5CC.md
  - stage-1-frame-architecture-Sonnet5CC.md
next-stage: Stage 2 — Plan
---

# Knowledge gaps — sibling 3/3

## Carried forward

None — first cycle of this project.

One item is inherited from the *research* codebase rather than a prior cycle: the
author's own note in `MASTER_CONFIG` that eligibility is evaluated per day-of-week when
it should apply to the whole AM/PM period. Captured below as **G7**.

## Closed during Frame

### G2 — Frozen Stage-1 export size — CLOSED

**Closure date:** 2026-08-20
**What we didn't know:** whether the frozen Stage-1 output would be small enough to ship
to a browser under C1/C4 (load in <3 s).
**Evidence:** measured `04_peak_period_result/c_daily_traffic_division_single_*_
speedbasedpeak_5_RDP_v_speed-solely.csv` — 141 files, 9.4 MB total; per-file range
70 KB–958 KB. The paper's 9 stations total ~3.6 MB raw. Schema inspection shows 7 of 14
columns are unused downstream and `off-peak` rows are droppable, giving a conservative
estimate well under 600 KB for all 9 stations, before per-station lazy loading.
**Closer:** Sonnet5CC

### G4 — Which insight angle leads — CLOSED

**Closure date:** 2026-08-20
**What we didn't know:** whether the site should lead with (a) β≈1-not-4, (b) rush hour
is not a fixed window, or (c) unsupervised recurrent-vs-incident separation.
**Evidence:** explicit author decision — (c), the unsupervised separator. Rationale: it
maps onto a problem the primary audience already owns. Recorded as **P2**.
**Closer:** jooneui

### G6 — Which parameter set is the C3 reference — CLOSED

**Closure date:** 2026-08-20
**What we didn't know:** whether the parity target should be the paper's Table 1 values
(AM ε = 0.3/0.2, PM ε = 0.2/0.3) or the notebook's last stored run (AM 0.15/0.15,
PM 0.19/0.19).
**Evidence:** explicit author decision — **AM ε = 0.15, PM ε = 0.19** are the current
optimal values and are authoritative. Recorded as **C3a**; also fixes the site's default
slider position. The paper's Table 1 values describe the single-station verification demo
(VDS 1203506, 2011) in Section 4, not the multi-station calibration in Section 5, so
there is no contradiction to resolve.
**Consequence:** the author further specified that the parity reference must be
**regenerated from the current Python code**, not lifted from the notebook's stored
outputs or any prior site data, both of which are treated as potentially stale. C3 was
rewritten accordingly, and G1's reference table is downgraded from "target" to
"indicative, pending regeneration."
**Closer:** jooneui

### G10 — Gate scope: does eligibility block recurrent detection, or only VDF? — CLOSED

**Closure date:** 2026-08-20
**What we didn't know:** whether ineligible station–periods should still display their
near-recurrent peak periods (author's initial requirement), which conflicted with current
pipeline behaviour — `plotting_stage2.py` skips recurrent detection *and* BPR.
**Evidence:** explicit author decision — **do not show recurrent peak periods when the
station–period is excluded from VDF calibration.** This reverts to the pipeline's existing
behaviour.
**Consequence:** the cleanest available resolution. No `traffic_utils` change is required,
C6 is preserved (no JS computation without a Python counterpart), and C3 parity remains
checkable for every cell including the excluded ones. C4a was rewritten accordingly.
**Non-consequence noted:** this does not leave the map sparse. Of the 18 station–periods,
10 are eligible, and **every one of the 9 stations has at least one eligible period** —
SR91-WB (PM), SR91-EB (AM+PM), I5 SB-1/2/3 (AM), I5 NB-1 (PM), SR134 WB-1 (AM+PM),
SR134 EB-1 (PM), SR134 EB-2 (PM). Exclusion appears only when toggling to the other
period at a given station, where it reads as a method result ("not congested enough to
calibrate") rather than missing data.
**Closer:** jooneui

### G3 — Which parameters get user controls — CLOSED

**Closure date:** 2026-08-20
**What we didn't know:** whether exposing all four RDP_v parameters would overwhelm a
2-minute visitor.
**Evidence:** explicit author decision — expose `epsilon_start`, `epsilon_end`,
`min_len` only. The `hg` gap parameter is not exposed.
**Closer:** jooneui

## New gaps

### G1 — JS/Python numerical parity

- **Status:** Open
- **What we don't know:** whether a JavaScript port of Stages 2–4 reproduces the Python
  pipeline's output within tolerance, in particular through `rdp_v`'s recursive split
  behavior, the gap-breakpoint union, `_dedup_multiple_peaks`, and the harmonic-mean
  aggregations.
- **Closure criterion:** run the JS implementation at the reference parameter set (C3a:
  AM ε = 0.15, PM ε = 0.19, `min_len` = 3) on all 9 paper stations; compare
  `(N, log α̃, β, R²)` per station–period against **a freshly regenerated Python
  reference**. Must agree to ≥3 decimal places on every row, and the excluded set must
  match exactly.
- **Prerequisite:** regenerate the Python reference by running the current
  `traffic_utils` pipeline at C3a parameters, and store it under `references/` as the
  parity target. This must happen before G1 can close.
- **Indicative table only** — notebook stored output at the same nominal parameters,
  retained for smell-testing the regenerated values, **not** as the parity target
  (it predates the 2026-08-20 threshold-default fix and possibly other changes):

  | VDS | Period | N | log α̃ | β |
  |---|---|---|---|---|
  | SR91-WB | PM | 21 | −3.244994 | 0.372615 |
  | SR91-EB | AM | 19 | −8.431254 | 0.960746 |
  | SR91-EB | PM | 13 | −6.661829 | 0.717877 |
  | I5 SB-1 | AM | 17 | −6.543353 | 0.872097 |
  | I5 SB-2 | AM | 32 | −7.484685 | — |
  | I5 SB-3 | AM | 29 | −5.273461 | — |
  | I5 NB-1 | PM | 21 | −13.909620 | — |
  | SR134 WB-1 | AM | 14 | −13.911850 | — |
  | SR134 WB-1 | PM | 27 | −2.126066 | — |
  | SR134 EB-1 | PM | 39 | −4.209620 | — |
  | SR134 EB-2 | PM | 10 | −3.644824 | — |

  (β values beyond the first four to be extracted from the full stored table during Plan.)
- **Assigned:** execute-P2 (port), verified in verify-P1
- **Blocks:** C3, C6

### G5 — Eligibility gate inputs and portability

- **Status:** Open
- **What we don't know:** whether the eligibility gate (C4) can be pre-computed in the
  exporter and shipped as a static flag, or whether it must be recomputed client-side.
  The gate screens on `density > 60` over the *segment-level* dataframe inside
  `plotting_stage2.py`, and it is not established that this input survives into the
  Stage-1 export described in the architecture sibling.
- **Why it matters:** if eligibility depends on the user-facing parameters, the whole
  frozen-export architecture needs revision. Current belief is that it does not — the
  gate screens density observations, which are independent of the RDP_v tolerances.
- **Closure criterion:** trace `df_segment`'s provenance into
  `plot_fd_with_threshold`-family calls; confirm (a) the `density` column's source, and
  (b) that `skip_flags` is invariant to `epsilon_start`/`epsilon_end`/`min_len`. Then
  either (i) bake a per-(station, period) eligibility flag into the export, or (ii)
  document why live recomputation is required.
- **Assigned:** plan (investigation), closed in execute-P1
- **Blocks:** C2, C4; the data contract in the architecture sibling

### G5 — Eligibility gate inputs and portability — CLOSED

**Closure date:** 2026-08-20
**What we didn't know:** whether eligibility (C4) could be pre-computed in the exporter
and shipped as a static flag, or must be recomputed client-side.
**Evidence:** traced the call order in `run_full_pipeline` — Stage 2 (eligibility) runs
and computes `skip_flags` **before** Stage 3 (RDP_v classification) ever executes, using
only the station's raw density record against `den_threshold`/`count_threshold_per_year`.
Neither input depends on `epsilon_start`, `epsilon_end`, or `min_len` — those parameters
don't exist yet at the point eligibility is decided. Confirmed structurally, not just by
inspection: the gate-inclusive regeneration run (G1) shows the excluded set is identical
regardless of the RDP_v parameters used downstream.
**Resolution:** eligibility is pre-computed once per (station, period) in the exporter
and shipped as a static boolean flag with the pass/fail rate for display. No live
recomputation needed. This closes the C2/C1 tension flagged in Frame — the frozen-export
architecture holds.
**Closer:** Sonnet5CC

### G9 — Free-flow travel time (ζ) availability — CLOSED

**Closure date:** 2026-08-20
**What we didn't know:** whether ζ is retrievable from existing config or must be
computed by the exporter.
**Evidence:** `MASTER_CONFIG['bpr_ff_speed_threshold']` already has explicit, named
values for all 9 paper stations: 1203481→68, 1203506→66, 1214006→67, 1205572→70,
1212611→69, 1205175→69, 774204→67, 761003→67, 760987→66 (mph). `load_and_annotate`
computes `free_traveltime = 60.0 / ff_speed` (h/mi) under `free_tt_method: 'offpeak_avg'`
— confirmed this is the mode MASTER_CONFIG uses.
**Resolution:** these 9 constants are baked into the exporter directly (no live
computation, no dependency on raw off-peak data at export time). ζ per station =
60 / bpr_ff_speed_threshold[vds].
**Closer:** Sonnet5CC

### G7 — Eligibility granularity: per-DOW vs per-period — CLOSED (moot, not resolved)

**Closure date:** 2026-08-20
**What we didn't know:** whether `no_peak_eligibility_threshold` (the author's flagged
per-DOW-vs-per-period concern) affected which pairs get calibrated.
**Evidence:** searched every `.py` file in the repository — `no_peak_eligibility_
threshold` is **read nowhere**. Its only occurrence anywhere is the single line defining
it inside `MASTER_CONFIG` itself. No function consumes it.
**Resolution:** the concern is real as a piece of unfinished work in the research code,
but it is currently **inert** — it affects zero current results, including the C3a
reference table, because the mechanism it would gate doesn't exist. Not "fixed" (per C6,
not this project's job to implement it); recorded so a future cycle doesn't rediscover
the same dead code and wonder if it's silently doing something. Candidate `wiki/topics/`
entry if this pattern (a config key that looks load-bearing but isn't) recurs elsewhere.
**Closer:** Sonnet5CC

### G13 — Direct-call regeneration produced identical AM/PM results — CLOSED

**Closure date:** 2026-08-20
**What happened:** a first regeneration attempt called `prepare_bpr_dataframe` +
`fit_bpr_ols_stats` directly, bypassing `run_full_pipeline`. Every station returned
identical AM/PM results — impossible if period filtering were working.
**Root cause:** eligibility filtering lives in `cfg['_fd_skip_map']`, populated by
Stage 2. The direct-call attempt never ran Stage 2, so `prepare_bpr_dataframe` silently
skipped the exclusion step entirely (its check is `if fd_skip_map and vds_key in
fd_skip_map`, which is false when the map was never populated).
**Resolution:** re-ran via the real entry point, `run_full_pipeline(MASTER_CONFIG,
stages=[2,3,4])` — no `traffic_utils` files modified, per author's instruction. This
produced correct, gate-respecting output in 21.5s.
**Closer:** Sonnet5CC

### G1 — JS/Python numerical parity — target CONFIRMED (port itself remains open)

**Confirmed 2026-08-20.** Regenerated via `run_full_pipeline(MASTER_CONFIG,
stages=[2,3,4])`, current unmodified `traffic_utils/`, no changes on the basis of this
run. Saved to `references/bpr_calibration_reference_C3a.csv`. Matches the earlier
"indicative" notebook table to 6+ decimal places on every value, and the excluded set
(N=0) is identical — 7 station-periods: SR91-WB AM, I5 SB-1 PM, I5 SB-2 PM, I5 SB-3 PM,
I5 NB-1 AM, SR134 EB-1 AM, SR134 EB-2 AM.

| VDS | Period | N | log α̃ | β | N₀ |
|---|---|---|---|---|---|
| SR91-WB | AM | 0 (excluded) | — | — | — |
| SR91-WB | PM | 21 | −3.244994 | 0.372615 | 37.24 |
| SR91-EB | AM | 19 | −8.431254 | 0.960746 | 898.84 |
| SR91-EB | PM | 13 | −6.661829 | 0.717877 | 762.97 |
| I5 SB-1 | AM | 17 | −6.543353 | 0.872097 | 205.96 |
| I5 SB-1 | PM | 0 (excluded) | — | — | — |
| I5 SB-2 | AM | 32 | −7.484685 | 0.859844 | 664.05 |
| I5 SB-2 | PM | 0 (excluded) | — | — | — |
| I5 SB-3 | AM | 29 | −5.273461 | 0.605328 | 264.46 |
| I5 SB-3 | PM | 0 (excluded) | — | — | — |
| I5 NB-1 | AM | 0 (excluded) | — | — | — |
| I5 NB-1 | PM | 21 | −13.909620 | 1.400448 | 5311.41 |
| SR134 WB-1 | AM | 14 | −13.911850 | 1.682400 | 1263.23 |
| SR134 WB-1 | PM | 27 | −2.126066 | 0.305394 | 2.12 |
| SR134 EB-1 | AM | 0 (excluded) | — | — | — |
| SR134 EB-1 | PM | 39 | −4.209620 | 0.539745 | 72.56 |
| SR134 EB-2 | AM | 0 (excluded) | — | — | — |
| SR134 EB-2 | PM | 10 | −3.644824 | 0.472139 | 40.51 |

**This is now the parity target.** The JS port (still to be written in Execute) is
checked against this table, not the paper, not `run_paper_results.py`.
**Note (confirms G12's closure):** re-running with the original 40/50 fallback defaults
(pre-2026-08-20 fix) was not tested here, since MASTER_CONFIG explicitly supplies
`den_threshold`/`count_threshold_per_year` and the fallback path is never hit in normal
pipeline execution. The earlier defensive fix stands but did not change this output.

### G12 — `run_paper_results.py` disagrees with C3a — CLOSED

**Closure date:** 2026-08-20
**What we found:** during regeneration, a script `run_paper_results.py` was discovered —
undocumented in Frame, not read by the author recently. Its `paper_config()` states it
reproduces "the calibration results reported in Sections 5 and 6 of the paper," using
θ = 0.25 uniformly for both AM/PM and both epsilon_start/epsilon_end, plus
`count_threshold_per_year = 50` (default). This disagrees with C3a (AM 0.15/0.15,
PM 0.19/0.19, count = 75) on both axes. The script's own comment additionally implies a
stale station list ("the eleven of the first draft, less two").
**Resolution:** explicit author decision — **`run_paper_results.py` and the paper it
targets are both outdated. MASTER_CONFIG's current values (AM ε=0.15, PM ε=0.19,
den=60, count/yr=75) are authoritative.** C3a stands unchanged. `run_paper_results.py`
is not used for this project and is not treated as a source of truth for anything.
**Consequence:** confirms G6's closure was correct. Recorded here rather than silently
because it's exactly the kind of stale-artifact confusion future cycles should be warned
about — a `wiki/topics/` entry may be warranted if this pattern (paper-tracking scripts
drifting from the live config) recurs.
**Closer:** jooneui

### G11 — Figure 6 lists AM periods the reference run marks ineligible — CONFIRMED REAL

**Status:** Open — genuine paper/code discrepancy, not a site defect
**Confirmed 2026-08-20:** the current pipeline, unmodified and run cleanly, excludes
**SR91-WB AM** (68.3/yr, need 75) and **SR134 EB-1 AM** (61.4/yr, need 75) — both below
threshold. The published Figure 6 lists both as analyzed for AM and PM. This is not
explained by the earlier fallback-default fix (ruled out — see G1 closure note); the
current `den_threshold=60` / `count_threshold_per_year=75` are MASTER_CONFIG's own
explicit, intentional values.
**What this means:** either the paper was produced under different threshold values (a
prior, looser `count_threshold_per_year`, plausibly 50 — recall `run_paper_results.py`'s
default, see G12), or the underlying data/processing has changed since the figure was
generated (e.g. `04_peak_period_result/` regenerated with different upstream
parameters).
**Disposition:** per C6 and the author's direction that the paper is an outdated
version, **the site follows the current code, not Figure 6.** This exclusion is not a
site bug and is not "fixed" here. Recorded as a known, confirmed discrepancy between the
current pipeline and the submitted paper — worth a note to co-author Wen-Long Jin if a
paper revision is still possible, but that is outside this project's scope.
**Assigned:** jooneui (whether/how to address in the paper); site treats it as closed
for site-design purposes.
**Blocks:** nothing further for this project.

### G7 — Eligibility granularity: per-DOW vs per-period

- **Status:** Open
- **What we don't know:** whether the published results were produced with eligibility
  evaluated per day-of-week or per whole AM/PM period. The author's own note in
  `MASTER_CONFIG` states: *"현재 eligibility 확인이 day of week별로 되어있는 것 같다.
  오전, 또는 오후 전체 적용하도록 설정필요"* — i.e. it is currently per-DOW but should be
  per-period. `no_peak_eligibility_threshold` is presently `1.0` (keep all facets).
- **Why it matters:** the two behaviors produce different eligible sets, so the site
  cannot reproduce "the paper" without knowing which one did.
- **Closure criterion:** determine which granularity produced the stored reference table;
  document it. If the intended (per-period) behavior differs from the behavior that
  produced the published numbers, that is a finding about the research code, not about
  the site — record it and do not silently "fix" it here (C6).
- **Assigned:** plan (investigation)
- **Blocks:** C3, C4

### G8 — Does the two-minute claim hold with a real stranger

- **Status:** Open
- **What we don't know:** whether P1/P2 actually work — i.e. whether a technical person
  unfamiliar with the research reaches "I understand what near-recurrent means and why
  it changes the fit" within two minutes.
- **Closure criterion:** show the built site to at least two people who have not read the
  paper; ask them to narrate what they think it shows, unprompted, and time it. Success =
  both articulate the recurrent-vs-non-recurrent distinction without being told.
- **Assigned:** verify-P2
- **Blocks:** success criterion 1

### G9 — Free-flow travel time (ζ) availability

- **Status:** Open
- **What we don't know:** whether per-station ζ is retrievable from existing config /
  outputs, or must be recomputed by the exporter from off-peak windows.
- **Closure criterion:** confirm `MASTER_CONFIG['offpeak_ff_speed_threshold']` and
  `bpr_ff_speed_threshold` cover all 9 paper stations and match what
  `compute_bpr_ff_speed_thresholds()` produces. If yes, bake into export; if no, add a
  computation step to the exporter.
- **Assigned:** execute-P1
- **Blocks:** Stage-4 port (β estimation requires ζ)

## Gap dependencies

```
G6 ✅ (reference params = AM 0.15 / PM 0.19)
G10 ✅ (gate scope: excludes entirely — no pipeline change)
  ↓
[regenerate Python reference from current code]  ← next concrete action
  ↓
G1 (JS/Python parity)  ←  G7 (eligibility granularity)
  ↑                            ↑         ↓
G9 (zeta availability)     G5 (eligibility portability)
                               ↓
                        data contract (architecture sibling)
                               ↓
                        G11 (Figure 6 vs. eligible set)

G8 (two-minute test) — independent; needs a built site
```

**Closure order:** nothing blocks Plan. The first concrete action is regenerating the
Python reference at C3a parameters — this is now unambiguous because no pipeline change
is pending. G5, G7, G9 are investigations that can run during Plan. G11 falls out of the
regeneration. G1 closes after the reference exists and the port is written. G8 is last.

## Open questions for the human

*None blocking.* All four Frame-stage questions are settled:

1. ~~G6 — reference parameters~~ — **settled:** AM ε = 0.15, PM ε = 0.19, `min_len` = 3.
2. ~~Directory name~~ — **settled:** `26 near-recurrent-explorer/` confirmed.
3. ~~Default slider position~~ — **settled:** opens at the reference parameters (C3a).
4. ~~G10 — treatment of ineligible station–periods~~ — **settled:** excluded entirely,
   no recurrent bands shown, matching the pipeline. No `traffic_utils` change required.

## How gaps interact with constraints

- **G5 vs C2:** if eligibility must be recomputed live and its inputs are large, C2
  (live recompute) and C1 (static hosting) come into tension. Resolution path: pre-compute
  eligibility, since it is parameter-independent. If that belief is wrong, C2 may need to
  be narrowed to "Stages 2–4 excluding eligibility."
- **G6/G7 vs C3:** C3 cannot be evaluated at all until G6 and G7 close. Until then the
  site has no defined notion of "correct."
- **G7 vs C6:** if the published numbers were produced by behavior the author considers a
  bug, C6 forbids silently correcting it here. The site must reproduce what was published
  and the discrepancy must be recorded — as a finding, propagated back, not patched.

## Uncertainty markers

- **Confident:** G2 is genuinely closed; the measurement is direct and the margin is
  large.
- **Confident:** the gap list is complete with respect to *numerical* reproduction.
- **Uncertain:** whether G5 is one gap or two — it may split into "where does `density`
  come from" and "is `skip_flags` parameter-invariant" once investigated.
- **Uncertain:** whether G8's closure criterion is strong enough. Two readers is a weak
  sample; it is chosen for feasibility, not rigor. If both fail, that is decisive; if both
  pass, confidence is moderate at best.
- **Not yet examined:** the `hg` (gap) parameter's semantics. It is excluded from the UI
  per G3, but the port must still implement whatever it does. This may surface a gap
  during Plan.
