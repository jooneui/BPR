from pathlib import Path
import copy
import json
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D

# cross-module imports
from .plotting_stage2 import (
    annotate_segment_selection_for_plot,
    plot_common_points,
)
from .segmentation import rdp_v
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
    fp = build_file_path(cfg)
    from .data_io import _ensure_local
    _ensure_local(fp)
    df_raw = pd.read_csv(fp)

    # A blank trailing row makes pandas read 'date' as float, so every value
    # stringifies as '70101.0' and then fails the '%y%m%d' parse below, which
    # silently empties the facet (N_qualifying == 0). Strip that before padding.
    df_raw['date'] = (df_raw['date'].astype(str)
                      .str.replace(r'\.0$', '', regex=True).str.zfill(6))
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
    
    week_bucket = df_peaks['date_dt'] - pd.to_timedelta(df_peaks['date_dt'].dt.dayofweek, unit='D')                                                                                                         
    unique_weeks = sorted(week_bucket.dropna().unique())                                                                                                                                                    
    week_map = {w: i + 1 for i, w in enumerate(unique_weeks)}                                                                                                                                               
    df_peaks['week_num'] = week_bucket.map(week_map)         

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
    drop_multiplecongestion_days=False,
    **_ignored,
):
    out = facet_df.copy()
    out['recurrent_band'] = False
    out['excluded_band'] = False

    # ── Step 0: Deduplicate multiple peaks per day ────────────────────────
    out, n_dropped = _dedup_multiple_peaks(out, drop_multiplecongestion_days=drop_multiplecongestion_days)

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
    drop_multiplecongestion_days=False,
    **_ignored,
):
    out = facet_df.copy()
    out['recurrent_band'] = False
    out['excluded_band'] = False

    # ── Step 0: Deduplicate multiple peaks per day ────────────────────────
    out, n_dropped = _dedup_multiple_peaks(out, drop_multiplecongestion_days=drop_multiplecongestion_days)

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
        if config_rc.get('drop_multiplecongestion_days', False):
            parts.append('drop')
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
        if config_rc.get('drop_multiplecongestion_days', False):
            parts.append('drop')
        return '_'.join(parts)
    if method == 'PELT':
        p = params.get('penalty', 20)
        ms = params.get('min_size', 2)
        j = params.get('jump', 1)
        lt = params.get('length_threshold', 4)
        tag = f'PELT_pen{p}_min{ms}_jump{j}_len{lt}'
        if config_rc.get('drop_multiplecongestion_days', False):
            tag += '_drop'
        return tag
    if method == 'RDP_v':
        eps_s = normalize_period_mapping(params.get('epsilon_start_by_period', 1.5))
        eps_e = normalize_period_mapping(params.get('epsilon_end_by_period', 1.5))
        minw  = config_rc.get('segment_min_weeks_by_period', {})
        selector = normalize_period_mapping(params.get('selector_by_period', 'both'))
        fvar = normalize_period_mapping(params.get('fixed_var_by_period', 'start_hour'))
        parts = ['RDP_v']
        for per in ALL_PERIODS:
            tag = _period_tag(per)
            sel = selector.get(per, 'both')
            fv = fvar.get(per, 'start_hour')
            fv_short = {'start_hour': 'sh', 'end_hour': 'eh'}.get(fv, fv[:2])
            parts.append(
                f"{tag}_es{eps_s.get(per, 1.5)}_ee{eps_e.get(per, 1.5)}"
                f"_min{minw.get(per, 2)}_{sel[0]}_{fv_short}"
            )
        if config_rc.get('drop_multiplecongestion_days', False):
            parts.append('drop')
        return '_'.join(parts)
    return str(method)


