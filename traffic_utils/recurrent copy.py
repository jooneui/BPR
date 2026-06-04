from pathlib import Path
import copy
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D

# cross-module imports
from .plotting import (
    annotate_segment_selection_for_plot,
    draw_fixed_band,
    plot_common_points,
    plot_start_end_boxplots,
    plot_start_end_histograms,
)
from .bpr_fitting import build_file_path


DAY_ORDER = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
ALL_PERIODS = ['morning-peak', 'afternoon-peak']


def time_to_fractional_hour(t_str, default_val=np.nan):
    if pd.isna(t_str) or t_str == '-':
        return default_val
    try:
        h, m = map(int, str(t_str).split(':'))
        return h + m / 60.0
    except Exception:
        return default_val


def prepare_peak_table(config_rc, vds_id, all_periods):
    cfg = copy.deepcopy(config_rc)
    cfg['VDS_num'] = str(vds_id)
    df_raw = pd.read_csv(build_file_path(cfg))

    df_raw['date'] = df_raw['date'].astype(str)
    df_raw['date_dt'] = pd.to_datetime(df_raw['date'], format='%y%m%d', errors='coerce')
    df_raw['dayofweek'] = df_raw['date_dt'].dt.strftime('%a')
    min_date = df_raw['date_dt'].min()

    df_raw['start_hour'] = df_raw['start_time'].apply(time_to_fractional_hour)
    df_raw['end_hour'] = df_raw['end_time'].apply(time_to_fractional_hour)

    all_dates = np.sort(df_raw['date_dt'].dropna().unique())
    template = pd.MultiIndex.from_product([all_dates, all_periods], names=['date_dt', 'period']).to_frame(index=False)

    merge_cols = [c for c in df_raw.columns if c not in ['dayofweek']]
    df_peaks = pd.merge(template, df_raw[merge_cols], on=['date_dt', 'period'], how='left')
    df_peaks['dayofweek'] = df_peaks['date_dt'].dt.strftime('%a')
    df_peaks['week_num'] = ((df_peaks['date_dt'] - min_date).dt.days // 7) + 1
    df_peaks['is_peak'] = np.where(df_peaks['start_hour'].isna() | df_peaks['end_hour'].isna(), -5, 1)

    df_peaks.loc[(df_peaks['is_peak'] == -5) & (df_peaks['period'] == 'morning-peak'), ['start_hour', 'end_hour']] = 0.0
    df_peaks.loc[(df_peaks['is_peak'] == -5) & (df_peaks['period'] == 'afternoon-peak'), ['start_hour', 'end_hour']] = 12.0
    df_peaks['vds_id'] = str(vds_id)
    return df_peaks


def _normalize_period_mapping(value, periods=None, default=None):
    periods = periods or ALL_PERIODS
    if isinstance(value, dict):
        return {per: value.get(per, default) for per in periods}
    return {per: value if value is not None else default for per in periods}


def _period_bounds(period):
    if period == 'morning-peak':
        return 0.0, 12.0
    if period == 'afternoon-peak':
        return 12.0, 24.0
    raise ValueError(f'Unknown period: {period}')


def _dominant_fixed_band(values, bandwidth_minutes, period):
    values = pd.Series(values).dropna().astype(float)
    if len(values) == 0 or bandwidth_minutes is None or pd.isna(bandwidth_minutes):
        return np.nan, np.nan, None, None

    bandwidth = float(bandwidth_minutes) / 60.0
    period_start, period_end = _period_bounds(period)
    edges = np.arange(period_start, period_end + bandwidth + 1e-9, bandwidth)
    if len(edges) < 2:
        return np.nan, np.nan, None, None

    counts, bin_edges = np.histogram(values, bins=edges)
    if len(counts) == 0 or counts.max() <= 0:
        return np.nan, np.nan, None, counts
    idx = int(np.argmax(counts))
    return float(bin_edges[idx]), float(bin_edges[idx + 1]), idx, counts


def _build_bound_mask(series, band, mode='two_sided', lower_allowance_minutes=None, upper_allowance_minutes=None, **_ignored):
    low, high = band
    if pd.isna(low) or pd.isna(high):
        return pd.Series(False, index=series.index)
    mode = mode or 'two_sided'
    if mode == 'two_sided':
        return series.between(float(low), float(high), inclusive='left')
    if mode == 'upper_only':
        return series <= float(high)
    if mode == 'lower_only':
        return series >= float(low)
    raise ValueError(f'Unknown bound mode: {mode}')


def classify_facet_fixed_band(
    facet_df,
    period,
    bandwidth=None,
    band_rules=None,
    selector_by_period=None,
    start_bandwidth_minutes_by_period=None,
    end_bandwidth_minutes_by_period=None,
    start_bound_mode_by_period=None,
    end_bound_mode_by_period=None,
    **_ignored,
):
    out = facet_df.copy()
    out['recurrent_band'] = False
    out['excluded_band'] = False

    selector_map = _normalize_period_mapping(selector_by_period or band_rules or {'morning-peak': 'both', 'afternoon-peak': 'both'})
    if start_bandwidth_minutes_by_period is None:
        start_bandwidth_minutes_by_period = bandwidth if bandwidth is not None else 30
    if end_bandwidth_minutes_by_period is None:
        end_bandwidth_minutes_by_period = bandwidth if bandwidth is not None else 30

    start_bw_map = _normalize_period_mapping(start_bandwidth_minutes_by_period, default=30)
    end_bw_map = _normalize_period_mapping(end_bandwidth_minutes_by_period, default=30)
    start_mode_map = _normalize_period_mapping(start_bound_mode_by_period, default='two_sided')
    end_mode_map = _normalize_period_mapping(end_bound_mode_by_period, default='two_sided')

    rule = selector_map.get(period, 'both')
    start_bw = start_bw_map.get(period)
    end_bw = end_bw_map.get(period)
    start_mode = start_mode_map.get(period, 'two_sided')
    end_mode = end_mode_map.get(period, 'two_sided')

    peak_mask = (out['is_peak'] == 1) & out['start_hour'].notna() & out['end_hour'].notna()
    meta = {
        'rule': rule,
        'sequence': rule,
        'start_band': None,
        'end_band': None,
        'start_mode': start_mode,
        'end_mode': end_mode,
        'start_bandwidth_minutes': start_bw,
        'end_bandwidth_minutes': end_bw,
    }
    if peak_mask.sum() == 0:
        return out, meta

    def apply_start(mask_source):
        low, high, idx, counts = _dominant_fixed_band(out.loc[mask_source, 'start_hour'], start_bw, period)
        mask = _build_bound_mask(out['start_hour'], (low, high), mode=start_mode)
        return mask, (low, high), idx, counts

    def apply_end(mask_source):
        low, high, idx, counts = _dominant_fixed_band(out.loc[mask_source, 'end_hour'], end_bw, period)
        mask = _build_bound_mask(out['end_hour'], (low, high), mode=end_mode)
        return mask, (low, high), idx, counts

    start_mask, start_band, start_idx, start_counts = apply_start(peak_mask)
    end_mask, end_band, end_idx, end_counts = apply_end(peak_mask)
    recurrent_mask = pd.Series(False, index=out.index)

    if rule == 'start_only':
        recurrent_mask = peak_mask & start_mask
    elif rule == 'end_only':
        recurrent_mask = peak_mask & end_mask
    elif rule == 'both':
        if period == 'morning-peak':
            primary_mask = peak_mask & start_mask
            meta['sequence'] = 'start_then_end'
            if primary_mask.any():
                end_mask, end_band, end_idx, end_counts = apply_end(primary_mask)
                recurrent_mask = primary_mask & end_mask
        else:
            primary_mask = peak_mask & end_mask
            meta['sequence'] = 'end_then_start'
            if primary_mask.any():
                start_mask, start_band, start_idx, start_counts = apply_start(primary_mask)
                recurrent_mask = primary_mask & start_mask
    else:
        raise ValueError(f'Unknown selector: {rule}')

    recurrent_mask = recurrent_mask.fillna(False)
    excluded_mask = peak_mask & ~recurrent_mask
    out.loc[recurrent_mask, 'recurrent_band'] = True
    out.loc[excluded_mask, 'excluded_band'] = True

    meta.update({
        'start_band': start_band,
        'end_band': end_band,
        'start_idx': start_idx,
        'end_idx': end_idx,
        'start_counts': start_counts,
        'end_counts': end_counts,
    })
    return out, meta



import ruptures as rpt
from pathlib import Path


def normalize_period_mapping(value, periods=None, default=None):
    return _normalize_period_mapping(value, periods=periods, default=default)


def format_pct(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return 'na'
    return f"{int(round(float(value) * 100)):02d}"


def shortest_coverage_interval(values, coverage):
    values = np.sort(pd.Series(values).dropna().astype(float).to_numpy())
    n = len(values)
    if n == 0 or coverage is None or pd.isna(coverage):
        return np.nan, np.nan
    k = max(1, int(math.ceil(float(coverage) * n)))
    if k >= n:
        return float(values[0]), float(values[-1]) + 1e-9
    best_i, best_width = 0, np.inf
    for i in range(0, n - k + 1):
        width = values[i + k - 1] - values[i]
        if width < best_width:
            best_width = width
            best_i = i
    return float(values[best_i]), float(values[best_i + k - 1]) + 1e-9


def build_bound_mask(series, band, mode='two_sided', lower_allowance_minutes=None, upper_allowance_minutes=None, **_ignored):
    return _build_bound_mask(series, band, mode=mode)


def classify_facet_shortest_interval(
    facet_df,
    period,
    selector_by_period=None,
    start_q_by_period=None,
    end_q_by_period=None,
    coverage_by_period=None,
    start_bound_mode_by_period=None,
    end_bound_mode_by_period=None,
    **_ignored,
):
    out = facet_df.copy()
    out['recurrent_band'] = False
    out['excluded_band'] = False

    selector_map = normalize_period_mapping(selector_by_period or {'morning-peak': 'both', 'afternoon-peak': 'both'})
    coverage_map = normalize_period_mapping(coverage_by_period, default=None)
    start_q_map = normalize_period_mapping(start_q_by_period, default=None)
    end_q_map = normalize_period_mapping(end_q_by_period, default=None)
    start_mode_map = normalize_period_mapping(start_bound_mode_by_period, default='two_sided')
    end_mode_map = normalize_period_mapping(end_bound_mode_by_period, default='two_sided')

    rule = selector_map.get(period, 'both')
    start_q = start_q_map.get(period)
    end_q = end_q_map.get(period)
    if start_q is None:
        start_q = coverage_map.get(period)
    if end_q is None:
        end_q = coverage_map.get(period)
    start_mode = start_mode_map.get(period, 'two_sided')
    end_mode = end_mode_map.get(period, 'two_sided')

    peak_mask = (out['is_peak'] == 1) & out['start_hour'].notna() & out['end_hour'].notna()
    meta = {
        'rule': rule,
        'sequence': rule,
        'start_band': None,
        'end_band': None,
        'start_mode': start_mode,
        'end_mode': end_mode,
        'start_q': start_q,
        'end_q': end_q,
    }
    if peak_mask.sum() == 0:
        return out, meta

    def apply_start(mask_source):
        low, high = shortest_coverage_interval(out.loc[mask_source, 'start_hour'], start_q)
        mask = build_bound_mask(out['start_hour'], (low, high), mode=start_mode)
        return mask, (low, high)

    def apply_end(mask_source):
        low, high = shortest_coverage_interval(out.loc[mask_source, 'end_hour'], end_q)
        mask = build_bound_mask(out['end_hour'], (low, high), mode=end_mode)
        return mask, (low, high)

    start_mask, start_band = apply_start(peak_mask)
    end_mask, end_band = apply_end(peak_mask)
    recurrent_mask = pd.Series(False, index=out.index)

    if rule == 'start_only':
        recurrent_mask = peak_mask & start_mask
    elif rule == 'end_only':
        recurrent_mask = peak_mask & end_mask
    elif rule == 'both':
        if period == 'morning-peak':
            primary_mask = peak_mask & start_mask
            meta['sequence'] = 'start_then_end'
            if primary_mask.any():
                end_mask, end_band = apply_end(primary_mask)
                recurrent_mask = primary_mask & end_mask
        else:
            primary_mask = peak_mask & end_mask
            meta['sequence'] = 'end_then_start'
            if primary_mask.any():
                start_mask, start_band = apply_start(primary_mask)
                recurrent_mask = primary_mask & start_mask
    else:
        raise ValueError(f'Unknown selector: {rule}')

    recurrent_mask = recurrent_mask.fillna(False)
    excluded_mask = peak_mask & ~recurrent_mask
    out.loc[recurrent_mask, 'recurrent_band'] = True
    out.loc[excluded_mask, 'excluded_band'] = True

    meta.update({'start_band': start_band, 'end_band': end_band})
    return out, meta


def _period_tag(period):
    return 'morning' if period == 'morning-peak' else 'afternoon'


def _selector_short(selector):
    return {'start_only': 's', 'end_only': 'e', 'both': 'b'}.get(selector, str(selector)[0])


def generate_config_name(config):
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
    else:
        return m_rm

    return (
        f"{m_rm}_"
        f"morning_{m_sel}_{m_sq}_"
        f"afternoon_{a_sel}{a_eq}"
    )


def build_recurrent_output_tag(config_rc):
    method = config_rc.get('recurrent_method', 'simpleband')
    params = config_rc.get('recurrent_method_params', {}).get(method, {})
    if method == 'simpleband':
        selector = normalize_period_mapping(params.get('selector_by_period', {'morning-peak': 'both', 'afternoon-peak': 'both'}))
        start_bw = normalize_period_mapping(params.get('start_bandwidth_minutes_by_period', 30), default=30)
        end_bw = normalize_period_mapping(params.get('end_bandwidth_minutes_by_period', 30), default=30)
        start_mode = normalize_period_mapping(params.get('start_bound_mode_by_period', 'two_sided'), default='two_sided')
        end_mode = normalize_period_mapping(params.get('end_bound_mode_by_period', 'two_sided'), default='two_sided')
        parts = ['simpleband']
        for per in ALL_PERIODS:
            tag = _period_tag(per)
            sel = selector.get(per)
            if sel == 'start_only':
                parts.append(f"{tag}_start{int(start_bw.get(per))}_{start_mode.get(per)}")
            elif sel == 'end_only':
                parts.append(f"{tag}_end{int(end_bw.get(per))}_{end_mode.get(per)}")
            elif sel == 'both':
                parts.append(f"{tag}_both_s{int(start_bw.get(per))}_{start_mode.get(per)}_e{int(end_bw.get(per))}_{end_mode.get(per)}")
            else:
                parts.append(f"{tag}_{sel}")
        return '_'.join(parts)
    if method == 'shortest_interval':
        selector = normalize_period_mapping(params.get('selector_by_period', {'morning-peak': 'both', 'afternoon-peak': 'both'}))
        start_q = normalize_period_mapping(params.get('start_q_by_period', None), default=None)
        end_q = normalize_period_mapping(params.get('end_q_by_period', None), default=None)
        coverage = normalize_period_mapping(params.get('coverage_by_period', None), default=None)
        start_mode = normalize_period_mapping(params.get('start_bound_mode_by_period', 'two_sided'), default='two_sided')
        end_mode = normalize_period_mapping(params.get('end_bound_mode_by_period', 'two_sided'), default='two_sided')
        parts = ['shortestinterval']
        for per in ALL_PERIODS:
            tag = _period_tag(per)
            sel = selector.get(per)
            sq = start_q.get(per) if start_q.get(per) is not None else coverage.get(per)
            eq = end_q.get(per) if end_q.get(per) is not None else coverage.get(per)
            if sel == 'start_only':
                parts.append(f"{tag}_start{format_pct(sq)}_{start_mode.get(per)}")
            elif sel == 'end_only':
                parts.append(f"{tag}_end{format_pct(eq)}_{end_mode.get(per)}")
            elif sel == 'both':
                parts.append(f"{tag}_both_s{format_pct(sq)}_{start_mode.get(per)}_e{format_pct(eq)}_{end_mode.get(per)}")
            else:
                parts.append(f"{tag}_{sel}")
        return '_'.join(parts)
    if method == 'PELT':
        p = params.get('penalty', 20)
        l = params.get('length_threshold', 4)
        return f'PELT_pen{p}_len{l}'
    return str(method)


def classify_facet_pelt(
    facet_df,
    period,
    penalty=20,
    min_size=2,
    jump=1,
    length_threshold=4,
    **_ignored,
):
    """PELT-based recurrent peak detection per (day-of-week, period) facet.

    Uses ruptures PELT on start_hour and end_hour time series to detect
    structural breakpoints. Weeks in stable segments between breakpoints
    are labelled recurrent; segments shorter than length_threshold are excluded.
    """
    out = facet_df.copy()
    out['recurrent_band'] = False
    out['excluded_band'] = False

    peak_mask = (out['is_peak'] == 1) & out['start_hour'].notna() & out['end_hour'].notna()
    meta = {
        'method': 'PELT',
        'penalty': penalty,
        'min_size': min_size,
        'jump': jump,
        'length_threshold': length_threshold,
        'n_bkpts_start': 0,
        'n_bkpts_end': 0,
        'segments': [],
    }

    if peak_mask.sum() == 0:
        return out, meta

    # Sort by date to get temporal ordering
    out = out.sort_values('date_dt').reset_index(drop=True)
    peak_mask = (out['is_peak'] == 1) & out['start_hour'].notna() & out['end_hour'].notna()

    # Use only peak weeks for PELT
    peak_idx = out.index[peak_mask].to_numpy()
    start_hours = out.loc[peak_mask, 'start_hour'].to_numpy()
    end_hours = out.loc[peak_mask, 'end_hour'].to_numpy()

    if len(start_hours) < 3:  # Too few points for meaningful change point detection
        return out, meta

    # Run PELT on start_hours
    signal_start = start_hours.reshape(-1, 1)
    try:
        algo_start = rpt.Pelt(custom_cost='l2', min_size=min_size, jump=jump).fit(signal_start)
        bkpts_start = algo_start.predict(pen=penalty)
    except Exception:
        bkpts_start = [len(start_hours)]
    # Remove the last breakpoint (always len(n))
    bkpts_start = [b for b in bkpts_start if b < len(start_hours)]
    meta['n_bkpts_start'] = len(bkpts_start)

    # Run PELT on end_hours
    signal_end = end_hours.reshape(-1, 1)
    try:
        algo_end = rpt.Pelt(custom_cost='l2', min_size=min_size, jump=jump).fit(signal_end)
        bkpts_end = algo_end.predict(pen=penalty)
    except Exception:
        bkpts_end = [len(end_hours)]
    bkpts_end = [b for b in bkpts_end if b < len(end_hours)]
    meta['n_bkpts_end'] = len(bkpts_end)

    # Merge breakpoints (union)
    all_bkpts = sorted(set(bkpts_start) | set(bkpts_end))
    # Add 0 and len as boundaries
    boundaries = [0] + all_bkpts + [len(start_hours)]

    # Build segments and label
    segments = []
    for i in range(len(boundaries) - 1):
        seg_start = boundaries[i]
        seg_end = boundaries[i + 1]
        seg_len = seg_end - seg_start
        segments.append({
            'start_idx': seg_start,
            'end_idx': seg_end,
            'length': seg_len,
            'retained': seg_len >= length_threshold,
        })
        # Label each observation in this segment
        for j in range(seg_start, seg_end):
            orig_idx = peak_idx[j]
            if seg_len >= length_threshold:
                out.loc[orig_idx, 'recurrent_band'] = True
                out.loc[orig_idx, 'excluded_band'] = False
            else:
                out.loc[orig_idx, 'recurrent_band'] = False
                out.loc[orig_idx, 'excluded_band'] = True

    meta['segments'] = segments
    meta['all_breakpoints'] = all_bkpts
    return out, meta


def draw_pelt_band(ax, meta):
    """Draw PELT segment boundaries as vertical dashed lines on the facet plot."""
    handles, labels = [], []
    if not meta or 'segments' not in meta:
        return handles, labels
    segments = meta.get('segments', [])
    for i, seg in enumerate(segments):
        x_start = seg.get('start_idx', 0)
        x_end = seg.get('end_idx', 0)
        color = 'green' if seg.get('retained', False) else 'grey'
        alpha = 0.15
        ax.axvspan(x_start - 0.5, x_end - 0.5, color=color, alpha=alpha)
    # Draw boundaries as vertical dashed lines
    bkpts = meta.get('all_breakpoints', [])
    for b in bkpts:
        ax.axvline(b - 0.5, color='red', linestyle='--', linewidth=0.8, alpha=0.6)
    from matplotlib.patches import Patch
    handles.append(Patch(facecolor='green', alpha=0.15, label='Recurrent segment'))
    handles.append(Patch(facecolor='grey', alpha=0.15, label='Excluded segment'))
    labels.append('Recurrent segment')
    labels.append('Excluded segment')
    return handles, labels


def _build_simpleband_plot_name(vds_id, config_rc):
    params = config_rc.get('recurrent_method_params', {}).get('simpleband', {})
    start_bw = normalize_period_mapping(params.get('start_bandwidth_minutes_by_period', 30), default=30)
    end_bw   = normalize_period_mapping(params.get('end_bandwidth_minutes_by_period',   30), default=30)
    selector = normalize_period_mapping(params.get('selector_by_period', {'morning-peak': 'both', 'afternoon-peak': 'both'}))
    m_bw = int(start_bw.get('morning-peak', 30))
    a_bw = int(end_bw.get('afternoon-peak', 30))
    # tag summarising selector shorthand per period
    suffix = ''.join(_selector_short(selector[p]) for p in ALL_PERIODS)
    return f'simpleband_{vds_id}_m{m_bw}_a{a_bw}_{suffix}.png'


def _build_shortestinterval_plot_name(vds_id, config_rc):
    params = config_rc.get('recurrent_method_params', {}).get('shortest_interval', {})
    start_q = normalize_period_mapping(params.get('start_q_by_period', None), default=None)
    end_q   = normalize_period_mapping(params.get('end_q_by_period',   None), default=None)
    selector = normalize_period_mapping(params.get('selector_by_period', {'morning-peak': 'both', 'afternoon-peak': 'both'}))
    m_sq = int(start_q.get('morning-peak', 90) * 100) if start_q.get('morning-peak') is not None else 90
    a_eq = int(end_q.get('afternoon-peak', 90) * 100)   if end_q.get('afternoon-peak') is not None else 90
    suffix = ''.join(_selector_short(selector[p]) for p in ALL_PERIODS)
    return f'shortestinterval_{vds_id}_m{m_sq}_a{a_eq}_{suffix}.png'


def plot_recurrent_facets(df_peaks, facet_meta, recurrent_col, excluded_col, draw_band_func, save_path=None, vds_id=None, cfg=None):
    data = annotate_segment_selection_for_plot(df_peaks, cfg, recurrent_col)
    fig, axes = plt.subplots(len(DAY_ORDER), len(ALL_PERIODS), figsize=(16, 22), sharex=False, sharey=False)
    for i, day in enumerate(DAY_ORDER):
        for j, per in enumerate(ALL_PERIODS):
            ax = axes[i, j]
            sub = data[(data['dayofweek'] == day) & (data['period'] == per)].copy()
            point_handles, point_labels = plot_common_points(ax, sub, recurrent_col, excluded_col)
            band_handles, band_labels = draw_band_func(ax, facet_meta.get((day, per), {}))
            handles = point_handles + band_handles
            labels = point_labels + band_labels
            if i == 0:
                ax.set_title(per, fontsize=12, fontweight='bold')
            if j == 0:
                ax.set_ylabel("Time (hour)")
                ax.text(-0.35, 0.5, day, transform=ax.transAxes,
                        rotation=90, va='center', ha='right', fontsize=11, fontweight='bold')
            ax.set_xlabel('Week Number')
            ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
            ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
            if per == 'morning-peak':
                ax.set_ylim(-0.5, 13)
            else:
                ax.set_ylim(11, 24.5)
            if i == 0 and j == 0 and handles:
                ax.legend(handles, labels, loc='upper left', fontsize=9, frameon=True)
    _labels = cfg.get('VDS_label_list', [])
    if isinstance(_labels, dict):
        _label = _labels.get(str(vds_id), str(vds_id))
    else:
        _vlist = [str(v) for v in cfg.get('VDS_list', [])]
        _idx = _vlist.index(str(vds_id)) if str(vds_id) in _vlist else -1
        _label = _labels[_idx] if 0 <= _idx < len(_labels) else str(vds_id)
    title = f"Recurrent Peak Selection ({_label})"
    fig.suptitle(title, fontsize=16)
    fig.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def run_band_recurrent_pipeline(
    config_rc,
    classify_facet_func,
    draw_band_func,
    recurrent_col,
    excluded_col,
    output_tag,
    plot_name_builder,
    save_dir=None,
    interval_bin_size=0.5,
):
    save_dir = Path(save_dir or config_rc.get('rc_save_dir', config_rc.get('save_dir', './02 fig/17 recurrent_checks')))
    save_dir.mkdir(parents=True, exist_ok=True)
    output_dir = Path('.')
    output_dir.mkdir(parents=True, exist_ok=True)

    all_excluded = []
    all_processed = []

    for vds_id in config_rc['VDS_list']:
        print(f'Running recurrent detection for VDS {vds_id} ({output_tag})')
        df_peaks = prepare_peak_table(config_rc, str(vds_id), ALL_PERIODS)
        processed_facets = []
        facet_meta = {}

        for day in DAY_ORDER:
            for per in ALL_PERIODS:
                facet_df = df_peaks[(df_peaks['dayofweek'] == day) & (df_peaks['period'] == per)].copy()
                facet_out, meta = classify_facet_func(facet_df, per)
                processed_facets.append(facet_out)
                facet_meta[(day, per)] = meta

        df_out = pd.concat(processed_facets, ignore_index=False).sort_index().copy()
        df_out['vds_id'] = str(vds_id)
        df_out = annotate_segment_selection_for_plot(df_out, config_rc, recurrent_col)
        all_processed.append(df_out)

        excluded = df_out[(df_out['is_peak'] == 1) & df_out[excluded_col].fillna(False)].copy()
        if not excluded.empty:
            all_excluded.append(excluded)

        base_name = plot_name_builder(str(vds_id))
        if not config_rc.get('dry_run', False) and config_rc.get('plots', {}).get('save_recurrent_checks', True):
            main_plot_path = save_dir / base_name
            plot_recurrent_facets(df_out, facet_meta, recurrent_col, excluded_col, draw_band_func, save_path=main_plot_path, vds_id=str(vds_id), cfg=config_rc)

            box_path = save_dir / f"{Path(base_name).stem}_boxplot.png"
            hist_path = save_dir / f"{Path(base_name).stem}_hist.png"
            plot_start_end_boxplots(df_out, save_path=box_path, vds_id=str(vds_id), cfg=config_rc)
            plot_start_end_histograms(df_out, bin_size=interval_bin_size, save_path=hist_path, vds_id=str(vds_id), cfg=config_rc)

    excluded_path = output_dir / f'05_recurrent_peak_result/excluded_recurrent_days_{output_tag}.csv'
    processed_path = output_dir / f'05_recurrent_peak_result/recurrent_days_labeled_{output_tag}.csv'
    df_excluded_all = pd.concat(all_excluded, ignore_index=True) if all_excluded else pd.DataFrame()
    df_processed_all = pd.concat(all_processed, ignore_index=True) if all_processed else pd.DataFrame()
    df_excluded_all.to_csv(excluded_path, index=False)
    df_processed_all.to_csv(processed_path, index=False)

    return {
        'output_tag': output_tag,
        'excluded_csv': str(excluded_path),
        'labeled_csv': str(processed_path),
    }


def run_recurrent_peak_pipeline(config_rc, save_dir=None):
    config_rc = copy.deepcopy(config_rc)
    method = config_rc.get('recurrent_method', 'simpleband')
    output_tag = build_recurrent_output_tag(config_rc)

    if method == 'simpleband':
        params = config_rc.get('recurrent_method_params', {}).get('simpleband', {})
        selector_by_period = params.get('selector_by_period', {'morning-peak': 'both', 'afternoon-peak': 'both'})
        start_bw = params.get('start_bandwidth_minutes_by_period', {'morning-peak': 30, 'afternoon-peak': 30})
        end_bw = params.get('end_bandwidth_minutes_by_period', {'morning-peak': 30, 'afternoon-peak': 30})
        print(f'Running simpleband recurrent detection: selector={selector_by_period}, start_bw={start_bw}, end_bw={end_bw}')
        bw_values = [v for v in list(normalize_period_mapping(start_bw).values()) + list(normalize_period_mapping(end_bw).values()) if v is not None]
        return run_band_recurrent_pipeline(
            config_rc=config_rc,
            classify_facet_func=lambda facet_df, per: classify_facet_fixed_band(
                facet_df,
                per,
                selector_by_period=selector_by_period,
                start_bandwidth_minutes_by_period=start_bw,
                end_bandwidth_minutes_by_period=end_bw,
                start_bound_mode_by_period=params.get('start_bound_mode_by_period'),
                end_bound_mode_by_period=params.get('end_bound_mode_by_period'),
            ),
            draw_band_func=draw_fixed_band,
            recurrent_col='recurrent_band',
            excluded_col='excluded_band',
            output_tag=output_tag,
            plot_name_builder=lambda vds_id: _build_simpleband_plot_name(vds_id, config_rc),
            save_dir=save_dir,
            interval_bin_size=(max(bw_values) / 60.0) if bw_values else 0.5,
        )

    if method == 'shortest_interval':
        params = config_rc.get('recurrent_method_params', {}).get('shortest_interval', {})
        print(f"Running shortest_interval recurrent detection: selector={params.get('selector_by_period')}, start_q={params.get('start_q_by_period')}, end_q={params.get('end_q_by_period')}")
        return run_band_recurrent_pipeline(
            config_rc=config_rc,
            classify_facet_func=lambda facet_df, per: classify_facet_shortest_interval(
                facet_df,
                per,
                selector_by_period=params.get('selector_by_period'),
                start_q_by_period=params.get('start_q_by_period'),
                end_q_by_period=params.get('end_q_by_period'),
                coverage_by_period=params.get('coverage_by_period'),
                start_bound_mode_by_period=params.get('start_bound_mode_by_period'),
                end_bound_mode_by_period=params.get('end_bound_mode_by_period'),
            ),
            draw_band_func=draw_fixed_band,
            recurrent_col='recurrent_band',
            excluded_col='excluded_band',
            output_tag=output_tag,
            plot_name_builder=lambda vds_id: _build_shortestinterval_plot_name(vds_id, config_rc),
            save_dir=save_dir,
            interval_bin_size=0.5,
        )

    if method == 'PELT':
        params = config_rc.get('recurrent_method_params', {}).get('PELT', {})
        pen = params.get('penalty', 20)
        min_size = params.get('min_size', 2)
        jump = params.get('jump', 1)
        length_threshold = params.get('length_threshold', 4)
        print(f'Running PELT recurrent detection: pen={pen}, min_size={min_size}, jump={jump}, length_threshold={length_threshold}')
        return run_band_recurrent_pipeline(
            config_rc=config_rc,
            classify_facet_func=lambda facet_df, per: classify_facet_pelt(
                facet_df,
                per,
                penalty=pen,
                min_size=min_size,
                jump=jump,
                length_threshold=length_threshold,
            ),
            draw_band_func=draw_pelt_band,
            recurrent_col='recurrent_band',
            excluded_col='excluded_band',
            output_tag=output_tag,
            plot_name_builder=lambda vds_id: f'PELT_{vds_id}_pen{pen}_min{min_size}_jump{jump}_len{length_threshold}.png',
            save_dir=save_dir,
            interval_bin_size=0.5,
        )

    raise ValueError(f'Unsupported recurrent_method: {method}')
