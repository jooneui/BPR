#!/usr/bin/env python3
"""
RDP_v Grid Search v2 — BPR R² over RDP_v recurrent analysis parameters.

Implements the plan in: 00 md plan/agents/RDP_grid_search_plan.md

Grid structure (decoupled start/end epsilon for peak_duration):

Case A: second_var_morning = end_hour, second_var_afternoon = start_hour
  (epsilon_start = epsilon_end, coupled)
  eps_m (morning start=end):  0.1, 0.2, …, 1.0  (10 values)
  eps_a (afternoon start=end): 0.1, 0.2, …, 1.5  (15 values)
  W (segment_min_weeks):      2, 3               (2 values)
  Total: 10 × 15 × 2 = 300

Case B: second_var_morning = end_hour, second_var_afternoon = peak_duration
  eps_m_start (morning start):       0.1, 0.2, …, 1.0  (10 values)
  eps_a_start (afternoon start):      0.1, 0.2, …, 1.5  (15 values)
  eps_m_end (morning end, controls end_hour): same as eps_m_start (coupled)
  eps_a_end (afternoon end, fixed variable): 0.1, 0.2, …, 1.5  (15 values)
  W (segment_min_weeks):              2, 3               (2 values)
  Total: 10 × 15 × 15 × 2 = 4,500

Case C: second_var_morning = peak_duration, second_var_afternoon = start_hour
  eps_m_start (morning start):       0.1, 0.2, …, 1.0  (10 values)
  eps_a_start (afternoon start, secondary): 0.1, 0.2, …, 1.5  (15 values)
  eps_m_end (morning end):             1.0, 1.5, 2.0        (3 values)
  eps_a_end (afternoon end, fixed):    same as eps_a_start (coupled)
  W: 2, 3 (2 values)
  Total: 10 × 15 × 3 × 2 = 900

Case D: second_var_morning = peak_duration, second_var_afternoon = peak_duration
  eps_m_start (morning start):       0.1, 0.2, …, 1.0  (10 values)
  eps_a_start (afternoon start, secondary): 0.1, 0.2, …, 1.5  (15 values)
  eps_m_end (morning end, controls duration): 1.0, 1.5, 2.0   (3 values)
  eps_a_end (afternoon end, fixed):   0.5, 1.0, 1.5, 2.0      (4 values)
  W: 2, 3 (2 values)
  Total: 10 × 15 × 3 × 4 × 2 = 3,600

Grand total: 300 + 4,500 + 900 + 3,600 = 9,300 combinations

Scoring: score = mean_r2 + 0.5 × min_r2  across 12 VDS×period cells
         n < 5 data points → R² = 0

Outputs:
  rdp_rdp_grid_search_results.csv  → summary per configuration
  rdp_rdp_grid_search_detail.csv   → R² per (setting × VDS × period)
"""

import copy
import io
import itertools
import sys
import os
import time
import warnings

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend — prevent plt.show() from blocking

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from traffic_utils.recurrent import run_recurrent_peak_pipeline, build_recurrent_output_tag
from traffic_utils.bpr_fitting import load_and_annotate, apply_filters, fit_bpr_ols_stats

warnings.filterwarnings('ignore')

# Suppress verbose print output from pipeline functions
class _SuppressPrint:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = io.StringIO()
        return self
    def __exit__(self, *args):
        sys.stdout = self._original_stdout

SUPPRESS_PIPELINE_OUTPUT = True  # Set False to debug

# ═══════════════════════════════════════════════════════════════════════════
# MASTER CONFIG (matches notebook)
# ═══════════════════════════════════════════════════════════════════════════

VDS_LIST = ['1203481', '1203506', '1205572', '1205583', '1212611', '1214006']

