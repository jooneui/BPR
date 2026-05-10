# Bug: Adjacent Retained Segments Should NOT Be Merged

## Problem Description

In `classify_facet_rdpv()`, when the RDP algorithm identifies breakpoints that create multiple segments, each segment is independently classified as `retained` (recurrent) or `excluded`. However, **adjacent retained segments are currently treated as one continuous recurrent region** in downstream processing.

### Example

Suppose RDP finds breakpoints at weeks 1, 5, and 10, creating two segments:

- **Segment 2–5**: recurrent peak (early-start weeks, e.g., start_hour ≈ 7:00)
- **Segment 6–10**: recurrent peak (late-start weeks, e.g., start_hour ≈ 8:30)

Current behavior: both segments mark `recurrent_band = True`, so downstream BPR fitting treats weeks 2–10 as one homogeneous group, fitting a single BPR curve to data from two distinct peak patterns.

**This degrades R²** because the two segments represent different traffic conditions (different start times, different durations), and forcing them into one BPR curve increases residual variance.

### Desired behavior

Each retained segment should remain **separate**. Weeks in segment 2–5 should be labeled with one `segment_id`, and weeks in segment 6–10 with a different `segment_id`, even though both are `recurrent_band = True`.

In the BPR fitting step (`aggregate_segment_level_bpr`), each `segment_id` within a (VDS, day, period) group produces its own aggregated data point. This preserves the distinct peak patterns and should improve R².

## Root Cause

The issue exists at two levels:

### 1. In `classify_facet_rdpv()` — the output DataFrame

Each row gets `recurrent_band = True/False` and `excluded_band = True/False`, but **no `segment_id` column**. This means downstream code cannot distinguish which retained segment a week belongs to — it only knows "this week is recurrent" or "this week is excluded."

**Fix**: Add a `segment_id` column to the output DataFrame in `classify_facet_rdpv()`. The segment_id should be:
- A unique integer for each retained segment (e.g., 1, 2, 3, ...)
- `NaN` or `-1` for excluded and no-peak weeks
- Reset per (dayofweek, period) facet

### 2. In `aggregate_segment_level_bpr()` — the aggregation logic

Current code groups by `(period, dayofweek)` and then creates `segment_id` based on **consecutive week numbers** (`week_num.diff().fillna(1).ne(1).cumsum()`). This groups ALL consecutive recurrent weeks together regardless of RDP breakpoints.

**Fix**: If `segment_id` already exists in the DataFrame (from the recurrent detection), use it directly instead of recomputing from week gaps. Only fall back to the week-gap method if `segment_id` is missing.

### 3. In `_apply_nonrecurrent_exclusion()` — the exclusion CSV

The exclusion file lists **excluded** days/weeks (those in non-retained segments). This is correct — only excluded segments are dropped. No change needed here, but the exclusion file should also carry `segment_id` for traceability.

## Implementation Plan

### Step 1: Add `segment_id` to `classify_facet_rdpv()` output

In `traffic_utils/recurrent.py`, in the Step 5&6 loop of `classify_facet_rdpv()`:

```python
# Before the segment loop:
out['segment_id'] = np.nan  # default: no segment

# Inside the segment loop, after the 'retained' check:
for row_idx in range(seg_start, seg_end):
    if is_peak_week[row_idx]:
        if retained:
            out.loc[row_idx, 'recurrent_band'] = True
            out.loc[row_idx, 'excluded_band'] = False
            out.loc[row_idx, 'segment_id'] = len(segments)  # unique per segment
        else:
            out.loc[row_idx, 'recurrent_band'] = False
            out.loc[row_idx, 'excluded_band'] = True
            # segment_id stays NaN for excluded
    else:
        out.loc[row_idx, 'recurrent_band'] = False
        out.loc[row_idx, 'excluded_band'] = False
```

Also add `'segment_id'` to the segment metadata dict for debugging:
```python
segments.append({
    'start_obs': seg_start,
    'end_obs': seg_end,
    'peak_count': peak_count,
    'retained': retained,
    'start_week': start_week,
    'end_week': end_week,
    'segment_id': len(segments),  # NEW
})
```

### Step 2: Propagate `segment_id` through `run_band_recurrent_pipeline()`

In `run_band_recurrent_pipeline()`, the per-facet DataFrames are concatenated with `ignore_index=True`. The `segment_id` column will survive this concat automatically. Add it to the output CSV.

### Step 3: Use `segment_id` in `aggregate_segment_level_bpr()`

In `traffic_utils/bpr_fitting.py`:

```python
# Current:
g['segment_id'] = (g['week_num'].diff().fillna(1).ne(1)).cumsum() + 1

# New:
if 'segment_id' in g.columns:
    # Use segment_id from recurrent detection (preserves RDP breakpoints)
    g = g.dropna(subset=['segment_id'])
    g['segment_id'] = g['segment_id'].astype(int)
else:
    # Fallback: compute from consecutive week_num gaps
    g['segment_id'] = (g['week_num'].diff().fillna(1).ne(1)).cumsum() + 1
```

This change ensures that:
- Each RDP-identified retained segment gets its own aggregated data point
- Adjacent retained segments with different peak patterns are NOT merged
- The week-gap fallback still works for methods that don't produce `segment_id`

### Step 4: Update grid search BPR fitting

In the grid search scripts, the BPR fitting step uses:
```python
df_p = df_use[df_use['period'] == period].copy()
```

After the `aggregate_segment_level_bpr` fix, each (VDS, dayofweek, period, segment_id) will produce its own row. This naturally increases the number of data points for BPR fitting (more segments → more data points), and should improve R² for patterns that were previously merged.

## Validation

After implementation:
1. Run one VDS with the best v2 config and verify:
   - `segment_id` column exists in the recurrent output
   - Adjacent retained segments have different `segment_id` values
   - BPR input data has more data points (one per segment per day per period)
   - R² improves for cells that previously had low R² (especially afternoon periods)
2. Compare R² before/after the fix to confirm improvement

## Scope of Changes

| File | Change |
|------|--------|
| `traffic_utils/recurrent.py` | Add `segment_id` column in `classify_facet_rdpv()` |
| `traffic_utils/bpr_fitting.py` | Use `segment_id` in `aggregate_segment_level_bpr()` when available |
| `rdp_grid_search_v2.py` | No change needed (uses existing pipeline) |

## Expected Impact

- **Morning-peak**: Minimal change (most configs have 1 retained segment)
- **Afternoon-peak**: Significant improvement expected. Weeks with late-start peaks (8:00+) and early-start peaks (4:00–5:00) were previously merged into one BPR curve. Keeping them separate should improve R².
- **Overall score**: Should improve, particularly for the `min_r2` bottleneck cells (VDS 1205583 afternoon, VDS 1203481 afternoon)