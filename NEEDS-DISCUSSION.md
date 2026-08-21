# Needs your input — 2026-08-20 autonomous session

Everything below is either a decision only you can make, or something worth knowing
before this goes further. Ordered by how much it blocks.

## 1. ~~Blocking deployment~~ RESOLVED — `.gitignore` updated

Added `!26 near-recurrent-explorer/**` to `01_BPR/.gitignore` (simple approach, per your
call): the whole project, including `data/*.json`, is now tracked. Not yet committed —
that's part of P5.

## 2. ~~D5's conventional-unit comparison~~ RESOLVED — permanently out of scope

Per your direction, these temporal units aren't of interest to this project. Not
deferred — dropped. Updated Plan's D5, Frame's P4 principle, and the phase-4 handoff to
reflect this as a settled scope decision rather than an open question. The
`traffic_utils` Stage-4 failure found while attempting this is now historical context
only, not something to investigate.

## 3. Not blocking, but worth knowing: one real research-code finding

- **Figure 6 discrepancy (Frame G11).** The current pipeline excludes SR91-WB AM and
  SR134 EB-1 AM (insufficient congestion: 68.3/yr and 61.4/yr against a 75/yr
  requirement) — but the published Figure 6 lists both as analyzed for AM and PM. Likely
  explanation: the paper used a looser threshold (possibly 50/yr, matching
  `run_paper_results.py`'s own default) that predates your update to 75/yr. Not fixed
  anywhere — the site follows current code per your instruction that the paper is
  outdated. Worth a note to Wen-Long if a paper revision is still possible.

~~`weighted_harmonic_mean` doesn't compute a harmonic mean~~ — **retracted.** On closer
review (working through Eq. 9 algebraically when you asked for detail), this is not a
discrepancy: a demand-weighted harmonic mean of speed and a demand-weighted arithmetic
mean of travel time are the same operation in two different units, and the function's
input is already travel-time (reciprocal) space. The code matches the paper exactly.
Corrected in the phase-2 handoff. Sorry for the false alarm — flagging the correction
here rather than quietly deleting the original claim.

## 4. Two smaller things I decided without asking — flag if you disagree

- **Two malformed-time bugs and a floating-point precision issue** in the exporter were
  found and fixed during P1 verification (details in phase-0/phase-1 handoffs). These
  are corrections to *my own new exporter code*, not to `traffic_utils` — no research
  code was touched. Mentioning in case you want to sanity-check the reasoning yourself;
  I'm confident in it (verified against the real pipeline output, not just argued for).
- **Export size** ended up at 1935 KB raw / ~478 KB gzipped — well over Plan's 1024 KB
  tripwire, growing each time correctness required more precision (rounding literally
  broke tie-breaking — see phase-1 handoff). I judged gzipped size against real load time
  as the constraint that actually matters and stopped optimizing there. If you disagree,
  this is revisitable (compression, lazy-loading per station, a lighter data format).

## 5. Still open from Frame, unrelated to this session's work

- **G8** (does a stranger actually understand the site in 2 minutes) — correctly belongs
  to Verify, not attempted here since it needs a real human tester.
- Cross-browser and mobile-layout testing — only verified in one desktop Chrome tab.

---

**Everything else is done and verified — not waiting on you.** P0–P4 are complete, the
core computation is proven correct against real pipeline output (not just internally
consistent), and the site works end-to-end in a real browser. Run
`python3 -m http.server 8099` from `26 near-recurrent-explorer/` to see it yourself.