BASE_CONFIG = {
    'VDS_list': VDS_LIST,
    'spatial_scope': 'single',
    'temporal_scale': 'speedbasedpeak',
    'aggregate_timeframe': 5,
    'method': 'RDP_v',
    'congest_method': 'speed-solely',
    'lane_map': {
        '1212611': [1, 2, 3, 4, 5, 6], '1205572': [1, 2, 3, 4, 5, 6],
        '1205583': [1, 2, 3, 4, 5, 6], '1203506': [1, 2, 3, 4],
        '1214006': [1, 2, 3, 4], '1203481': [1, 2, 3, 4],
    },
    'W_minutes': 60,
    'free_tt_mode': 'fixed',
    'free_tt_method': 'offpeak_avg',
    'bpr_ff_speed_threshold': {
        '1203481': 68, '1203506': 67,
        '1214006': 68, '1205583': 70,
        '1205572': 70, '1212611': 69,
    },
    'period_include': {'speedbasedpeak': ['morning-peak', 'afternoon-peak']},
    # ── Fixed BPR flags (NOT varied in grid search) ──
    'drop_nonrecurrent_days': True,
    'drop_days_weird_peak_times': False,
    'drop_multiplecongestion_days': False,
    'segment_aggregation': True,
    'dayofweek_exclude': [],
    'month_exclude': [],
    'year_exclude': [],
    # ── Disable plots ──
    'dry_run': True,
    'plots': {'save_recurrent_checks': False},
    'speedbased_params': {
        'pelt_min_length': 5, 'min_off_len': 90, 'min_peak_len': 0,
        'speed_upper': 60, 'speed_gap_threshold': 15,
        'offpeak_ff_speed_threshold': {
            '1203506': 55, '1212611': 57, '1205572': 57,
            '1205583': 57, '1214006': 57, '1203481': 55,
        },
        'FD_phase': 'three_phases',
    },
}

XCOL = 'ln_totaldemandoverlanes'
YCOL = 'ln_t_tau'

# ═══════════════════════════════════════════════════════════════════════════
# Grid definition v2 (decoupled start/end epsilon)
# ═══════════════════════════════════════════════════════════════════════════

EPS_M_START  = list(np.round(np.arange(0.1, 1.1, 0.1), 1))   # 0.1–1.0  (10 values)
EPS_A_START  = list(np.round(np.arange(0.1, 1.6, 0.1), 1))   # 0.1–1.5  (15 values)
EPS_A_END    = list(np.round(np.arange(0.1, 1.6, 0.1), 1))   # 0.1–1.5  (15 values)  — for Case B afternoon end
EPS_M_END_PD = [1.0, 1.5, 2.0]                                   # morning end ε   (3 values)
EPS_A_END_PD = [0.5, 1.0, 1.5, 2.0]                              # afternoon end ε (4 values)
MIN_WEEKS    = [2, 3]

# Build the full grid
grid = []  # list of dicts with all epsilon and config params

# ── Case A: morning=end_hour, afternoon=start_hour (both coupled) ──
#   fixed_var: morning=start_hour, afternoon=end_hour
#   morning: second_var=end_hour, eps_m controls both (start=end)
#   afternoon: second_var=start_hour, eps_a controls both (start=end)
for eps_m in EPS_M_START:
    for eps_a in EPS_A_START:
        for W in MIN_WEEKS:
            grid.append({
                'eps_m_start': eps_m, 'eps_a_start': eps_a,
                'eps_m_end': eps_m,    'eps_a_end': eps_a,   # coupled
                'min_weeks': W,
                'second_var_morning': 'end_hour',
                'second_var_afternoon': 'start_hour',
            })

# ── Case B: morning=end_hour, afternoon=peak_duration ──
#   fixed_var: morning=start_hour, afternoon=end_hour
#   morning: second_var=end_hour, eps_m_end=eps_m_start (coupled for end_hour)
#   afternoon: second_var=peak_duration, eps_a controls start (secondary), eps_a_end controls end (fixed)
for eps_m_start in EPS_M_START:
    for eps_a_start in EPS_A_START:
        for eps_a_end in EPS_A_END:
            for W in MIN_WEEKS:
                grid.append({
                    'eps_m_start': eps_m_start, 'eps_a_start': eps_a_start,
                    'eps_m_end': eps_m_start,   # coupled for morning end_hour
                    'eps_a_end': eps_a_end,      # afternoon end (fixed variable)
                    'min_weeks': W,
                    'second_var_morning': 'end_hour',
                    'second_var_afternoon': 'peak_duration',
                })

