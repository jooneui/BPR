"""
Legacy / dead code from traffic_utils.

This module is NOT imported by default (``from traffic_utils import *`` will
not load it).  Use an explicit opt-in when needed::

    from traffic_utils._legacy import *

Functions are preserved here for reference and for the notebook's CV appendix
(cell 100).
"""

# ──────────────────────────────────────────────────────────────
# Imports required by legacy functions
# ──────────────────────────────────────────────────────────────
from itertools import chain
import os
import pickle
import re

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.signal import find_peaks

# ══════════════════════════════════════════════════════════════
# FROM _helpers.py — dead / unused functions
# ══════════════════════════════════════════════════════════════

# ── internal helpers (never called outside _helpers) ──────────


def _extract_date_from_filename(fn: str) -> str:
    """Match your existing logic: last 11..-5 slice already used elsewhere."""
    return fn[-11:-5]   # e.g., '250915' for YYMMDD


def _index_files_by_date(base_path: str) -> dict:
    """
    Return {date_str: filename} for a given VDS directory.
    base_path = f"{config['path']}/11 Rawdata/{config['dir']}/{VDS}"
    """
    files = sorted(os.listdir(base_path))
    files = [f for f in files if not f.startswith('.')]
    out = {}
    for f in files:
        try:
            d = _extract_date_from_filename(f)
            out[d] = f
        except Exception:
            continue
    return out


def _dow_from_yymmdd(d: str) -> str:
    """Return weekday string using your Day_list mapping."""
    Day_list = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    from datetime import datetime as _dt
    dt = _dt.strptime('20' + d, '%Y%m%d')
    return Day_list[dt.weekday()]


def _resolve_speed_threshold(speed_thre, vds_id, cfg=None):
    """Resolve speed threshold for a VDS, with fallback to base VDS prefix.

    For section-combined names like 'C1_S1_D1', tries:
      1. speed_thre['C1_S1_D1']  (per-section, user-specified)
      2. speed_thre['C1']        (base VDS, user-specified)
      3. 55                       (hard default)
    """
    if isinstance(speed_thre, dict):
        if vds_id in speed_thre:
            return speed_thre[vds_id]
        base = vds_id.split('_')[0] if '_' in vds_id else vds_id
        if base in speed_thre:
            return speed_thre[base]
        return 55
    return speed_thre


# ── merge_period_columns_wide (dead CSV merge utility) ──────

from pathlib import Path
from functools import reduce as _reduce


def _read(fp, ext=".csv"):
    if ext == ".csv":
        return pd.read_csv(fp, sep=None, engine="python")
    elif ext == ".parquet":
        return pd.read_parquet(fp)
    else:
        raise ValueError("Unsupported ext; use .csv or .parquet")


def merge_period_columns_wide(folder, prefix_before_v, ext=".csv",
                              join_keys=None, strict=False):
    """
    Column-wise merge of files like:
      <prefix_before_v>v_speed-duration-only<ext>
      <prefix_before_v>v_speedgap-neighbor<ext>
      <prefix_before_v>v_occ<ext>
      <prefix_before_v>v_occ-solely<ext>

    Keeps shared keys once; adds one column per method: period_<method>.
    """
    folder = Path(folder)
    files = sorted(folder.glob(f"{prefix_before_v}v_*{ext}"))
    if not files:
        raise FileNotFoundError(f"No files match {folder}/{prefix_before_v}v_*{ext}")

    first = _read(files[0], ext)
    if join_keys is None:
        candidate_keys = ["date", "division", "start_time", "end_time", "duration",
                          "year", "dayofweek", "totaldemand", "avg_flow",
                          "traveltimes", "avg_speed", "density", "avg_occ"]
        join_keys = [k for k in candidate_keys if k in first.columns]
        if not join_keys:
            join_keys = [c for c in first.columns if c != "period"]

    skinny = []
    base_nonperiod = None

    for fp in files:
        method = fp.stem.split("v_", 1)[-1]
        print(method)
        df = _read(fp, ext)

        if strict:
            cols_to_check = [c for c in df.columns if c != "period"]
            if base_nonperiod is None:
                base_nonperiod = df[cols_to_check].copy()
            else:
                merged_chk = pd.merge(base_nonperiod, df[cols_to_check], on=join_keys, how="outer", indicator=True)
                if (merged_chk["_merge"] != "both").any():
                    raise ValueError(f"Row mismatch vs base in {fp.name}. Check join_keys or data.")

        keep = join_keys + ["period"]
        missing = set(keep) - set(df.columns)
        if missing:
            raise ValueError(f"{fp.name} missing columns: {missing}")

        slim = df[keep].drop_duplicates(join_keys, keep="last")
        slim = slim.rename(columns={"period": f"period_{method}"})
        skinny.append(slim)

    merged = _reduce(lambda L, R: pd.merge(L, R, on=join_keys, how="outer"), skinny)
    period_cols = [c for c in merged.columns if c.startswith("period_")]
    merged = merged[join_keys + period_cols]
    return merged


# ── extract_peak_intervals (dead) ─────────────────────────────


