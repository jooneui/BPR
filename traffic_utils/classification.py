from scipy import stats
import numpy as np
import pandas as pd


import numpy as np
import pandas as pd

def _compute_seg_stats(df, value_col, aggregate_timeframe):
    """
    Returns per-segment stats: mean/min/max/size and length in seconds.
    If value_col == 'speed', seg_mean is computed as sum(flow) / sum(density).
    Expects df['segment'] already assigned.
    """

    g = df.groupby("segment")

    if value_col == "speed":
        # Weighted mean speed = sum(flow) / sum(density)
        seg_mean = (g["flow"].sum() / g["density"].sum()).rename("seg_mean")
        
        # For min/max you probably still want the min/max *speed* values
        seg_minmax = g["speed"].agg(seg_min="min", seg_max="max", seg_size="size")
        seg_stats = pd.concat([seg_mean, seg_minmax], axis=1).reset_index()

    else:
        seg_stats = (
            g[value_col]
              .agg(seg_mean="mean", seg_min="min", seg_max="max", seg_size="size")
              .reset_index()
        )

    seg_stats["seg_len_sec"] = seg_stats["seg_size"] * aggregate_timeframe
    return seg_stats

def _build_peak_list(df, aggregate_timeframe):
    """
    Build [{'idx', 'start','end','length'}] from df['division'] and df['time_slot'] (seconds).
    Uses ± half-bin convention for boundaries.
    """
    if df["division"].max() <= 0:
        return []
    bounds = (
        df.loc[df["division"] > 0]
          .groupby("division")["time_slot"]
          .agg(["min", "max"])
          .reset_index()
    )
    # bounds["start_time"] = bounds["min"] - aggregate_timeframe / 2
    # bounds["end_time"]   = bounds["max"] + aggregate_timeframe / 2

    bounds["start_time"] = bounds["min"] 
    bounds["end_time"]   = bounds["max"] 

    
    bounds["length"] = bounds["end_time"] - bounds["start_time"]
    return [
        {
            "idx": int(row["division"]),
            "start": f"{int(row['start_time'] // 60):02d}:{int(row['start_time'] % 60):02d}",
            "end":   f"{int(row['end_time']   // 60):02d}:{int(row['end_time']   % 60):02d}",
            "length": float(row["length"]),
        }
        for _, row in bounds.iterrows()
    ]

#congest_method: speed-duration-only

def label_divisions_speed(
    df,
    column,
    aggregate_timeframe,
    min_off_len,
    offpeak_ff_speed_threshold,
    speed_gap_threshold
):
    """
    1) Off-peak vs peak per segment by speed & duration.
    2) Collapse to contiguous peak blocks -> df['division'].
    3) Remove 'islands' (small gap, high mean, isolated by off-peak neighbors).
    4) Renumber by contiguity.
    Returns: df with 'division' updated (np.int32)
    """
    # --- 1) Per-segment stats (already computed above) ---
    # seg_stats has: columns ['segment','seg_mean','seg_min','seg_max','seg_size','seg_len_sec']
    seg_stats = _compute_seg_stats(df, column, aggregate_timeframe)
    
    # --- 2) Initial classification (your baseline rule) ---
    is_offpeak_seg = (seg_stats["seg_len_sec"] >= min_off_len) & \
                     (seg_stats["seg_mean"]    >= offpeak_ff_speed_threshold)
    
    is_peak_seg = ~is_offpeak_seg
    
    # --- 5) Demote peaks that are NOT isolated-offpeak but look free-flow ---
    # “firstly detected as congested” = is_peak_seg
    # Need to convert to uncongested if (~isolated_offpeak & looks_freeflow)
    is_peak_seg_final = is_peak_seg
    
    # Re-index by segment id for mapping to rows
    is_peak_seg_final.index = seg_stats["segment"]
    
    # --- 6) Map to rows and collapse to contiguous divisions ---
    is_peak_rows = (
        pd.Series(is_peak_seg_final, index=is_peak_seg_final.index)
          .reindex(df["segment"])
          .to_numpy()
    )

    # ✅ If segment is not peak (False), set segment value to 0
    df['seg_con'] = 0
    df.loc[is_peak_rows, "seg_con"] = 1
    
    starts = is_peak_rows & (~pd.Series(is_peak_rows).shift(fill_value=False).to_numpy())
    div = starts.cumsum()
    div[~is_peak_rows] = 0
    df["division"] = div.astype(np.int32)

    return df