# ── Case C: morning=peak_duration, afternoon=start_hour ──
#   fixed_var: morning=start_hour, afternoon=end_hour
#   morning: second_var=peak_duration, eps_m_start=start, eps_m_end=duration
#   afternoon: second_var=start_hour, eps_a coupled (start=end)
for eps_m_start in EPS_M_START:
    for eps_a_start in EPS_A_START:
        for eps_m_end in EPS_M_END_PD:
            for W in MIN_WEEKS:
                grid.append({
                    'eps_m_start': eps_m_start, 'eps_a_start': eps_a_start,
                    'eps_m_end': eps_m_end,     # morning duration
                    'eps_a_end': eps_a_start,   # coupled for afternoon start_hour
                    'min_weeks': W,
                    'second_var_morning': 'peak_duration',
                    'second_var_afternoon': 'start_hour',
                })

# ── Case D: morning=peak_duration, afternoon=peak_duration ──
#   fixed_var: morning=start_hour, afternoon=end_hour
#   morning: second_var=peak_duration, eps_m_end controls duration
#   afternoon: second_var=peak_duration, eps_a_start controls duration, eps_a_end controls fixed (end)
for eps_m_start in EPS_M_START:
    for eps_a_start in EPS_A_START:
        for eps_m_end in EPS_M_END_PD:
            for eps_a_end in EPS_A_END_PD:
                for W in MIN_WEEKS:
                    grid.append({
                        'eps_m_start': eps_m_start, 'eps_a_start': eps_a_start,
                        'eps_m_end': eps_m_end,     'eps_a_end': eps_a_end,
                        'min_weeks': W,
                        'second_var_morning': 'peak_duration',
                        'second_var_afternoon': 'peak_duration',
                    })

N_COMBOS = len(grid)
count_A = sum(1 for g in grid if g['second_var_morning'] == 'end_hour' and g['second_var_afternoon'] == 'start_hour')
count_B = sum(1 for g in grid if g['second_var_morning'] == 'end_hour' and g['second_var_afternoon'] == 'peak_duration')
count_C = sum(1 for g in grid if g['second_var_morning'] == 'peak_duration' and g['second_var_afternoon'] == 'start_hour')
count_D = sum(1 for g in grid if g['second_var_morning'] == 'peak_duration' and g['second_var_afternoon'] == 'peak_duration')
assert count_A == 10 * 15 * 2, f"Case A expected 300, got {count_A}"
assert count_B == 10 * 15 * 15 * 2, f"Case B expected 4500, got {count_B}"
assert count_C == 10 * 15 * 3 * 2, f"Case C expected 900, got {count_C}"
assert count_D == 10 * 15 * 3 * 4 * 2, f"Case D expected 3600, got {count_D}"
assert N_COMBOS == 9300, f"Expected 9300, got {N_COMBOS}"

print(f"RDP_v grid search v4 — decoupled start/end epsilon + asymmetric second_var")
print(f"  Case A (m=end_hour, a=start_hour, coupled ε):  {count_A} combos")
print(f"  Case B (m=end_hour, a=peak_duration):           {count_B} combos")
print(f"  Case C (m=peak_duration, a=start_hour):         {count_C} combos")
print(f"  Case D (m=peak_duration, a=peak_duration):     {count_D} combos")
print(f"  Total: {N_COMBOS} combos")
print(f"  ε_m_start: {EPS_M_START}")
print(f"  ε_a_start: {EPS_A_START}")
print(f"  ε_a_end (Case B afternoon fixed): {EPS_A_END}")
print(f"  ε_m_end (peak_duration, morning): {EPS_M_END_PD}")
print(f"  ε_a_end (peak_duration, afternoon): {EPS_A_END_PD}")
print(f"  min_weeks: {MIN_WEEKS}")
print()

# ═══════════════════════════════════════════════════════════════════════════
# Run grid search
# ═══════════════════════════════════════════════════════════════════════════

results = []
detail_rows = []
t0 = time.time()

