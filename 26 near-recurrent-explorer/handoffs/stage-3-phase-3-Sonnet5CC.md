---
stage: 3-execute
artifact: phase-3-handoff
project: near-recurrent-explorer
phase: P3 — Parity harness
status: complete
created-at: 2026-08-20
authors: [Sonnet5CC]
reads:
  - stage-2-plan-Sonnet5CC.md (P3 specification)
  - references/bpr_calibration_reference_C3a.csv
next-stage: Stage 3 Phase 4 — Site UI (parallel branch, does not depend on this phase
  completing — but this phase's PASS is what makes P4 trustworthy to build on)
---

# Stage 3 Phase 3 — Parity harness

## Headline

`src/parity.js` runs the full JS pipeline (P0 export → P1 classify → P2 aggregate/fit)
against the confirmed reference for all 18 station-periods. **ALL PASS.** This is the
actual, direct closure of Frame's G1 and Plan's success criterion 4 — not asserted, run.

## Deliverables

- `src/parity.js` — the harness
- `references/parity-report-2026-08-20.md` — committed evidence (full run output)

## Verification ran

```
$ node parity.js
[... see references/parity-report-2026-08-20.md for full table ...]
ALL PASS
```

18/18 station-periods pass:
- 11 eligible: N matches exactly; log α̃/β agree to 4-5 decimals (tolerance was 1e-3;
  actual differences ranged ~5e-5 to ~5e-4)
- 7 excluded: JS's static eligibility flags match the reference's N=0 rows exactly

## Divergences

None in this phase itself — this phase is where P0/P1/P2's divergences (documented in
their own handoffs) got confirmed as actually resolved, not just believed resolved.

## Gaps touched

**Closes G1** (JS/Python numerical parity) for real — Frame's version of G1 confirmed
the *target* existed; this phase confirms the *port* matches it. Success criterion 4
("At the reference parameter set, the site's calibration table matches a freshly
regenerated Python reference to ≥3 decimals") is met.

## What unblocks Phase 5

Nothing directly — P4 (site UI) doesn't depend on P3 finishing (Plan's parallel-branch
design), but P5 (deploy) needs both P3 and P4 done. This phase being PASS means P4 can
be built with confidence the underlying computation is correct, so any bugs found while
building the UI are UI bugs, not silently-wrong math.

## Uncertainty markers

- **Confident:** the core computation (P0+P1+P2 combined) is verified correct against
  real, confirmed ground truth across every eligible station-period, not spot-checked.
- **Uncertain (carried from P2):** the small residual numerical difference (well within
  tolerance, but not zero) between this port's fit and the reference's — two candidate
  explanations offered in the parity report, neither confirmed. Not blocking; flagged
  for anyone who later tightens the tolerance below ~1e-4.
- **Not yet exercised:** the harness only tests at the single C3a reference parameter
  set. It does not (and per Plan, doesn't need to) verify correctness at *other*
  parameter settings a user might drag the sliders to — there's no Python ground truth
  to check those against. P1's algorithmic fidelity (verified segment-by-segment for two
  facets, not just aggregate counts) is what gives confidence the port generalizes
  correctly to untested parameter values, not a second parity check.
