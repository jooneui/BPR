from pathlib import Path
import copy
import numpy as np
import os
import pandas as pd
import subprocess
import time

# --- cross-module imports (extracted from notebook globals) ---
from .data_io import (
    aggregate_rawdata_5min,
    c_daily_traffic_save,
    get_unique_sections,
    load_raw,
    load_section_combined,
    set_peak_period_save,
    skip_if_missing,
    _ensure_local,
)
from .plotting_stage1 import (
    speedprofile_plot,
    plot_duration_demand_all_in_one_png_3x3,
    plot_totaldemand_histogram_all_in_one_png_3x3,
)
from .plotting_stage2 import plot_fd_all_in_one_png
from .metrics import process_daily_traffic
from .plotting_stage3 import plot_bpr_all_in_one_png_3x3
from .recurrent import build_recurrent_output_tag, run_recurrent_peak_pipeline
from .segmentation import detect_speed_peaks



# --- small utilities ---
def _should_save(cfg: dict, flag_name: str) -> bool:
    """Return True if cfg permits saving/plotting for flag_name and dry_run is off."""
    if cfg.get('dry_run', False):
        return False
    return cfg.get('plots', {}).get(flag_name, False)

def cleaned_file_list(folder: Path) -> list[str]:
    files = sorted(p.name for p in folder.iterdir() if p.is_file())
    return [f for f in files if f != '.DS_Store']

def apply_peak_detection(df, date, cfg):
    """Set 'division'/'segment' per cfg['temporal_scale']; return (df, peaks_or_None)."""
    if cfg['temporal_scale'] == 'speedbasedpeak':
        df, peaks = detect_speed_peaks(df, date, cfg)
        # return df, peaks
    # df['division'] = 0
    # df['segment']  = 0
    return df, peaks

def append_daily_results(df, cfg, date, raw, results_div, results_seg):    
    results_div = process_daily_traffic(df, cfg, date, raw, "division", results_div)
    results_seg = process_daily_traffic(df, cfg, date, raw, "segment", results_seg)
    return results_div, results_seg