for idx, params in enumerate(grid):
    eps_m_start = params['eps_m_start']
    eps_a_start = params['eps_a_start']
    eps_m_end  = params['eps_m_end']
    eps_a_end  = params['eps_a_end']
    min_weeks  = params['min_weeks']
    second_var_morning = params['second_var_morning']
    second_var_afternoon = params['second_var_afternoon']

    elapsed = time.time() - t0
    remaining = (elapsed / (idx + 1)) * (N_COMBOS - idx - 1) if idx > 0 else 0
    print(f"[{idx+1}/{N_COMBOS}] es_m={eps_m_start} es_a={eps_a_start} "
          f"ee_m={eps_m_end} ee_a={eps_a_end} W={min_weeks} "
          f"sv_m={second_var_morning} sv_a={second_var_afternoon}  "
          f"(elapsed {elapsed:.0f}s, ETA {remaining/60:.1f} min)", flush=True)

    # ── Build config for this grid point ──
    cfg = copy.deepcopy(BASE_CONFIG)
    cfg['recurrent_method'] = 'RDP_v'
    cfg['recurrent_method_params'] = {'RDP_v': {
        'epsilon_start_by_period':        {'morning-peak': eps_m_start, 'afternoon-peak': eps_a_start},
        'epsilon_end_by_period':          {'morning-peak': eps_m_end,   'afternoon-peak': eps_a_end},
        'segment_min_weeks_by_period':    {'morning-peak': min_weeks,   'afternoon-peak': min_weeks},
        'selector_by_period':             {'morning-peak': 'both',      'afternoon-peak': 'both'},
        'second_var_by_period':           {'morning-peak': second_var_morning, 'afternoon-peak': second_var_afternoon},
        'fixed_var_by_period':            {'morning-peak': 'start_hour', 'afternoon-peak': 'end_hour'},
    }}
    cfg['segment_min_weeks_by_period']  = {'morning-peak': min_weeks, 'afternoon-peak': min_weeks}
    cfg['drop_nonrecurrent_days'] = True
    cfg['segment_aggregation'] = True
    cfg['drop_days_weird_peak_times'] = False
    cfg['drop_multiplecongestion_days'] = False

    # ── Step 1: Recurrent analysis (Stage 2) ──
    try:
        if SUPPRESS_PIPELINE_OUTPUT:
            with _SuppressPrint():
                result = run_recurrent_peak_pipeline(cfg)
        else:
            result = run_recurrent_peak_pipeline(cfg)
    except Exception as e:
        print(f"  RDP_v pipeline FAILED: {e}")
        continue

    # Determine the actual output tag
    actual_tag = build_recurrent_output_tag(cfg)

    # ── Step 2: Run BPR fitting for each VDS × period (Stage 3) ──
    r2_values = []
    for vds_id in VDS_LIST:
        bpr_cfg = copy.deepcopy(cfg)
        bpr_cfg['VDS_num'] = vds_id
        bpr_cfg['lane_num'] = bpr_cfg['lane_map'].get(vds_id, [])
        bpr_cfg['recurrent_output_tag'] = actual_tag
        bpr_cfg['drop_nonrecurrent_days'] = True

        try:
            if SUPPRESS_PIPELINE_OUTPUT:
                with _SuppressPrint():
                    df_all = load_and_annotate(bpr_cfg)
                    df_use = apply_filters(df_all, bpr_cfg)
                    if bpr_cfg.get('segment_aggregation'):
                        from traffic_utils.bpr_fitting import aggregate_segment_level_bpr
                        df_use = aggregate_segment_level_bpr(df_use, bpr_cfg)
            else:
                df_all = load_and_annotate(bpr_cfg)
                df_use = apply_filters(df_all, bpr_cfg)
                if bpr_cfg.get('segment_aggregation'):
                    from traffic_utils.bpr_fitting import aggregate_segment_level_bpr
                    df_use = aggregate_segment_level_bpr(df_use, bpr_cfg)
        except Exception as e:
            print(f"  VDS {vds_id}: load/filter error: {e}, R² → 0 for both periods")
            for period in ['morning-peak', 'afternoon-peak']:
                r2_values.append(0.0)
                detail_rows.append({
                    'eps_m_start': eps_m_start, 'eps_a_start': eps_a_start,
                    'eps_m_end': eps_m_end, 'eps_a_end': eps_a_end,
                    'min_weeks': min_weeks, 'second_var_morning': second_var_morning, 'second_var_afternoon': second_var_afternoon,
                    'output_tag': actual_tag,
                    'vds_id': vds_id, 'period': period,
                    'r2': 0.0, 'n_points': 0,
                })
            bpr_skip = True
        else:
            bpr_skip = False

        # Check that 'period' column exists (may be lost in edge cases)
        if not bpr_skip and (df_use is None or df_use.empty or 'period' not in df_use.columns):
            print(f"  VDS {vds_id}: no period column after aggregation, R² → 0 for both periods")
            for period in ['morning-peak', 'afternoon-peak']:
                r2_values.append(0.0)
                detail_rows.append({
                    'eps_m_start': eps_m_start, 'eps_a_start': eps_a_start,
                    'eps_m_end': eps_m_end, 'eps_a_end': eps_a_end,
                    'min_weeks': min_weeks, 'second_var_morning': second_var_morning, 'second_var_afternoon': second_var_afternoon,
                    'output_tag': actual_tag,
                    'vds_id': vds_id, 'period': period,
                    'r2': 0.0, 'n_points': 0,
                })
            continue

        if bpr_skip:
            continue

        for period in ['morning-peak', 'afternoon-peak']:
            try:
                df_p = df_use[df_use['period'] == period].copy()
                df_p = df_p.replace([np.inf, -np.inf], np.nan).dropna(subset=[XCOL, YCOL])
                n_pts = len(df_p)

                if n_pts < 5:
                    # Too few points → R² = 0 (penalize sparse configurations)
                    print(f"  VDS {vds_id} {period}: only {n_pts} points (< 5), R² set to 0")
                    r2_values.append(0.0)
                    detail_rows.append({
                        'eps_m_start': eps_m_start, 'eps_a_start': eps_a_start,
                        'eps_m_end': eps_m_end, 'eps_a_end': eps_a_end,
                        'min_weeks': min_weeks, 'second_var_morning': second_var_morning, 'second_var_afternoon': second_var_afternoon,
                        'output_tag': actual_tag,
                        'vds_id': vds_id, 'period': period,
                        'r2': 0.0, 'n_points': n_pts,
                    })
                else:
                    if SUPPRESS_PIPELINE_OUTPUT:
                        with _SuppressPrint():
                            fit = fit_bpr_ols_stats(df_p, xcol=XCOL, ycol=YCOL)
                    else:
                        fit = fit_bpr_ols_stats(df_p, xcol=XCOL, ycol=YCOL)
                    if fit:
                        r2 = fit['r2']
                        n = fit['n']
                    else:
                        r2 = 0.0
                        n = n_pts
                    r2_values.append(r2)
                    detail_rows.append({
                        'eps_m_start': eps_m_start, 'eps_a_start': eps_a_start,
                        'eps_m_end': eps_m_end, 'eps_a_end': eps_a_end,
                        'min_weeks': min_weeks, 'second_var_morning': second_var_morning, 'second_var_afternoon': second_var_afternoon,
                        'output_tag': actual_tag,
                        'vds_id': vds_id, 'period': period,
                        'r2': r2, 'n_points': n,
                    })
            except Exception as e:
                print(f"  VDS {vds_id} {period}: BPR fit error: {e}")
                # Record as R² = 0 for errors too
                r2_values.append(0.0)
                detail_rows.append({
                    'eps_m_start': eps_m_start, 'eps_a_start': eps_a_start,
                    'eps_m_end': eps_m_end, 'eps_a_end': eps_a_end,
                    'min_weeks': min_weeks, 'second_var_morning': second_var_morning, 'second_var_afternoon': second_var_afternoon,
                    'output_tag': actual_tag,
                    'vds_id': vds_id, 'period': period,
                    'r2': 0.0, 'n_points': 0,
                })
                continue

    # ── Incremental save every 100 iterations ──
    if (idx + 1) % 100 == 0 and len(results) > 0:
        pd.DataFrame(results).to_csv('rdp_rdp_grid_search_results_partial.csv', index=False)
        pd.DataFrame(detail_rows).to_csv('rdp_rdp_grid_search_detail_partial.csv', index=False)
        print(f"  [checkpoint] Saved {len(results)} results, {len(detail_rows)} detail rows", flush=True)

    # ── Aggregate metrics for this grid point ──
    # Always have 12 cells (6 VDS × 2 periods); R²=0 for n<5 or errors
    r2_arr = np.array(r2_values) if r2_values else np.array([np.nan])
    n_total = len(r2_values)  # should be 12
    n_valid = int(np.sum(r2_arr > 0))  # count of fits with n>=5
    if len(r2_arr) > 0 and not np.all(np.isnan(r2_arr.astype(float))):
        mean_r2 = float(np.mean(r2_arr))
        min_r2  = float(np.min(r2_arr))
        max_r2  = float(np.max(r2_arr))
        std_r2  = float(np.std(r2_arr))
        score   = mean_r2 + 0.5 * min_r2
    else:
        mean_r2 = min_r2 = max_r2 = std_r2 = score = np.nan

    results.append({
        'eps_m_start': eps_m_start, 'eps_a_start': eps_a_start,
        'eps_m_end': eps_m_end,     'eps_a_end': eps_a_end,
        'min_weeks': min_weeks, 'second_var_morning': second_var_morning, 'second_var_afternoon': second_var_afternoon,
        'output_tag': actual_tag,
        'mean_r2': mean_r2, 'min_r2': min_r2,
        'max_r2': max_r2, 'std_r2': std_r2,
        'score': score,
        'n_r2_values': n_total,
        'n_valid_fits': n_valid,
    })

    print(f"  mean_r2={mean_r2:.4f}, min_r2={min_r2:.4f}, max_r2={max_r2:.4f}, "
          f"score={score:.4f}, n_total={n_total}, n_valid={n_valid}", flush=True)

