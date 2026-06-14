from scipy import stats
import copy
import math
import numpy as np
import os
import pandas as pd
import statsmodels.api as sm
from typing import Callable, Dict, Tuple

# ── Linear transform registry (kept here to avoid circular imports) ──
LinearTransform = Callable[[pd.DataFrame], Tuple[np.ndarray, np.ndarray, str, str]]

def v2_lnN_vs_lnttau():
    return (
        "ln_totaldemand",
        "ln_t_tau",
        r"$\ln(Tq)$",
        r"$\ln\!\left(\frac{z(r)}{\zeta}-1\right)$",
    )

def v3_lnN_vs_lnttau():
    return (
        "ln_totaldemandoverlanes",
        "ln_t_tau",
        r"$\ln(Q)$",
        r"$\ln\!\left(\frac{z(Q)}{\zeta}-1\right)$",
    )

def v10_lnq_vs_lnttau():
    return (
        "ln_avg_flow",
        "ln_t_tau",
        r"$\ln(q)$",
        r"$\ln\!\left(\frac{z(q)}{\zeta}-1\right)$",
    )

LINEAR_REGISTRY_BPR: Dict[str, LinearTransform] = {
    "v2": v2_lnN_vs_lnttau,
    "v3": v3_lnN_vs_lnttau,
    "v10": v10_lnq_vs_lnttau,
}


def time_to_fractional_hour(t_str, default_val=np.nan):
    if pd.isna(t_str) or t_str == '-':
        return default_val
    try:
        h, m = map(int, str(t_str).split(':'))
        return h + m / 60.0
    except Exception:
        return default_val


def build_file_path(cfg: dict) -> str:
    print(cfg['spatial_scope'])
    if cfg['spatial_scope'] == 'multi_vds':
        file_path = f"./04_peak_period_result/c_daily_traffic_division_{cfg['spatial_scope']}_{cfg['VDS_list']}_{cfg['temporal_scale']}_{cfg['aggregate_timeframe']}_{cfg['method']}_{cfg['congest_method']}.csv"
        print(file_path)
    elif cfg['spatial_scope'] == 'network':
        file_path = (f"./04_peak_period_result/c_daily_traffic_division_network_{cfg['VDS_num']}"
                     f"_{cfg['temporal_scale']}_{cfg['aggregate_timeframe']}"
                     f"_{cfg['method']}_{cfg['congest_method']}.csv")
    else:
        file_path = f"./04_peak_period_result/c_daily_traffic_division_{cfg['spatial_scope']}_{cfg['VDS_num']}_{cfg['temporal_scale']}_{cfg['aggregate_timeframe']}_{cfg['method']}_{cfg['congest_method']}.csv"
    return file_path


# === Shared utilities ===


def to_categorical_day(df: pd.DataFrame) -> pd.DataFrame:
    day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    if 'dayofweek' in df.columns:
        df['dayofweek'] = pd.Categorical(df['dayofweek'], categories=day_order, ordered=True)
    return df


def build_default_recurrent_output_tag_from_bpr(cfg: dict) -> str:
    method = cfg.get('nonrecurrent_method', 'simpleband')
    if cfg.get('recurrent_output_tag'):
        return cfg['recurrent_output_tag']
    if method == 'simpleband':
        return f"simpleband_{int(cfg.get('bandwidth', 30))}minbinsize_{cfg.get('bandwidth_method', 'bb')}"
    if method == 'PELT':
        pen = cfg.get('pelt_penalty', 20)
        min_size = cfg.get('pelt_min_size', 2)
        jump = cfg.get('pelt_jump', 1)
        length_threshold = cfg.get('pelt_length_threshold', 4)
        return f"PELT_pen{pen}_min{min_size}_jump{jump}_len{length_threshold}"
    if method == 'RDP_v':
        from .recurrent import normalize_period_mapping
        eps_s = cfg.get('epsilon_start_by_period', {'morning-peak': 1.5, 'afternoon-peak': 1.5})
        eps_e = cfg.get('epsilon_end_by_period', {'morning-peak': 1.5, 'afternoon-peak': 1.5})
        minw  = cfg.get('segment_min_weeks_by_period', {'morning-peak': 2, 'afternoon-peak': 2})
        parts = ['RDP_v']
        for per in ['morning-peak', 'afternoon-peak']:
            parts.append(f"es{eps_s.get(per, 1.5)}_ee{eps_e.get(per, 1.5)}_min{minw.get(per, 2)}")
        return '_'.join(parts)
    return str(method)


