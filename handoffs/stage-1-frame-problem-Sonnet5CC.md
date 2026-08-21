---
stage: 1-frame
artifact: problem-statement
project: near-recurrent-explorer
status: draft
created-at: 2026-08-20
authors: [Sonnet5CC, jooneui]
reads:
  - 22 Research paper/TRB2027_near-recurrent-peak_20260801_F.pdf
  - 2nd_phase_BPR_function.ipynb (MASTER_CONFIG, stored outputs)
  - traffic_utils/recurrent.py, bpr_fitting.py, plotting_stage2.py
  - website/PLAN.md (prior attempt)
siblings:
  - stage-1-frame-architecture-Sonnet5CC.md
  - stage-1-frame-gaps-Sonnet5CC.md
next-stage: Stage 2 — Plan
---

# Problem statement — sibling 1/3

## TL;DR

The near-recurrent peak-period method has one parameter set (the RDP_v tolerances
`epsilon_start`, `epsilon_end`, and minimum length `min_len`) whose effect *is* the
method: it decides which weeks count as stable, which determines the BPR calibration,
which produces the paper's headline result. That effect is currently invisible — locked
in 141 pre-computed CSVs and a notebook only its author can run. This project builds a
static, zero-install web page where a technical stranger moves those controls and
watches the near-recurrent bands and the BPR fit recompute live, and understands in two
minutes why the temporal unit matters.

## Problem (in plain English)

The TRB2027 paper establishes a framework that automatically separates **demand-driven
recurring congestion** from **one-off non-recurrent congestion**, using only detector
data and no labels. It then shows that calibrating a volume–delay function over the
resulting near-recurrent peak period yields theoretically admissible exponents
(β ≈ 0.2–1.3), whereas conventional fixed-clock temporal units produce
theoretically-inadmissible *negative* exponents in several cases.

Three problems follow from the current state of that work:

1. **The method's central parameter is untouchable.** Changing `epsilon_start` /
   `epsilon_end` / `min_len` currently requires running a Jupyter notebook against
   several GB of PeMS data with a local `traffic_utils` install. Nobody but the author
   can do it, so nobody but the author develops intuition for what the parameter does.

2. **The headline finding is invisible in every existing artifact.** The three prior
   website attempts visualize Stage 1 (daily peaks) and Stage 2 (recurrent labels) but
   contain no BPR calibration and no comparison against conventional temporal units —
   i.e. they omit the contribution.

3. **The work is not demonstrable to the audience that matters right now.** The author
   needs to explain this research, cold, to interviewers and practitioners who will
   give it roughly two minutes and will not read a 20-page paper.

## Why this matters now

The paper is final (submitted 2026-07-30). The research contribution is settled; what
is missing is a way to *transmit* it. The author's near-term need is explaining this
work in interview settings at mapping/mobility companies (Google Maps, Uber, Waymo) and
to transportation agencies (Caltrans). A static link that works instantly is the highest
-leverage artifact available, and it is achievable because — per the architecture
sibling — the expensive stage can be frozen and the interesting stage runs in a browser.

## Audience

**Primary: a technical stranger with ~2 minutes and no context.**
Concretely: an interviewer or engineer at a mapping/mobility company, or a Caltrans
engineer. They have not read the paper. They will not install anything. They will click
a link, look, form an impression, and leave. If they cannot reach the point in two
minutes, the artifact has failed.

**Secondary: the author.** A working instrument for parameter intuition and for
sanity-checking pipeline output against the published numbers.

**Explicitly not the audience (for v1):** TRB reviewers verifying the paper line by
line. That is a different artifact (a reproducibility appendix) and would pull the
design toward completeness over legibility.

## Principles

- **P1. The visitor is a stranger with two minutes.** Everything must be legible cold,
  without the paper. Any element requiring prior context is a defect.
- **P2. Lead with the anomaly story.** The chosen lead is the *unsupervised
  recurrent-vs-incident separator*: "how much of this station's congestion is not
  explainable as recurring demand?" This maps onto a problem the primary audience
  already owns. The β≈1 finding and the drifting-rush-hour finding are supporting acts,
  not the opening.
- **P3. Demonstrate reasoning, not just data.** The value to an interviewer is evidence
  that the author can define a problem, build a method, and prove it beats the
  alternative. A data browser does not do this; a before/after comparison does.
- **P4. ~~The comparison is the payload~~ — REVISED (2026-08-20, during Execute).**
  Originally: near-recurrent vs. fixed-peak-hour vs. hourly, shown together. Dropped —
  the author confirmed conventional fixed-clock temporal units are not of interest to
  this project; not deferred, out of scope. The lead-angle framing (P2, the anomaly
  story) and the live-recompute demonstration (P5) remain the actual payload. A
  `traffic_utils` Stage-4 failure for those temporal units was found while attempting
  this (Execute phase-4 handoff) and is now moot — not to be investigated.
- **P5. Live recompute over pre-baked results.** Moving a control must actually run the
  algorithm, not swap between cached outputs. The credibility of the demonstration
  depends on the visitor believing the computation is real.