def extract_peak_intervals(df_vds, bin_size):
    """
    Identifies the most frequent 20-min bin for start and end hours.
    """
    results = []
    day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    periods = ["morning-peak", "afternoon-peak"]

    vds_id = df_vds["vds_id"].iloc[0]

    for day in day_order:
        for per in periods:
            subset = df_vds[(df_vds["dayofweek"] == day) & (df_vds["period"] == per)]

            if subset.empty:
                continue

            row_res = {"vds_id": vds_id, "dayofweek": day, "period": per}

            for col in ["start_hour", "end_hour"]:
                bins = (subset[col] // bin_size) * bin_size

                if bins.dropna().empty:
                    row_res[f"{col}_peak_bin"] = None
                    continue

                peak_bin_start = bins.mode()[0]
                peak_bin_end = peak_bin_start + bin_size

                def to_time_str(h):
                    hour = int(h)
                    minutes = int(round((h - hour) * 60))
                    return f"{hour:02d}:{minutes:02d}"

                interval_str = f"{to_time_str(peak_bin_start)}-{to_time_str(peak_bin_end)}"
                row_res[f"{col}_peak_bin"] = interval_str

            results.append(row_res)

    return pd.DataFrame(results)


# ── filter_peaks_by_mode_csv (dead) ───────────────────────────


def parse_to_hour(time_str):
    """Converts 'HH:MM' string to float hour (e.g., '07:20' -> 7.333)."""
    h, m = map(int, time_str.split(':'))
    return h + m / 60.0


def parse_interval(interval_str):
    """Converts 'HH:MM-HH:MM' to (start_hour, end_hour)."""
    if pd.isna(interval_str):
        return None, None
    s, e = interval_str.split('-')
    return parse_to_hour(s), parse_to_hour(e)


def filter_peaks_by_mode_csv(df_peaks, mode_csv_path):
    """
    Filters df_peaks using the 'peak_interval_summary_simpleband.csv' file.
    """
    df_modes = pd.read_csv(mode_csv_path)
    print(df_modes.head())

    filtered_results = []

    for _, mode_row in df_modes.iterrows():
        vds = str(mode_row['vds_id'])
        day = mode_row['dayofweek']
        per = mode_row['period']

        if per == 'morning-peak':
            low, high = parse_interval(mode_row['start_hour_peak_bin'])
            target_col = 'start_hour'
        else:
            print("mode_row['end_hour_peak_bin']:", mode_row['end_hour_peak_bin'])
            low, high = parse_interval(mode_row['end_hour_peak_bin'])
            target_col = 'end_hour'

        if low is None:
            continue

        mask = (
            (df_peaks['vds_id'] == vds)
            & (df_peaks['dayofweek'] == day)
            & (df_peaks['period'] == per)
            & (df_peaks[target_col] >= low)
            & (df_peaks[target_col] < high)
        )

        print("minmax", df_peaks[mask][target_col].min(), df_peaks[mask][target_col].max())
        filtered_results.append(df_peaks[mask])

    if not filtered_results:
        return pd.DataFrame(columns=df_peaks.columns)

    return pd.concat(filtered_results, ignore_index=True)


# ── identify_top_80_percent_peaks (dead) ──────────────────────


def identify_top_80_percent_peaks(df, day, period, bandwidth, ind_threshold):
    """
    Identifies major peak regimes using Mean Shift clustering.
    Includes missing dates as defaults (0 or 12).
    Selects enough clusters to cover at least 80% of total possible days.
    """
    from sklearn.cluster import MeanShift, estimate_bandwidth

    sub = df[(df['dayofweek'] == day) & (df['period'] == period)]

    sub['start_hour'] = pd.to_numeric(sub['start_hour'], errors='coerce')
    sub['end_hour'] = pd.to_numeric(sub['end_hour'], errors='coerce')

    if period == 'morning-peak':
        sub['start_hour'] = sub['start_hour'].fillna(0.0)
        sub['end_hour'] = sub['end_hour'].fillna(0.0)
    else:
        sub['start_hour'] = sub['start_hour'].fillna(12.0)
        sub['end_hour'] = sub['end_hour'].fillna(12.0)

    total_datapoints = len(sub)

    if total_datapoints < 3:
        sub['is_significant'] = False
        sub['cluster'] = -1
        return sub, []

    X = sub[['start_hour', 'end_hour']].values

    ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)
    ms.fit(X)

    sub['cluster'] = ms.labels_

    cluster_counts = sub['cluster'].value_counts().sort_values(ascending=False)
    real_clusters = cluster_counts.drop(-1, errors='ignore')

    if real_clusters.empty:
        sub['is_significant'] = False
        return sub, []

    significant_clusters = []
    current_sum = 0

    for cid, count in real_clusters.items():
        if count < ind_threshold * total_datapoints:
            break
        significant_clusters.append(cid)
        current_sum += count

    sub['is_significant'] = sub['cluster'].isin(significant_clusters)

    summaries = []
    cluster_centers = ms.cluster_centers_

    for cid in significant_clusters:
        summaries.append({
            'cluster_id': cid,
            'start': cluster_centers[cid][0],
            'end': cluster_centers[cid][1],
            'share': real_clusters[cid] / total_datapoints
        })

    return sub, summaries


# ── process_and_visualize_recurrent_peaks (dead) ───────────────


def process_and_visualize_recurrent_peaks(df_peaks, vds_id, day_order, save_dir: str,
                                           show_temporal, show_cluster_space):
    """
    Modular function to identify recurrent peaks and visualize them.
    Allows independent activation of Temporal and Cluster Space plots.
    """
    all_outliers_vds = []
    day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    periods = ['morning-peak', 'afternoon-peak']

    g = None
    fig_clust = None
    axes_clust = None

    if show_temporal:
        g = sns.FacetGrid(
            df_peaks, row='dayofweek', col='period',
            row_order=day_order, col_order=periods,
            height=4, aspect=1, sharey=False, sharex=True
        )

    if show_cluster_space:
        fig_clust, axes_clust = plt.subplots(
            nrows=len(day_order), ncols=2,
            figsize=(12, 4 * len(day_order)),
            constrained_layout=True
        )

    for d_idx, row_val in enumerate(day_order):
        for p_idx, col_val in enumerate(periods):
            df_res, top_summaries = identify_top_80_percent_peaks(
                df_peaks, row_val, col_val, bandwidth=0.8, ind_threshold=0.05)

            outliers = df_res[df_res['is_significant'] == False].copy()
            outliers['vds_id'] = vds_id
            all_outliers_vds.append(outliers)

            if show_temporal and g is not None:
                ax_temp = g.axes_dict[(row_val, col_val)]

                for data, color, size, alpha in [
                    (df_res[df_res['is_significant']], None, 50, 1.0),
                    (df_res[~df_res['is_significant']], 'grey', 20, 0.3)
                ]:
                    if not data.empty:
                        sns.scatterplot(data=data, x='week_num', y='start_hour', ax=ax_temp,
                                        color=color, hue=('cluster' if color is None else None),
                                        palette='Set1', s=size, alpha=alpha, zorder=3, legend=False)
                        sns.scatterplot(data=data, x='week_num', y='end_hour', ax=ax_temp,
                                        color=color, hue=('cluster' if color is None else None),
                                        palette='Set1', s=size, alpha=alpha, zorder=3, legend=False)

                for i, s in enumerate(top_summaries):
                    band_color = plt.cm.Set1(i % 9)
                    ax_temp.axhspan(s['start'], s['end'], color=band_color, alpha=0.15)
                    ax_temp.text(df_peaks['week_num'].max() + 0.5, (s['start'] + s['end']) / 2,
                                f"{s['share']:.0%}", fontsize=9, weight='bold', color=band_color,
                                transform=ax_temp.get_yaxis_transform())

                ax_temp.set_xlim(0, df_peaks['week_num'].max() + 2)
                curr_lim = (-0.5, 12) if col_val == 'morning-peak' else (11.5, 22)
                ax_temp.set_ylim(curr_lim)
                ax_temp.yaxis.set_major_locator(ticker.MultipleLocator(2))

            if show_cluster_space and axes_clust is not None:
                ax_clust = axes_clust[d_idx, p_idx]

                noise = df_res[df_res['cluster'] == -1]
                ax_clust.scatter(noise['start_hour'], noise['end_hour'], c='grey', alpha=0.3, s=30)

                real_c = df_res[df_res['cluster'] != -1]
                if not real_c.empty:
                    ax_clust.scatter(real_c['start_hour'], real_c['end_hour'],
                                     c=real_c['cluster'], cmap='Set1', s=40, edgecolors='w')

                for s in top_summaries:
                    ax_clust.plot(s['start'], s['end'], 'kx', markersize=12, mew=2)

                ax_clust.set_title(f"{row_val} {col_val}")
                curr_lim = (-0.5, 12) if col_val == 'morning-peak' else (11.5, 23)
                ax_clust.set_xlim(curr_lim)
                ax_clust.set_ylim(curr_lim)
                ax_clust.grid(True, alpha=0.3)

    if show_temporal and g:
        g.fig.suptitle(f"Recurrent Peaks (Temporal) - VDS: {vds_id}", fontsize=15)
        g.fig.savefig(os.path.join(save_dir, f"Temporal_{vds_id}.png"), dpi=150, bbox_inches='tight')

    if show_cluster_space and fig_clust:
        fig_clust.suptitle(f"Cluster Space (Start vs End) - VDS: {vds_id}", fontsize=15)
        fig_clust.savefig(os.path.join(save_dir, f"ClusterSpace_{vds_id}.png"), dpi=150)

    plt.show()
    plt.close('all')

    return all_outliers_vds


