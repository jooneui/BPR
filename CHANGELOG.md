# Changelog

Running history of code changes in this repo, most recent first. One entry
per work session/date; each entry is a short bullet list of what changed and
why. This file (not git log) is the place to look when you've lost track of
what was recently touched.

Claude Code: after making a non-trivial code change in this repo (edits to
`traffic_utils/*.py`, the notebook, or pipeline behavior), append an entry
under today's date (create a new `## YYYY-MM-DD` section if today doesn't
have one yet). One subsection per change: a one-line summary, then a
**Before / After table** — one row per changed line/behavior, exact code (or
`—` / "did not exist" for pure additions). No prose diffs, no `diff` fences
unless a table genuinely can't represent the change. Keep it to what
actually changed, not the surrounding unchanged code. Don't log pure
exploration/no-op sessions or plain data/output file cleanup (one line, no
table needed).

---

## 2026-08-17

### Moved `BPR_input_*.csv` output into `06_BPR_input/`, tagged filenames

New `build_bpr_input_path()` in `traffic_utils/bpr_fitting.py`; used at both
`dfg.to_csv(...)` call sites in `traffic_utils/plotting_stage3.py`.

| | Before | After |
|---|---|---|
| Save location | project root | `06_BPR_input/` |
| Filename | `BPR_input_{vds_id}_{period}.csv` | `BPR_input_{vds_id}_{period}__{tag}.csv` (`{tag}` = recurrent-classification parameter tag) |
| Collision behavior | every parameter run overwrote the same file | different parameter runs get different files |
| `plotting_stage3.py` call (×2) | `dfg.to_csv(f"BPR_input_{vds_id}_{per}.csv")` | `dfg.to_csv(build_bpr_input_path(cfg_i, vds_id, per))` |
| `bpr_fitting.py` | *(function did not exist)* | `build_bpr_input_path(cfg, vds_id, period)` — resolves tag, `os.makedirs`, returns path |

Also deleted the ~80 stale `BPR_input_*.csv` files that had accumulated in
the project root (regenerated data, not source — plain cleanup).

### Confirmed `date`/`start_time`/`end_time` already use `;` — CSVs on disk were just stale

No code change needed — `aggregate_segment_level_bpr()` in
`traffic_utils/bpr_fitting.py` was already fixed (uncommitted, from an
earlier session). The CSVs on disk just predated that fix.

| Column | Before (old code / stale CSVs) | After (current code) |
|---|---|---|
| `date` | `seg['end_date'].iloc[0] if 'end_date' in seg.columns else seg['date'].iloc[-1]` (one date) | `';'.join(seg['date'].astype(str))` (all member dates) |
| `start_time` | `seg['start_time'].iloc[-1]` | `';'.join(seg['start_time'].astype(str))` |
| `end_time` | `seg['end_time'].iloc[-1]` | `';'.join(seg['end_time'].astype(str))` |
| CSV cell, e.g. | `"110711,110718,110725"` | `"110711;110718;110725"` |

Re-running Stage 4 (after the path change above) regenerates the CSVs with
the current code.

### Added `plot_recurrent_time_distribution_by_dow()` — single-station, 2x3 day-of-week grid

New function in `traffic_utils/plotting_stage2.py` (~line 715), right after
the existing `plot_recurrent_time_distribution_grid()`. Reuses that
function's per-panel KDE+rug logic verbatim; only the panel axis changes.

| | Before (`..._grid`) | After (new `..._by_dow`) |
|---|---|---|
| One panel = | one station (`vds_id`), all days of week pooled | one day-of-week group, for one chosen station |
| Panels / grid | all of `cfg['VDS_list']`, `ncols` param → `nrows = ceil(n/ncols)` | fixed 2×3: Mon, Tue, Wed, Thu, Fri, Weekend (Sat+Sun pooled) |
| Row filter | `df[df['vds_id'] == vds_id]` | `df[df['dayofweek'].isin(dow_values)]` (from new `_DOW_PANEL_GROUPS`) |
| Panel title | station label | day-of-week label |
| Call | `plot_recurrent_time_distribution_grid(cfg, ncols=3, out_name=...)` | `plot_recurrent_time_distribution_by_dow(cfg, vds_num=RC_VDS_num)` |

Notebook: new cell inserted after the existing grid-plot cell (unchanged),
defining the station and calling it:

```python
RC_VDS_num = MASTER_CONFIG['VDS_list'][0]  # <-- set to the single station to inspect
plot_recurrent_time_distribution_by_dow(cfg=MASTER_CONFIG, vds_num=RC_VDS_num)
```

### Added `CHANGELOG.md` + a pointer to it in `CLAUDE.md`

| | Before | After |
|---|---|---|
| `CHANGELOG.md` | did not exist | this file — dated history, Before/After tables per change |
| `CLAUDE.md` | no mention of a change log | new "Change Log" section: append an entry here after non-trivial changes |