def _dedup_multiple_peaks(out, drop_multiplecongestion_days=False, period='morning-peak'):
    """Deduplicate multiple peaks per day.

    Parameters
    ----------
    out : DataFrame
        Facet dataframe with is_peak, date_dt, start_hour, end_hour columns.
    drop_multiplecongestion_days : bool
        If True, drop all peaks on days that have multiple peak entries
        (mark as excluded / no-peak).
        If False (default), keep only the longest-duration peak per date
        (tiebreak = earliest start_hour).

    Returns
    -------
    out : DataFrame
        Modified dataframe with duplicates resolved.
    multi_peak_days : int
        Number of peak rows removed.
    """
    if 'duration_hours' not in out.columns:
        out['duration_hours'] = out['end_hour'] - out['start_hour']

    # Drop no-peak placeholders if a real peak exists for same date
    has_real_peak = out[out['is_peak'] == 1]['date_dt'].unique()
    if len(has_real_peak) > 0:
        placeholder_mask = (out['is_peak'] == -5) & (out['date_dt'].isin(has_real_peak))
        out = out[~placeholder_mask].copy()

    # Find dates with multiple peak entries
    peak_rows = out[out['is_peak'] == 1]
    counts_per_date = peak_rows.groupby('date_dt').size()
    multi_peak_dates = set(counts_per_date[counts_per_date > 1].index)
    n_before_dedup = len(peak_rows)

    # drop the day if it has multiple peaks, otherwise keep the longest-duration peak (tiebreak = earliest start_hour)
    if drop_multiplecongestion_days and multi_peak_dates:
        # Drop ALL peaks on dates with multiple peaks (mark as excluded)
        # multi_mask = (out['is_peak'] == 1) & out['date_dt'].isin(multi_peak_dates)
        # n_dropped = int(multi_mask.sum())
        # out = out[~multi_mask].copy()
        sentinel_hour = 0 if period == 'morning-peak' else 12

        multi_mask = (out['is_peak'] == 1) & out['date_dt'].isin(multi_peak_dates)
        n_dropped = int(multi_mask.sum())

        # Replace all multi-peak rows with a single sentinel row per date
        out.loc[multi_mask, ['is_peak', 'start_hour', 'end_hour', 'duration_hours']] = [-5, sentinel_hour, sentinel_hour, 0]

        # Collapse to one sentinel row per date (drop the now-duplicate extras)
        sentinel_mask = (out['is_peak'] == -5) & out['date_dt'].isin(multi_peak_dates)
        out = pd.concat([
            out[~sentinel_mask],
            out[sentinel_mask].drop_duplicates(subset='date_dt', keep='first')
        ]).sort_values('date_dt').reset_index(drop=True)
    else:
        # Keep longest-duration peak per date; tiebreak = earliest start_hour
        out = (
            out.sort_values(['date_dt', 'duration_hours', 'start_hour'], ascending=[True, False, True])
            .drop_duplicates(subset='date_dt', keep='first')
        )
        n_dropped = n_before_dedup - len(out[out['is_peak'] == 1])

    return out, n_dropped


def classify_facet_pelt(
    facet_df,
    period,
    penalty=20,
    min_size=2,
    jump=1,
    length_threshold=4,
    drop_multiplecongestion_days=False,
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
        'drop_multiplecongestion_days': drop_multiplecongestion_days,
        'n_bkpts_start': 0,
        'n_bkpts_end': 0,
        'segments': [],
        'multi_peak_days': 0,
    }

    if peak_mask.sum() == 0:
        return out, meta

    # ── Step 0: Deduplicate multiple peaks per day ────────────────────────
    out, n_dropped = _dedup_multiple_peaks(out, drop_multiplecongestion_days=drop_multiplecongestion_days)
    meta['multi_peak_days'] = n_dropped

    # Sort by date to get temporal ordering (keep original index for labeling)
    out = out.sort_values('date_dt')
    peak_mask = (out['is_peak'] == 1) & out['start_hour'].notna() & out['end_hour'].notna()

    # Use only peak weeks for PELT
    peak_indices = out.index[peak_mask].tolist()
    start_hours = out.loc[peak_mask, 'start_hour'].to_numpy()
    end_hours = out.loc[peak_mask, 'end_hour'].to_numpy()

    n_peaks = len(start_hours)
    if n_peaks < 3:  # Too few points for meaningful change point detection
        return out, meta

    # Run PELT on start_hours
    signal_start = start_hours.reshape(-1, 1)
    try:
        algo_start = rpt.Pelt(custom_cost='l2', min_size=min_size, jump=jump).fit(signal_start)
        bkpts_start = algo_start.predict(pen=penalty)
    except Exception:
        bkpts_start = [n_peaks]
    # Remove the last breakpoint (always len(n))
    bkpts_start = [b for b in bkpts_start if b < n_peaks]
    meta['n_bkpts_start'] = len(bkpts_start)

    # Run PELT on end_hours
    signal_end = end_hours.reshape(-1, 1)
    try:
        algo_end = rpt.Pelt(custom_cost='l2', min_size=min_size, jump=jump).fit(signal_end)
        bkpts_end = algo_end.predict(pen=penalty)
    except Exception:
        bkpts_end = [n_peaks]
    bkpts_end = [b for b in bkpts_end if b < n_peaks]
    meta['n_bkpts_end'] = len(bkpts_end)

    # Merge breakpoints (union)
    all_bkpts = sorted(set(bkpts_start) | set(bkpts_end))
    # Add 0 and len as boundaries
    boundaries = [0] + [b + 1 for b in all_bkpts] + [n_peaks]

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
        # Label each observation in this segment using original indices
        for j in range(seg_start, seg_end):
            orig_idx = peak_indices[j]
            if seg_len >= length_threshold:
                out.loc[orig_idx, 'recurrent_band'] = True
                out.loc[orig_idx, 'excluded_band'] = False
            else:
                out.loc[orig_idx, 'recurrent_band'] = False
                out.loc[orig_idx, 'excluded_band'] = True

    meta['segments'] = segments
    meta['all_breakpoints'] = all_bkpts
    return out, meta


