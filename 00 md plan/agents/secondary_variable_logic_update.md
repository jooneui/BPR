# Secondary Variable Logic Update

## 1. Current Behavior

Both `morning-peak` and `afternoon-peak` use the **same `second_var_by_period`** option for both periods:

| Period | Fixed Variable | Secondary Variable Options | RDP Epsilon for Secondary |
|--------|---------------|---------------------------|---------------------------|
| morning-peak | start_hour (`epsilon_start`) | `end_hour` or `peak_duration` | `epsilon_end_by_period['morning-peak']` |
| afternoon-peak | start_hour (`epsilon_start`) | `end_hour` or `peak_duration` | `epsilon_end_by_period['afternoon-peak']` |

In the current code (`traffic_utils/recurrent.py`, `rdp_v_classify_facet`):
- `epsilon_start` always controls RDP for the **start-hour** cumulative curve
- `epsilon_end` always controls RDP for the **second-variable** cumulative curve
- The `second_var` parameter swaps what the second curve *represents*:
  - `second_var='end_hour'` → second curve = cumulative **end_hour** (toleranced by `epsilon_end`)
  - `second_var='peak_duration'` → second curve = cumulative **peak_duration** (toleranced by `epsilon_end`)

**Both periods share the same `second_var`** in the current grid search:
```python
'second_var_by_period': {'morning-peak': second_var, 'afternoon-peak': second_var}
```

## 2. Proposed New Behavior

The key change: **different periods use different fixed and secondary variables**, and the choice of secondary variable is determined by **different epsilon parameters** for each period.

| Period | Fixed Variable | Secondary Variable Option A | Secondary Variable Option B | Epsilon Criterion |
|--------|---------------|----------------------------|-----------------------------|-------------------|
| morning-peak | `start_hour` (`epsilon_start`) | `end_hour` | `peak_duration` | `epsilon_end_by_period['morning-peak']` |
| afternoon-peak | `end_hour` (`epsilon_end`) | `start_hour` | `peak_duration` | `epsilon_start_by_period['afternoon-peak']` |

### What changes

#### Morning-peak (NO CHANGE)
- **Fixed**: `start_hour` — always present, controlled by `epsilon_start_by_period['morning-peak']`
- **Secondary**: `end_hour` or `peak_duration` — controlled by `epsilon_end_by_period['morning-peak']`
- This is **identical to the current behavior**

#### Afternoon-peak (CHANGED)
- **Fixed**: `end_hour` — always present, controlled by `epsilon_end_by_period['afternoon-peak']`
- **Secondary**: `start_hour` or `peak_duration` — controlled by `epsilon_start_by_period['afternoon-peak']`
- Previously: secondary was `end_hour` or `peak_duration`, controlled by `epsilon_end_by_period['afternoon-peak']`
- **Key differences from current logic**:
  1. The **fixed variable** shifts from `start_hour` → `end_hour` for afternoon-peak
  2. The **secondary variable** options shift from `end_hour`/`peak_duration` → `start_hour`/`peak_duration`
  3. The **epsilon parameter** that governs secondary shifts from `epsilon_end_by_period` → `epsilon_start_by_period`

### Conceptual rationale

For **morning-peak**, the *start* hour is naturally more stable (people arrive at a consistent time), making `start_hour` the fixed anchor, while the *end* time varies more — it is the secondary variable to model.

For **afternoon-peak**, the *end* hour is naturally more stable (people leave at a consistent time, e.g., after work), making `end_hour` the fixed anchor, while the *start* time varies more — it becomes the secondary variable to model.

The table below summarizes the symmetry:

```
Morning-peak:   start_hour (FIXED anchor)  →  RDP with epsilon_start
                end_hour / peak_duration (SECONDARY)  →  RDP with epsilon_end

Afternoon-peak: end_hour (FIXED anchor)  →  RDP with epsilon_end
                start_hour / peak_duration (SECONDARY)  →  RDP with epsilon_start
```

## 3. Code Changes Required

### 3.1 `traffic_utils/recurrent.py` — `rdp_v_classify_facet()`

**Current flow (simplified)**:
```python
# Both periods: epsilon_start → start_hour curve, epsilon_end → secondary curve
if selector in ('start_only', 'both'):
    simplified_start = rdp_v(pts_start, epsilon=epsilon_start)
if selector in ('end_only', 'both'):
    simplified_end = rdp_v(pts_end, epsilon=epsilon_end)
```

**New flow**: Add a `fixed_var` parameter that swaps the role of start/end for afternoon-peak:

```python
if period == 'afternoon-peak' and fixed_var == 'end_hour':
    # Afternoon-peak with end_hour as fixed anchor:
    #   Fixed curve = end_hour (toleranced by epsilon_end)
    #   Secondary curve = start_hour (toleranced by epsilon_start)
    #     or peak_duration (toleranced by epsilon_start)
    
    # Fixed: end_hour
    if selector in ('end_only', 'both'):  # 'end_only' acts as 'fixed_only'
        simplified_fixed = rdp_v(pts_end, epsilon=epsilon_end)
        bp_fixed = simplified_fixed[:, 0].astype(int).tolist()
    
    # Secondary: start_hour or peak_duration
    if selector in ('start_only', 'both'):  # 'start_only' acts as 'secondary_only'
        if second_var == 'start_hour':
            secondary_full = start_hours_full
        else:  # peak_duration
            secondary_full = duration_full
        
        C_secondary = np.cumsum(secondary_full)
        pts_secondary = np.column_stack([week_idx, C_secondary])
        simplified_secondary = rdp_v(pts_secondary, epsilon=epsilon_start)
        bp_secondary = simplified_secondary[:, 0].astype(int).tolist()
```