def build_excluded_recurrent_days_path(cfg: dict) -> str:
    if cfg.get('recurrent_output_path'):
        return cfg['recurrent_output_path']
    tag = build_default_recurrent_output_tag_from_bpr(cfg)
    return f"./05_recurrent_peak_result/excluded_recurrent_days_{tag}.csv"


def build_labeled_recurrent_days_path(cfg: dict) -> str:
    """Return the path to the labeled recurrent days CSV for the current cfg."""
    tag = cfg.get('recurrent_output_tag') or build_default_recurrent_output_tag_from_bpr(cfg)
    return f"./05_recurrent_peak_result/recurrent_days_labeled_{tag}.csv"


def merge_segment_id(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Merge segment_id from the labeled recurrent output into the BPR data.

    This ensures that adjacent retained segments with different RDP breakpoints
    are kept separate during aggregation, instead of being merged into one
    continuous group.
    """
    labeled_path = build_labeled_recurrent_days_path(cfg)
    if not os.path.exists(labeled_path):
        print(f'[merge_segment_id] Labeled file not found: {labeled_path}, skipping merge')
        return df

    df_labeled = pd.read_csv(labeled_path)
    if 'vds_id' in df_labeled.columns:
        df_labeled = df_labeled[df_labeled['vds_id'].astype(str) == str(cfg.get('VDS_num', ''))]

    if 'segment_id' not in df_labeled.columns:
        print('[merge_segment_id] No segment_id column in labeled file, skipping merge')
        return df

    # Normalize date column in the labeled file
    if 'date' not in df_labeled.columns and 'date_dt' in df_labeled.columns:
        df_labeled['date'] = pd.to_datetime(df_labeled['date_dt'], errors='coerce').dt.strftime('%y%m%d')
    if 'date' in df_labeled.columns:
        df_labeled['date'] = df_labeled['date'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(6)

    # Only keep rows with segment_id (retained segments) and needed columns
    seg_cols = [c for c in ['date', 'period', 'dayofweek', 'week_num', 'vds_id', 'segment_id'] if c in df_labeled.columns]
    df_seg = df_labeled[seg_cols].dropna(subset=['segment_id']).drop_duplicates()

    if df_seg.empty:
        return df

    # Merge on matching keys
    work = df.copy()
    work['date'] = work['date'].astype(str)
    merge_on = [c for c in ['date', 'period', 'dayofweek'] if c in work.columns and c in df_seg.columns]
    if not merge_on:
        print('[merge_segment_id] No matching merge columns, skipping merge')
        return df

    # Drop existing segment_id if it exists (from a stale merge)
    if 'segment_id' in work.columns:
        work = work.drop(columns=['segment_id'])

    work = work.merge(df_seg[['segment_id'] + merge_on], on=merge_on, how='left')

    n_with_seg = work['segment_id'].notna().sum()
    print(f'[merge_segment_id] Merged segment_id: {n_with_seg}/{len(work)} rows have segment_id')
    return work


# === Load + annotate once ===
def load_and_annotate(cfg: dict) -> pd.DataFrame:
    fp = build_file_path(cfg)
    df = pd.read_csv(fp)
    df['date'] = df['date'].astype(str)
    df['month'] = df['date'].str.slice(0, 4)

    if cfg['free_tt_mode'] == 'by_date_offpeak':
        off = df[df['period'] == 'off-peak']
        free_map = off.set_index('date')['traveltimes'].to_dict()
        df['free_traveltime'] = df['date'].map(free_map)
    else:
        if cfg['free_tt_method'] == 'FD':
            if cfg['spatial_scope'] == 'single':
                df['free_traveltime'] = cfg['free_tt_FD'][cfg['VDS_num']]
            else:
                df['free_traveltime'] = cfg['free_tt_FD']['multi_vds']
        elif cfg['free_tt_method'] == 'offpeak_avg':
            # Step 3 uses bpr_ff_speed_threshold (data-derived from 0-3am + 22-24 off-peak)
            ff_map = cfg.get('bpr_ff_speed_threshold', {})
            if not ff_map:
                # Fallback to old unified parameter for backward compatibility
                sp = cfg.get('speedbased_params', {})
                ff_map = sp.get('offpeak_ff_speed_threshold', {})
            if cfg['spatial_scope'] in ('single', 'network'):
                ff_speed = ff_map.get(cfg['VDS_num'], ff_map.get('multi_vds', 55))
            else:
                ff_speed = ff_map.get('multi_vds', 55)
            df['free_traveltime'] = 60.0 / ff_speed

    if cfg['spatial_scope'] == 'single':
        _lane_map = cfg.get('lane_map', {})
        lane_num = _lane_map.get(cfg['VDS_num'], cfg.get('lane_num', []))
        if lane_num:
            df['totaldemandoverlanes'] = df['totaldemand'] * len(lane_num)
        else:
            df['totaldemandoverlanes'] = df['totaldemand']
    else:  # 'multi_vds' or 'network' — demand already network/multi level
        df['totaldemandoverlanes'] = df['totaldemand']

    df['ln_totaldemandoverlanes'] = np.nan
    mask = df['totaldemandoverlanes'] > 0
    df.loc[mask, 'ln_totaldemandoverlanes'] = np.log(df.loc[mask, 'totaldemandoverlanes'])

    df['ln_avg_flow'] = np.nan
    mask = df['avg_flow'] > 0
    df.loc[mask, 'ln_avg_flow'] = np.log(df.loc[mask, 'avg_flow'])

    df['ln_totaldemand'] = np.nan
    mask = df['totaldemand'] > 0
    df.loc[mask, 'ln_totaldemand'] = np.log(df.loc[mask, 'totaldemand'])

    tau_ratio = df['traveltimes'] / df['free_traveltime'] - 1.0
    df['ln_t_tau'] = np.nan
    mask = tau_ratio > 0
    df.loc[mask, 'ln_t_tau'] = np.log(tau_ratio[mask])

    W_hour = cfg['W_minutes'] / 60.0
    df['avgdemand'] = np.where(df['division'] == 0, df['totaldemand'], df['totaldemand'] / W_hour)
    return df


def weighted_harmonic_mean(values, weights):
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    mask = np.isfinite(values) & np.isfinite(weights) & (values > 0) & (weights > 0)
    if not np.any(mask):
        return np.nan
    return float(np.sum(weights[mask] * values[mask]) / weights[mask].sum())


def aggregate_segment_level_bpr(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    if not cfg.get('segment_aggregation', False):
        return df
    if cfg.get('temporal_scale') not in ('speedbasedpeak', 'entireday', 'hour'):
        print('segment_aggregation is not supported for this temporal_scale. Returning unaggregated data.')
        return df
    if df.empty:
        return df

    period_include = cfg['period_include'][cfg['temporal_scale']]
    min_weeks_map = cfg.get('segment_min_weeks_by_period', {'morning-peak': 2, 'afternoon-peak': 2, 'off-peak': 2})

    out = df.copy()
    out['date'] = out['date'].astype(str)
    out['date_dt'] = pd.to_datetime(out['date'], format='%y%m%d', errors='coerce')
    min_date = out['date_dt'].min()
    out['week_num'] = ((out['date_dt'] - min_date).dt.days // 7) + 1
    has_time = 'start_time' in out.columns and out['start_time'].notna().any()
    if has_time:
        out['start_hour'] = out['start_time'].apply(time_to_fractional_hour)
        out['end_hour'] = out['end_time'].apply(time_to_fractional_hour)
        if 'duration' not in out.columns:
            out['duration'] = (out['end_hour'] - out['start_hour']) * 60.0
    else:
        out['start_hour'] = np.nan
        out['end_hour'] = np.nan
        if 'duration' not in out.columns:
            out['duration'] = np.nan

    rows = []
    for period in period_include:
        dfl = out[out['period'] == period].copy()
        if dfl.empty:
            continue
        for day, g in dfl.groupby('dayofweek', dropna=False):
            g = g.sort_values(['week_num', 'date_dt']).copy()
            # If segment_id is provided by the recurrent detection (RDP_v),
            # use it to keep adjacent retained segments separate.
            # Otherwise, fall back to grouping by consecutive week_num gaps.
            if 'segment_id' in g.columns:
                # segment_id from RDP_v: keep only rows in retained segments,
                # then group by segment_id so adjacent retained segments
                # are NOT merged into one.
                g_retained = g.dropna(subset=['segment_id']).copy()
                g_retained['segment_id'] = g_retained['segment_id'].astype(int)
                grouped = g_retained.groupby('segment_id', dropna=False)
            else:
                # No segment_id from pipeline: fall back to consecutive week gaps
                g['segment_id'] = (g['week_num'].diff().fillna(1).ne(1)).cumsum() + 1
                grouped = g.groupby('segment_id', dropna=False)
            for segment_id, seg in grouped:
                min_weeks = int(min_weeks_map.get(period, 2))
                print("seghead",seg.head())
                if len(seg) < min_weeks:
                    continue
                avg_demand = float(seg['totaldemandoverlanes'].mean())
                avg_totaldemand = float(seg['totaldemand'].mean()) if 'totaldemand' in seg.columns else np.nan

                avg_avg_flow = float(seg['totaldemand'].mean()/(seg['duration'].mean()/60)) if 'avg_flow' in seg.columns else np.nan
                # avg_avg_flow = float(seg['avg_flow'].mean()) if 'avg_flow' in seg.columns else np.nan

                avg_tt = weighted_harmonic_mean(seg['traveltimes'], seg['totaldemandoverlanes'])
                free_tt = float(seg['free_traveltime'].median())
                tau_ratio = avg_tt / free_tt - 1.0 if pd.notna(avg_tt) and pd.notna(free_tt) and free_tt > 0 else np.nan
                rows.append({
                    'period': period,
                    'dayofweek': day,
                    'segment_id': int(segment_id),
                    'n_days': int(len(seg)),
                    'date': seg['end_date'].iloc[0] if 'end_date' in seg.columns else seg['date'].iloc[-1],
                    'duration': float(seg['duration'].mean()) if seg['duration'].notna().any() else np.nan,
                    'traveltimes': avg_tt,
                    'free_traveltime': free_tt,
                    'totaldemandoverlanes': avg_demand,
                    'totaldemand': avg_totaldemand,
                    'avg_flow': avg_avg_flow,
                    'ln_totaldemandoverlanes': np.log(avg_demand) if avg_demand > 0 else np.nan,
                    'ln_totaldemand': np.log(avg_totaldemand) if pd.notna(avg_totaldemand) and avg_totaldemand > 0 else np.nan,
                    'ln_avg_flow': np.log(avg_avg_flow) if pd.notna(avg_avg_flow) and avg_avg_flow > 0 else np.nan,
                    'ln_t_tau': np.log(tau_ratio) if pd.notna(tau_ratio) and tau_ratio > 0 else np.nan,
                    'start_time': seg['start_time'].iloc[-1] if has_time else np.nan,
                    'end_time': seg['end_time'].iloc[-1] if has_time else np.nan,
                    'start_hour': float(seg['start_hour'].mean()) if has_time else np.nan,
                    'end_hour': float(seg['end_hour'].mean()) if has_time else np.nan,
                })
    return pd.DataFrame(rows)


def _apply_nonrecurrent_exclusion(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    exclusion_file = build_excluded_recurrent_days_path(cfg)
    if not os.path.exists(exclusion_file):
        raise FileNotFoundError(f"Exclusion file not found: {exclusion_file}. Run the recurrent detection cell first.")

    df_excl = pd.read_csv(exclusion_file)
    if 'vds_id' in df_excl.columns:
        df_excl = df_excl[df_excl['vds_id'].astype(str) == str(cfg['VDS_num'])]
    if df_excl.empty:
        return df

    if 'date' not in df_excl.columns and 'date_dt' in df_excl.columns:
        df_excl['date'] = pd.to_datetime(df_excl['date_dt'], errors='coerce').dt.strftime('%y%m%d')
    df_excl['date'] = df_excl['date'].astype(str)

    initial_len = len(df)

    # For entireday/hour, main df has period='off-peak' but exclusion file has
    # morning-peak/afternoon-peak rows. Drop any date that appears at all.
    if cfg.get('temporal_scale') in ('entireday', 'hour'):
        bad_dates = set(df_excl['date'])
        result = df[~df['date'].astype(str).isin(bad_dates)]
        print(f"Excluded {initial_len - len(result)} rows ({len(bad_dates)} dates) based on {os.path.basename(exclusion_file)}")
        return result

    if 'start_hour' not in df_excl.columns and 'start_time' in df_excl.columns:
        df_excl['start_hour'] = df_excl['start_time'].apply(time_to_fractional_hour)
    if 'end_hour' not in df_excl.columns and 'end_time' in df_excl.columns:
        df_excl['end_hour'] = df_excl['end_time'].apply(time_to_fractional_hour)

    work = df.copy()
    work['date'] = work['date'].astype(str)
    work['start_hour_tmp'] = work['start_time'].apply(time_to_fractional_hour)
    work['end_hour_tmp'] = work['end_time'].apply(time_to_fractional_hour)

    merge_left = ['date', 'period']
    merge_right = ['date', 'period']
    if 'start_hour' in df_excl.columns:
        merge_left.append('start_hour_tmp')
        merge_right.append('start_hour')
    if 'end_hour' in df_excl.columns:
        merge_left.append('end_hour_tmp')
        merge_right.append('end_hour')

    work = work.merge(df_excl[merge_right].drop_duplicates(), left_on=merge_left, right_on=merge_right, how='left', indicator=True)
    work = work[work['_merge'] == 'left_only'].drop(columns=['_merge'])
    drop_cols = [col for col in ['start_hour_tmp', 'end_hour_tmp'] + merge_right if col in work.columns and col not in df.columns]
    work = work.drop(columns=drop_cols, errors='ignore')
    print(f"Excluded {initial_len - len(work)} rows based on {os.path.basename(exclusion_file)}")
    return work


# === One place to filter ===
def apply_filters(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    df = df.copy()
    if 'division' in df.columns:
        df = df[df['division'] != -1]

    if cfg.get('dayofweek_exclude'):
        df = df[~df['dayofweek'].isin(cfg['dayofweek_exclude'])]
    if cfg.get('month_exclude'):
        df = df[~df['month'].isin(cfg['month_exclude'])]
    if cfg.get('year_exclude') and 'year' in df.columns:
        df = df[~df['year'].isin(cfg['year_exclude'])]

    df = df[df['period'].isin(cfg['period_include'][cfg['temporal_scale']])]

    if cfg.get('spatial_scope') == 'single' and str(cfg.get('VDS_num')) == '1205541':
        df = df[df['month'].isin(['2401', '2402', '2403'])]

    # df_sb ──→ drop_days_weird_peak_times filter  (checks start_time outliers)     
    if cfg.get('drop_days_weird_peak_times'):
        _sp = cfg.get('speedbased_params', {})
        _method  = cfg.get('method',         _sp.get('method',         'RDP_v'))
        _congest = cfg.get('congest_method',  _sp.get('congest_method', 'speed-solely'))
        if cfg['spatial_scope'] == 'multi_vds':
            file_path_sb = (f"./04_peak_period_result/c_daily_traffic_division_{cfg['spatial_scope']}_"
                            f"{cfg['VDS_list']}_speedbasedpeak_{cfg['aggregate_timeframe']}_"
                            f"{_method}_{_congest}.csv")
        else:
            file_path_sb = (f"./04_peak_period_result/c_daily_traffic_division_{cfg['spatial_scope']}_"
                            f"{cfg['VDS_num']}_speedbasedpeak_{cfg['aggregate_timeframe']}_"
                            f"{_method}_{_congest}.csv")
        if not os.path.exists(file_path_sb):
            print(f"[drop_days_weird_peak_times] CSV not found, skipping: {file_path_sb}")
            df_sb = None
        else:
            df_sb = pd.read_csv(file_path_sb)
            df_sb = df_sb[df_sb['period'].isin(['morning-peak', 'afternoon-peak'])]
            df_sb['date'] = df_sb['date'].astype(str)
    else:
        df_sb = None


    if cfg.get('drop_days_weird_peak_times') and df_sb is not None:
        morning_earliest = cfg.get('morning_earliest', '05:00')
        afternoon_latest = cfg.get('afternoon_latest', '19:00')
        st = pd.to_datetime(df_sb['start_time'], format='%H:%M', errors='coerce').dt.time
        t_me = pd.to_datetime(morning_earliest).time()
        t_al = pd.to_datetime(afternoon_latest).time()
        bad_mask = (
            ((df_sb['period'] == 'morning-peak')   & (st < t_me)) |
            ((df_sb['period'] == 'afternoon-peak') & (st > t_al))
        )
        bad_dates = set(df_sb.loc[bad_mask, 'date'].astype(str))
        before = len(df)
        df = df[~df['date'].astype(str).isin(bad_dates)]
        print(f"[drop_days_weird_peak_times] Removed {before - len(df)} rows from {len(bad_dates)} dates "
              f"| morning_earliest: {morning_earliest}, afternoon_latest: {afternoon_latest}")

    # if cfg.get('drop_multiplecongestion_days') and df_sb is not None:
    #     for period in ['morning-peak', 'afternoon-peak']:
    #         counts_per_date = df_sb[df_sb['period'] == period].groupby('date').size()
    #         bad_dates = set(counts_per_date[counts_per_date > 1].index.astype(str))
    #         if cfg['temporal_scale'] in ['entireday', 'hour']:
    #             df = df[~df['date'].astype(str).isin(bad_dates)]
    #         elif cfg['temporal_scale'] == 'speedbasedpeak':
    #             df = df[~((df['date'].astype(str).isin(bad_dates)) & (df['period'] == period))]

    if cfg.get('drop_nonrecurrent_days'):
        df = _apply_nonrecurrent_exclusion(df, cfg)

    # Merge segment_id from recurrent detection output (keeps adjacent retained
    # segments separate instead of merging them into one continuous group)
    if cfg.get('recurrent_method') == 'RDP_v' or cfg.get('recurrent_output_tag', '').startswith('RDP_v'):
        df = merge_segment_id(df, cfg)

    df_f = to_categorical_day(df.copy())
    df_f.to_csv("final_dates.csv")

    return to_categorical_day(df.copy())


def prepare_bpr_dataframe(cfg: dict) -> pd.DataFrame:
    df_all = load_and_annotate(cfg)
    df_use = apply_filters(df_all, cfg)
    if cfg.get('segment_aggregation'):
        df_use = aggregate_segment_level_bpr(df_use, cfg)
    return to_categorical_day(df_use.copy())


# stat

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.stattools import jarque_bera
from statsmodels.stats.diagnostic import linear_reset


def fit_bpr_ols_stats(dfg, xcol=None, ycol=None):
    """
    Fits: y = a + b x  (a = ln(tilde_alpha), b = beta)
    Returns a dict with tilde_alpha, t-stats, p-values, and R^2.
    """
    dfg = dfg.replace([np.inf, -np.inf], np.nan).dropna(subset=[xcol, ycol]).copy()
    print(dfg)
               
    if len(dfg) < 5:
        return None

    duration_col = None
    for candidate in ['duration', 'duration_min_mean']:
        if candidate in dfg.columns:
            duration_col = candidate
            break
    mean_val = dfg[duration_col].mean() if duration_col else np.nan
    median_val = dfg[duration_col].median() if duration_col else np.nan

    x = dfg[xcol].to_numpy()
    y = dfg[ycol].to_numpy()
    if np.nanmax(x) == np.nanmin(x):
        return None

    X = sm.add_constant(x)
    model = sm.OLS(y, X).fit()
    a = model.params[0]
    b = model.params[1]

    jb_stat, jb_pvalue, skew, kurt = jarque_bera(model.resid)
    reset_res = linear_reset(model, power=(2, 3), use_f=True)
    reset_stat = float(reset_res.fvalue)
    reset_p = float(reset_res.pvalue)

    y_hat = model.fittedvalues
    X_link = sm.add_constant(np.column_stack([y_hat, y_hat ** 2]))
    link_model = sm.OLS(y, X_link).fit()
    link_stat = float(link_model.tvalues[2])
    link_p = float(link_model.pvalues[2])

    N_0 = (0.15 / math.exp(a)) ** (1 / b)
    return {
        'ln_tilde_alpha': a,
        'alpha_t': float(model.tvalues[0]),
        'alpha_p': float(model.pvalues[0]),
        'N_0': float(N_0),
        'beta': float(b),
        'beta_t': float(model.tvalues[1]),
        'beta_p': float(model.pvalues[1]),
        'r2': float(model.rsquared),
        'n': int(model.nobs),
        'jb_stat': float(jb_stat),
        'jb_p': float(jb_pvalue),
        'reset_stat': reset_stat,
        'reset_p': reset_p,
        'link_t': link_stat,
        'link_p': link_p,
        'median': median_val,
        'mean': mean_val,
    }
