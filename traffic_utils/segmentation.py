from scipy import stats
import copy
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import ruptures as rpt

from .classification import (
    label_divisions_occupancy,
    label_divisions_speed,
    label_divisions_speedgap_islands,
    label_solely_occupancy,
    label_solely_speed,
)

# rdp.py: 'rdp_v': rdp itself algorithm: the manual function to recursively find the changepoint by RDP. it is applied in the "rdp_v_segmentation_pea"
import numpy as np

def rdp_v(points, epsilon):
    """
    Ramer–Douglas–Peucker with **vertical error** (y-axis) and full recursion.
    Returns the kept points as [[x0, y0], [x1, y1], ..., [xM, yM]] in order.

    Parameters
    ----------
    points : array-like, shape (n, 2)
        Polyline points ordered by x (e.g., time index, cumulative value).
        Column 0 = x (index or time), Column 1 = y (cumulative/signal).
    epsilon : float
        Vertical tolerance (same units as y). Larger epsilon -> fewer points.

    Returns
    -------
    simplified : ndarray, shape (m, 2)
        Subset of `points` (first and last always included), preserving order.
    """
    P = np.asarray(points, dtype=float)
    if P.ndim != 2 or P.shape[1] != 2:
        raise ValueError("`points` must be a (n, 2) array-like.")

    # Ensure sorted by x (defensive; your df.index is already increasing)
    order = np.argsort(P[:, 0], kind="stable")
    P = P[order]

    return _rdp_vertical_recursive(P, float(epsilon))


def _rdp_vertical_recursive(P, epsilon):
    n = P.shape[0]
    if n <= 2:
        return P

    x1, y1 = P[0]
    x2, y2 = P[-1]
    dx = x2 - x1

    # Predicted y on the straight line at each x (vertical projection)
    if dx == 0.0:
        # Degenerate: identical x at ends; interpolate along param t
        t = np.linspace(0.0, 1.0, n)
        y_line = y1 + t * (y2 - y1)
    else:
        t = (P[:, 0] - x1) / dx
        y_line = y1 + t * (y2 - y1)

    vertical_err = np.abs(P[:, 1] - y_line)

    # Find interior point with max vertical error
    if n > 2:
        slice_err = vertical_err[1:-1]
        
        # First max
        idx_rel = np.argmax(slice_err)
        idx_max = idx_rel + 1
        dmax = vertical_err[idx_max]
        
        # Mask out first max
        slice_err[idx_rel] = -np.inf
        
        # Second max
        idx2_rel = np.argmax(slice_err)
        idx2_abs = idx2_rel + 1
        dmax2 = vertical_err[idx2_abs]
        
    
    else:
        dmax = 0.0
        idx_max = None

    if dmax > epsilon:
        # Split and recurse on both halves (full recursion)
        left = _rdp_vertical_recursive(P[:idx_max + 1], epsilon)
        right = _rdp_vertical_recursive(P[idx_max:], epsilon)
        # Concatenate without duplicating the split point
        return np.vstack((left[:-1], right))
    else:
        # Endpoints approximate this span within tolerance
        return P[[0, -1]]

def _build_peak_list(df, aggregate_timeframe):
    """Build peak_list from 'division' column. Shared by all segmentation methods."""
    if df["division"].max() <= 0:
        return []
    bounds = (
        df.loc[df["division"] > 0]
          .groupby("division")["time_slot"]
          .agg(["min", "max"])
          .reset_index()
    )
    bounds["start_time"] = bounds["min"] - aggregate_timeframe / 2
    bounds["end_time"]   = bounds["max"] + aggregate_timeframe / 2
    bounds["length"]     = bounds["end_time"] - bounds["start_time"]
    return [
        {
            "idx":    int(row["division"]),
            "start":  f"{int(row['start_time'] // 60):02d}:{int(row['start_time'] % 60):02d}",
            "end":    f"{int(row['end_time']   // 60):02d}:{int(row['end_time']   % 60):02d}",
            "length": float(row["length"]),
        }
        for _, row in bounds.iterrows()
    ]