**Alternative (simpler)**: Instead of adding `fixed_var`, we can re-map how `selector` and the epsilon/secondary curves are assigned for afternoon-peak inside the caller function (the one that loops over periods). This keeps `rdp_v_classify_facet()` unchanged:

```python
# In the caller, for afternoon-peak with fixed_var='end_hour':
#   Swap: epsilon_start ↔ epsilon_end, selector 'start_only' ↔ 'end_only'
#   Swap second_var: 'end_hour' → 'start_hour'
#   Then call rdp_v_classify_facet as normal
```

### 3.2 `rdp_rdp_grid_search.py` — Grid definition

**Current**: Both periods share the same `second_var`:
```python
'second_var_by_period': {'morning-peak': second_var, 'afternoon-peak': second_var}
```

**New**: Periods can have different secondary variables:
```python
'second_var_by_period': {
    'morning-peak': second_var_m,   # 'end_hour' or 'peak_duration'
    'afternoon-peak': second_var_a  # 'start_hour' or 'peak_duration'
}
```

### 3.3 Grid search combinations

**Current (v3)**:
- Case A: `second_var = end_hour` for both periods (coupled epsilon)
- Case B: `second_var = peak_duration` for both periods (decoupled epsilon)
- Total: 3,900

**New (v4)**: Four cases:

| Case | Morning second_var | Afternoon second_var | Epsilon coupling | Combinations |
|------|-------------------|---------------------|-----------------|-------------|
| A | `end_hour` | `start_hour` | Coupled per period | es_m(10) × es_a(15) × W(2) = 300 |
| B | `end_hour` | `peak_duration` | Morning: ee_m(3), Afternoon: es_a controls dur | es_m(10) × es_a(15) × ee_m(3) × W(2) = 900 |
| C | `peak_duration` | `start_hour` | Morning: ee_m(3) controls dur, Afternoon: es_a | es_m(10) × es_a(15) × ee_m(3) × W(2) = 900 |
| D | `peak_duration` | `peak_duration` | Fully decoupled per period | es_m(10) × es_a(10) × ee_m(3) × ee_a(4) × W(2) = 2,400 |
| | | | | **Total: 4,500** |

Alternative (reduced): Since morning-peak generally performs well and afternoon-peak is the bottleneck, we could limit the morning second_var to `end_hour` only and only vary the afternoon:
- Cases B+C merged (morning=end_hour, afternoon=start_hour or peak_duration): fewer combos

> **Open question**: Should we reduce the grid by fixing morning's second_var to `end_hour` (which performed best in v3) and only varying afternoon's second_var?

### 3.4 `build_recurrent_output_tag()` — Tag generation

The output tag must reflect the new period-specific logic. Current format:
```
RDP_v_m_es0.1_ee0.1_min2_hg2.0_b_end_afternoon_es0.1_ee0.1_min2_hg2.0_b_dur
```

New format (proposed):
```
RDP_v_m_es0.1_ee0.6_min2_hg2.0_b_end_afternoon_es0.5_ee0.1_min2_hg2.0_b_start
```

Where the suffix after `b_` for afternoon now says `start` instead of `end`, reflecting that `start_hour` is now a secondary variable option.

### 3.5 BPR fitting — Stage 3

The BPR fitting must use the correct independent variable depending on the period and `second_var`:

| Period | second_var | X column for BPR |
|--------|-----------|-----------------|
| morning-peak | `end_hour` | `end_hour` (from recurrent output) |
| morning-peak | `peak_duration` | `end_hour - start_hour` |
| afternoon-peak | `start_hour` | `start_hour` (from recurrent output) |
| afternoon-peak | `peak_duration` | `end_hour - start_hour` |

The fixed variable for each period is always included in the BPR model but is not the independent variable being regressed:
- Morning-peak: `start_hour` is fixed, BPR fits traffic volume vs. `end_hour` or `peak_duration`
- Afternoon-peak: `end_hour` is fixed, BPR fits traffic volume vs. `start_hour` or `peak_duration`

## 4. Summary of Asymmetry

```
                    Morning-peak              Afternoon-peak
                    ─────────────             ──────────────
Fixed (always):     start_hour                end_hour
  └ RDP epsilon:    epsilon_start              epsilon_end
  └ selector role:  'start_only' / 'both'      'end_only' / 'both'

Secondary:          end_hour / peak_duration   start_hour / peak_duration
  └ RDP epsilon:    epsilon_end                epsilon_start
  └ selector role:  'end_only' / 'both'        'start_only' / 'both'
```

This mirrors the real-world traffic intuition:
- Morning peak: people arrive at consistent start times; the *end* (or *duration*) of the peak is more variable
- Afternoon peak: people leave at consistent end times; the *start* (or *duration*) of the peak is more variable