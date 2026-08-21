# near-recurrent-explorer

An interactive, static web page for the TRB2027 near-recurrent peak-period framework
(Hong & Jin). Move the RDP_v tolerances and minimum-length control; the near-recurrent
bands and the BPR calibration recompute live in the browser.

Run as an **FPEV-cadenced project** (Frame → Plan → Execute → Verify).
See `handoffs/` for stage outputs.

## Layout

- `handoffs/`           — FPEV stage outputs (the durable record)
- `wiki/topics/`        — cross-cycle lessons worth keeping
- `references/`         — evidence: parity reports, reference tables, reviews
- `workbench/surfaces/` — generated decision surfaces (derived; regenerable)
- `src/`                — exporter (Python) + JS ports + parity harness
- `data/`               — generated site JSON (derived; regenerable)

## Core architecture

Stage 1 (raw 5-min PeMS → daily congested periods) is **expensive**; it stays in Python,
runs offline, and is frozen to JSON. Stages 2–4 (near-recurrent identification → BPR
calibration) operate on ≤53 points per facet and are **trivial**; they are ported to
JavaScript and run live in the browser. No backend.

## Canonical values

- **Reference parameters (site default):** AM ε = **0.15**, PM ε = **0.19**,
  `min_len` = **3**. Adjustable in the UI from there.
- **Eligibility gate:** density > **60** veh/mi/ln, ≥ **75** congested points per year of
  record. Failing station–periods are excluded entirely — no recurrent bands, no BPR fit —
  matching the pipeline, and marked with the reason.
- **User-facing parameters:** `epsilon_start`, `epsilon_end`, `min_len`.

## Authority

`traffic_utils/` is the canonical implementation of the science. The JavaScript port is
a derived reimplementation for interactivity. If they disagree, Python wins and the port
is the defect. The parity reference is regenerated from the **current** Python code;
notebook stored outputs and prior site data are treated as stale.

## Status

**Stage 3 Execute — P0 through P4 complete and verified. P5 (deploy) intentionally not
started — needs your decision, see below.**

- **P0 (exporter):** built, then amended twice after real bugs surfaced in P1 testing.
- **P1 (RDP_v port):** all 11 eligible station-periods match the confirmed reference
  exactly, after finding and fixing 3 real bugs (missing dedup step, malformed source
  time strings, a floating-point precision issue in duplicate-date tie-breaking).
- **P2 (BPR fit port):** done; faithfully replicates a real paper/code naming
  discrepancy (`weighted_harmonic_mean` doesn't compute a harmonic mean) rather than
  "fixing" it, since C3 requires matching the code, not the paper's prose.
- **P3 (parity harness):** **ALL PASS**, 18/18 station-periods — see
  `references/parity-report-2026-08-20.md`.
- **P4 (site UI):** built and verified in an actual browser (real clicks, real slider
  moves, real recomputed numbers) — with one committed scope cut: D5's static
  conventional-unit comparison panel is **not implemented** (the `traffic_utils` code
  path for it failed and wasn't debuggable within this session's scope; see phase-4
  handoff).
- **P5 (deploy):** not started. Two things need your input first — see project root's
  summary / ask in chat.

Run locally: `python3 -m http.server 8099` from this directory, then open
`http://localhost:8099`.