# ── model_bpr_avgdemand / run_v5 (dead BPR v5) ───────────────

from typing import Optional


def model_bpr_avgdemand(x, a, b, free_tt, c_fixed, W_minutes):
    t0 = free_tt
    W = W_minutes / 60.0
    return t0 * (1.0 + a * (x / (c_fixed * W)) ** b)


def run_v5(df: pd.DataFrame, cfg: dict, xlim: Optional[list] = None, ylim: Optional[list] = None, save_name: Optional[str] = None):
    group_key = cfg["label_criterion"]
    c_fixed = cfg["capacity_fixed"]
    Wm = cfg["W_minutes"]

    if cfg["free_tt_method"] == "FD":
        if cfg['spatial_scope'] == 'single':
            vds = cfg["VDS_num"]
            free_tt = cfg['free_tt_FD'].get(vds, cfg['free_tt_FD'].get(vds.split('_')[0], cfg['free_tt_FD'].get('multi_vds', 60 / 55)))
        elif cfg['spatial_scope'] == 'multi_vds':
            free_tt = cfg['free_tt_FD']['multi_vds']
    elif cfg["free_tt_method"] == "offpeak_avg":
        ff_map = cfg.get('bpr_ff_speed_threshold', {})
        if not ff_map:
            sp = cfg.get('speedbased_params', {})
            ff_map = sp.get('offpeak_ff_speed_threshold', {})
        if cfg['spatial_scope'] == 'single':
            vds = cfg["VDS_num"]
            ff_speed = ff_map.get(vds,
                                  ff_map.get(vds.split('_')[0],
                                             ff_map.get('multi_vds', 55)))
        elif cfg['spatial_scope'] == 'multi_vds':
            ff_speed = ff_map.get('multi_vds', 55)
        else:
            ff_speed = 55
        free_tt = 60.0 / ff_speed

    fig, ax = plt.subplots(1, 1, figsize=(8.5, 6))
    legends = []

    for name, grp in df.groupby(group_key):
        x = grp["totaldemandoverlanes"].to_numpy()
        y = grp["traveltimes"].to_numpy()

        ax.plot(x, y, marker="o", linestyle="", label=str(name))

        ax.set_xlim(0, x.max() * 1.1)

        if xlim:
            ax.set_xlim(*xlim)
        if ylim:
            ax.set_ylim(*ylim)

        ax.set_xlabel(r"$N$ (veh)", fontsize=12)
        ax.set_ylabel("Average travel time (min/mile)", fontsize=12)
        ax.grid(True)
        ax.set_title(f"BPR calibration (V5) at VDS {cfg['VDS_num']} [{cfg['method']}]", fontsize=12)

        if save_name is None:
            if cfg['spatial_scope'] == "multi_vds":
                save_name = (f"{cfg['save_dir']}/{cfg['period_include'][cfg['temporal_scale']]}/v5/"
                             f"BPR_calibration_{cfg['spatial_scope']}_{cfg['VDS_list']}_"
                             f"{cfg['temporal_scale']}_v5_{cfg['method']}_{cfg['free_tt_method']}_"
                             f"{cfg['period_include']}.png")
            else:
                save_name = (f"{cfg['save_dir']}/{cfg['period_include'][cfg['temporal_scale']]}/v5/"
                             f"BPR_calibration_{cfg['spatial_scope']}_{cfg['VDS_num']}_"
                             f"{cfg['temporal_scale']}_v5_{cfg['method']}_{cfg['free_tt_method']}_"
                             f"{cfg['period_include']}.png")

        plt.savefig(save_name, bbox_inches="tight")
        plt.close(fig)


# ── plot_bpr_multi_scale_diagnostics_normalized (dead) ────────


def plot_bpr_multi_scale_diagnostics_normalized(
    cfg_base,
    version_key,
    vds_list,
    vds_label_map,
    diagnostic_type,  # 'qq' or 'residual'
    font_add=2,
    out_name="BPR_Diagnostic_Comparison"
):
    """
    Creates a 3x3 grid where each panel represents one VDS.
    'speedbasedpeak' is split into morning-peak and afternoon-peak.
    """
    from .bpr_fitting import load_and_annotate, apply_filters, LINEAR_REGISTRY_BPR
    import statsmodels.api as sm
    from statsmodels.graphics.gofplots import ProbPlot

    scales_to_compare = ['hour', 'entireday', 'speedbasedpeak']

    colors = {
        'hour': '#A9C6DA',
        'entireday': '#2ca02c',
        'morning-peak': '#FF4500',
        'afternoon-peak': '#800000'
    }
    label_set = {
        'hour': 'Hour',
        'entireday': 'Entire-day',
        'morning-peak': 'Peak (AM)',
        'afternoon-peak': 'Peak (PM)'
    }

    positions = [(0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)]

    fig, axs = plt.subplots(3, 3, figsize=(14, 11), constrained_layout=True)
    for ax in axs.ravel():
        ax.set_visible(False)

    trans = LINEAR_REGISTRY_BPR[version_key]
    xcol, ycol, _, _ = trans()

    for i, vds_id in enumerate(vds_list):
        if i >= len(positions):
            break
        r, c = positions[i]
        ax = axs[r, c]
        ax.set_visible(True)

        tag = vds_label_map.get(str(vds_id), str(vds_id))
        ax.set_title(f"VDS {tag}", fontsize=14 + font_add, fontweight='bold')

        for scale in scales_to_compare:
            cfg_s = copy.deepcopy(cfg_base)
            cfg_s['temporal_scale'] = scale
            cfg_s['VDS_num'] = vds_id
            cfg_s['VDS_list'] = vds_id

            if scale == 'speedbasedpeak':
                cfg_s['period_include'] = ['morning-peak', 'afternoon-peak']
            else:
                cfg_s['period_include'] = ['off-peak']

            try:
                df_all = load_and_annotate(cfg_s)
                if str(vds_id) == "1205541" and "month" in df_all.columns:
                    df_all = df_all[~df_all["month"].isin(["2401", "2402", "2403", "2404"])]
                df_raw = apply_filters(df_all, cfg_s)

                if scale == 'speedbasedpeak':
                    sub_periods = ['morning-peak', 'afternoon-peak']
                else:
                    sub_periods = [scale]

                for sp in sub_periods:
                    if scale == 'speedbasedpeak':
                        df_use = df_raw[df_raw['period'] == sp].copy()
                    else:
                        df_use = df_raw.copy()

                    df_fit = df_use[[xcol, ycol]].dropna()
                    if df_fit.empty:
                        continue

                    X = sm.add_constant(df_fit[xcol].to_numpy())
                    y = df_fit[ycol].to_numpy()
                    model = sm.OLS(y, X).fit()

                    resids = model.resid
                    y_hat = model.fittedvalues

                    y_hat_min, y_hat_max = y_hat.min(), y_hat.max()
                    y_hat_norm = (y_hat - y_hat_min) / (y_hat_max - y_hat_min) if y_hat_max != y_hat_min else y_hat

                    current_color = colors.get(sp, '#000000')
                    current_label = label_set.get(sp, sp)

                    if diagnostic_type == 'qq':
                        std_resids = (resids - resids.mean()) / resids.std()
                        pp = ProbPlot(std_resids, fit=True)
                        theoretical = pp.theoretical_quantiles
                        sample = pp.sample_quantiles

                        ax.scatter(theoretical, sample, color=current_color, alpha=0.3, s=12, label=current_label)
                        if scale == scales_to_compare[0] and sp == sub_periods[0]:
                            line_val = [min(theoretical), max(theoretical)]
                            ax.plot(line_val, line_val, color='black', linestyle='--', alpha=0.5)
                        ax.set_xlabel("Theoretical Quantiles", fontsize=10 + font_add)
                        ax.set_ylabel("Std. Sample Quantiles", fontsize=10 + font_add)

                    elif diagnostic_type == 'residual':
                        ax.scatter(y_hat_norm, resids, color=current_color, alpha=0.3, s=12, label=current_label)
                        ax.axhline(0, color='black', linestyle='--', alpha=0.5)

                        ax.set_xlabel("Norm. Fitted [0, 1]", fontsize=10 + font_add)
                        ax.set_ylabel("Residuals", fontsize=10 + font_add)

            except Exception as e:
                print(f"Skipping {vds_id} for {scale}/{sp}: {e}")

        if i == 0:
            ax.legend(fontsize=10 + font_add, loc='best', frameon=True)

    suptitle_text = "Q-Q Plots" if diagnostic_type == 'qq' else "Residuals vs Normalized Fitted"
    fig.suptitle(f"{suptitle_text}", fontsize=18 + font_add, y=1.02)

    save_dir = cfg_base.get("save_dir", ".")
    out_path = os.path.join(save_dir, f"{out_name}_norm_{diagnostic_type}_split.png")
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.show()
    return out_path