def PELT_plot(df, bkpts, date, VDS_num, aggregate_timeframe, peak_list=None, method=None, epsilon=None):
    """Save a speed-profile + breakpoint plot to ./02 fig/16 PELT/."""
    time_slot_arr = df["time_slot"].to_numpy() / 60.0

    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax1.set_xlabel("Time Interval (Hours)")
    ax1.set_ylabel("Speed (mph)")
    ax1.set_title("Cumulative Speed with Detected Peak Periods")
    ax1.grid(True)
    ax1.set_xlim(0, 25)
    ax1.set_xticks(np.arange(0, 25, 1))

    # 1. Changepoints (black dashed lines)
    for i, bkpt in enumerate(bkpts):
        if 0 <= bkpt < len(time_slot_arr):
            ax1.axvline(x=time_slot_arr[bkpt], color="black", linestyle="--",
                        label="Changepoints" if i == 0 else "")

    # 2. Peak-period boundaries and shaded regions
    if peak_list:
        for i, element in enumerate(peak_list):
            if element.get('idx', 0) > 0:
                # Parse HH:MM start / end
                s_hours, s_minutes = map(int, element['start'].split(':'))
                s_total = s_hours + s_minutes / 60
                e_hours, e_minutes = map(int, element['end'].split(':'))
                e_total = e_hours + e_minutes / 60

                # Shade the congested period (opaque red)
                label_span = 'Peak period' if i == 0 else ""
                ax1.axvspan(s_total, e_total, color='red', alpha=0.15,
                            label=label_span)

                # Boundary lines (red dashed)
                # label_line = 'Congested periods boundary' if i == 0 else ""
                # ax1.axvline(x=s_total, color='red', linestyle='--',
                #             linewidth=2, label=label_line)
                # ax1.axvline(x=e_total, color='red', linestyle='--',
                #             linewidth=2)

    ax1.plot(time_slot_arr, df["speed"].to_numpy(), color="green",
             linewidth=1, label="Speed")
    ax1.set_ylim(0, 80)

    cs_col = "cumsum_speed" if "cumsum_speed" in df.columns else None
    if cs_col:
        ts_re = np.concatenate([[0], time_slot_arr])
        cs_re = np.concatenate([[0], df[cs_col].to_numpy()])
        ax2 = ax1.twinx()
        ax2.plot(ts_re, cs_re, color="blue", linewidth=1,
                 label="Cumulative Speed")
        ax2.set_ylabel("Cumulative Speed")
        ax2.set_ylim(0, max(cs_re) if max(cs_re) > 0 else 1)
        lines2, labels2 = ax2.get_legend_handles_labels()
    else:
        lines2, labels2 = [], []

    lines1, labels1 = ax1.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    fig.tight_layout()
    save_dir = f"./02 fig/16 PELT/{VDS_num}"
    os.makedirs(save_dir, exist_ok=True)
    fig.savefig(f"{save_dir}/{VDS_num}_{date}_{aggregate_timeframe}_{method}_{epsilon}.png")
    plt.close(fig)


# Version1: pelt based

import numpy as np
import pandas as pd
import ruptures as rpt