#congest_method: speedgap-neighbor
def label_divisions_speedgap_islands(
    df,
    column,
    aggregate_timeframe,
    min_off_len,
    offpeak_ff_speed_threshold,
    speed_gap_threshold
):
    """
    1) Off-peak vs peak per segment by speed & duration.
    2) Collapse to contiguous peak blocks -> df['division'].
    3) Remove 'islands' (small gap, high mean, isolated by off-peak neighbors).
    4) Renumber by contiguity.
    Returns: df with 'division' updated (np.int32)
    """
    # --- 1) Per-segment stats (already computed above) ---
    # seg_stats has: columns ['segment','seg_mean','seg_min','seg_max','seg_size','seg_len_sec']
    seg_stats = _compute_seg_stats(df, column, aggregate_timeframe)
    seg_stats["speed_gap"] = seg_stats["seg_max"] - seg_stats["seg_min"]
    
    # --- 2) Initial classification (your baseline rule) ---
    is_offpeak_seg = (seg_stats["seg_len_sec"] >= min_off_len) & \
                     (seg_stats["seg_mean"]    >= offpeak_ff_speed_threshold)
    is_peak_amb_seg = (seg_stats["seg_len_sec"] < min_off_len) & \
                     (seg_stats["seg_mean"]    >= offpeak_ff_speed_threshold)
    
    is_peak_seg = ~is_offpeak_seg
    
    # (Optional) edge handling: treat ends as their own neighbor to avoid edge artifacts
    prev_is_peak = is_peak_seg.shift(1)
    next_is_peak = is_peak_seg.shift(-1)
    if not is_peak_seg.empty:
        prev_is_peak.iloc[0]  = is_peak_seg.iloc[0]
        next_is_peak.iloc[-1] = is_peak_seg.iloc[-1]
    
    # --- 3) Isolated OFF-PEAK: off-peak segment between two peak segments ---
    isolated_peak = is_peak_amb_seg & prev_is_peak & next_is_peak
    
    # --- 4) "Looks free-flow" (flat & fast) ---
    looks_freeflow = (seg_stats["speed_gap"] < speed_gap_threshold)
    
    # --- 5) Demote peaks that are NOT isolated-offpeak but look free-flow ---
    # “firstly detected as congested” = is_peak_seg
    # Need to convert to uncongested if (~isolated_offpeak & looks_freeflow)
    demote_mask = is_peak_amb_seg & (~isolated_peak) & looks_freeflow
    is_peak_seg_final = is_peak_seg & (~demote_mask)
    
    # Re-index by segment id for mapping to rows
    is_peak_seg_final.index = seg_stats["segment"]
    
    # --- 6) Map to rows and collapse to contiguous divisions ---
    is_peak_rows = (
        pd.Series(is_peak_seg_final, index=is_peak_seg_final.index)
          .reindex(df["segment"])
          .to_numpy()
    )

    # ✅ If segment is not peak (False), set segment value to 0
    df['seg_con'] = 0
    df.loc[is_peak_rows, "seg_con"] = 1
    
    starts = is_peak_rows & (~pd.Series(is_peak_rows).shift(fill_value=False).to_numpy())
    div = starts.cumsum()
    div[~is_peak_rows] = 0
    df["division"] = div.astype(np.int32)

    return df