# ── detect_twopeak (dead) ─────────────────────────────────────


def detect_twopeak(time_frame_peak, time_frame, rawdata, lane_num, gfactor, height, width):
    num_frame = time_frame_peak / time_frame
    traffic_day = pd.DataFrame({'speed': [], 'time': [], 'flow': [], 'density': []})

    plot_date = []

    for hour in range(0, 24):
        for minute in range(0, int(60 / time_frame_peak)):
            start_time = hour * 100 + minute * time_frame_peak
            end_time = start_time + time_frame_peak
            mask = (rawdata['time_filter'] >= start_time) & (rawdata['time_filter'] < end_time)
            rawdata_filter = rawdata[mask]

            if not rawdata_filter.empty:
                avg_speed, avg_time, avg_flow, avg_density = avg_traffic_state(rawdata_filter, time_frame, lane_num, gfactor)
                traffic_day.loc[len(traffic_day)] = [avg_speed, avg_time, avg_flow, avg_density]

    peaks, _ = find_peaks(traffic_day['flow'], height=height, width=width)
    return len(peaks)


# ══════════════════════════════════════════════════════════════
# FROM _helpers.py — CV appendix functions (notebook cell 100)
# ══════════════════════════════════════════════════════════════


def avg_traffic_state(rawdata, time_frame, lane_num):
    """
    Calculate traffic state parameters without gfactor.
    Density is computed as flow / speed.
    """
    flow_variable = [f'flow_{lane}' for lane in lane_num]
    speed_variable = [f'speed_{lane}' for lane in lane_num]

    rawdata_flow_df = rawdata[flow_variable]
    rawdata_flow = np.array(rawdata_flow_df) * (60 / time_frame)
    rawdata_speed = np.array(rawdata[speed_variable])

    with np.errstate(divide='ignore', invalid='ignore'):
        rawdata_density = rawdata_flow / rawdata_speed
    rawdata_density[~np.isfinite(rawdata_density)] = 0

    agg_flow_per_lane = np.mean(rawdata_flow, axis=0)
    cv_flow = np.std(agg_flow_per_lane, ddof=0) / np.mean(agg_flow_per_lane)

    agg_density_per_lane = np.mean(rawdata_density, axis=0)
    cv_density = np.std(agg_density_per_lane, ddof=0) / np.mean(agg_density_per_lane)

    agg_speed_per_lane = np.mean(rawdata_speed, axis=0)
    cv_speed = np.std(agg_speed_per_lane, ddof=0) / np.mean(agg_speed_per_lane)

    rawdata_flow_flat = rawdata_flow.flatten()
    rawdata_speed_flat = rawdata_speed.flatten()

    with np.errstate(divide='ignore', invalid='ignore'):
        multiply = rawdata_flow_flat * (1 / rawdata_speed_flat)

    sum_flow = np.nansum(rawdata_flow_flat)
    sum_product = np.nansum(multiply)

    avg_speed = sum_flow / sum_product if sum_product != 0 else 0
    avg_time = 60 / avg_speed if avg_speed != 0 else 0
    avg_flow = np.mean(rawdata_flow_flat)
    avg_density = avg_flow / avg_speed if avg_speed != 0 else 0

    return (avg_speed, avg_time, avg_flow, avg_density,
            cv_flow, cv_density, cv_speed,
            agg_flow_per_lane, agg_density_per_lane, agg_speed_per_lane)


def aggregate_rawdata(rawdata, aggregate_timeframe, raw_timeframe, date, lane_num, VDS_num):
    """
    Legacy aggregation — superseded by aggregate_rawdata_5min in data_io.
    """
    rawdata['time_slot'] = np.floor(rawdata['time_filter'] / aggregate_timeframe) * aggregate_timeframe

    traffic_within_day = pd.DataFrame()
    plot_date = []

    for time_slot, group in rawdata.groupby('time_slot'):
        if not group.empty:
            (avg_speed, avg_time, avg_flow, avg_density,
             cv_flow, cv_density, cv_speed,
             agg_flow_per_lane, agg_density_per_lane, agg_speed_per_lane) = avg_traffic_state(
                group, raw_timeframe, lane_num)

            traffic_per_lane = pd.DataFrame([list(agg_flow_per_lane) + list(agg_density_per_lane) + list(agg_speed_per_lane)])
            traffic_per_lane.columns = [f'{metric}_{lane}' for metric in ['flow', 'density', 'speed'] for lane in lane_num]

            traffic_entire_lanes = pd.DataFrame({
                'time_slot': group['time_slot'].unique(),
                'speed': avg_speed, 'time': avg_time,
                'flow': avg_flow, 'density': avg_density,
                'cv_flow': cv_flow, 'cv_density': cv_density, 'cv_speed': cv_speed
            })

            traffic_within_day = pd.concat([traffic_within_day, pd.concat([traffic_per_lane, traffic_entire_lanes], axis=1)], ignore_index=True)
            plot_date.append(time_slot)

    path_directory = f'./12 python file/{VDS_num}'
    os.makedirs(path_directory, exist_ok=True)

    with open(f'./12 python file/{VDS_num}/traffic_within_day_{date}_{aggregate_timeframe}aggmin_{lane_num}.p', 'wb') as file:
        pickle.dump(traffic_within_day, file)

    with open(f'./12 python file/{VDS_num}/plot_date_{date}_{aggregate_timeframe}aggmin.p', 'wb') as file:
        pickle.dump(plot_date, file)

    return traffic_within_day, plot_date