def pelt_speedbased_peak(
    model,
    df,
    column,
    offpeak_ff_speed_threshold,
    speed_gap_threshold,
    aggregate_timeframe,
    date,
    VDS_num,
    pelt_penalty,
    pelt_min_length,
    min_off_len,
    min_peak_len,
    method,
):
    """
    Detect peak periods using PELT on the (raw) speed series, then classify and post-process
    exactly like the optimized RDP pipeline:
      1) Segment via PELT
      2) Classify segments as off-peak vs peak (long&fast => off-peak; else => peak)
      3) Collapse adjacent peak rows into contiguous division IDs (1..K; off-peak=0)
      4) Drop 'island' divisions (small gap, high mean, isolated by off-peak)
      5) Renumber divisions to be consecutive
      6) Apply min_peak_len filter
      7) Build peak_list for plotting/reporting

    Notes:
      - Ruptures' PELT returns breakpoints as *end indices* (with the last one equal to n).
        We convert to standard half-open segments [start:end) using: starts = [0] + bkpts[:-1], ends = bkpts.
      - The function uses vectorized groupby/agg and cumsum tricks to avoid per-group loops.

    Returns
    -------
    df_out : DataFrame
        Original df with added 'segment' and 'division' columns.
    peak_list : list[dict]
        [{'idx': k, 'start': 'HH:MM', 'end': 'HH:MM', 'length': seconds}, ...]
    """
    df = df.copy()

    # 1) (Optional) cumulative curve if you prefer; kept for parity with RDP version
    cs_name = f"cumsum_{column}"
    df[cs_name] = df[column].cumsum() * aggregate_timeframe / 60.0  # minutes

    # 2) PELT segmentation over the raw speed series (works well for level/slope shifts)
    signal = df[column].to_numpy()
    n = len(df)
    # min_size is in samples; pelt_min_length is in seconds ⇒ convert
    min_size = max(1, int(pelt_min_length / aggregate_timeframe))
    algo = rpt.Pelt(model=model, min_size=min_size, jump=1).fit(signal)

    bkpts = algo.predict(pen=pelt_penalty)  # list of end indices; last should be n
    # Safety: ensure last point included
    if bkpts[-1] != n:
        bkpts.append(n)

    # Build half-open segment bounds [start:end)
    starts = [0] + bkpts[:-1]
    ends   = bkpts

    # 3) Assign segment IDs (1..S) using positions; avoid chained assignment
    seg_id = np.zeros(n, dtype=np.int32)
    seg = 1
    for s, e in zip(starts, ends):
        if e > s:                       # ignore degenerate pieces
            seg_id[s:e] = seg
            seg += 1
    df["segment"] = seg_id

    # 4) Per-segment stats (vectorized)
    seg_stats = (
        df.groupby("segment")[column]
          .agg(seg_mean="mean", seg_min="min", seg_max="max", seg_size="size")
          .reset_index()
    )
    seg_stats["seg_len_sec"] = seg_stats["seg_size"] * aggregate_timeframe

    # 5) Off-peak vs peak for each segment (your rule)
    is_offpeak_seg = (seg_stats["seg_len_sec"] >= min_off_len) & \
                     (seg_stats["seg_mean"] >= offpeak_ff_speed_threshold)
    seg_stats["is_peak_seg"] = ~is_offpeak_seg

    # Map segment-level labels back to each row (one boolean per row)
    is_peak = (
        seg_stats
        .set_index("segment")["is_peak_seg"]
        .reindex(df["segment"])
        .to_numpy()
    )

    # 6) Collapse adjacent peak rows into block ids: 0 for off-peak, 1..K for peaks
    starts_flag = (is_peak) & (~pd.Series(is_peak).shift(fill_value=False).to_numpy())
    peak_block_id = starts_flag.cumsum()
    peak_block_id[~is_peak] = 0
    df["division"] = peak_block_id.astype(np.int32)

    # 7) Remove "short high-speed islands" (isolated peak blocks that look like free-flow)
    #    Division-level stats
    if df["division"].max() > 0:
        div_stats = (
            df.loc[df["division"] > 0]
              .groupby("division")[column]
              .agg(avg_speed="mean", vmin="min", vmax="max", size="size")
              .reset_index()
        )
        div_stats["speed_gap"] = div_stats["vmax"] - div_stats["vmin"]
        div_stats["len_sec"]   = div_stats["size"] * aggregate_timeframe

        # Division bounds (first/last indices) in a vectorized way
        first_idx = (
            df.loc[df["division"] > 0]
              .groupby("division")
              .head(1)
              .groupby("division")
              .apply(lambda g: g.index[0])
        )
        last_idx = (
            df.loc[df["division"] > 0]
              .groupby("division")
              .tail(1)
              .groupby("division")
              .apply(lambda g: g.index[0])
        )
        div_bounds = pd.DataFrame(
            {"division": first_idx.index, "first": first_idx.values, "last": last_idx.values}
        )
        div_all = div_stats.merge(div_bounds, on="division", how="left")

        div_arr = df["division"].to_numpy()
        first_arr = div_all["first"].to_numpy()
        last_arr  = div_all["last"].to_numpy()

        prev_div_vals = np.where(first_arr > 0, div_arr[first_arr - 1], 0)
        next_div_vals = np.where(last_arr  < n - 1, div_arr[last_arr + 1], 0)

        island_mask = (
            (div_all["speed_gap"] <= speed_gap_threshold) &
            (div_all["avg_speed"] >  offpeak_ff_speed_threshold) &
            (prev_div_vals == 0) &
            (next_div_vals == 0)
        )
        islands = set(div_all.loc[island_mask, "division"].to_numpy())
        if islands:
            df.loc[df["division"].isin(islands), "division"] = 0

            # Rebuild contiguous division IDs after island removal
            is_peak2 = df["division"].to_numpy() > 0
            starts2  = (is_peak2) & (~pd.Series(is_peak2).shift(fill_value=False).to_numpy())
            peak_block_id2 = starts2.cumsum()
            peak_block_id2[~is_peak2] = 0
            df["division"] = peak_block_id2.astype(np.int32)

    # 8) Apply min_peak_len filter (drop very short peaks), then renumber again
    if df["division"].max() > 0 and (min_peak_len is not None) and (min_peak_len > 0):
        bounds_tmp = (
            df.loc[df["division"] > 0]
              .groupby("division")["time_slot"]
              .agg(["min", "max"])
              .reset_index()
        )
        # Use ± half bin to get inclusive duration
        bounds_tmp["start_time"] = bounds_tmp["min"] - aggregate_timeframe / 2
        bounds_tmp["end_time"]   = bounds_tmp["max"] + aggregate_timeframe / 2
        bounds_tmp["length"]     = bounds_tmp["end_time"] - bounds_tmp["start_time"]

        short_divs = set(bounds_tmp.loc[bounds_tmp["length"] < min_peak_len, "division"].to_numpy())
        if short_divs:
            df.loc[df["division"].isin(short_divs), "division"] = 0
            # Renumber after removal
            is_peak3 = df["division"].to_numpy() > 0
            starts3  = (is_peak3) & (~pd.Series(is_peak3).shift(fill_value=False).to_numpy())
            peak_block_id3 = starts3.cumsum()
            peak_block_id3[~is_peak3] = 0
            df["division"] = peak_block_id3.astype(np.int32)

    # 9) Build peak_list (vectorized)
    if df["division"].max() > 0:
        bounds = (
            df.loc[df["division"] > 0]
              .groupby("division")["time_slot"]
              .agg(["min", "max"])
              .reset_index()
        )
        bounds["start_time"] = bounds["min"] - aggregate_timeframe / 2
        bounds["end_time"]   = bounds["max"] + aggregate_timeframe / 2
        bounds["length"]     = bounds["end_time"] - bounds["start_time"]

        peak_list = [
            {
                "idx": int(row["division"]),
                "start": f"{int(row['start_time'] // 60):02d}:{int(row['start_time'] % 60):02d}",
                "end":   f"{int(row['end_time']   // 60):02d}:{int(row['end_time']   % 60):02d}",
                "length": float(row["length"]),
            }
            for _, row in bounds.iterrows()
        ]
    else:
        peak_list = []

    # Optional: visualize (uses your existing function)
    # For plotting consistency with your RDP plotter, pass 'bkpts' (end indices)
    PELT_plot(df, bkpts, date, VDS_num, aggregate_timeframe, peak_list, method, pelt_penalty)

    return df, peak_list