- **P6. Cultivate, don't pre-plan.** Build for the current 9 stations rigorously before
  generalizing to new corridors. (Author's explicit direction.)

## Hard constraints

- **C1. Static hosting only.** No backend, no server that can be unreachable or cold
  when someone opens the link. Follows from the audience: a sleeping server is worse
  than no link.
- **C2. Stages 2–4 must recompute live in the browser.** Pre-computed dropdowns do not
  satisfy the requirement. Stage 1 output is frozen input.
- **C3. Output must match a freshly regenerated Python reference.** At the reference
  parameter set the site's (log α̃, β, R², N) must reproduce the Python pipeline's output
  to ≥3 decimal places. **The reference table must be regenerated by running the current
  `traffic_utils` code** — the notebook's stored outputs and all prior site data are
  treated as potentially stale and are not the authority. A site that disagrees with the
  author's own current results damages rather than helps.
- **C3a. Reference parameter set: AM ε = 0.15, PM ε = 0.19, `min_len` = 3.** These are
  the author's current optimal values and are the site's default slider position. The
  paper's Table 1 values (AM 0.3/0.2, PM 0.2/0.3) describe the single-station
  verification demo (VDS 1203506, 2011), not the multi-station calibration, and are not
  the reference here.
- **C4. The eligibility gate is part of the method and must be reproduced.**
  Density threshold **60 veh/mi/ln**, minimum **75 congested points per year of
  record**. These values are canonical; code fallbacks were corrected to match on
  2026-08-20.
- **C4a. Ineligible station–periods are excluded entirely, matching the pipeline.**
  A station–period failing the gate shows neither near-recurrent bands nor a BPR fit; it
  is marked excluded, with the reason (observed rate vs. the 75/yr requirement) stated.
  This matches current pipeline behaviour exactly — `plotting_stage2.py` skips recurrent
  detection *and* BPR — so no `traffic_utils` change is required and every site cell has
  a Python counterpart to check parity against.
- **C5. Markdown/JSON canonical, generated artifacts derived.** Exported site data is
  regenerated from `04_peak_period_result/` by a scripted export; never hand-edited.
- **C6. No modification of published research results.** The site reads the pipeline's
  output; it does not become a second, divergent implementation of the science. Any
  discrepancy between JS and Python is a defect in the port, not a new result.

## What this is NOT

- **Not a new corridor expansion.** New freeways/stations are explicitly deferred
  (author's direction: rigorous on current stations first).
- **Not a Stage-1 reimplementation.** Raw 5-minute PeMS processing stays in Python,
  offline, frozen.
- **Not a backend service.** No Flask/FastAPI, no database, no auth.
- **Not a paper-verification appendix.** Completeness is subordinate to legibility.
- **Not a replacement for `website/`, `25 product/`, or `peak-atlas-site/`.** Those
  remain as-is; this is a clean directory that borrows from them freely.
- **Not a general-purpose PeMS explorer.** Scope is this paper's method and its claim.

## Success criteria

1. A stranger who has never seen this work can open the link and, within two minutes,
   state what "near-recurrent" means and why it changes the BPR fit.
2. Moving `epsilon_start` / `epsilon_end` / `min_len` visibly changes the recurrent
   bands **and** the BPR fit, recomputed live, with no page reload and no server.
3. The site opens at the reference parameters (C3a) so the first view is the author's
   current best result; the controls are adjustable from there.
4. At the reference parameter set, the site's calibration table matches a freshly
   regenerated Python reference to ≥3 decimals (C3).
5. Station–periods failing the eligibility gate are visibly marked excluded, with the
   reason shown, and the excluded set matches the pipeline's `[SKIP]` set exactly
   (C4, C4a).
5. The site loads and is interactive in under 3 seconds on a normal connection.
6. The author can send the URL in an interview context without caveats or setup notes.

## Uncertainty markers

- **Confident:** Stages 2–4 are computationally trivial (RDP on ≤53 points per facet;
  OLS on a handful of points) and are portable to JS. Verified by reading
  `classify_facet_rdpv` and `run_full_pipeline(stages=[2,3,4])`.
- **Confident:** Stage-1 export size is not a constraint. Measured: 9.4 MB across 141
  station files; the paper's 9 stations are ~3.6 MB raw and compress well below 1 MB
  after dropping off-peak rows and unused columns.
- **Uncertain — the eligibility gate's true input.** The gate reads a `density` column
  and lives inside `plotting_stage2.py`, a *rendering* module. Whether its input is
  available in the Stage-1 export, or requires a separate density series, is unresolved
  (G5). This is the highest-risk unknown: if eligibility needs data we are not
  exporting, C4 and C2 come into tension.
- **Uncertain — per-DOW vs per-period eligibility.** The author's own note in
  `MASTER_CONFIG` states eligibility is currently evaluated per day-of-week but should
  apply to the whole AM/PM period. Reproducing "the paper" therefore requires deciding
  which behavior produced the published numbers (G7).
- **Uncertain — which parameter set is the reference.** The paper reports
  ε=0.3/0.2 (AM) and 0.2/0.3 (PM); the notebook's last stored run used 0.15/0.15 (AM)
  and 0.19/0.19 (PM). These are different. (G6)
- **Uncertain — whether one lead angle is enough.** P2 commits to the anomaly framing,
  but it is untested on a real reader. Verify should test it on someone unfamiliar.