def cv_calculation(agg_data, lane_num, date, time, raw_timeframe, plot_whyCV, plot_time, plot_flow):
    flow_variable = [f'flow_{lane}' for lane in lane_num]
    density_variable = [f'density_{lane}' for lane in lane_num]
    speed_variable = [f'speed_{lane}' for lane in lane_num]
    occ_variable = [f'occ_{lane}' for lane in lane_num]

    agg_flow = np.array(agg_data[flow_variable])
    agg_density = np.array(agg_data[density_variable])
    agg_speed = np.array(agg_data[speed_variable])

    daily_flow = agg_flow.mean(axis=0)
    daily_density = agg_density.mean(axis=0)

    cv_flow_day = np.std(daily_flow, ddof=0) / np.mean(daily_flow)
    cv_density_day = np.std(daily_density, ddof=0) / np.mean(daily_density)

    daily_speed = []

    cv_flow_interval = np.std(agg_flow, axis=1, ddof=0) / np.mean(agg_flow, axis=1)
    cv_density_interval = np.std(agg_density, axis=1, ddof=0) / np.mean(agg_density, axis=1)
    cv_flow_day_v2 = np.mean(cv_flow_interval)
    cv_density_day_v2 = np.mean(cv_density_interval)

    for lane in lane_num:
        flow_unit = agg_flow.transpose()[(lane - 1)].flatten()
        speed_unit = agg_speed.transpose()[(lane - 1)].flatten()
        density_unit = agg_density.transpose()[(lane - 1)].flatten()

        rest_flow_df = agg_data[flow_variable]

        daily_speed_per_lane = average_speed_calculation(flow_unit, speed_unit, density_unit, rest_flow_df, malfunc_inclusion=True)
        daily_speed.append(daily_speed_per_lane)

    cv_speed_day = np.std(daily_speed, ddof=0) / np.mean(daily_speed)

    return cv_flow_day, cv_density_day, cv_speed_day, cv_flow_day_v2, cv_density_day_v2, daily_flow, daily_density