# Version2: RDP_v based
from rdp import rdp
import numpy as np
import pandas as pd

def rdp_v_segmentation_peak(
    df, column, epsilon, offpeak_ff_speed_threshold, speed_gap_threshold,
    aggregate_timeframe, date, VDS_num, min_off_len, min_peak_len, method, congest_method, occ_threshold, FD_phase):
    
    df = df.copy()

    # 1) Prepend artificial free-flow row as RDP_v anchor
    cs_name = f"cumsum_{column}"
    art_speed = offpeak_ff_speed_threshold
    art_row = pd.Series({column: art_speed}, name=-1)
    df_aug = pd.concat([art_row.to_frame().T, df], ignore_index=True)
    df_aug[cs_name] = df_aug[column].cumsum() * aggregate_timeframe / 60.0

    # 2) RDP on (pos, cumsum) — on augmented data
    pos = np.arange(len(df_aug))
    pts = np.column_stack([pos, df_aug[cs_name].to_numpy()])
    bp = rdp_v(pts, epsilon)[:, 0].astype(int)  # vertical-distance RDP
    if bp[-1] != pos[-1]:
        bp = np.append(bp, pos[-1])

    # 3) Assign segment ids via slices (fast, no chained assignment)
    #    seg_id[0]=1 now hits the disposable artificial row
    seg_id = np.zeros(len(df_aug), dtype=np.int32)
    seg_id[0] = 1
    seg = 0
    for s, e in zip(bp[:-1], bp[1:]):
        seg += 1
        seg_id[s+1:e+1] = seg

    # 4) Remove artificial first row; strip art-row breakpoint (x=0)
    bp_real = bp[bp != 0]          # real-data breakpoints only
    df_aug = df_aug.iloc[1:].reset_index(drop=True)
    seg_id = seg_id[1:]
    df_aug["segment"] = seg_id
    # Recompute cumsum on real data (augmented cumsum is offset by art_speed)
    df_aug[cs_name] = df_aug[column].cumsum() * aggregate_timeframe / 60.0
    df = df_aug

    # speed-duration-only, 'speedgap-neighbor', 'occ', occ-soley
    if congest_method == 'speedgap-neighbor':
        df = label_divisions_speedgap_islands(
            df=df, column="speed", aggregate_timeframe=aggregate_timeframe, min_off_len=min_off_len,
            offpeak_ff_speed_threshold=offpeak_ff_speed_threshold,
            speed_gap_threshold=speed_gap_threshold)

    elif congest_method == 'speed-duration-only':
        df = label_divisions_speed(df=df, column="speed", aggregate_timeframe=aggregate_timeframe, min_off_len=min_off_len, offpeak_ff_speed_threshold=offpeak_ff_speed_threshold, speed_gap_threshold=speed_gap_threshold)

    elif congest_method == 'occ':
        df = label_divisions_occupancy(
            df=df, column="occ",
            aggregate_timeframe=aggregate_timeframe, min_off_len=min_off_len, offpeak_ff_speed_threshold=offpeak_ff_speed_threshold, occ_threshold=occ_threshold)

    elif congest_method == 'occ-solely':
        df = label_solely_occupancy(
            df=df, column="occ",
            aggregate_timeframe=aggregate_timeframe, min_off_len=min_off_len, offpeak_ff_speed_threshold=offpeak_ff_speed_threshold, occ_threshold=occ_threshold[VDS_num], FD_phase=FD_phase)

    elif congest_method == 'speed-solely':
        df = label_solely_speed(
            df=df, aggregate_timeframe=aggregate_timeframe, offpeak_ff_speed_threshold=offpeak_ff_speed_threshold)

    peak_list = _build_peak_list(df, aggregate_timeframe)

    # 9) Plot + return (reuse your existing plotter)
    PELT_plot(df, bp_real.tolist(), date, VDS_num, aggregate_timeframe, peak_list, method, epsilon)
    return df, peak_list