def classify_facet_rdpv(
    facet_df,
    period,
    epsilon_start=1.5,
    epsilon_end=1.5,
    segment_min_weeks=2,
    selector='both',
    fixed_var='start_hour',
    drop_multiplecongestion_days=False,
    **_ignored,
):
    """RDP_v-based recurrent peak detection per (day-of-week, period) facet.

    Builds cumulative start-hour (S) and end-hour (E) series over the
    qualifying-week subsequence (weeks with is_peak==1 only).  PM times are
    first shifted by -12 so that epsilon carries the same geometric meaning
    across AM and PM.  RDP_v is applied independently to S and E; interior
    breakpoints from both series are unioned with calendar-gap positions
    (weeks in the qualifying subsequence separated by more than one calendar
    week) to form segment boundaries.  Segments with fewer than
    segment_min_weeks qualifying weeks are excluded.

    fixed_var controls which variable is the temporal anchor and which epsilon
    drives it:
      'start_hour' (AM default): epsilon_start drives S; epsilon_end drives E
      'end_hour'   (PM default): epsilon_end   drives E; epsilon_start drives S

    Parameters
    ----------
    facet_df : DataFrame
        One (day-of-week, period) facet from prepare_peak_table().
    period : str
        'morning-peak' or 'afternoon-peak'.
    epsilon_start : float
        RDP vertical tolerance for the start-hour cumulative series.
    epsilon_end : float
        RDP vertical tolerance for the end-hour cumulative series.
    segment_min_weeks : int
        Minimum qualifying weeks per segment to be labelled recurrent (L).
    selector : str
        'both' (spec-compliant), 'start_only', or 'end_only'.
    fixed_var : str
        'start_hour' (default) or 'end_hour'. Determines epsilon assignment.
    drop_multiplecongestion_days : bool
        If True, treat days with multiple detected peaks as no-peak days.

    Returns
    -------
    out : DataFrame
        facet_df with added columns recurrent_band, excluded_band, segment_id.
    meta : dict
        Diagnostics: breakpoints, gap positions, segments, etc.
    """
    out = facet_df.copy()
    out['recurrent_band'] = False
    out['excluded_band'] = False
    out['segment_id'] = np.nan

    meta = {
        'method': 'RDP_v',
        'epsilon_start': epsilon_start,
        'epsilon_end': epsilon_end,
        'segment_min_weeks': segment_min_weeks,
        'selector': selector,
        'fixed_var': fixed_var,
        'breakpoints_start': [],
        'breakpoints_end': [],
        'gap_positions': [],
        'all_breakpoints': [],
        'breakpoint_weeks_start': [],
        'breakpoint_weeks_end': [],
        'breakpoint_weeks_gap': [],
        'breakpoint_weeks': [],
        'segments': [],
        'multi_peak_days': 0,
        'N_qualifying': 0,
    }

    # ── Step 0: Deduplicate multiple peaks per day ────────────────────────
    out, n_dropped = _dedup_multiple_peaks(
        out, drop_multiplecongestion_days=drop_multiplecongestion_days, period=period
    )
    meta['multi_peak_days'] = n_dropped

    # ── Step 1: Sort; isolate qualifying weeks (is_peak == 1) ────────────
    out = out.sort_values('date_dt').reset_index(drop=True)

    peak_positions = np.where((out['is_peak'] == 1).to_numpy())[0]  # positions in out
    N = len(peak_positions)
    meta['N_qualifying'] = N

    if N == 0:
        return out, meta

    peak_df = out.iloc[peak_positions].reset_index(drop=True)
    # peak_df.iloc[i] ↔ out.iloc[peak_positions[i]]

    # ── Step 1b: Apply PM shift ───────────────────────────────────────────
    # Centers both series at 0 so epsilon has identical geometric meaning for
    # AM (hours ≈ 0–12) and PM (hours ≈ 12–24 → shifted to 0–12).
    shift = 12.0 if period == 'afternoon-peak' else 0.0
    start_shifted = peak_df['start_hour'].to_numpy(dtype=float) - shift
    end_shifted   = peak_df['end_hour'].to_numpy(dtype=float) - shift

    # ── Step 1c: Epsilon assignment (fixed_var-aware) ────────────────────
    # fixed_var='start_hour': eps_primary=epsilon_start (drives S), eps_secondary=epsilon_end (drives E)
    # fixed_var='end_hour':   eps_primary=epsilon_end   (drives E), eps_secondary=epsilon_start (drives S)
    if fixed_var == 'start_hour':
        eps_primary, eps_secondary = epsilon_start, epsilon_end
    elif fixed_var == 'end_hour':
        eps_primary, eps_secondary = epsilon_end, epsilon_start
    else:
        raise ValueError(f"fixed_var must be 'start_hour' or 'end_hour', got '{fixed_var}'")

    # ── Step 2: Build cumulative series S_{0:N} and E_{0:N} ──────────────
    # x = subsequence index n = 0..N; S_0 = E_0 = 0 by construction.
    x  = np.arange(N + 1, dtype=float)
    S  = np.concatenate([[0.0], np.cumsum(start_shifted)])
    E  = np.concatenate([[0.0], np.cumsum(end_shifted)])

    if fixed_var == 'start_hour':
        pts_primary, pts_secondary = np.column_stack([x, S]), np.column_stack([x, E])
    else:  # fixed_var == 'end_hour'
        pts_primary, pts_secondary = np.column_stack([x, E]), np.column_stack([x, S])

    # ── Step 3: Apply RDP_v; extract interior breakpoints ────────────────
    # "Interior" = positions strictly between 0 and N (spec: ρ ∈ {1,...,N-1}).
    def _interior(pts, eps):
        simplified = rdp_v(pts, epsilon=eps)
        return sorted(int(xi) for xi in simplified[:, 0] if 0 < xi < N)

    if fixed_var == 'start_hour':
        apply_primary   = selector in ('start_only', 'both')
        apply_secondary = selector in ('end_only',   'both')
    else:  # fixed_var == 'end_hour'
        apply_primary   = selector in ('end_only',   'both')
        apply_secondary = selector in ('start_only', 'both')

    bp_primary   = _interior(pts_primary,   eps_primary)   if apply_primary   else []
    bp_secondary = _interior(pts_secondary, eps_secondary) if apply_secondary else []

    # Map back to canonical start / end names for meta and plotting
    if fixed_var == 'start_hour':
        bp_start, bp_end = bp_primary, bp_secondary
    else:
        bp_start, bp_end = bp_secondary, bp_primary

    meta['breakpoints_start'] = bp_start
    meta['breakpoints_end']   = bp_end

    # ── Step 4: Calendar gap positions ───────────────────────────────────
    # A gap at position n means w_n and w_{n-1} are not consecutive calendar
    # weeks — demand was absent between them, so a segment boundary is forced.
    peak_week_nums = peak_df['week_num'].to_numpy()
    gap_positions = [
        n for n in range(1, N)
        if peak_week_nums[n] - peak_week_nums[n - 1] > 1
    ]
    meta['gap_positions'] = gap_positions

    # ── Step 5: Union all interior breakpoints ────────────────────────────
    if selector == 'start_only':
        rdp_bkpts = set(bp_start)
    elif selector == 'end_only':
        rdp_bkpts = set(bp_end)
    else:
        rdp_bkpts = set(bp_start) | set(bp_end)
    all_bkpts = sorted(rdp_bkpts | set(gap_positions))
    meta['all_breakpoints'] = all_bkpts

    # ── Step 6: Form right-closed segments (ρ_{k-1}, ρ_k] ───────────────
    boundaries = [0] + all_bkpts + [N]
    segments = []

    for k in range(len(boundaries) - 1):
        r_start = boundaries[k]      # exclusive left boundary
        r_end   = boundaries[k + 1]  # inclusive right boundary

        # Qualifying weeks in this segment: peak_df.iloc[r_start : r_end]
        seg_peak = peak_df.iloc[r_start:r_end]
        seg_len  = r_end - r_start   # ℓ_k
        retained = seg_len >= segment_min_weeks

        seg_week_nums = seg_peak['week_num'].tolist()
        start_week = float(min(seg_week_nums)) if seg_week_nums else np.nan
        end_week   = float(max(seg_week_nums)) if seg_week_nums else np.nan

        segments.append({
            'start_obs':  r_start,
            'end_obs':    r_end,
            'peak_count': seg_len,
            'retained':   retained,
            'start_week': start_week,
            'end_week':   end_week,
            'segment_id': k,
            'peak_weeks': seg_week_nums,
        })

        # ── Step 7: Label rows ────────────────────────────────────────────
        orig_pos_list = [peak_positions[i] for i in range(r_start, r_end)]
        for orig_pos in orig_pos_list:
            if retained:
                out.at[orig_pos, 'recurrent_band'] = True
                out.at[orig_pos, 'segment_id']     = float(k)
            else:
                out.at[orig_pos, 'excluded_band']  = True

        # Assign segment_id to non-qualifying rows whose date falls within the
        # retained segment's date range (needed by BPR segment_aggregation).
        if retained and not seg_peak.empty:
            first_date = seg_peak['date_dt'].min()
            last_date  = seg_peak['date_dt'].max()
            nonpeak_mask = (
                (out['date_dt'] >= first_date) &
                (out['date_dt'] <= last_date) &
                (out['is_peak'] != 1)
            )
            out.loc[nonpeak_mask, 'segment_id'] = float(k)

    meta['segments'] = segments

    # ── Step 8: Store breakpoint calendar-week numbers for plotting ───────
    # Breakpoint ρ is after qualifying week n=ρ, i.e. peak_df.iloc[ρ-1].
    meta['breakpoint_weeks_start'] = [float(peak_df.at[r - 1, 'week_num']) for r in bp_start]
    meta['breakpoint_weeks_end']   = [float(peak_df.at[r - 1, 'week_num']) for r in bp_end]
    meta['breakpoint_weeks_gap']   = [float(peak_df.at[r - 1, 'week_num']) for r in gap_positions]
    meta['breakpoint_weeks']       = [float(peak_df.at[r - 1, 'week_num']) for r in all_bkpts]

    return out, meta