# congest_method: occ
def label_divisions_occupancy(
    df,
    column,
    aggregate_timeframe,
    min_off_len,
    offpeak_ff_speed_threshold,
    occ_threshold
):
    
    """
    1) Off-peak vs peak per segment by speed & duration.
    2) Collapse to contiguous peak blocks -> df['division'].
    3) Remove 'islands' (small gap, high mean, isolated by off-peak neighbors).
    4) Renumber by contiguity.
    Returns: df with 'division' updated (np.int32)
    """
    # Per-segment stats on the speed column
    seg_stats_speed = _compute_seg_stats(df, 'speed', aggregate_timeframe)
    seg_stats_occ = _compute_seg_stats(df, 'occ', aggregate_timeframe)
    
    # --- 2) Initial classification (your baseline rule) ---
    is_offpeak_seg = (seg_stats_speed["seg_len_sec"] >= min_off_len) & \
                     (seg_stats_speed["seg_mean"]    >= offpeak_ff_speed_threshold)
    
    is_peak_seg = ~is_offpeak_seg
    is_cong_amb = (seg_stats_speed["seg_len_sec"] < min_off_len) & (seg_stats_speed["seg_mean"]    >= offpeak_ff_speed_threshold)

    looks_freeflow = (seg_stats_occ["seg_mean"] < occ_threshold)

    # --- 5) Demote peaks that are NOT isolated-offpeak but look free-flow ---
    # “firstly detected as congested” = is_peak_seg
    # Need to convert to uncongested if (~isolated_offpeak & looks_freeflow)
    demote_mask = is_cong_amb  & looks_freeflow
    is_peak_seg_final = is_peak_seg & (~demote_mask)
    
    # Re-index by segment id for mapping to rows
    # is_peak_seg_final: 각 seg의 con/uncon 상태를 아렬줌 (T/F) 동시에 seg_stats_occ는 inde를 가짐. 이것을 df['segment']로 mapping
    is_peak_seg_final.index = seg_stats_occ["segment"]
    
    # --- 6) Map to rows and collapse to contiguous divisions ---
    is_peak_rows = (
        pd.Series(is_peak_seg_final, index=is_peak_seg_final.index)
          .reindex(df["segment"])
          .to_numpy()
    )

    # ✅ If segment is not peak (False), set segment value to 0
    df['seg_con'] = 0
    df.loc[is_peak_rows, "seg_con"] = 1
    
    starts = is_peak_rows & (~pd.Series(is_peak_rows).shift(fill_value=False).to_numpy())
    div = starts.cumsum()
    div[~is_peak_rows] = 0
    df["division"] = div.astype(np.int32)

    return df

# congest_method: occ-soley
def label_solely_occupancy(
    df,
    column,
    aggregate_timeframe,
    min_off_len,
    offpeak_ff_speed_threshold,
    occ_threshold,
    FD_phase):
        