# ═══════════════════════════════════════════════════════════════════════════
# Save results
# ═══════════════════════════════════════════════════════════════════════════

df_results = pd.DataFrame(results)
df_detail = pd.DataFrame(detail_rows)

# Round numeric columns
for c in ['mean_r2', 'min_r2', 'max_r2', 'std_r2', 'score']:
    df_results[c] = df_results[c].round(4)
df_detail['r2'] = df_detail['r2'].round(4)

# Add VDS labels
vds_labels = {
    '1203481': 'SB-WB', '1203506': 'SB-EB', '1214006': 'I-5 SB-1',
    '1205583': 'I-5 SB-2', '1205572': 'I-5 SB-3', '1212611': 'I-5 SB-4'
}
df_detail['vds_id'] = df_detail['vds_id'].astype(str)
df_detail['vds_label'] = df_detail['vds_id'].map(vds_labels)

# Add meets_targets flag
df_results['meets_targets'] = (df_results['mean_r2'] >= 0.5) & (df_results['min_r2'] >= 0.3)

# Case column for easier filtering
# Derive case from the two second_var columns
def derive_case(row):
    m = row['second_var_morning']
    a = row['second_var_afternoon']
    if m == 'end_hour' and a == 'start_hour':
        return 'A_end_start'
    elif m == 'end_hour' and a == 'peak_duration':
        return 'B_end_dur'
    elif m == 'peak_duration' and a == 'start_hour':
        return 'C_dur_start'
    elif m == 'peak_duration' and a == 'peak_duration':
        return 'D_dur_dur'
    else:
        return 'unknown'