# Version4: RDP based
# def rdp_segmentation_peak(df, column, epsilon, freeflow_speed, freeflow_speed_epsilon, aggregate_timeframe, date, VDS_num, min_off_len, min_peak_len, method):

from rdp import rdp
import numpy as np
import pandas as pd

def rdp_segmentation_peak(df, column, epsilon, freeflow_speed, freeflow_speed_epsilon,
                          aggregate_timeframe, date, VDS_num, min_off_len, min_peak_len, method):
    """
    Segment cumulative speed using RDP and classify segments as peak/non-peak.
    Args:
        df (DataFrame): Input DataFrame with 'time_slot' and speed column.
        column (str): Speed column name.
        epsilon (float): Tolerance for RDP (controls segmentation granularity).
        speed_upper (float): Threshold to define peak periods.
        aggregate_timeframe (int): Seconds per row (e.g., 300).
        date (str): For plotting.
        VDS_num (str): For plotting.
    
    """
    df = df.copy()
    df["cumsum_" + column] = df[column].cumsum() * aggregate_timeframe / 60

    # Apply RDP
    points = np.column_stack([df.index, df["cumsum_" + column].values])
    
    rdp_indices = rdp(points, epsilon=epsilon)[:, 0].astype(int).tolist()
    if rdp_indices[-1] != df.index[-1]:
        rdp_indices.append(df.index[-1])

    print("RDP_Breakpoints:", rdp_indices)
    df["division"] = 0
    peak_list = []
    idx = 0
    prev_peak_end = 0

    for start, end in zip(rdp_indices[:-1], rdp_indices[1:]):
        seg_mean = df[column].iloc[(start):(end+1)].mean()
        seg_len = (end+1 - start) * aggregate_timeframe

        if seg_len > min_off_len and abs(seg_mean - freeflow_speed) < freeflow_speed_epsilon:
            continue
        else:
            if prev_peak_end != start:
                idx += 1
            df["division"].iloc[(start):(end+1)] = idx
            # df["division"].iloc[start] = idx
            ## Since it is hard to explain, ignore including one more point at the congested period.
            # if end+1 <= (len(df) -1) :
            #     df["division"].iloc[(end+1)] = idx
                    
            prev_peak_end = end

    for div_idx, group in df.groupby("division"):
        # start_time = group["time_slot"].min() - aggregate_timeframe/2
        # end_time = group["time_slot"].max() + aggregate_timeframe/2
        start_time = group["time_slot"].min()
        end_time = group["time_slot"].max()
        seg_len = end_time - start_time

        if seg_len < min_peak_len and div_idx != 0:
            df.loc[df['division'] == div_idx, 'division'] = -1
            div_idx = -1

        if div_idx != 0:
            peak_list.append({
                "idx": div_idx,
                "start": f"{int(start_time // 60):02d}:{int(start_time % 60):02d}",
                "end": f"{int(end_time // 60):02d}:{int(end_time % 60):02d}",
                "length": seg_len
            })

    PELT_plot(df, rdp_indices, date, VDS_num, aggregate_timeframe, peak_list, method)

    return df, peak_list