# --- core runners ---
def run_single_vds(cfg, base_path: Path, vds_num: str, timeframe_min: int, c_lane_num: dict = None):
    c_lane_num = c_lane_num or {}
    lane_num = c_lane_num.get(vds_num, cfg.get('lane_num', []))
    if cfg.get('data_format') == 'section_combined':
        lane_num = [1]  # dummy; not used for section-level data
    elif not lane_num:
        raise KeyError(
            f"lane_num missing for VDS '{vds_num}'. "
            f"Add it to MASTER_CONFIG['lane_map'] or cfg['lane_num']."
        )
    cfg = dict(cfg, VDS_num=vds_num, lane_num=lane_num)

    data_dir = base_path / cfg.get('dir', '5min') / vds_num
    file_list = cleaned_file_list(data_dir) if cfg.get('data_format') != 'section_combined' else []

    results_div = {"date": [],"division": [],"period": [],"dayofweek": [],"duration": [],"start": [],"end": [],"total_demand": [],"avg_flow": [],"traveltime": [],"avg_speed":[],"density":[],"avg_occ":[]}
    results_seg = {"date": [],"segment": [],"period": [],"dayofweek": [],"duration": [],"start": [],"end": [],"total_demand": [],"avg_flow": [],"traveltime": [],"avg_speed":[],"density":[],"avg_occ":[]}
    set_peak_period = pd.DataFrame(columns=["date", "peak_list"])

    # ── section_combined branch ────────────────────────────────
    if cfg.get('data_format') == 'section_combined':
        dates, _ = _common_dates_and_files(cfg)
        for date in dates:
            print(f"[section_combined] {vds_num} — {date}")
            traffic, _ = _build_traffic_for_vds(date, None, cfg, vds_num, timeframe_min, None)
            if traffic is None:
                continue
            df_date = pd.Timestamp('20' + date) if len(str(date)) == 6 else pd.Timestamp(date)
            traffic['time'] = df_date + pd.to_timedelta(traffic['time_slot'], unit='m')
            
            # DEBUG: show threshold vs. data so user can verify it's appropriate
            if cfg.get('temporal_scale') == 'speedbasedpeak':
                sp = cfg.get('speedbased_params', {})
                thre_map = sp.get('offpeak_ff_speed_threshold', {})
                thre = thre_map.get(vds_num, thre_map.get(vds_num.split('_')[0] if '_' in vds_num else vds_num, 'N/A'))
                print(f"[threshold check] VDS={vds_num}  date={date}  "
                      f"threshold={thre}  mean_speed={traffic['speed'].mean():.1f}")

            if cfg['temporal_scale'] == 'entireday':
                traffic[['segment','division']] = 0
                peaks = []
            elif cfg['temporal_scale'] == 'speedbasedpeak':
                traffic, peaks = apply_peak_detection(traffic, date, cfg)
            elif cfg['temporal_scale'] == 'hour':
                step = int(cfg['aggregate_timeframe'])
                rows_per_hour = int(60//step)
                idx = np.arange(len(traffic))
                hour_id = (idx // rows_per_hour) + 1
                traffic['segment'] = hour_id
                traffic['division'] = hour_id
                peaks = []

            if peaks is not None:
                set_peak_period = pd.concat(
                    [set_peak_period, pd.DataFrame([{'date': date, 'peak_list': peaks}])],
                    ignore_index=True
                )

            # raw is not available for section_combined; pass empty placeholder
            raw = traffic.copy()
            results_div, results_seg = append_daily_results(traffic, cfg, date, raw, results_div, results_seg)

        return results_div, results_seg, set_peak_period

    # ── legacy per-day file branch ─────────────────────────────
    for fname in file_list:
        print(fname)
        raw, date = load_raw(fname, cfg)
        if skip_if_missing(raw, cfg):
            continue
        traffic, _date = aggregate_rawdata_5min(raw, timeframe_min, date, lane_num, vds_num)

        if cfg['temporal_scale'] == 'entireday':
            traffic[['segment','division']]=0
            peaks = []
            
        elif cfg['temporal_scale'] == 'speedbasedpeak':
            traffic, peaks = apply_peak_detection(traffic, date, cfg)

        elif (cfg['temporal_scale'] == 'hour'):
            step = int(cfg['aggregate_timeframe'])
            rows_per_hour = int(60//step)

            idx = np.arange(len(traffic))

            hour_id = (idx // rows_per_hour) + 1

            traffic['segment']=hour_id
            traffic['division']=hour_id
            peaks = []

        # traffic.to_csv(f"./traffic_{vds_num}_{fname}.csv")
        if peaks is not None:
            set_peak_period = pd.concat(
                [set_peak_period, pd.DataFrame([{'date': date, 'peak_list': peaks}])],ignore_index=True)

        results_div, results_seg = append_daily_results(traffic, cfg, date, raw, results_div, results_seg)

    return results_div, results_seg, set_peak_period

def run_multi_vds(cfg, timeframe_min: int, c_lane_num: dict):
    dates_common, date_to_files = _common_dates_and_files(cfg)
    if not dates_common:
        print("No common dates across VDS_list; nothing to process.")
        return None, None, pd.DataFrame(columns=["date", "peak_list"])

    multi_label = "MULTI_" + "+".join(cfg['VDS_list'])
    temp_cfg = dict(cfg, VDS_num=multi_label)

    results_div = {"date": [],"division": [],"period": [],"dayofweek": [],"duration": [],"start": [],"end": [],"total_demand": [],"avg_flow": [],"traveltime": [],"avg_speed":[],"density":[],"avg_occ":[]}
    results_seg = {"date": [],"segment": [],"period": [],"dayofweek": [],"duration": [],"start": [],"end": [],"total_demand": [],"avg_flow": [],"traveltime": [],"avg_speed":[],"density":[],"avg_occ":[]}
    set_peak_period = pd.DataFrame(columns=["date", "peak_list"])

    for date in dates_common:
        coverage_lengths = []
        per_vds = []

        for vds in cfg['VDS_list']:
            cfg_vds  = _make_vds_config(cfg, vds, c_lane_num)
            base_dir = Path(cfg_vds.get('path', cfg_vds.get('file_path', '.'))) / '11 Rawdata' / cfg_vds.get('dir', '5min') / vds
            fname    = date_to_files[date][vds]
            traffic, cov_len = _build_traffic_for_vds(date, fname, cfg_vds, vds, timeframe_min, c_lane_num)
            if traffic is None:
                per_vds = []
                break
            per_vds.append(traffic)
            coverage_lengths.append(cov_len)

        if not per_vds:
            continue

        if _should_save(cfg, 'plot_peak_detection'):
            speedprofile_plot(per_vds, timeframe_min, cfg, date)

        traffic_combo = _combine_vds_traffic(per_vds, cfg['aggregate_timeframe'], coverage_lengths)
        if traffic_combo is None:
            continue

        # Detect peaks and summarize
        traffic_combo, peaks = apply_peak_detection(traffic_combo, date, temp_cfg)
        traffic_combo.to_csv(f"./traffic_combo_{fname}.csv")
        if peaks is not None:
            set_peak_period = pd.concat(
                [set_peak_period, pd.DataFrame([{'date': date, 'peak_list': peaks}])],
                ignore_index=True
            )

        results_div, results_seg = append_daily_results(traffic_combo, cfg, date, raw=None, results_div=results_div, results_seg=results_seg)

    return results_div, results_seg, set_peak_period

# =====================================================================
# NETWORK-LEVEL C1 PIPELINE  (spatial_scope = 'network')
# Functions mirror run_single_vds but aggregate across all sections.
# Run run_network_c1(CONFIG_RC) to generate daily-traffic CSVs, then
# proceed with run_recurrent_peak_pipeline as usual.
# =====================================================================

def load_network_c1(cfg):
    """Load C1 Detector.csv + SectionLength.csv, merge, and clean."""
    from pathlib import Path
    data_path = Path(cfg.get('network_data_path', './01_1_BPR_network/C1data'))
    det = pd.read_csv(data_path / 'Detector.csv', header=None,
                      names=['route_id','direction','section_id','date',
                             'interval','volume','speed','occupancy','n_vehicles'])
    sec = pd.read_csv(data_path / 'SectionLength.csv', header=None,
                      names=['route_id','direction','section_id','unknown','length_m'])
    sec['length_km'] = sec['length_m'] / 1000.0
    det = det.merge(sec[['direction','section_id','length_km']],
                    on=['direction','section_id'], how='left')
    det['date'] = pd.to_datetime(det['date'].astype(str), format='%Y%m%d')
    det['time_slot'] = (det['interval'] - 1) * 5          # minutes from midnight
    det = det[(det['speed'] > 0) & (det['volume'] >= 0)].dropna(
          subset=['speed','volume','length_km'])
    return det


def build_network_traffic_day(det_day, date):
    """
    Network-level traffic profile for one (direction, date).

    Per 5-min interval j across sections s:
      v_net(j) = Σ[q_s·ℓ_s] / Σ[q_s·ℓ_s/v_s]   [km/h, VMT-harmonic mean speed]
      Q_net(j) = Σ[q_s·ℓ_s]                       [veh·km/5min, TTD rate]
      k_net(j) = Q_net / v_net

    Column names match the traffic DataFrame expected by the existing pipeline:
      time_slot, time, speed, flow, occ, density
    """
    records = []
    for ts, g in det_day.groupby('time_slot'):
        vmt = (g['volume'] * g['length_km']).sum()
        vtt = (g['volume'] * g['length_km'] / g['speed']).sum()
        if vmt > 0 and vtt > 0:
            v_net = vmt / vtt          # network space-mean speed [km/h]
            k_net = vmt / v_net
        else:
            v_net = k_net = np.nan
        records.append({'time_slot': ts,
                        'speed':   v_net,
                        'flow':    vmt if not np.isnan(v_net) else np.nan,
                        'occ':     np.nan,
                        'density': k_net})
    df = pd.DataFrame(records).sort_values('time_slot').reset_index(drop=True)
    df['time'] = pd.Timestamp(date) + pd.to_timedelta(df['time_slot'], unit='m')
    return df


def _wrap_network_cfg_for_detection(cfg):
    """Bridge flat CONFIG_RC keys → nested speedbased_params for detect_speed_peaks.
    If cfg already has speedbased_params (config/cell-134 style), return as-is."""
    if 'speedbased_params' in cfg:
        return cfg
    return {
        **cfg,
        'speedbased_params': {
            'method':          cfg.get('method', 'RDP_v'),
            'congest_method':  cfg.get('congest_method', 'speed-solely'),
            'pelt_min_length': cfg.get('pelt_min_length', 5),
            'min_off_len':     cfg.get('min_off_len', 90),
            'min_peak_len':    cfg.get('min_peak_len', 0),
            'speed_upper':     cfg.get('speed_upper', 60),
            'offpeak_ff_speed_threshold': cfg.get('offpeak_ff_speed_threshold', {}),
            'speed_gap_threshold':       cfg.get('speed_gap_threshold', 15),
            'occ_threshold':             cfg.get('occ_threshold', {}),
            'FD_phase':                  cfg.get('FD_phase', 'three_phases'),
        },
    }


def _save_network_daily_results(cfg, results, criterion):
    """Save network daily-traffic CSV; path matches build_file_path('network')."""
    c_daily = pd.DataFrame({
        'date':        results['date'],
        'dayofweek':   results['dayofweek'],
        criterion:     results[criterion],
        'period':      results['period'],
        'duration':    results['duration'],
        'start_time':  results['start'],
        'end_time':    results['end'],
        'totaldemand': results['total_demand'],   # TTD [veh·km] over congested period
        'avg_flow':    results['avg_flow'],        # avg TTD rate [veh·km/5min]
        'traveltimes': results['traveltime'],      # [min/km] = 60 / v̄_net
        'avg_speed':   results['avg_speed'],       # [km/h]
        'avg_density': results['density'],
        'avg_occ':     results['avg_occ'],
    })
    # Support both config styles: flat (CONFIG_RC) and nested (config/cell-134)
    _sp = cfg.get('speedbased_params', {})
    _method  = cfg.get('method',        _sp.get('method',        'RDP_v'))
    _congest = cfg.get('congest_method', _sp.get('congest_method','speed-solely'))
    path = (f"./04_peak_period_result/c_daily_traffic_{criterion}_network_{cfg['VDS_num']}"
            f"_{cfg['temporal_scale']}_{cfg['aggregate_timeframe']}"
            f"_{_method}_{_congest}.csv")
    c_daily.to_csv(path, index=False)
    print(f"  -> Saved: {path}")


def run_network_c1(cfg):
    """
    Full network-level BPR pipeline for C1 (equivalent to run_single_vds).

    Steps:
      1. load_network_c1        -> per-section detector records
      2. build_network_traffic_day -> (v_net, Q_net) per 5-min interval
      3. apply_peak_detection   -> division / segment labels (same RDP_v logic)
      4. process_daily_traffic  -> demand–traveltime metrics per division
      5. _save_network_daily_results -> CSV compatible with build_file_path

    cfg: CONFIG_RC or CONFIG_BPR with spatial_scope='network'.
    """
    det_all   = load_network_c1(cfg)
    directions = cfg.get('network_directions', {1: 'C1_D1', 2: 'C1_D2'})
    Day_list   = cfg.get('Day_list', ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])
    empty_res  = lambda crit: {k: [] for k in
                               ['date', crit, 'period', 'dayofweek', 'duration',
                                'start', 'end', 'total_demand', 'avg_flow',
                                'traveltime', 'avg_speed', 'density', 'avg_occ']}

    # Build iteration list: directional (one entry per direction) or
    # bidirectional (all sections aggregated into a single 'C1_BD' profile).
    aggregation = cfg.get('network_aggregation', 'directional')
    if aggregation == 'bidirectional':
        iter_dirs = [('C1_BD', det_all.copy())]
    else:
        iter_dirs = [(dir_id, det_all[det_all['direction'] == direction_int].copy())
                     for direction_int, dir_id in directions.items()]

    for dir_id, det_dir in iter_dirs:
        print(f"\n=== C1 {'bidirectional' if aggregation == 'bidirectional' else dir_id} ===")
        cfg_dir  = {**cfg, 'VDS_num': dir_id, 'Day_list': Day_list}
        cfg_det  = _wrap_network_cfg_for_detection(cfg_dir)   # adds speedbased_params

        res_div  = empty_res('division')
        res_seg  = empty_res('segment')
        peak_recs = []

        for date_ts, day_det in det_dir.groupby('date'):
            # date_ts: Timestamp (for df['time'] column)
            # date_str: '%%y%%m%%d' string — matches existing pipeline's date format
            date_str = date_ts.strftime('%y%m%d')
            traffic  = build_network_traffic_day(day_det, date_ts)

            miss = traffic['speed'].isna().mean()
            if miss > cfg_dir.get('missing_ratio', 0.05):
                print(f"  Skip {date_str}: {miss:.0%%} missing")
                continue

            if cfg_dir.get('temporal_scale', 'speedbasedpeak') == 'speedbasedpeak':
                traffic, peaks = apply_peak_detection(traffic, date_str, cfg_det)
            else:
                traffic['division'] = 0
                traffic['segment']  = 0
                peaks = []

            if peaks:
                peak_recs.append({'date': date_str, 'peak_list': peaks})

            res_div, res_seg = append_daily_results(
                traffic, cfg_dir, date_str, traffic, res_div, res_seg)
            print(f"  {date_str} ok")

        _save_network_daily_results(cfg_dir, res_div, 'division')
        _save_network_daily_results(cfg_dir, res_seg, 'segment')

        pk_df = (pd.DataFrame(peak_recs) if peak_recs
                 else pd.DataFrame(columns=['date', 'peak_list']))
        set_peak_period_save({**cfg_dir, 'spatial_scope': 'single'}, pk_df)

    print("\nNetwork pipeline complete.")


def _make_section_config(base_cfg: dict, base_vds: str, sec_id):
    """Create a sub-config treating one section as an independent VDS."""
    import copy
    sec_id = int(sec_id)   # <-- cast np.int64 → Python int
    sub = copy.deepcopy(base_cfg)

    # Direction-aware naming (so D1 / D2 results never collide)
    scp = sub.get('section_combined_params', {})
    direction = scp.get('direction_filter')
    dir_suffix = f"_D{direction}" if direction is not None else ""
    sec_name = f"{base_vds}_S{sec_id}{dir_suffix}"

    sub['VDS_num'] = sec_name
    sub['base_vds'] = base_vds
    sub['VDS_list'] = [sec_name]
    sub['lane_num'] = [1]
    scp = scp.copy()
    scp['section_filter'] = sec_id
    sub['section_combined_params'] = scp

    # --- auto-fill VDS-specific defaults from base VDS ---
    # speed threshold (canonical free-flow speed in mph)
    sp = sub.setdefault('speedbased_params', {})
    thre_map = sp.setdefault('offpeak_ff_speed_threshold', {})
    base_thre = thre_map.get(base_vds, 55)
    thre_map.setdefault(sec_name, base_thre)

    # free_tt_FD (data-derived from fundamental diagram — keep separate)
    d_fd = sub.setdefault('free_tt_FD', {})
    base_val_fd = d_fd.get(base_vds, 60 * (1 / 55))
    d_fd.setdefault(sec_name, base_val_fd)
    # NOTE: free_tt_offpeak_avg is auto-derived as 60 / offpeak_ff_speed_threshold

    # BPR-specific free-flow speed threshold (data-derived from 0-3am + 22-24 off-peak)
    bpr_ff = sub.setdefault('bpr_ff_speed_threshold', {})
    base_bpr_ff = bpr_ff.get(base_vds, thre_map.get(base_vds, 55))
    bpr_ff.setdefault(sec_name, base_bpr_ff)

    # labels
    labels = sub.setdefault('VDS_label_list', {})
    base_label = labels.get(base_vds, base_vds)
    dir_label = f" D{direction}" if direction is not None else ""
    labels.setdefault(sec_name, f"{base_label} S{sec_id}{dir_label}")

    # lane map
    lanes = sub.setdefault('lane_map', {})
    lanes.setdefault(sec_name, [1])

    return sub


def _run_pipeline_core(cfg: dict, stages: list):
    """Original run_full_pipeline body (single VDS / single call)."""
    from pathlib import Path
    import copy

    base_path = Path(cfg.get('path', cfg.get('file_path', '.'))) / '11 Rawdata'
    c_lane_num = cfg.get('lane_map', {})
    raw_timeframe = cfg.get('raw_timeframe', 5)
    rc_result = None

    if 1 in stages:
        print("=" * 60)
        print("STAGE 1: Peak Period Detection")
        print("=" * 60)

        if cfg['spatial_scope'] == 'single':
            for vds in cfg['VDS_list']:
                cfg_vds = dict(cfg, VDS_num=vds, lane_num=c_lane_num.get(vds, []))
                div, seg, peaks = run_single_vds(cfg_vds, base_path, vds, raw_timeframe, c_lane_num)
                set_peak_period_save(cfg_vds, peaks)
                c_daily_traffic_save(cfg_vds, div, "division")
                c_daily_traffic_save(cfg_vds, seg, "segment")
                print(f"  VDS {vds}: done")

        elif cfg['spatial_scope'] == 'multi_vds':
            div, seg, peaks = run_multi_vds(cfg, raw_timeframe, c_lane_num)
            set_peak_period_save(cfg, peaks)
            c_daily_traffic_save(cfg, div, "division")
            c_daily_traffic_save(cfg, seg, "segment")

        elif cfg['spatial_scope'] == 'network':
            run_network_c1(cfg)

    if 2 in stages:
        print("\n" + "=" * 60)
        print("STAGE 2: Fundamental Diagram + Density Threshold Check")
        print("=" * 60)

        skip_map = {}
        if cfg['plots'].get('plot_fundamental_diagram'):
            if cfg['data_format'] == 'section_combined':
                _xlim = [0, 600]
                _ylim = [0, 8000]
            elif cfg['data_format'] == 'network':
                _xlim = [0, 600]
                _ylim = [0, 8000]
            elif cfg['data_format'] == 'raw':
                _xlim = [0, 150]
                _ylim = [0, 2000]

            try:
                print(_xlim, _ylim)
                _, skip_map = plot_fd_all_in_one_png(
                    cfg=cfg, variable="qk", version_key="speed",
                    speed_thre=cfg['speedbased_params']['offpeak_ff_speed_threshold'],
                    xlim=_xlim, ylim=_ylim,
                    title_suffix="", out_name="FD_all_in_one"
                )
                cfg['_fd_skip_map'] = skip_map
            except Exception as e:
                print(f"  FD plotting skipped or failed: {e}")
        else:
            print("  plot_fundamental_diagram is disabled; skip_map will be empty.")
            cfg['_fd_skip_map'] = {}

    if 3 in stages:
        print("\n" + "=" * 60)
        print("STAGE 3: Recurrent Peak Detection")
        print("=" * 60)

        rc_result = run_recurrent_peak_pipeline(cfg)
        if rc_result:
            print(f"  Recurrent output tag: {rc_result.get('output_tag', 'N/A')}")
            print(f"  Labeled CSV: {rc_result.get('labeled_csv', 'N/A')}")
        else:
            print("  No recurrent result returned.")

    if 4 in stages:
        print("\n" + "=" * 60)
        print("STAGE 4: BPR Calibration")
        print("=" * 60)

        cfg_bpr = copy.deepcopy(cfg)

        if rc_result is not None and 'output_tag' in rc_result:
            cfg_bpr['recurrent_output_tag'] = rc_result['output_tag']
        else:
            cfg_bpr['recurrent_output_tag'] = build_recurrent_output_tag(cfg)

        if _should_save(cfg_bpr, 'plot_bpr_fit'):
            try:
                cfg_bpr_plot = copy.deepcopy(cfg_bpr)
                cfg_bpr_plot['save_dir'] = cfg_bpr.get('bpr_save_dir', cfg_bpr.get('save_dir', '.'))
                if cfg.get('temporal_scale') == 'entireday':
                    _override = cfg.get('bpr_xlim_override', {})
                    _xlim = [_override.get(str(v), None) for v in cfg.get('VDS_list', [])] or [None]
                else:
                    _xlim = [None]  # data-driven per panel
                if cfg.get('temporal_scale') == 'entireday':
                    _ylim = [-4, 0]
                elif cfg.get('spatial_scope') == 'network':
                    _ylim = [-6, 1]
                else:
                    _ylim = [-3.5, 3]
                plot_bpr_all_in_one_png_3x3(
                    cfg=cfg_bpr_plot,
                    version_key=cfg.get('bpr_version_key', 'v3'),
                    xlim=_xlim,
                    ylim=_ylim,
                    suptitle="Log-Transformed BPR Function",
                    out_name=build_recurrent_output_tag(cfg)
                )

                
            except Exception as e:
                print(f"  BPR fit plotting skipped or failed: {e}")

        if _should_save(cfg_bpr, 'plot_demand_histogram'):
            try:
                plot_duration_demand_all_in_one_png_3x3(cfg_bpr, dt_min=5, duration_unit="auto")
                plot_totaldemand_histogram_all_in_one_png_3x3(cfg_bpr, bins=25, density=True)
            except Exception as e:
                print(f"  Demand histogram plotting skipped or failed: {e}")

    print("\nPipeline complete. Stages run:", stages)


def run_full_pipeline(cfg: dict, stages: list = None):
    """
    Runs the specified stages of the BPR analysis pipeline.
    For 'section_combined' data, auto-expands each base VDS into its
    individual sections and runs the pipeline per section.

    Stages:
        1 — Daily peak detection
        2 — Fundamental Diagram plot + density threshold check
        3 — Recurrent peak classification
        4 — BPR calibration
    """
    if stages is None:
        stages = [1, 2, 3, 4]

    # ── section_combined expansion ──────────────────────────────
    if cfg.get('data_format') == 'section_combined' and cfg.get('spatial_scope') == 'single':
        all_section_names = []
        all_sec_cfgs = []   # keep full configs for merging keys later
        for base_vds in cfg['VDS_list']:
            sections = get_unique_sections(cfg, base_vds)
            scp = cfg.get('section_combined_params', {})
            direction = scp.get('direction_filter')
            dir_info = f" (Direction {direction})" if direction is not None else ""
            print(f"\n{'=' * 60}")
            print(f"Base VDS {base_vds}{dir_info}: {len(sections)} sections → {sections[:5]}{'…' if len(sections) > 5 else ''}")
            print(f"{'=' * 60}")
            for sec_id in sections:
                sec_cfg = _make_section_config(cfg, base_vds, sec_id)
                all_section_names.append(sec_cfg['VDS_num'])
                all_sec_cfgs.append(sec_cfg)
                _run_pipeline_core(sec_cfg, [s for s in stages if s != 3])

        # Run Stage 3 once with combined VDS list (so grid shows all sections)
        if 3 in stages:
            # Gather per-section keys into a single combined config
            combined_cfg = copy.deepcopy(cfg)
            combined_cfg['VDS_list'] = all_section_names
            _is_c1 = all_section_names and all(name.startswith('C1') for name in all_section_names)
            if _is_c1:
                combined_cfg['bpr_xlim_default'] = [5.5, 9.5]

            # Merge per-section maps from sec_cfg (free_tt_FD, lane_map, etc.)
            for _sec_cfg in all_sec_cfgs:
                _sec_name = _sec_cfg['VDS_num']
                # speed threshold
                _sp_b = combined_cfg.setdefault('speedbased_params', {})
                _th_b = _sp_b.setdefault('offpeak_ff_speed_threshold', {})
                _sp_s = _sec_cfg.get('speedbased_params', {})
                if _sec_name in _sp_s.get('offpeak_ff_speed_threshold', {}):
                    _th_b[_sec_name] = _sp_s['offpeak_ff_speed_threshold'][_sec_name]
                # free_tt_FD
                _ft = combined_cfg.setdefault('free_tt_FD', {})
                if _sec_name in _sec_cfg.get('free_tt_FD', {}):
                    _ft[_sec_name] = _sec_cfg['free_tt_FD'][_sec_name]
                # lane_map
                _lm = combined_cfg.setdefault('lane_map', {})
                if _sec_name in _sec_cfg.get('lane_map', {}):
                    _lm[_sec_name] = _sec_cfg['lane_map'][_sec_name]
                # bpr_ff_speed_threshold (Section 3 free-flow filter)
                _bpr_b = combined_cfg.setdefault('bpr_ff_speed_threshold', {})
                if _sec_name in _sec_cfg.get('bpr_ff_speed_threshold', {}):
                    _bpr_b[_sec_name] = _sec_cfg['bpr_ff_speed_threshold'][_sec_name]
                # labels
                _vl = combined_cfg.setdefault('VDS_label_list', {})
                if _sec_name in _sec_cfg.get('VDS_label_list', {}):
                    _vl[_sec_name] = _sec_cfg['VDS_label_list'][_sec_name]

            # Auto-populate corridor_groups for base VDS (e.g. C1 → [C1_S1_D1, ...])
            # so grid plots render C1 sections as a corridor panel.
            if combined_cfg.get('corridor_groups') is not None:
                for base_vds in cfg['VDS_list']:
                    sec_names_for_base = [n for n in all_section_names if n.startswith(f"{base_vds}_S")]
                    if sec_names_for_base:
                        existing = combined_cfg['corridor_groups'].get(base_vds)
                        if existing is None:
                            combined_cfg['corridor_groups'][base_vds] = sec_names_for_base
                        # if user already specified the group, keep it
            else:
                # No corridor_groups defined at all — create one per base VDS
                combined_cfg['corridor_groups'] = {}
                for base_vds in cfg['VDS_list']:
                    sec_names_for_base = [n for n in all_section_names if n.startswith(f"{base_vds}_S")]
                    if sec_names_for_base:
                        combined_cfg['corridor_groups'][base_vds] = sec_names_for_base

            _run_pipeline_core(combined_cfg, [3])
        return

    # ── legacy path ─────────────────────────────────────────────
    _run_pipeline_core(cfg, stages)


def _common_dates_and_files(config) -> tuple[list, dict]:
    """
    For config['VDS_list'], compute intersection of dates and map to filenames.
    Returns:
      dates_common (sorted list),
      date_to_files: {date: {vds: filename_or_None}}
    """
    # Handle section_combined format
    if config.get('data_format') == 'section_combined':
        from .data_io import _section_cache
        import pandas as pd
        from pathlib import Path

        scp = config.get('section_combined_params', {})
        _path = config.get('path', config.get('file_path', '.'))
        _dir = config.get('dir', '5min')
        fname = scp.get('filename', 'Detector.csv')
        # For per-section configs, use base_vds for folder path
        base_vds = config.get('base_vds', config['VDS_list'][0])
        fpath = Path(_path) / '11 Rawdata' / _dir / base_vds / fname

        df = _section_cache.get(str(fpath))
        if df is None:
            _ensure_local(str(fpath))
            df = pd.read_csv(fpath)
            _section_cache[str(fpath)] = df
            
        df.columns = ['Route_ID', 'Direction', 'Section_ID', 'Date', 'Time_interval', 'Volume', 'Speed', 'Occ', 'Density']
        dformat = scp.get('date_format', '%Y%m%d')
        dates = sorted(df['Date'].astype(str).unique())
        # Strip century for consistency if needed
        if dformat == '%Y%m%d':
            dates = [d[2:] for d in dates]  # 20180701 → 180701

        date_to_files = {d: {vds: None for vds in config['VDS_list']} for d in dates}
        return dates, date_to_files

    # --- legacy per-day file format ---
    date_maps = {}
    _path = config.get('path', config.get('file_path', '.'))
    _dir  = config.get('dir', '5min')
    for vds in config['VDS_list']:
        base = os.path.join(_path, '11 Rawdata', _dir, vds)
        date_maps[vds] = _index_files_by_date(base)

    # intersection of date keys
    sets = [set(dmap.keys()) for dmap in date_maps.values()]
    dates_common = sorted(set.intersection(*sets))

    date_to_files = {d: {vds: date_maps[vds][d] for vds in config['VDS_list']} for d in dates_common}
    return dates_common, date_to_files


def _make_vds_config(config, vds: str, c_lane_num: dict = None):
    """Shallow clone with per-VDS fields."""
    cfg = dict(config)
    cfg['VDS_num']  = vds
    cfg['base_vds'] = vds
    if c_lane_num and vds in c_lane_num:
        cfg['lane_num'] = c_lane_num[vds]
    else:
        cfg['lane_num'] = config.get('lane_num', [])
    return cfg


def _build_traffic_for_vds(date: str, filename: str, cfg_vds, vds, timeframe_min: int = None, c_lane_num: dict = None):
    """Reuses your existing functions to get a per-VDS day traffic frame."""
    data_format = cfg_vds.get('data_format', 'per_day_per_lane')

    if data_format == 'section_combined':
        traffic, coverage_length = load_section_combined(cfg_vds, date)
        return traffic, coverage_length

    # --- legacy per-day per-lane path ---
    rawdata, date = load_raw(filename, cfg_vds)
    if skip_if_missing(rawdata, cfg_vds):
        print("skip", date)
        return None

    lane_num = (c_lane_num or {}).get(vds, cfg_vds.get('lane_num', []))
    coverage_length = rawdata['length'].iloc[0]

    agg_tf = timeframe_min if timeframe_min is not None else cfg_vds.get('aggregate_timeframe', 5)
    traffic, plot_date = aggregate_rawdata_5min(rawdata, agg_tf, date, lane_num, vds)

    return traffic, coverage_length


def _combine_vds_traffic(traffic_list: list[pd.DataFrame], agg_min: int, c_coverage_length: list) -> pd.DataFrame:
    """
    Given multiple per-VDS daily DataFrames (already interpolated to identical
    time_slot grids), return a single DataFrame with:
        ['time_slot','speed','time','flow','density','occ']
    computed as simple arithmetic means across VDS for each time_slot.
    """
    # keep only columns we can consistently average
    keep = ['time','time_slot', 'speed', 'flow', 'density','occ']
    stacked = []
    for t in traffic_list:
        if t is not None:
            stacked.append(t[keep].copy())

    if not stacked:
        return None

    # Concatenate with keys and average by time_slot
    # combo = (pd.concat(stacked, keys=range(len(stacked)))
    #            .groupby('time_slot', as_index=False)[['flow','density']].mean())

    combo = (
        pd.concat(stacked, keys=range(len(stacked)))
          .groupby(['time', 'time_slot'], as_index=False)
          .apply(lambda g: pd.Series({
              'flow':    np.average(g['flow'],    weights=c_coverage_length),
              'density': np.average(g['density'], weights=c_coverage_length),
              'occ':     np.average(g['occ'],     weights=c_coverage_length)
          }))
          .reset_index(drop=True))

    # recompute time (min/mile) from averaged speed
    combo['speed'] = combo['flow'] / combo['density']
    combo['traveltime'] = 60.0 / combo['speed']

    # ensure standard ordering like your per-day frames
    combo = combo[['time','time_slot','speed','traveltime','flow','density','occ']].sort_values('time_slot').reset_index(drop=True)
    return combo