df_results['case'] = df_results.apply(derive_case, axis=1)
df_detail['case'] = df_detail.apply(derive_case, axis=1)

results_file = 'rdp_rdp_grid_search_results.csv'
detail_file = 'rdp_rdp_grid_search_detail.csv'

df_results.to_csv(results_file, index=False, float_format='%.4f')
df_detail.to_csv(detail_file, index=False, float_format='%.4f')

elapsed_total = time.time() - t0
print(f"\nResults saved to {results_file} ({len(df_results)} rows)")
print(f"Details saved to {detail_file} ({len(df_detail)} rows)")
print(f"Total runtime: {elapsed_total/60:.1f} minutes")

# ═══════════════════════════════════════════════════════════════════════════
# Analysis: best configuration and summary statistics
# ═══════════════════════════════════════════════════════════════════════════

valid = df_results.dropna(subset=['score'])
if len(valid) > 0:
    best = valid.loc[valid['score'].idxmax()]

    print("\n" + "=" * 70)
    print("BEST CONFIGURATION (by score = mean_r2 + 0.5 × min_r2)")
    print("=" * 70)
    print(f"  eps_m_start  = {best['eps_m_start']}")
    print(f"  eps_a_start  = {best['eps_a_start']}")
    print(f"  eps_m_end    = {best['eps_m_end']}")
    print(f"  eps_a_end    = {best['eps_a_end']}")
    print(f"  min_weeks    = {best['min_weeks']}")
    print(f"  second_var_m = {best['second_var_morning']}")
    print(f"  second_var_a = {best['second_var_afternoon']}")
    print(f"  mean_r2      = {best['mean_r2']:.4f}")
    print(f"  min_r2       = {best['min_r2']:.4f}")
    print(f"  max_r2       = {best['max_r2']:.4f}")
    print(f"  score        = {best['score']:.4f}")
    print(f"  n_valid_fits = {int(best['n_valid_fits'])}/12")

    # Best per case
    for case_name, case_label in [('A_end_start', 'Case A (m=end_hour, a=start_hour)'),
                                   ('B_end_dur', 'Case B (m=end_hour, a=peak_duration)'),
                                   ('C_dur_start', 'Case C (m=peak_duration, a=start_hour)'),
                                   ('D_dur_dur', 'Case D (m=peak_duration, a=peak_duration)')]:
        sub = valid[valid['case'] == case_name]
        if len(sub) > 0:
            best_sub = sub.loc[sub['score'].idxmax()]
            print(f"\n  Best for {case_label}:")
            print(f"    es_m={best_sub['eps_m_start']}, es_a={best_sub['eps_a_start']}, "
                  f"ee_m={best_sub['eps_m_end']}, ee_a={best_sub['eps_a_end']}, "
                  f"W={best_sub['min_weeks']}, sv_m={best_sub['second_var_morning']}, sv_a={best_sub['second_var_afternoon']}")
            print(f"    score={best_sub['score']:.4f}, mean_r2={best_sub['mean_r2']:.4f}, "
                  f"min_r2={best_sub['min_r2']:.4f}, n_valid={int(best_sub['n_valid_fits'])}")

    # Top 5 overall
    print("\n  Top 5 overall:")
    top5 = valid.nlargest(5, 'score')
    for i, (_, row) in enumerate(top5.iterrows()):
        print(f"    {i+1}. es_m={row['eps_m_start']}, es_a={row['eps_a_start']}, "
              f"ee={row['eps_m_end']}/{row['eps_a_end']}, W={row['min_weeks']}, "
              f"sv_m={row['second_var_morning']}, sv_a={row['second_var_afternoon']}, score={row['score']:.4f}, "
              f"mean_r2={row['mean_r2']:.4f}, min_r2={row['min_r2']:.4f}, "
              f"n_valid={int(row['n_valid_fits'])}")

    # Settings meeting targets
    meet = valid[(valid['mean_r2'] >= 0.5) & (valid['min_r2'] >= 0.3)]
    print(f"\nSettings meeting targets (mean_r2>=0.5, min_r2>=0.3): {len(meet)} / {len(valid)}")

    # Summary by case
    print("\n" + "=" * 70)
    print("SUMMARY BY CASE")
    print("=" * 70)
    for case_name, case_label in [('A_coupled', 'Case A (end_hour)'), ('B_decoupled', 'Case B (peak_duration)')]:
        sub = valid[valid['case'] == case_name]
        if len(sub) > 0:
            print(f"\n  {case_label}:")
            print(f"    N configs: {len(sub)}")
            print(f"    Best score: {sub['score'].max():.4f}")
            print(f"    Best mean_r2: {sub['mean_r2'].max():.4f}")
            print(f"    Mean score: {sub['score'].mean():.4f}")

    # Main effects
    print("\n" + "=" * 70)
    print("MAIN EFFECTS (averaged over all other variables)")
    print("=" * 70)
    for col, label in [('eps_m_start', 'eps_m_start (morning start ε)'),
                        ('eps_a_start', 'eps_a_start (afternoon start ε)'),
                        ('eps_m_end', 'eps_m_end (morning end ε — peak_duration only)'),
                        ('eps_a_end', 'eps_a_end (afternoon end ε — peak_duration only)'),
                        ('min_weeks', 'min_weeks'),
                        ('second_var_morning', 'second_var_morning'),
                        ('second_var_afternoon', 'second_var_afternoon')]:
        grp = valid.groupby(col)['score'].agg(['mean', 'count']).reset_index()
        print(f"\n  By {label}:")
        for _, row in grp.iterrows():
            print(f"    {row[col]:<20} mean_score={row['mean']:.4f}  n={int(row['count'])}")

elapsed_total = time.time() - t0
print(f"\nTotal runtime: {elapsed_total/60:.1f} minutes")