# Version5: def speedbasedpeak(df, column, speed_upper, min_minutes, max_outliers, aggregate_timeframe, method):
def speedbasedpeak(df, column, speed_upper, min_minutes, max_outliers, aggregate_timeframe, method):
    start = 0
    outliers = 0
    idx = 1

    prev = 0
    continuity = 0
    peak_list = []
    changepoints = []

    df = df.copy()
    df["cumsum_" + column] = df[column].cumsum()
    
    df['division'] = 0
    interval_size = df['time_slot'][1] - df['time_slot'][0]
    
    for i in range(len(df)):
        if df[column][i] >= speed_upper:
            outliers += 1

            # prev == i-1
            if prev == (i-1):
                continuity +=1
                prev = i
            else:
                continuity = 0

            if continuity > max_outliers/3: 
                outliers = 0
                continuity = 0
                start = i

        if outliers > max_outliers:
            if (i - start) * interval_size > min_minutes:
                df['division'].iloc[start:i] = idx
                
                start_time = df.iloc[start]["time_slot"] - aggregate_timeframe/2
                end_time = df.iloc[i-1]["time_slot"] + aggregate_timeframe/2
                
                length = end_time - start_time
                
                peak_list.append({
                    "idx": idx,
                    "start": f"{int(start_time // 60):02d}:{int(start_time % 60):02d}",
                    "end": f"{int((end_time) // 60):02d}:{int((end_time) % 60):02d}",
                    "length": length
                })
                changepoints.append(start)
                changepoints.append(i)

                idx += 1
                
            start = i
            outliers = 0
            prev = i

    # Plot with RDP breakpoints
    PELT_plot(df, changepoints, date, VDS_num, aggregate_timeframe, peak_list, method)
    
    return df, peak_list

