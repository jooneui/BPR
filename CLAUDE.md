# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a traffic engineering research codebase for **BPR (Bureau of Public Roads) function calibration** from freeway detector data. The workflow identifies peak congestion periods, classifies recurrent vs. non-recurrent congestion, and fits log-linearized BPR travel-time functions.

Primary interface: `2nd_phase_BRP_function.ipynb`. All logic lives in `traffic_utils/`.

## Running the Pipeline

The notebook is the main entry point. Reload modules after any edit to `traffic_utils/`:

```python
import importlib, sys
to_remove = [k for k in sys.modules if k.startswith('traffic_utils')]
for k in to_remove:
    del sys.modules[k]
import traffic_utils
```

Run the full 3-stage pipeline:
```python
run_full_pipeline(MASTER_CONFIG, stages=[1, 2, 3])
```

Run individual stages (e.g., just recurrent + BPR):
```python
run_full_pipeline(MASTER_CONFIG, stages=[2, 3])
```

There are no build/lint/test commands — this is a research notebook project with no CI setup.

## Three-Stage Pipeline Architecture

**Stage 1 — Daily Peak Detection** (`pipeline.py`)
- Reads raw PeMS 5-min detector files from `11 Rawdata/5min/<VDS_num>/`
- Aggregates lane-level data into speed/flow/occupancy profiles
- Detects congested periods using the method specified in `speedbased_params.method`
- Saves per-day results to `04_peak_period_result/c_daily_traffic_division_*.csv`

**Stage 2 — Recurrent Peak Classification** (`recurrent.py`)
- Reads Stage 1 CSVs, groups by (VDS, day-of-week, period)
- Applies the `recurrent_method` algorithm to label each week as recurrent or non-recurrent
- Saves labeled tables to `05_recurrent_peak_result/`

**Stage 3 — BPR Calibration** (`bpr_fitting.py`, `plotting.py`)
- Fits log-linearized BPR: `ln(z(Q)/ζ - 1)` vs `ln(Q)` using WLS
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
| `dry_run` | Set `True` to skip all file writes |
| `plots` | Dict of boolean flags per output type |

`speedbased_params.offpeak_ff_speed_threshold` maps VDS ID → free-flow speed (mph). This is the canonical free-flow speed used by both Stage 1 detection and Stage 3 BPR fitting.

After editing `MASTER_CONFIG`, run `compute_bpr_ff_speed_thresholds(MASTER_CONFIG)` once to auto-populate `bpr_ff_speed_threshold` from 0–3am and 22–24h off-peak data.

## traffic_utils Module Map

| Module | Responsibility |
|--------|----------------|
| `pipeline.py` | `run_full_pipeline`, `run_single_vds`, `run_network_c1` — orchestrates all stages |
| `segmentation.py` | `rdp_v` (Ramer–Douglas–Peucker with vertical error), `detect_speed_peaks`, PELT/RDP wrappers |
| `recurrent.py` | `classify_facet_rdpv`, `classify_facet_fixed_band`, `run_recurrent_peak_pipeline` |
| `bpr_fitting.py` | `build_file_path`, BPR linear transforms registry, WLS fitting |
| `data_io.py` | Raw data loading, `aggregate_rawdata_5min`, section-combined loader |
| `metrics.py` | `process_daily_traffic`, `compute_metrics` — demand/travel-time aggregation |
| `plotting.py` | All matplotlib output functions |
| `_helpers.py` | Multi-VDS combination, speed profile plots |
| `classification.py` | `label_solely_speed`, `label_divisions_occupancy`, etc. — congestion labeling strategies |

## Peak Detection Methods

The `speedbased_params.method` key selects the intra-day segmentation algorithm:

- **`RDP_v`** (default): Applies Ramer–Douglas–Peucker with **vertical** error on the cumulative speed curve. The custom `rdp_v()` in `segmentation.py` replaces the `rdp` library's Euclidean variant. Epsilon controls the sensitivity (larger = fewer breakpoints).
- **`pelt`**: PELT change-point detection on raw speed via the `ruptures` library.
- **`RDP`**: Standard RDP using Euclidean distance (legacy).

## Recurrent Classification Methods

The `recurrent_method` key controls Stage 2:

- **`RDP_v`**: Applies `rdp_v()` to the cumulative start-hour and end-hour series across calendar weeks. `fixed_var_by_period` determines whether start (morning) or end (afternoon) is the anchor variable. Breakpoints split the time series into stable segments; segments shorter than `segment_min_weeks` are excluded as non-recurrent.
- **`simpleband`**: Histogram-based fixed-bandwidth window around the modal start/end hour.
- **`shortest_interval`**: Finds the narrowest interval covering a given coverage fraction of peak times.
- **`PELT`**: Change-point detection on the week-by-week peak time series.

## Output File Naming

Stage 1 CSV: `04_peak_period_result/c_daily_traffic_division_{spatial_scope}_{VDS_num}_{temporal_scale}_{aggregate_timeframe}_{method}_{congest_method}.csv`

Stage 2 labeled CSV: `05_recurrent_peak_result/recurrent_days_labeled_{output_tag}.csv`

The `output_tag` is auto-generated by `build_recurrent_output_tag()` encoding all method parameters into a readable string.

## Data Directory Layout

```
11 Rawdata/5min/<VDS_num>/    ← raw PeMS Excel files (not in git)
04_peak_period_result/        ← Stage 1 outputs
05_recurrent_peak_result/     ← Stage 2 outputs
02 fig/                       ← all plot outputs
01_1_BPR_network/C1data/      ← C1 network data (Detector.csv, SectionLength.csv)
```

Raw data and outputs are excluded from git (`.gitignore` whitelists only notebooks and `.py` scripts).

## section_combined Data Format

When `data_format='section_combined'`, the pipeline reads a single `Detector.csv` (C1 format) and auto-expands each base VDS into per-section sub-configs via `_make_section_config()`. Stage 3 runs once on the combined `VDS_list` of all sections. The `section_combined_params.direction_filter` key selects a single direction (1 or 2).