def draw_rdpv_band(ax, meta):
    """Draw RDP_v segment boundaries on the facet plot.

    Shading uses week_num coordinates.  For retained segments, green
    shading covers only the individual peak-week positions (avoiding
    no-peak gaps within the segment).  For excluded segments, grey
    shading covers individual peak-week positions.  Changepoint lines
    are drawn separately for start_hour (blue dashed) and end_hour
    (orange dashed) to show where each variable's trend changes.
    """
    handles, labels = [], []
    if not meta or 'segments' not in meta:
        return handles, labels
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D

    segments = meta.get('segments', [])

    for seg in segments:
        peak_weeks = seg.get('peak_weeks', [])
        if not peak_weeks:
            continue  # skip purely no-peak segments
        # Shade only retained segments (green). Non-retained weeks are left
        # unshaded so the panels are not cluttered by grey vertical strips.
        if not seg.get('retained', False):
            continue
        for w in peak_weeks:
            ax.axvspan(w - 0.5, w + 0.5, color='green', alpha=0.15)

    # Vertical changepoint / gap guide lines: start-hour CP (blue dashed),
    # end-hour CP (orange dashed), calendar gap (grey dotted).
    has_start = False
    for bw in meta.get('breakpoint_weeks_start', []):
        ax.axvline(bw + 0.5, color='blue', linestyle='--', linewidth=0.8, alpha=0.6)
        has_start = True
    has_end = False
    for bw in meta.get('breakpoint_weeks_end', []):
        ax.axvline(bw + 0.5, color='darkorange', linestyle='--', linewidth=0.8, alpha=0.6)
        has_end = True
    has_gap = False
    for bw in meta.get('breakpoint_weeks_gap', []):
        ax.axvline(bw + 0.5, color='grey', linestyle=':', linewidth=1.0, alpha=0.8)
        has_gap = True

    if has_start:
        handles.append(Line2D([0], [0], color='blue', linestyle='--', linewidth=0.8, alpha=0.6, label='Start-hour CP'))
        labels.append('Start-hour CP')
    if has_end:
        handles.append(Line2D([0], [0], color='darkorange', linestyle='--', linewidth=0.8, alpha=0.6, label='End-hour CP'))
        labels.append('End-hour CP')
    if has_gap:
        handles.append(Line2D([0], [0], color='grey', linestyle=':', linewidth=1.0, alpha=0.8, label='Calendar gap'))
        labels.append('Calendar gap')

    return handles, labels


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