# Version6: divisions based on fixed temporal_range.

def detect_speed_peaks(traffic, date, config):
    """
    Identify peak periods based on speed using chosen method (pelt, derivative, RDP, etc.).
    Returns updated DataFrame and list of peak intervals.
    """
    params = dict(config['speedbased_params'])
    params.setdefault('method', config.get('method', 'RDP_v'))
    params.setdefault('congest_method', config.get('congest_method', 'speed-solely'))
    if params['method'] == 'RDP':
        return rdp_segmentation_peak(
            df = traffic, column='speed',
            epsilon=1.5, freeflow_speed=params['freeflow_speed'],
            freeflow_speed_epsilon=params['freeflow_speed_epsilon'],
            aggregate_timeframe=config['aggregate_timeframe'],
            date=date, VDS_num=config['VDS_num'],
            min_off_len=params['min_off_len'],
            min_peak_len=params['min_peak_len'],
            method=params['method']
        )
    elif params['method'] == 'RDP_v':
        print(config['VDS_num'])
        return rdp_v_segmentation_peak(
            df = traffic, column='speed',
            # epsilon=12,3,5(이값이 현재최신),4,10, 4(최신), 3(ㅚ신)
            epsilon=2.5, 
            offpeak_ff_speed_threshold= params['offpeak_ff_speed_threshold'].get(config['VDS_num'], 55),
            # offpeak_ff_speed_threshold= params['offpeak_ff_speed_threshold'],
            speed_gap_threshold = params['speed_gap_threshold'],
            aggregate_timeframe=config['aggregate_timeframe'],
            date=date, VDS_num=config['VDS_num'],
            min_off_len=params['min_off_len'],
            min_peak_len=params['min_peak_len'],
            method=params['method'],
            congest_method = params['congest_method'],
            occ_threshold = params['occ_threshold'],
            FD_phase = params['FD_phase'],
        )
    elif params['method'] == 'pelt':
        return pelt_speedbased_peak(
            model = "l2",
            df = traffic, column='speed', 
            offpeak_ff_speed_threshold= params['offpeak_ff_speed_threshold'],
            speed_gap_threshold = params['speed_gap_threshold'],
            aggregate_timeframe=config['aggregate_timeframe'],
            date=date, VDS_num=config['VDS_num'],
            # pelt_penalty = 320,2500 # (previous value in TRB), 200z
            pelt_penalty = 100,
            pelt_min_length = params['pelt_min_length'],
            min_off_len=params['min_off_len'],
            min_peak_len=params['min_peak_len'],
            method=params['method']
        )
    elif params['method'] == 'pelt_directpeak':
        return pelt_speedbased_directpeak(
            model = "l2",
            df = traffic, column='speed', 
            freeflow_speed=params['freeflow_speed'],
            freeflow_speed_epsilon=params['freeflow_speed_epsilon'],
            aggregate_timeframe=config['aggregate_timeframe'],
            date=date, VDS_num=config['VDS_num'],
            pelt_penalty = 1000,
            pelt_min_length = params['pelt_min_length'],
            min_off_len=params['min_off_len'],
            min_peak_len=params['min_peak_len'],
            method=params['method']
        )
    elif params['method'] == 'derivative':
        return derivative_based_segmentation(
            df = traffic, column='speed', 
            slope_threshold=80, window=15, min_gap=10, speed_upper=speed_upper, 
            aggregate_timeframe=config['aggregate_timeframe'], 
            min_length = params['min_length'], 
            method = params['method'])
            # traffic_within_day_intpol, peak_list = derivative_based_segmentation(traffic_within_day_intpol, column='speed', slope_threshold=15, window=60, min_gap=10, speed_upper=55, aggregate_timeframe=aggregate_timeframe, min_length= min_length, method = method)
    elif params['method'] == 'joon':
         return speedbasedpeak(
             df = traffic, column='speed', 
             speed_upper = params['speed_upper'], min_minutes = params['min_peak_len'], 
             max_outliers = 0, aggregate_timeframe = config['aggregate_timeframe'], 
             method = params['method'])
