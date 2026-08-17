# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a traffic engineering research codebase for **BPR (Bureau of Public Roads) function calibration** from freeway detector data. The workflow identifies peak congestion periods, classifies recurrent vs. non-recurrent congestion, and fits log-linearized BPR travel-time functions.

Primary interface: `2nd_phase_BPR_function.ipynb`. All logic lives in `traffic_utils/`.

## Change Log

`CHANGELOG.md` in this directory is a running, dated history of code changes
(most recent first). **After making a non-trivial code change** (edits to
`traffic_utils/*.py`, the notebook, or pipeline behavior), append a bullet
under today's date — create a new `## YYYY-MM-DD` section if one doesn't
exist yet. Keep it to one line per change: file(s) touched + plain-language
reason. Skip pure exploration/no-op sessions.

## Running the Pipeline

The notebook is the main entry point. Reload modules after any edit to `traffic_utils/`:

```python
import importlib, sys
to_remove = [k for k in sys.modules if k.startswith('traffic_utils')]
for k in to_remove:
    del sys.modules[k]
import traffic_utils
```

Run the full 4-stage pipeline:
```python
run_full_pipeline(MASTER_CONFIG, stages=[1, 2, 3, 4])
```

Run individual stages (e.g., just recurrent + BPR):
```python
run_full_pipeline(MASTER_CONFIG, stages=[3, 4])
```

There are no build/lint/test commands — this is a research notebook project with no CI setup.

## Four-Stage Pipeline Architecture

**Stage 1 — Daily Peak Detection** (`pipeline.py`)
- Reads raw PeMS 5-min detector files from `11 Rawdata/5min/<VDS_num>/`
- Aggregates lane-level data into speed/flow/occupancy profiles
- Detects congested periods using the method specified in `speedbased_params.method`
- Saves per-day results to `04_peak_period_result/c_daily_traffic_division_*.csv`

**Stage 2 — Fundamental Diagram Check** (`plotting_stage2.py`)
- Plots FD (density vs. flow) and runs a density threshold check
- Produces `cfg['_fd_skip_map']`: a per-VDS dict `{vds_id: {'AM': bool, 'PM': bool}}` flagging whether each period has sufficient congested data
- This skip map flows into Stages 3 and 4 to suppress periods with no congestion

**Stage 3 — Recurrent Peak Classification** (`recurrent.py`)
- Reads Stage 1 CSVs, groups by (VDS, day-of-week, period)
- Applies the `recurrent_method` algorithm to label each week as recurrent or non-recurrent
- Saves labeled tables to `05_recurrent_peak_result/recurrent_days_labeled_<tag>.csv`
- Saves excluded days to `05_recurrent_peak_result/excluded_recurrent_days_<tag>.csv`

**Stage 4 — BPR Calibration** (`bpr_fitting.py`, `plotting_stage3.py`)
- Fits log-linearized BPR: `ln(z(Q)/ζ - 1)` vs `ln(Q)` using OLS/WLS
- The linearization version is selected via `bpr_version_key` (see registry below)
- Generates plots in `02 fig/12 Daily BPR/`

## Key Configuration — MASTER_CONFIG

All parameters are in a single dict in notebook cell 3. The most important keys:

| Key | Effect |
|-----|--------|
| `VDS_list` | List of detector IDs to process |
| `spatial_scope` | `'single'` (per-VDS), `'multi_vds'` (combined), `'network'` (C1 data) |
| `data_format` | `'raw'` (PeMS Excel files) or `'section_combined'` (C1 Detector.csv) |
| `temporal_scale` | `'speedbasedpeak'` (adaptive), `'entireday'`, `'hour'` |
| `recurrent_method` | `'RDP_v'` (default), `'simpleband'`, `'shortest_interval'`, `'PELT'` |
| `bpr_version_key` | `'v3'` (default) — selects linearization from `LINEAR_REGISTRY_BPR` |
| `free_tt_mode` | `'by_date_offpeak'` or `'fixed'` — how free-flow travel time is sourced |
| `free_tt_method` | `'offpeak_avg'` (uses `bpr_ff_speed_threshold`) or `'FD'` (uses `free_tt_FD`) |
| `W_minutes` | Width of the aggregation window in minutes (used to normalize demand) |
| `segment_aggregation` | `True` to aggregate BPR data per stable RDP_v segment rather than per day |
| `segment_min_weeks_by_period` | Min weeks per segment for retention, e.g. `{'morning-peak': 2, 'afternoon-peak': 2}` |
| `period_include` | Dict of `temporal_scale → [period names]` to include in BPR fitting |
| `drop_nonrecurrent_days` | `True` to exclude non-recurrent days from BPR fit |
| `dry_run` | `True` to skip all file writes |
| `plots` | Dict of boolean flags per output type |

### Speed threshold keys

`speedbased_params.offpeak_ff_speed_threshold` maps VDS ID → free-flow speed (mph). This is the canonical free-flow speed used by Stage 1 detection.

`bpr_ff_speed_threshold` maps VDS ID → free-flow speed used exclusively by Stage 4 BPR fitting (data-derived from 0–3 am and 22–24 h off-peak). Run `compute_bpr_ff_speed_thresholds(MASTER_CONFIG)` once after editing `MASTER_CONFIG` to auto-populate this from the data.

### BPR linearization registry

`LINEAR_REGISTRY_BPR` in `bpr_fitting.py` defines three transforms:

| Key | X variable | Notes |
|-----|------------|-------|
| `v3` (default) | `ln(Q)` where Q = `totaldemandoverlanes` | **all-lane total** demand |
| `v2` | `ln(Tq)` where Tq = `totaldemand` | **per-lane** demand |

⚠️ The column names are the reverse of what they suggest. `data_io.py` sets
`flow` to the *mean* across lanes, so `totaldemand` is already a **per-lane**
vehicle count; `bpr_fitting.py` then computes
`totaldemandoverlanes = totaldemand * len(lane_num)`, i.e. the **all-lane total**
("over lanes" means *summed over* lanes, not *divided by*). So `v3` fits all-lane
demand and `v2` fits per-lane demand.
| `v10` | `ln(q)` — avg_flow | flow rate |

## traffic_utils Module Map

| Module | Responsibility |
|--------|----------------|
| `pipeline.py` | `run_full_pipeline`, `run_single_vds`, `run_network_c1` — orchestrates all stages |
| `segmentation.py` | `rdp_v` (Ramer–Douglas–Peucker with vertical error), `detect_speed_peaks`, PELT/RDP wrappers |
| `recurrent.py` | `classify_facet_rdpv`, `classify_facet_fixed_band`, `run_recurrent_peak_pipeline` |
| `bpr_fitting.py` | `build_file_path`, `LINEAR_REGISTRY_BPR`, `load_and_annotate`, `apply_filters`, OLS fit |
| `data_io.py` | Raw data loading, `aggregate_rawdata_5min`, section-combined loader |
| `metrics.py` | `process_daily_traffic`, `compute_metrics` — demand/travel-time aggregation |
| `plotting_stage1.py` | Speed profile plots, duration-demand panels, total-demand histograms |
| `plotting_stage2.py` | FD plots (`plot_fd_all_in_one_png`), recurrent-facet shared helpers |
| `plotting_stage3.py` | BPR fit grid plots (`plot_bpr_all_in_one_png_3x3`, `plot_bpr_section_grid`) |
| `classification.py` | `label_solely_speed`, `label_divisions_occupancy`, etc. — congestion labeling strategies |
| `_legacy.py` | Old plotting/analysis code kept for reference — not imported by `__init__.py` |

## Peak Detection Methods

The `speedbased_params.method` key selects the intra-day segmentation algorithm:

- **`RDP_v`** (default): Applies Ramer–Douglas–Peucker with **vertical** error on the cumulative speed curve. The custom `rdp_v()` in `segmentation.py` replaces the `rdp` library's Euclidean variant. Epsilon controls sensitivity (larger = fewer breakpoints).
- **`pelt`**: PELT change-point detection on raw speed via the `ruptures` library.
- **`RDP`**: Standard RDP using Euclidean distance (legacy).

## Recurrent Classification Methods

The `recurrent_method` key controls Stage 3. All methods write their per-VDS parameters under `recurrent_method_params.<method>`:

- **`RDP_v`**: Applies `rdp_v()` to cumulative start-hour and end-hour series across calendar weeks. `fixed_var_by_period` determines which variable is the temporal anchor (`start_hour` for morning, `end_hour` for afternoon). Breakpoints split the series into segments; segments shorter than `segment_min_weeks` are excluded as non-recurrent. When `segment_aggregation=True`, adjacent retained segments are kept separate via `segment_id` merged from the labeled CSV.
- **`simpleband`**: Histogram-based fixed-bandwidth window around the modal start/end hour.
- **`shortest_interval`**: Finds the narrowest interval covering a given coverage fraction.
- **`PELT`**: Change-point detection on the week-by-week peak time series via `ruptures`.

## Output File Naming

Stage 1 CSV: `04_peak_period_result/c_daily_traffic_division_{spatial_scope}_{VDS_num}_{temporal_scale}_{aggregate_timeframe}_{method}_{congest_method}.csv`

Stage 3 labeled CSV: `05_recurrent_peak_result/recurrent_days_labeled_{output_tag}.csv`
Stage 3 excluded CSV: `05_recurrent_peak_result/excluded_recurrent_days_{output_tag}.csv`
Stage 3 facet meta CSV: `05_recurrent_peak_result/facet_meta_{output_tag}.csv`

The `output_tag` is auto-generated by `build_recurrent_output_tag()` in `recurrent.py` encoding all method parameters into a readable string.

## Data Directory Layout

```
11 Rawdata/5min/<VDS_num>/    ← raw PeMS Excel files (not in git)
04_peak_period_result/        ← Stage 1 outputs
05_recurrent_peak_result/     ← Stage 2/3 outputs
02 fig/                       ← all plot outputs
01_1_BPR_network/C1data/      ← C1 network data (Detector.csv, SectionLength.csv)
```

Raw data and outputs are excluded from git (`.gitignore` whitelists only notebooks and `.py` scripts).

## section_combined Data Format

When `data_format='section_combined'`, the pipeline reads a single `Detector.csv` (C1 format) and auto-expands each base VDS into per-section sub-configs via `_make_section_config()`. Stage 4 runs once on the combined `VDS_list` of all sections. The `section_combined_params.direction_filter` key selects a single direction (1 or 2).

## Network (C1) Pipeline

When `spatial_scope='network'`, Stage 1 calls `run_network_c1()` instead of `run_single_vds()`. This computes VMT-harmonic-mean network speed and total travel distance demand across all C1 sections per 5-min interval. Results are written to the same `04_peak_period_result/` directory with prefix `c_daily_traffic_division_network_`.
