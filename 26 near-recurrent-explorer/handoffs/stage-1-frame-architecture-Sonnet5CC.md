---
stage: 1-frame
artifact: architecture
project: near-recurrent-explorer
status: draft
created-at: 2026-08-20
authors: [Sonnet5CC, jooneui]
reads:
  - stage-1-frame-problem-Sonnet5CC.md
  - traffic_utils/recurrent.py (classify_facet_rdpv, rdp_v)
  - traffic_utils/bpr_fitting.py
  - traffic_utils/plotting_stage2.py (eligibility gate, L108–179)
  - traffic_utils/pipeline.py (run_full_pipeline stage separation)
siblings:
  - stage-1-frame-problem-Sonnet5CC.md
  - stage-1-frame-gaps-Sonnet5CC.md
next-stage: Stage 2 — Plan
---

# Architecture sketch — sibling 2/3

## TL;DR

The pipeline already separates along exactly the line the project needs: Stage 1 is
expensive and operates on millions of raw rows; Stages 2–4 are trivial and operate on
small daily-summary tables. Freeze Stage 1 as exported JSON, port Stages 2–4 to
JavaScript, and the "move a slider, the algorithm runs" requirement is satisfied with
no backend.

## The load-bearing observation

| Stage | What it does | Input size | Cost | Disposition |
|---|---|---|---|---|
| **1** | Raw 5-min PeMS → daily congested periods (RDP on cumulative distance, speed threshold, merge) | ~10⁵–10⁶ rows/station | Expensive | **Freeze.** Export to JSON. |
| **2** | RDP_v on weekly start/end series → near-recurrent bands | ≤53 points per (station, period, DOW) | Trivial | **Port to JS.** |
| **3** | Aggregate retained intervals → (N_r, z_r) observations | tens of points | Trivial | **Port to JS.** |
| **4** | OLS on log-linear BPR form → (log α̃, β, R², t, p) | tens of points | Trivial | **Port to JS.** |

Evidence: `classify_facet_rdpv(epsilon_start, epsilon_end, ...)` calls
`rdp_v(pts, epsilon=eps)` on cumulative start/end series indexed by *week*, of which
there are at most ~53 per facet. `run_full_pipeline(MASTER_CONFIG, stages=[2,3,4])`
confirms the stages are already invocable independently of Stage 1.

## What stays (no-touch list)

- **`traffic_utils/` remains the canonical implementation of the science.** The JS port
  is a derived reimplementation for interactivity, never an authority (C6). If they
  disagree, Python wins and the port is fixed.
- **`04_peak_period_result/*.csv` remain the canonical Stage-1 outputs.** The exporter
  reads them; it does not regenerate or alter them.
- **The published paper's numbers remain fixed.** Nothing here revises a result.
- **`website/`, `25 product/`, `peak-atlas-site/` remain untouched.** No migration, no
  deletion; this directory borrows ideas and code freely but does not depend on them.

## What changes

1. **A new export script** (`src/export_site_data.py`) producing slim per-station JSON
   from `04_peak_period_result/`. Drops off-peak rows and unused columns; rounds floats.
2. **A JS port of Stage 2** — `rdp_v` + facet classification + gap-breakpoint logic.
3. **A JS port of Stages 3–4** — interval aggregation (arithmetic mean for N,
   N-weighted harmonic mean for speed) and OLS on `ln(z/ζ − 1) = ln α̃ + β ln N`.
4. **A JS port of the eligibility gate** (C4) — or, if its inputs are unavailable
   client-side, a pre-computed eligibility flag baked into the export (see G5).
5. **A single-page site** with live controls for `epsilon_start`, `epsilon_end`,
   `min_len` (G3 closed: only these three get controls).
6. **A parity harness** — runs the JS implementation against the notebook's stored
   reference table and reports per-cell deviation (this is how C3/G1 close).

## Data contract (draft)

Per station, the frozen Stage-1 export carries only what Stages 2–4 consume:

```
date, dayofweek, period, start_time, end_time, totaldemand, avg_speed
```

Dropped: `division`, `duration`, `avg_flow`, `traveltimes`, `density`, `avg_occ`,
`year` (derivable), and all `off-peak` rows.

