---
stage: 3-execute
artifact: phase-4-handoff
project: near-recurrent-explorer
phase: P4 — Site UI
status: complete
created-at: 2026-08-20
authors: [Sonnet5CC]
reads:
  - stage-2-plan-Sonnet5CC.md (P4 specification, D1/D4/D5)
  - stage-3-phase-3-Sonnet5CC.md (verified computation engine, this phase's dependency)
next-stage: Stage 3 Phase 5 — Deploy (blocked pending author decision — see below)
---

# Stage 3 Phase 4 — Site UI

## Headline

`index.html` + `src/ui.js` + `src/style.css` — Leaflet map, week×DOW heatmap (D1: hand-
rolled SVG), two live sliders (ε tolerance, min segment length L), and a BPR scatter+fit
chart. Verified in an actual Chrome tab, not just by reading the code: station selection,
live slider recompute, and the excluded-period path all confirmed working via dispatched
real DOM events. **D5's static conventional-unit overlay is NOT implemented** — see
Divergences; this is the one item most needing your decision.

## Deliverables

- `index.html` — page structure, loads Leaflet from CDN + local scripts, no build step
- `src/ui.js` — map init, station/period selection, slider wiring, heatmap + BPR rendering
- `src/style.css` — dark theme, status-pill-style legend, responsive-ish layout

## Verification ran

Served locally (`python3 -m http.server 8099`) and driven in an actual Chrome tab:

1. **Load check:** all resources (`index.html`, `manifest.json`, `rdpv.js`, `bpr.js`,
   `ui.js`, `style.css`, station JSON) returned `200`. Zero console errors on load.
2. **Map renders:** 9 stations plotted at correct lat/lon, colored green (fully eligible)
   or orange (one period excluded) correctly per `manifest.json`.
3. **Station selection (real click, not simulated):** dispatched a genuine `MouseEvent`
   on the Leaflet marker's actual SVG path element (not a coordinate-based click — my
   screenshot tool's coordinate system didn't match the page's actual viewport, a tooling
   artifact caught and worked around, not a site bug). Result: selecting I5 SB-2
   correctly updated the station header, toggle, and rendered the heatmap.
4. **Live recompute confirmed with real numbers:** moved the ε slider from 0.15 → 0.35 on
   I5 SB-2 AM. BPR stats changed from `N=32, β=0.860, R²=0.766` (0.15 — matches the
   confirmed reference exactly) to `N=122, β=0.802, R²=0.608` (0.35) — a real, immediate
   recompute, not a cached swap.
5. **Excluded-period path:** toggled I5 SB-2 to PM (excluded per reference). Notice
   rendered with the correct rate-based explanation; sliders and heatmap correctly hidden
   rather than showing empty/broken panels.

## Divergences

**Resolution (2026-08-20, post-handoff):** author confirmed conventional temporal units
are out of scope for this project entirely — not a gap to close later. D5 revised in
Plan; Frame's P4 principle revised accordingly. The Stage-4 `traffic_utils` failure
below is now historical context, not an open investigation.

**R4 (original entry, kept for the record) — D5's static conventional-unit overlay
dropped, not deferred silently.**
Plan committed to showing pre-computed peak-hour and hourly-unit BPR fits alongside the
live near-recurrent fit (D5), computed once in Python since they don't depend on the
live parameters. Attempted this by running `run_full_pipeline` with
`temporal_scale='peak'` and `temporal_scale='hour_split'` on MASTER_CONFIG (Stage-1 data
for both already existed on disk). **Both failed** at Stage 4 with a swallowed exception
(`"BPR fit plotting skipped or failed: 'peak'"` / `'hour_split'` — no traceback surfaced).
The only known-working path for these temporal scales is `run_paper_results.py`'s
`paper_config(unit)`, which Frame's G12 already established as untrustworthy (stale
11-station list, stale parameters). Rather than either (a) spend unbudgeted time
reverse-engineering what `paper_config` does differently, or (b) fabricate placeholder
comparison numbers, **the site ships without this panel**. Classified R4 rather than R2:
this isn't a broken build, it's a considered scope cut under real constraints, made
explicit rather than silently shipped as "done." Reasoning: an unverified conventional-
unit comparison would actively damage the site's core credibility claim if wrong (C3's
spirit) — worse than the panel simply not existing yet.
**Propagate-back candidate:** if you want this panel, the actual blocker is understanding
why `temporal_scale` in `[peak, hour_split]` fails at Stage 4 with the current
`MASTER_CONFIG` — that's a `traffic_utils` investigation, not a site-side fix, and out of
this project's stated scope (C6: never modify `traffic_utils` without explicit
instruction).

**R3 — map click coordinates, tooling artifact.** Not a site defect — recorded because it
cost real debugging time and is worth remembering: automated screenshot-based clicking
tools can have a coordinate system that doesn't match the actual page viewport (here,
screenshots were rendered ~15-20% smaller than the real 1745px-wide viewport). Confirmed
by dispatching a real `MouseEvent` directly on the target element instead of relying on
pixel coordinates from a screenshot.

## Gaps touched

None from Frame. This phase's D5 gap is new, self-contained, and explicitly not filed as
a formal Frame-style gap since it doesn't block anything else — recorded here as the
divergence trail, and surfaced prominently in the end-of-session summary for you.

## What unblocks Phase 5

Everything needed for a basic deploy is present and locally verified. **Phase 5 (deploy)
is intentionally not started** — publishing to a public URL is an outward-facing,
not-easily-reversible action, and per this session's operating constraints that requires
your explicit go-ahead rather than proceeding autonomously. See the end-of-session
summary for what's needed from you to unblock it.

## Uncertainty markers

- **Confident:** the core interactive loop (select station → adjust parameters → see
  live-recomputed classification and fit) works correctly, verified with real events and
  real numbers, not just code review.
- **Not verified:** cross-browser behavior (only tested in one Chromium-based tab), or
  actual real-network load time (only tested over `localhost`, which trivially satisfies
  any timing budget — the gzip estimate from earlier phases is the real evidence for the
  live-network case, not this test).
- **Not verified:** mobile/narrow-viewport layout. The CSS has some responsive
  provisions (flexible widths) but was not tested at a phone-sized viewport.
- **Open, needs your decision:** whether D5's missing panel is acceptable for a first
  version, or whether it's worth investigating the `traffic_utils` Stage-4 failure before
  this ships anywhere.