# 1) Compare off-peak and peak segments by speed and duration.
# 2) Merge contiguous peak blocks into 'df['division']'.
# 3) Remove 'islands' (small gaps, high mean values, isolated by off-peak neighbors).
# 4) Renumber based on contiguity.
# Returns: df with 'division' updated (np.int32).

    # Per-segment stats on the speed column
    seg_stats_occ = _compute_seg_stats(df, 'occ', aggregate_timeframe)
    seg_stats_speed = _compute_seg_stats(df, 'speed', aggregate_timeframe)

    is_peak_seg = None  # initialize
    is_peak_seg_final = None  # initialize


    # --- 2) Initial classification (your baseline rule) ---
    if FD_phase == 'three_phases':      
        is_uc_seg = (seg_stats_occ["seg_mean"]   < occ_threshold['occ_l'])
        is_oc_seg = (seg_stats_occ["seg_mean"]  >= occ_threshold['occ_h'])

        mid_band = (seg_stats_occ["seg_mean"]  >= occ_threshold['occ_l']) & (seg_stats_occ["seg_mean"]   < occ_threshold['occ_h'])
        A_long = (seg_stats_occ["seg_len_sec"] >= min_off_len)
        B_fast = (seg_stats_speed["seg_mean"] >= offpeak_ff_speed_threshold)

        # final segment labels
        is_uc_seg = is_uc_seg | (mid_band & A_long & B_fast)
        is_oc_seg = is_oc_seg
        is_c_seg  = mid_band & (~(A_long & B_fast))         # short OR long-but-not-fast
        
        # congested side = C ∪ OC
        is_peak_seg = is_c_seg | is_oc_seg
    
    elif FD_phase == 'two_phases':
        occ_c = occ_threshold['occ_c']
        
        is_uc_seg  = seg["occ_mean"] <  occ_c
        is_oc_seg  = seg["occ_mean"] >= occ_c
        
        is_c_seg   = pd.Series(False, index=seg.index)      # no mid-band in two-phase
        is_peak_seg = is_oc_seg
        
    is_peak_seg_final = is_peak_seg
    
    # Re-index by segment id for mapping to rows
    is_peak_seg_final.index = seg_stats_occ["segment"]
    
    # --- 6) Map to rows and collapse to contiguous divisions ---
    is_peak_rows = (
        pd.Series(is_peak_seg_final, index=is_peak_seg_final.index)
          .reindex(df["segment"])
          .to_numpy())
   
    # uncongested(uc): 0, c: 1
    df['seg_con'] = 0
    df.loc[is_peak_rows, "seg_con"] = 1
    
    if FD_phase == 'three_phases':
        is_c_seg = is_c_seg.rename(index=lambda x: x+1)
        
        is_c_rows = (
        pd.Series(is_c_seg, index=is_peak_seg_final.index)
          .reindex(df["segment"])
          .to_numpy())

        df.loc[(~is_c_rows) & (is_peak_rows), "seg_con"] = 2
    
    starts = is_peak_rows & (~pd.Series(is_peak_rows).shift(fill_value=False).to_numpy())
    div = starts.cumsum()
    div[~is_peak_rows] = 0

    # starts_d = np.where((div[:-1] == 0) & (div[1:] != 0))[0]
    # # set the 0 value just before the run to match the upcoming non-zero value
    # for s in starts_d:
    #     div[s] = div[s + 1]
    
    df["division"] = div.astype(np.int32)

    return df

# congest_method: occ-soley
def label_solely_speed(
    df,
    aggregate_timeframe,
    offpeak_ff_speed_threshold):
        
# 1) Compare off-peak and peak segments by speed and duration.
# 2) Merge contiguous peak blocks into 'df['division']'.
# 3) Remove 'islands' (small gaps, high mean values, isolated by off-peak neighbors).
# 4) Renumber based on contiguity.
# Returns: df with 'division' updated (np.int32).

    # Per-segment stats on the speed column
    seg_stats_speed = _compute_seg_stats(df, 'speed', aggregate_timeframe)

    is_peak_seg = None  # initialize
    is_peak_seg_final = None  # initialize

    # --- 2) Initial classification (your baseline rule) ---
    is_c_seg = (seg_stats_speed["seg_mean"]   < offpeak_ff_speed_threshold)
    is_uc_seg = ~is_c_seg
    
    # congested side = C ∪ OC
    is_peak_seg_final = is_c_seg
    
    # Re-index by segment id for mapping to rows
    is_peak_seg_final.index = seg_stats_speed["segment"]
    
    # --- 6) Map to rows and collapse to contiguous divisions ---
    is_peak_rows = (
        pd.Series(is_peak_seg_final, index=is_peak_seg_final.index)
          .reindex(df["segment"])
          .to_numpy())
   
    # uncongested(uc): 0, c: 1
    df['seg_con'] = 0
    df.loc[is_peak_rows, "seg_con"] = 1
    
    starts = is_peak_rows & (~pd.Series(is_peak_rows).shift(fill_value=False).to_numpy())
    div = starts.cumsum()
    div[~is_peak_rows] = 0
    
    df["division"] = div.astype(np.int32)
    return df