def average_speed_calculation(flow_unit, speed_unit, density_unit, rest_flow_df, malfunc_inclusion):
    flow_unit = np.array(flow_unit)
    speed_unit = np.array(speed_unit)
    density_unit = np.array(density_unit)

    if malfunc_inclusion:
        flow_bound = 24
        density_bound = 0.4

        zero_row_id = list(set(chain(
            (idx for idx, value in enumerate(flow_unit) if value < flow_bound),
            (idx for idx, value in enumerate(density_unit) if value < density_bound))))

        if len(zero_row_id) > 0:
            if len(flow_unit) == rest_flow_df.shape[0]:
                flow_unit[zero_row_id] = rest_flow_df.iloc[zero_row_id].mean(axis=1)
                speed_unit[zero_row_id] = 1
            elif len(flow_unit) > rest_flow_df.shape[0]:
                zero_idx_list = [(idx // rest_flow_df.shape[0], idx % rest_flow_df.shape[0]) for idx in zero_row_id]
                for idx, (col_idx, row_idx) in enumerate(zero_idx_list):
                    flow_unit[zero_row_id[idx]] = rest_flow_df.drop(columns=[f'flow_{col_idx + 1}']).iloc[row_idx].mean()
                    speed_unit[zero_row_id[idx]] = 1

    with np.errstate(divide='ignore', invalid='ignore'):
        multiply = np.multiply(flow_unit, 1 / speed_unit)

    sum_flow = flow_unit.sum()
    sum_product = np.nansum(multiply)

    avg_speed = sum_flow / sum_product
    return avg_speed


def plot_within_day(traffic_day, plot_date, directory, file_name, VDS_num, Day, aggregate_timeframe, date, lane_num):
    fig, ax = plt.subplots(1, 2, figsize=(18, 6))
    fig.suptitle(f'Traffic State within a Day using {directory} data(Date: {file_name[8:-5]}({Day}))', fontsize=18)
    ax[0].plot(plot_date, traffic_day['flow'], color='tab:blue')

    x_ticks = range(0, 1440, 60)
    x_labels = range(0, 24, 1)
    ax[0].set_xticks(ticks=x_ticks, labels=x_labels, fontsize=10)
    ax[0].locator_params(axis='x', nbins=25)

    ax[0].set_title(f'Average Flow and Speed over time (aggregated by every {aggregate_timeframe} min)', fontsize=13)
    ax[0].set_ylabel('Flow rates (vphpl)', color='tab:blue', fontsize=12)
    ax[0].tick_params(axis='y', labelcolor='tab:blue')
    ax[0].set_xlabel('Time (hr)', fontsize=12)
    ax[0].set_ylim(0, 2500)
    ax[0].set_yticks(range(0, 2600, 200))

    ax2 = ax[0].twinx()
    ax2.plot(plot_date, traffic_day['speed'], color='tab:red')
    ax2.tick_params(axis='y', labelcolor='tab:red')
    ax2.set_ylim(0, 100)
    ax2.set_yticks(range(0, 100, 10))
    ax2.set_ylabel('Speed (mph)', color='tab:red', fontsize=12)

    ax[1].scatter(traffic_day['flow'], traffic_day['time'])
    ax[1].set_title('z over q', fontsize=13)
    ax[1].set_ylabel('z (min/mile)', fontsize=12)
    ax[1].set_xlabel('q (vphpl)', fontsize=12)
    ax[1].set_yticks(range(0, 8))

    ax[0].grid(True)
    ax[1].grid(True)

    directory_path = f"./02 fig/11 Unit time/{VDS_num}"
    os.makedirs(directory_path, exist_ok=True)
    plt.savefig(f'{directory_path}/{date}_{lane_num}.png')
    plt.close()


def plot_within_day_flow(traffic_day, plot_date, directory, file_name, VDS_num, Day, aggregate_timeframe, date, lane_num):
    fig, ax = plt.subplots(1, 1, figsize=(6, 6))
    color_dict = ['red', 'blue', 'black', 'green', 'yellow', 'purple']

    for idx, lane in enumerate(lane_num):
        ax.plot(plot_date, traffic_day[f'flow_{lane}'], label=f'lane {lane}', linewidth=0.8, color=color_dict[idx])

    x_ticks = range(0, 1440, 60)
    x_labels = range(0, 24, 1)
    ax.set_xticks(ticks=x_ticks, labels=x_labels, fontsize=9)
    ax.locator_params(axis='x', nbins=25)
    ax.legend(fontsize=13)

    ax.set_ylabel('Flow rates (vphpl)', fontsize=13)
    ax.tick_params(axis='y')
    ax.set_xlabel('Time (hour)', fontsize=13)
    ax.set_ylim(0, 3600)
    ax.set_yticks(range(0, 3600, 200))
    ax.grid(True)

    directory_path = os.path.join('./02 fig/11 Unit time_flow', f'{VDS_num}')
    os.makedirs(directory_path, exist_ok=True)
    plt.savefig(f'{directory_path}/{date}_flow_{lane_num}.png')
    plt.close()


def plot_CV_within_day(traffic_within_day, rawdata, date, aggregate_timeframe, VDS_num):
    mean_flow = traffic_within_day['flow']
    cv_flow = traffic_within_day['cv_flow']
    mean_density = traffic_within_day['density']
    cv_density = traffic_within_day['cv_density']
    mean_speed = traffic_within_day['speed']
    cv_speed = traffic_within_day['cv_speed']

    raw_time = [list(rawdata.loc[(rawdata['time_filter'] == idx), 'time']) for idx in traffic_within_day['time_slot']]
    raw_row = [rawdata.index[rawdata['time_slot'] == idx].tolist() for idx in traffic_within_day['time_slot']]
    time_r = [[str(ts) for ts in sublist] for sublist in raw_time]

    for idx, sublist in enumerate(time_r):
        if len(sublist) == 0:
            time_r[idx] = [rawdata.loc[raw_row[idx][0], 'time']]

    time = [str(sublist[0]) for sublist in time_r if sublist]

    fig, ax = plt.subplots(1, 3, figsize=(18, 6))
    ax[0].scatter(mean_flow, cv_flow, s=10)
    ax[0].set_title(f'CV across mean flow within {date} (Aggregated by {aggregate_timeframe}min)', fontsize=15)
    ax[0].set_xlabel('mean flow(vphpl)', fontsize=20)
    ax[0].set_ylabel('CV', fontsize=20)
    ax[0].grid(True)
    ax[0].set_ylim(0, 2)
    ax[0].set_yticks(np.arange(0, 2, 0.2))

    ax[1].scatter(mean_density, cv_density, s=10)
    ax[1].set_title(f'CV across mean density within {date} (Aggregated by {aggregate_timeframe}min)', fontsize=15)
    ax[1].set_xlabel('mean density(vpmpl)', fontsize=20)
    ax[1].set_ylabel('CV', fontsize=20)
    ax[1].grid(True)
    ax[1].set_ylim(0, 2)
    ax[1].set_yticks(np.arange(0, 2, 0.2))

    ax[2].scatter(mean_speed, cv_speed, s=10)
    ax[2].set_title(f'CV across mean speed within {date} (Aggregated by {aggregate_timeframe}min)', fontsize=15)
    ax[2].set_xlabel('mean speed(mph)', fontsize=20)
    ax[2].set_ylabel('CV', fontsize=20)
    ax[2].grid(True)
    ax[2].set_ylim(0, 2)
    ax[2].set_yticks(np.arange(0, 2, 0.2))
    ax[2].set_xlim(0, 80)

    plot2_dir = os.path.join('./02 fig/03_2 CV_across_flow', f'{VDS_num}', f'{aggregate_timeframe}min')
    os.makedirs(plot2_dir, exist_ok=True)
    plt.savefig(os.path.join(plot2_dir, f'CV across mean_{date}.png'))


# ══════════════════════════════════════════════════════════════
# FROM data_io.py — dead functions
# ══════════════════════════════════════════════════════════════


def highfreeflowspeed_conversion(df, lane_num_list, freeflowspeed):
    """Clip speeds above free-flow threshold."""
    for lane in lane_num_list:
        speed_col = f'speed_{lane}'
        df[speed_col] = df[speed_col].clip(upper=freeflowspeed)
    return df




def load_or_aggregate(base_path, vds_id, date_str, cfg, agg_timeframe=5):
    """Cache loader — replaced by other code path."""
    import os
    fname = f"traffic_{vds_id}_{date_str}_{agg_timeframe}min.parquet"
    fpath = os.path.join(base_path, fname)
    if os.path.exists(fpath):
        return pd.read_parquet(fpath)
    return None


# ══════════════════════════════════════════════════════════════
# FROM bpr_fitting.py — dead functions
# ══════════════════════════════════════════════════════════════


def v3_lnN_vs_lnttau(x, y, alpha=1.0):
    """BPR v3 transform — not in LINEAR_REGISTRY_BPR."""
    import numpy as np
    return alpha * np.log(x + 1)


def v4_speeddep_lnN_vs_lnttau(x, y, v_free=65.0, alpha=1.0):
    """BPR v4 transform — alias for v2, not in registry."""
    import numpy as np
    return alpha * np.log(x + 1) * (v_free / 65.0)


def r2_score(y_true, y_pred):
    """Standalone R² — never called (statsmodels used instead)."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - ss_res / ss_tot


def rmse(y_true, y_pred):
    """RMSE — never called."""
    return np.sqrt(np.mean((y_true - y_pred) ** 2))


# ══════════════════════════════════════════════════════════════
# FROM classification.py — dead helpers
# ══════════════════════════════════════════════════════════════

import pandas as pd


def _divisions_from_segment_mask(df, is_peak_seg_bool):
    """
    Map a per-segment boolean (True=peak) to per-row 'division' labels:
    0 for off-peak rows; 1..K for contiguous peak blocks.
    """
    is_peak_rows = (
        pd.Series(is_peak_seg_bool, index=is_peak_seg_bool.index)
          .reindex(df["segment"])
          .to_numpy()
    )
    starts = (is_peak_rows) & (~pd.Series(is_peak_rows).shift(fill_value=False).to_numpy())
    div = starts.cumsum()
    div[~is_peak_rows] = 0
    return div.astype(np.int32)


def _renumber_by_contiguity(div):
    """
    Renumber any positive divisions to 1..K by contiguity; zeros stay zero.
    """
    is_peak = div > 0
    starts = (is_peak) & (~pd.Series(is_peak).shift(fill_value=False).to_numpy())
    new_ids = starts.cumsum()
    new_ids[~is_peak] = 0
    return new_ids.astype(np.int32)


# ══════════════════════════════════════════════════════════════
# FROM segmentation.py — dead function
# ══════════════════════════════════════════════════════════════


def assign_fixedtime_peaks(df, peak_hours_morning=(6, 10), peak_hours_afternoon=(15, 19)):
    """Fixed-time peak detection — never called."""
    df = df.copy()
    df['period'] = 'off-peak'
    morning_mask = (df['time_slot'] / 60).between(peak_hours_morning[0], peak_hours_morning[1])
    afternoon_mask = (df['time_slot'] / 60).between(peak_hours_afternoon[0], peak_hours_afternoon[1])
    df.loc[morning_mask, 'period'] = 'morning-peak'
    df.loc[afternoon_mask, 'period'] = 'afternoon-peak'
    df['is_peak'] = 0
    df.loc[df['period'] != 'off-peak', 'is_peak'] = 1
    return df


# ══════════════════════════════════════════════════════════════
# FROM plotting.py — dead functions
# ══════════════════════════════════════════════════════════════


def PELT_plot_all(df, date, VDS_num, aggregate_timeframe, peak_list_PELT, peak_list_RDP, peak_list_PELT_direct, purpose):
    """PELT vs RDP comparison — never called."""
    from matplotlib.gridspec import GridSpec  # already imported at top but just in case

    time_slot_hour = df['time_slot'] / 60
    date_v2 = f'{date[2:4]}/{date[4:6]}/20{date[0:2]}'

    title_name = {'RDP': f'Congestion Period Detection from PELT and RDP (VDS: {VDS_num}, Date: {date_v2})',
                  'PELT_direct': f'Comparison of Proposed and Previous Approaches (VDS: {VDS_num}, Date: {date_v2})'}

    label_name = {'RDP': ['PELT-detected congestion boundaries', 'RDP-detected congestion boundaries'],
                  'PELT_direct': ['Proposed method: congested period boundary', 'Previous method: congested period boundary']}

    fig, ax1 = plt.subplots(figsize=(12, 5))

    ax1.set_xlabel('Time (Hours)', fontsize=16)
    ax1.set_ylabel('Speed (mph)', fontsize=16, color='green')
    ax1.set_title(title_name[purpose], fontsize=18)
    ax1.grid(True)
    ax1.set_xlim(0, 24 + .1)
    ax1.set_xticks(np.arange(0, 25, 1))

    select_date_PELT = peak_list_PELT.loc[(peak_list_PELT['date'] == int(date)), 'peak_list'].iloc[0]
    select_date_RDP = peak_list_RDP.loc[(peak_list_RDP['date'] == int(date)), 'peak_list'].iloc[0]

    if purpose == 'RDP':
        select_date_purpose = select_date_RDP
    elif purpose == 'PELT_direct':
        select_date_purpose = peak_list_PELT_direct.loc[(peak_list_PELT_direct['date'] == int(date)), 'peak_list'].iloc[0]

    for element in select_date_PELT:
        if len(element) == 0:
            continue
        if element['idx'] > 0:
            s_hours, s_minutes = map(int, element['start'].split(':'))
            s_total_hours = s_hours + s_minutes / 60
            label = label_name[purpose][0] if element['idx'] == 1 else ''
            ax1.axvline(x=s_total_hours, color='red', linewidth=2.5, linestyle='-', label=label)
            e_hours, e_minutes = map(int, element['end'].split(':'))
            e_total_hours = e_hours + e_minutes / 60
            ax1.axvline(x=e_total_hours, color='red', linewidth=2.5, linestyle='-')

    for element in select_date_purpose:
        if len(element) == 0:
            continue
        if element['idx'] > 0:
            s_hours, s_minutes = map(int, element['start'].split(':'))
            s_total_hours = s_hours + s_minutes / 60
            label = label_name[purpose][1] if element['idx'] == 1 else ''
            ax1.axvline(x=s_total_hours, color='purple', linewidth=2.5, linestyle='--', label=label)
            e_hours, e_minutes = map(int, element['end'].split(':'))
            e_total_hours = e_hours + e_minutes / 60
            ax1.axvline(x=e_total_hours, color='purple', linewidth=2.5, linestyle='--')

    ax1.plot(time_slot_hour, df['speed'], color='green', linewidth=1, label='Speed')
    ax1.set_ylim(0, 85)
    ax1.set_yticks(np.arange(0, 85 + 1, 10))
    ax1.tick_params(axis='y', colors='black')
    ax1.spines['left'].set_color('green')

    time_slot_hour_re = [0] + time_slot_hour.to_list()
    cumsum_speed_re = [0] + df['cumsum_speed'].to_list()

    ax2 = ax1.twinx()
    ax2.plot(time_slot_hour_re, cumsum_speed_re, color='blue', linewidth=1, label='Cumulative speed')
    ax2.set_ylabel('Cumulative Speed (miles)', fontsize=16, color='blue')
    ax2.set_ylim(0, 1600)
    ax2.set_yticks(np.arange(0, 1600 + 1, 200))
    ax2.tick_params(axis='y', colors='blue')
    ax2.spines['right'].set_color('blue')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=15)

    fig.tight_layout()
    plt.savefig(f'./02 fig/16 PELT/All_{purpose}_{VDS_num}_{date}_{aggregate_timeframe}.png')


def draw_fixed_band(ax, meta):
    """Simpleband band drawing — never called."""
    handles, labels = [], []
    rule = meta.get('rule', 'both')
    start_band = meta.get('start_band')
    end_band = meta.get('end_band')

    if start_band is not None and rule in ['start_only', 'both']:
        s_low, s_high = start_band
        if pd.notna(s_low) and pd.notna(s_high):
            ax.axhspan(s_low, s_high, color='orange', alpha=0.20, zorder=1)

    if end_band is not None and rule in ['end_only', 'both']:
        e_low, e_high = end_band
        if pd.notna(e_low) and pd.notna(e_high):
            ax.axhspan(e_low, e_high, color='orange', alpha=0.20, zorder=1)

    if rule == 'start_only' and start_band is not None:
        label = 'Start Time Band'
    elif rule == 'end_only' and end_band is not None:
        label = 'End Time Band'
    elif rule == 'both' and (start_band is not None or end_band is not None):
        label = 'Start/End Time Bands'
    else:
        label = None

    if label is not None:
        handles.append(plt.Line2D([0], [0], color='orange', linewidth=6, alpha=0.2))
        labels.append(label)

    return handles, labels


def draw_dual_hist(data, **kwargs):
    """Histogram helper — never called (used by dead plot_start_end_histograms)."""
    if data.empty:
        return
    period = data['period'].iloc[0]
    if period == 'morning-peak':
        x_range = (0, 12)
    else:
        x_range = (12, 24)
    local_bin_size = 0.5
    bins = np.arange(x_range[0], x_range[1] + local_bin_size, local_bin_size)

    sns.histplot(data=data, x='start_hour', bins=bins, color='#4C72B0', alpha=0.55, label='Start Hour', edgecolor='white', linewidth=0.5)
    sns.histplot(data=data, x='end_hour', bins=bins, color='#C44E52', alpha=0.55, label='End Hour', edgecolor='white', linewidth=0.5)

    ax = plt.gca()
    ax.set_xlim(x_range)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))


def plot_start_end_boxplots(df_peaks, save_path=None, vds_id=None, cfg=None, showfliers=True, figsize=(14, 10)):
    """Start/end time distributions — imported but commented out in recurrent.py."""
    plot_df = df_peaks[df_peaks['is_peak'] == 1].copy()
    plot_df['dayofweek'] = pd.Categorical(plot_df['dayofweek'], categories=DAY_ORDER, ordered=True)

    fig, axes = plt.subplots(2, 2, figsize=figsize, sharex=True)
    hour_types = ['start_hour', 'end_hour']
    periods = ['morning-peak', 'afternoon-peak']

    for i, hour_col in enumerate(hour_types):
        for j, period in enumerate(periods):
            ax = axes[i, j]
            sub = plot_df[plot_df['period'] == period].copy()
            sns.boxplot(data=sub, x='dayofweek', y=hour_col, order=DAY_ORDER, ax=ax, showfliers=showfliers)
            if i == 0:
                ax.set_title(f"{'Morning' if j == 0 else 'Afternoon'} Peak", fontsize=14, fontweight='bold')
            ax.set_ylabel('Start Hour' if (j == 0 and i == 0) else ('End Hour' if j == 0 else ''))
            ax.set_xlabel('Day of Week' if i == 1 else '')
            ax.set_ylim((-0.5, 13) if period == 'morning-peak' else (11, 25))
            ax.yaxis.set_major_locator(ticker.MultipleLocator(1))

    from .plotting import _vds_label_dict
    fig.suptitle(f"Distribution of Peak Start and End Times by Day of Week (VDS: {_vds_label_dict(cfg).get(str(vds_id), str(vds_id))})", fontsize=16, y=1.02)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def plot_start_end_histograms(df_peaks, bin_size=None, save_path=None, vds_id=None, cfg=None, figsize=(14, 20)):
    """Start/end time histograms — imported but commented out in recurrent.py."""
    from .plotting import _vds_label_dict, DAY_ORDER

    plot_df = df_peaks.copy()
    plot_df['dayofweek'] = pd.Categorical(plot_df['dayofweek'], categories=DAY_ORDER, ordered=True)

    g = sns.FacetGrid(
        plot_df,
        row='dayofweek', col='period',
        col_order=['morning-peak', 'afternoon-peak'],
        sharey=False, sharex=False,
        height=2.5, aspect=2.8,
    )

    g.map_dataframe(draw_dual_hist)

    top_left_ax = g.axes[0, 0]
    handles, labels = top_left_ax.get_legend_handles_labels()
    if handles:
        top_left_ax.legend(handles, labels, fontsize=11, frameon=True, loc='upper right', facecolor='white', framealpha=1)

    g.set_titles(row_template='{row_name}', col_template='{col_name} Peak')
    g.set_axis_labels('Hour of Day', 'Frequency (Count)')
    plt.subplots_adjust(top=0.94, hspace=0.4, wspace=0.15)
    g.fig.suptitle(f"Histogram of Peak Start & End Hours (VDS: {_vds_label_dict(cfg).get(str(vds_id), str(vds_id))})", fontsize=18, fontweight='bold')

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def plot_within_flowspeed_day(traffic_day, plot_date, directory, file_name, VDS_num, Day, aggregate_timeframe, date, lane_num):
    """Within-day flow+speed time series — never called."""
    fig, ax = plt.subplots(1, 1, figsize=(9, 6))
    fig.suptitle(f'Traffic State within a Day using {directory} data(Date: {file_name[8:-5]}({Day}))', fontsize=18)
    ax.plot(plot_date, traffic_day['flow'], color='tab:blue')

    x_ticks = range(0, 1500, 60)
    x_labels = range(0, 25, 1)
    ax.set_xticks(ticks=x_ticks, labels=x_labels, fontsize=10)
    ax.locator_params(axis='x', nbins=25)

    ax.set_title(f'Average Flow and Speed over time (aggregated by every {aggregate_timeframe} min)', fontsize=13)
    ax.set_ylabel('Flow rates (vphpl)', color='tab:blue', fontsize=12)
    ax.tick_params(axis='y', labelcolor='tab:blue')
    ax.set_xlabel('Time (hr)', fontsize=12)
    ax.set_ylim(0, 2500)
    ax.set_yticks(range(0, 2600, 200))

    ax2 = ax.twinx()
    ax2.plot(plot_date, traffic_day['speed'], color='tab:red')
    ax2.set_ylabel('Average Speed (mph)', color='tab:red', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='tab:red')
    ax2.set_ylim(0, 120)
    ax2.set_yticks(range(0, 130, 10))

    ax.grid(True)

    directory_path = f"./02 fig/15 Unit time_flowspeed_all/{VDS_num}"
    os.makedirs(directory_path, exist_ok=True)
    plt.savefig(f'{directory_path}/{date}_{lane_num}.png')
    plt.close()


def plot_within_densityspeed_day(traffic_day, plot_date, directory, file_name, VDS_num, Day, aggregate_timeframe, date, lane_num):
    """Within-day density+speed time series — never called."""
    fig, ax = plt.subplots(1, 1, figsize=(9, 6))
    fig.suptitle(f'Traffic State within a Day using {directory} data(Date: {file_name[8:-5]}({Day}))', fontsize=18)
    ax.plot(plot_date, traffic_day['density'], color='tab:blue')

    x_ticks = range(0, 1500, 60)
    x_labels = range(0, 25, 1)
    ax.set_xticks(ticks=x_ticks, labels=x_labels, fontsize=10)
    ax.locator_params(axis='x', nbins=25)

    ax.set_title(f'Average Flow and Speed over time (aggregated by every {aggregate_timeframe} min)', fontsize=13)
    ax.set_ylabel('Densities (vpmpl)', color='tab:blue', fontsize=12)
    ax.tick_params(axis='y', labelcolor='tab:blue')
    ax.set_xlabel('Time (hr)', fontsize=12)
    ax.set_ylim(0, 80)
    ax.set_yticks(range(0, 85, 5))

    ax2 = ax.twinx()
    ax2.plot(plot_date, traffic_day['speed'], color='tab:red')
    ax2.set_ylabel('Average Speed (mph)', color='tab:red', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='tab:red')
    ax2.set_ylim(0, 120)
    ax2.set_yticks(range(0, 130, 10))

    ax.grid(True)

    directory_path = f"./02 fig/15 Unit time_densityspeed_all/{VDS_num}"
    os.makedirs(directory_path, exist_ok=True)
    plt.savefig(f'{directory_path}/{date}_{lane_num}.png')
    plt.close()


def generate_config_name(config):
    """Config name generator — duplicate in recurrent.py, never called from pipeline."""
    m_rm = config['recurrent_method']
    si = config['recurrent_method_params'][m_rm]

    def fmt_q(val):
        return int(val * 100) if val is not None else ""

    if m_rm == 'shortest_interval':
        m_sel = si['selector_by_period']['morning-peak']
        m_sq = f"s{fmt_q(si['start_q_by_period']['morning-peak'])}"
        m_eq = f"e{fmt_q(si['end_q_by_period']['morning-peak'])}"
        a_sel = si['selector_by_period']['afternoon-peak']
        a_eq = fmt_q(si['end_q_by_period']['afternoon-peak'])
    elif m_rm == 'simpleband':
        m_sel = si['selector_by_period']['morning-peak']
        m_sq = f"s{si['start_bandwidth_minutes_by_period']['morning-peak']}"
        m_eq = f"s{si['end_bandwidth_minutes_by_period']['morning-peak']}"
        a_sel = si['selector_by_period']['afternoon-peak']
        a_eq = f"s{si['end_bandwidth_minutes_by_period']['afternoon-peak']}"
    elif m_rm == 'RDP_v':
        m_sel = si['selector_by_period']['morning-peak']
        m_sq = f"s{si['epsilon_start_by_period']['morning-peak']}_s{si['epsilon_end_by_period']['morning-peak']}"
        a_sel = si['selector_by_period']['afternoon-peak']
        a_eq = f"s{si['epsilon_start_by_period']['afternoon-peak']}_s{si['epsilon_end_by_period']['afternoon-peak']}"

    name = (
        f"{m_rm}_"
        f"morning_{m_sel}_{m_sq}_"
        f"afternoon_{a_sel}{a_eq}"
    )
    return name


# ══════════════════════════════════════════════════════════════
# FROM recurrent.py — dead function
# ══════════════════════════════════════════════════════════════

# (generate_config_name from recurrent.py already included above from plotting.py)