**Caveat (G5):** `density` is dropped above, but the eligibility gate screens on
`density > 60`. Either the gate's input must be retained in some aggregated form, or
eligibility must be pre-computed server-side (i.e. in the export) and shipped as a flag.
The second option is likely correct — eligibility does not depend on the three
user-facing parameters, so it need not be recomputed live. **This must be confirmed in
Plan.**

Additionally required, station-level and parameter-independent:
- `zeta` (free-flow travel time per unit distance), estimated off-peak per station
- lane count `Λ`
- station metadata: lat/lon, freeway, direction, corridor label
- eligibility flag per (station, period)

## Known structural problem in the source

**The eligibility gate is implemented inside a plotting function.**
`traffic_utils/plotting_stage2.py` L108–179 both draws the fundamental-diagram figure
and computes `skip_flags` that determine which station–period pairs proceed to recurrent
detection and BPR calibration. A scientific gate embedded in rendering code is:

- hard to locate (it is why G5 exists),
- hard to port (its inputs are figure-local),
- a reproducibility hazard in the research code independent of this project.

Two fallback defaults in that function disagreed with `MASTER_CONFIG`
(`den_threshold` 40 vs 60; `count_threshold_per_year` 50 vs 75). **Corrected 2026-08-20**
so that a call omitting the config screens at the canonical values rather than silently
at different ones. Recorded as a divergence in the gaps sibling.

Extracting the gate into a pure function is *not* in this project's scope, but should be
noted as a candidate improvement to the research code.

## Backward compatibility

- Reads existing `04_peak_period_result/` CSVs as-is; no schema change requested
  upstream.
- Reference values come from the notebook's stored outputs, which remain the arbiter.
- Nothing in this directory is imported by `traffic_utils` or the notebook; the
  dependency is strictly one-directional (site → pipeline output).

## Dependencies

- **Export step:** Python 3, pandas (already present in the environment).
- **Site:** no framework required. Leaflet for the map (already used in `website/`),
  a plotting library for charts. Explicitly no build step if avoidable — a build step
  is a maintenance liability for an artifact meant to still work in three years.
- **Hosting:** GitHub Pages or equivalent static host (C1).
- **No runtime Python, no server, no database.**

## File-layout sketch (end state)

```
26 near-recurrent-explorer/
├── handoffs/           ← FPEV stage outputs
├── wiki/topics/        ← cross-cycle lessons
├── references/         ← evidence: parity reports, reference tables
├── workbench/surfaces/ ← generated decision surfaces
├── src/
│   ├── export_site_data.py   ← Stage-1 CSV → slim JSON
│   ├── rdpv.js               ← Stage 2 port
│   ├── bpr.js                ← Stages 3–4 port
│   └── parity.*              ← JS-vs-Python comparison harness
├── data/               ← generated JSON (derived; regenerable)
├── index.html
└── README.md
```

## Uncertainty markers

- **Confident:** the Stage 1 / Stage 2+ split is real and clean. Directly verified in
  `pipeline.py` and `recurrent.py`.
- **Confident:** export size is not a constraint (measured, see problem sibling).
- **Uncertain (high impact):** whether eligibility can be pre-computed rather than
  recomputed live. If it turns out to depend on the user-facing parameters, the
  architecture above needs revision. Current belief: it does not depend on them, because
  the gate screens on density observations, not on RDP tolerances. **G5.**
- **Uncertain:** whether `zeta` is stored anywhere reusable or must be recomputed by the
  exporter. `compute_bpr_ff_speed_thresholds()` exists and MASTER_CONFIG holds
  per-station `bpr_ff_speed_threshold` / `offpeak_ff_speed_threshold`, so it is likely
  available — unconfirmed.
- **Uncertain:** whether a charting library can be avoided entirely (hand-rolled SVG).
  Deferred to Plan; not a Frame concern.
- **Uncertain:** whether `min_len` interacts with the gap-breakpoint logic in a way that
  makes the JS port subtler than a direct transcription. `_dedup_multiple_peaks` and the
  gap-breakpoint union in `classify_facet_rdpv` are the parts most likely to hide
  behavior.