def plot_recurrent_facets(df_peaks, facet_meta, recurrent_col, excluded_col, draw_band_func,
                        save_path=None, vds_id=None, cfg=None,
                        merge_excluded_to_not_selected=False):
    """Plot recurrent-peak facets.

    Parameters
    ----------
    merge_excluded_to_not_selected : bool
        For segmentation methods (RDP_v, PELT) set True so that
        excluded-band peaks appear as dark-orange circles ("Not Selected")
        instead of crimson diamonds ("Non-Recurrent").
    """
    data = annotate_segment_selection_for_plot(df_peaks, cfg, recurrent_col)
    fig, axes = plt.subplots(len(DAY_ORDER), len(ALL_PERIODS), figsize=(16, 22), sharex=False, sharey=False)
    for i, day in enumerate(DAY_ORDER):
        for j, per in enumerate(ALL_PERIODS):
            ax = axes[i, j]
            sub = data[(data['dayofweek'] == day) & (data['period'] == per)].copy()
            print(f"Plotting facet for {day} {per}, n={len(sub)}", sub.head())
            point_handles, point_labels = plot_common_points(
                ax, sub, recurrent_col, excluded_col,
                merge_excluded_to_not_selected=merge_excluded_to_not_selected)
            band_handles, band_labels = draw_band_func(ax, facet_meta.get((day, per), {}))
            handles = point_handles + band_handles
            labels = point_labels + band_labels
            if i == 0:
                ax.set_title(per, fontsize=18, fontweight='bold')
            if j == 0:
                ax.set_ylabel("Time (hour)", fontsize=15)
                ax.text(-0.1, 0.5, day, transform=ax.transAxes,
                        rotation=90, va='center', ha='right', fontsize=17, fontweight='bold')
            ax.set_xlabel('Week Number', fontsize=15)
            ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
            ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
            if per == 'morning-peak':
                ax.set_ylim(-0.5, 12.5)
            else:
                ax.set_ylim(11.5, 24.5)
            if i == 0 and j == 0 and handles:
                ax.legend(handles, labels, loc='lower left', fontsize=11, frameon=True)

    
    _raw = cfg.get('VDS_label_list', {})
    # Flatten nested dict: {'SR91': {'1203481': 'SR91-WB', ...}} → {'1203481': 'SR91-WB', ...}
    _flat_labels = {}
    for _key, _val in _raw.items():
        if isinstance(_val, dict):
            _flat_labels.update({_k: _v for _k, _v in _val.items()})
        else:
            _flat_labels[_key] = _val

    _label = _flat_labels.get(str(vds_id), str(vds_id))

    title = f"Near-Recurrent Peak-Period Identification (VDS: {vds_id})"
    fig.suptitle(title, fontsize=30, y=1.0)
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
    merge_excluded_to_not_selected=False,
):
    save_dir = Path(save_dir or config_rc.get('rc_save_dir', config_rc.get('save_dir', './02 fig/17 recurrent_checks')))
    save_dir.mkdir(parents=True, exist_ok=True)
    output_dir = Path('.')
    output_dir.mkdir(parents=True, exist_ok=True)

    all_excluded = []
    all_processed = []
    all_meta_rows = []

    _AM_PM_TO_PERIOD = {'AM': 'morning-peak', 'PM': 'afternoon-peak'}
    fd_skip_map = config_rc.get('_fd_skip_map', {})

    for vds_id in config_rc['VDS_list']:
        print(f'Running recurrent detection for VDS {vds_id} ({output_tag})')
        vds_flags = fd_skip_map.get(str(vds_id), {})
        skipped_periods = {
            period_name
            for am_pm, period_name in _AM_PM_TO_PERIOD.items()
            if vds_flags.get(am_pm) is False
        }

        df_peaks = prepare_peak_table(config_rc, str(vds_id), ALL_PERIODS)
        processed_facets = []
        facet_meta = {}

        for day in DAY_ORDER:
            for per in ALL_PERIODS:
                if per in skipped_periods:
                    print(f"  [SKIP] VDS {vds_id} {per} ({day}) — failed FD density threshold.")
                    continue
                facet_df = df_peaks[(df_peaks['dayofweek'] == day) & (df_peaks['period'] == per)].copy()
                facet_out, meta = classify_facet_func(facet_df, per)
                processed_facets.append(facet_out)
                facet_meta[(day, per)] = meta

        # Accumulate facet_meta rows for later CSV export
        for (day, per), m in facet_meta.items():
            row = {'vds_id': str(vds_id), 'dayofweek': day, 'period': per}
            for k, v in m.items():
                if isinstance(v, (list, dict)):
                    row[k] = json.dumps(v, default=str)
                elif isinstance(v, np.ndarray):
                    row[k] = json.dumps(v.tolist(), default=str)
                else:
                    row[k] = v
            all_meta_rows.append(row)
        

        if not processed_facets:
            print(f"  [SKIP] VDS {vds_id}: all periods skipped — no recurrent output generated.")
            continue
        df_out = pd.concat(processed_facets, ignore_index=True).copy()
        df_out['vds_id'] = str(vds_id)
        df_out = annotate_segment_selection_for_plot(df_out, config_rc, recurrent_col)
        all_processed.append(df_out)

        excluded = df_out[(df_out['is_peak'] == 1) & df_out[excluded_col].fillna(False)].copy()
        if not excluded.empty:
            all_excluded.append(excluded)

        base_name = plot_name_builder(str(vds_id))
        if not config_rc.get('dry_run', False) and config_rc.get('plots', {}).get('save_recurrent_checks', True):
            main_plot_path = save_dir / base_name
            plot_recurrent_facets(df_out, facet_meta, recurrent_col, excluded_col, draw_band_func,
                                   save_path=main_plot_path, vds_id=str(vds_id), cfg=config_rc,
                                   merge_excluded_to_not_selected=merge_excluded_to_not_selected)

            box_path = save_dir / f"{Path(base_name).stem}_boxplot.png"
            hist_path = save_dir / f"{Path(base_name).stem}_hist.png"
            # plot_start_end_boxplots(df_out, save_path=box_path, vds_id=str(vds_id), cfg=config_rc)
            # plot_start_end_histograms(df_out, bin_size=interval_bin_size, save_path=hist_path, vds_id=str(vds_id), cfg=config_rc)

    excluded_path = output_dir / f'05_recurrent_peak_result/excluded_recurrent_days_{output_tag}.csv'
    processed_path = output_dir / f'05_recurrent_peak_result/recurrent_days_labeled_{output_tag}.csv'
    df_excluded_all = pd.concat(all_excluded, ignore_index=True) if all_excluded else pd.DataFrame()
    df_processed_all = pd.concat(all_processed, ignore_index=True) if all_processed else pd.DataFrame()
    # start_time/end_time are the raw Stage 1 strings; start_hour/end_hour (already
    # computed) are what every downstream consumer (BPR fitting, plotting) reads.
    # Dropped here since they duplicate start_hour/end_hour but can go stale (e.g.
    # is_peak==-5 sentinel rows keep the raw string while the hour is overwritten).
    df_excluded_all = df_excluded_all.drop(columns=['start_time', 'end_time'], errors='ignore')
    df_processed_all = df_processed_all.drop(columns=['start_time', 'end_time'], errors='ignore')
    df_excluded_all.to_csv(excluded_path, index=False)
    df_processed_all.to_csv(processed_path, index=False)

    # Export all facet_meta as one CSV (one row per vds_id × dayofweek × period)
    meta_csv_path = output_dir / f'05_recurrent_peak_result/facet_meta_{output_tag}.csv'
    if all_meta_rows:
        df_meta_all = pd.DataFrame(all_meta_rows)
        df_meta_all.to_csv(meta_csv_path, index=False)
    else:
        pd.DataFrame().to_csv(meta_csv_path, index=False)

    return {
        'output_tag': output_tag,
        'excluded_csv': str(excluded_path),
        'labeled_csv': str(processed_path),
        'meta_csv': str(meta_csv_path),
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
        drop_multi = config_rc.get('drop_multiplecongestion_days', False)
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
                drop_multiplecongestion_days=drop_multi,
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
        drop_multi = config_rc.get('drop_multiplecongestion_days', False)
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
                drop_multiplecongestion_days=drop_multi,
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
        drop_multi = config_rc.get('drop_multiplecongestion_days', False)
        print(f'Running PELT recurrent detection: pen={pen}, min_size={min_size}, jump={jump}, length_threshold={length_threshold}, drop_multi={drop_multi}')
        return run_band_recurrent_pipeline(
            config_rc=config_rc,
            classify_facet_func=lambda facet_df, per: classify_facet_pelt(
                facet_df,
                per,
                penalty=pen,
                min_size=min_size,
                jump=jump,
                length_threshold=length_threshold,
                drop_multiplecongestion_days=drop_multi,
            ),
            draw_band_func=draw_pelt_band,
            recurrent_col='recurrent_band',
            excluded_col='excluded_band',
            output_tag=output_tag,
            plot_name_builder=lambda vds_id: f'PELT_{vds_id}_pen{pen}_min{min_size}_jump{jump}_len{length_threshold}.png',
            save_dir=save_dir,
            interval_bin_size=0.5,
            merge_excluded_to_not_selected=True,
        )

    if method == 'RDP_v':
        params = config_rc.get('recurrent_method_params', {}).get('RDP_v', {})
        eps_start_map = normalize_period_mapping(params.get('epsilon_start_by_period', 1.5))
        eps_end_map   = normalize_period_mapping(params.get('epsilon_end_by_period', 1.5))
        min_weeks_map = config_rc.get('segment_min_weeks_by_period', {'morning-peak': 2, 'afternoon-peak': 2})
        selector_map  = normalize_period_mapping(params.get('selector_by_period', 'both'))
        fixed_var_map = normalize_period_mapping(params.get('fixed_var_by_period', 'start_hour'))
        drop_multi = config_rc.get('drop_multiplecongestion_days', False)
        print(f'Running RDP_v recurrent detection: eps_start={dict(eps_start_map)}, eps_end={dict(eps_end_map)}, '
              f'min_weeks={min_weeks_map}, selector={dict(selector_map)}, '
              f'fixed_var={dict(fixed_var_map)}, drop_multi={drop_multi}')
        return run_band_recurrent_pipeline(
            config_rc=config_rc,
            classify_facet_func=lambda facet_df, per: classify_facet_rdpv(
                facet_df,
                per,
                epsilon_start=eps_start_map.get(per, 1.5),
                epsilon_end=eps_end_map.get(per, 1.5),
                segment_min_weeks=min_weeks_map.get(per, 2),
                selector=selector_map.get(per, 'both'),
                fixed_var=fixed_var_map.get(per, 'start_hour'),
                drop_multiplecongestion_days=drop_multi,
            ),
            draw_band_func=draw_rdpv_band,
            recurrent_col='recurrent_band',
            excluded_col='excluded_band',
            output_tag=output_tag,
            plot_name_builder=lambda vds_id: f'RDP_v_{vds_id}_{output_tag}.png',
            save_dir=save_dir,
            interval_bin_size=0.5,
            merge_excluded_to_not_selected=True,
        )

    raise ValueError(f'Unsupported recurrent_method: {method}')
