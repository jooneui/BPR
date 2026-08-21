"""
Stage-1 CSV -> slim per-station JSON, for the near-recurrent-explorer site.

Reads from ../04_peak_period_result/ (untouched, canonical Stage-1 output).
Writes to ../data/{vds}.json and ../data/manifest.json.

Does NOT modify anything under traffic_utils/ or 04_peak_period_result/.
Does NOT recompute the eligibility gate's formula from scratch out of thin air —
it is transcribed exactly from traffic_utils/plotting_stage2.py L108-179
(den_threshold, count_threshold_per_year, record_years-from-distinct-days), since that
gate does not depend on the RDP_v parameters the site's sliders control (Frame G5).

Reference: FPEV Stage-2 Plan, phase P0. See ../handoffs/stage-2-plan-Sonnet5CC.md.
"""
import json
import math
import os
import sys

import pandas as pd

# ---------------------------------------------------------------------------
# Canonical constants (D2, D3 — see stage-2-plan-Sonnet5CC.md)
# ---------------------------------------------------------------------------

DEN_THRESHOLD = 60          # veh/mile/lane — matches MASTER_CONFIG (Frame C4)
COUNT_PER_YEAR_THRESHOLD = 75  # matches MASTER_CONFIG (Frame C4)

STATIONS = ['1203481', '1203506', '1214006', '1205572', '1212611',
            '1205175', '774204', '761003', '760987']

STATION_LABELS = {
    '1203481': 'SR91-WB',  '1203506': 'SR91-EB',
    '1214006': 'I5 SB-1',  '1205572': 'I5 SB-2',  '1212611': 'I5 SB-3',
    '1205175': 'I5 NB-1',
    '774204':  'SR134 WB-1',
    '761003':  'SR134 EB-1', '760987': 'SR134 EB-2',
}

CORRIDORS = {
    '1203481': 'SR91',      '1203506': 'SR91',
    '1214006': 'I5-SB',     '1205572': 'I5-SB', '1212611': 'I5-SB',
    '1205175': 'I5-NB',
    '774204':  'SR134-WB',
    '761003':  'SR134-EB',  '760987': 'SR134-EB',
}

# From MASTER_CONFIG['bpr_ff_speed_threshold'] (Frame G9 — closed; these are static,
# author-set constants, not derived at export time).
FF_SPEED_MPH = {
    '1203481': 68, '1203506': 66, '1214006': 67, '1205572': 70,
    '1212611': 69, '1205175': 69, '774204': 67, '761003': 67, '760987': 66,
}

# Eligibility (C4 gate: density > 60, >= 75 congested points per year of record) is
# NOT recomputed here. It is read from the already-confirmed, pipeline-generated
# reference (references/bpr_calibration_reference_C3a.csv), which was produced by
# run_full_pipeline(MASTER_CONFIG, stages=[2,3,4]) through its real entry point.
#
# Divergence note (R3, execute-P0): an earlier version of this exporter tried to
# recompute eligibility from c_daily_traffic_division_{vds}...csv (the "division"
# file). That produced wrong exclusions (e.g. SR91-WB PM incorrectly excluded). The
# gate actually reads a *different* Stage-1 file, c_daily_traffic_segment_{vds}...csv
# (traffic_utils/plotting_stage2.py L437-445) -- a finer-grained, sub-day-interval
# table this project has not otherwise needed to read. Rather than reverse-engineer
# a second raw-data format, eligibility is read from the confirmed pipeline output.
# Eligibility genuinely does not depend on the RDP_v parameters (Frame G5), so a
# static lookup is correct, not just convenient. See stage-3-phase-0 handoff.
EXCLUDED_STATION_PERIODS = {
    ('1203481', 'AM'), ('1214006', 'PM'), ('1205572', 'PM'), ('1212611', 'PM'),
    ('1205175', 'AM'), ('761003', 'AM'), ('760987', 'AM'),
}

RAW_DIR = os.path.join('..', '..', '04_peak_period_result')
META_PATH = os.path.join('..', '..', '01 PeMS API', 'station_meta.csv')
OUT_DIR = os.path.join('..', 'data')

KEEP_COLUMNS = ['date', 'dayofweek', 'period', 'start_time', 'end_time',
                'totaldemand', 'avg_speed', 'traveltimes']

# From MASTER_CONFIG['lane_map'] -- needed for P2's N_j = totaldemand * lane_count
# (matches load_and_annotate's totaldemandoverlanes). traveltimes itself is NOT
# 1/avg_speed (verified: they don't match numerically -- traveltimes carries a
# per-station distance unit this project doesn't otherwise need to know), so it
# is carried through from the source CSV rather than re-derived, avoiding a
# units-mismatch risk against the reference (C3).
LANE_COUNT = {
    '1203481': 4, '1203506': 4, '1214006': 4, '1205572': 6,
    '1212611': 6, '1205175': 5, '774204': 4, '761003': 4, '760987': 4,
}


def time_to_fractional_hour(t_str):
    """Transcribed from traffic_utils/recurrent.py::time_to_fractional_hour."""
    if pd.isna(t_str) or t_str == '-':
        return float('nan')
    try:
        h, m = map(int, str(t_str).split(':'))
        return h + m / 60.0
    except Exception:
        return float('nan')


def raw_path(vds):
    return os.path.join(
        RAW_DIR,
        f'c_daily_traffic_division_single_{vds}_speedbasedpeak_5_RDP_v_speed-solely.csv'
    )


def eligibility_for(vds):
    """Static lookup against the confirmed pipeline reference. See divergence note
    above EXCLUDED_STATION_PERIODS."""
    out = {}
    for ampm in ('AM', 'PM'):
        excluded = (vds, ampm) in EXCLUDED_STATION_PERIODS
        out[ampm] = {
            'passes': not excluded,
            'den_threshold': DEN_THRESHOLD,
            'count_threshold_per_year': COUNT_PER_YEAR_THRESHOLD,
            'source': 'references/bpr_calibration_reference_C3a.csv (confirmed pipeline run)',
        }
    return out


def export_station(vds):
    df = pd.read_csv(raw_path(vds))
    eligibility = eligibility_for(vds)

    df = df[df['period'].isin(['morning-peak', 'afternoon-peak'])].copy()
    df['date'] = df['date'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(6)
    df = df[KEEP_COLUMNS]

    # Tightened further after the columnar pass still landed 39% over budget
    # (1425 KB vs. 1024 KB). dayofweek -> int code (0=Mon..6=Sun, JS re-expands
    # via a 7-entry lookup); times -> fractional hours (numeric, matches what
    # the RDP_v port needs to consume anyway -- no string parsing required
    # downstream). Both are lossless for what P1/P2 actually need.
    DOW_CODE = {'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6}
    df['dayofweek_code'] = df['dayofweek'].map(DOW_CODE)
    df['start_hour'] = df['start_time'].apply(time_to_fractional_hour)
    df['end_hour'] = df['end_time'].apply(time_to_fractional_hour)

    # Malformed time strings exist in the raw data (e.g. "24:00:00" — three
    # colon-separated parts, out-of-range hour; found in every station except
    # 1205572/1212611, up to 156 rows for VDS 761003). time_to_fractional_hour
    # returns NaN for these (unpacking failure), exactly as
    # traffic_utils/recurrent.py's own copy does -- and upstream, that NaN is
    # what makes prepare_peak_table mark the row is_peak=-5 (non-qualifying),
    # excluding it from classify_facet_rdpv's input entirely.
    #
    # Divergence (R2, execute-P1): the first version of this exporter parsed
    # times the same way but never dropped the resulting nulls, so these rows
    # survived into the export as phantom "qualifying" days. Found via
    # parity testing (P1) against the real pipeline: VDS 1203481 Tuesday PM
    # was off by exactly 1 retained segment, traced to date 2013-01-15
    # surviving in JS but not in Python. Fixed by dropping here, matching
    # is_peak=-5 exclusion exactly rather than re-deriving it downstream.
    n_before = len(df)
    df = df[df['start_hour'].notna() & df['end_hour'].notna()].copy()
    n_dropped = n_before - len(df)

    daily_peaks = {
        'date': df['date'].astype(int).tolist(),  # JS re-pads to 6 digits on read
        'dow': df['dayofweek_code'].tolist(),
        'is_am': (df['period'] == 'morning-peak').tolist(),
        # NOT rounded, deliberately -- see phase-1 handoff. Rounding to even 6
        # decimals still perturbs the float64 bit pattern enough to flip a
        # genuine duration tie during dedup: two rows on the same date can be
        # mathematically identical durations (both exactly 35 minutes, e.g.
        # 07:35-08:10 vs 10:55-11:30) computed via different h+m/60.0 paths,
        # landing on different float64 values by a few ULP. Python's tie-break
        # depends on that exact bit pattern. json.dump serializes Python
        # floats with enough digits to round-trip to the identical float64 in
        # any IEEE754 reader (including JS), so leaving these unrounded is
        # what makes JS's dedup tie-break match Python's exactly, not an
        # oversight.
        'start_h': [x if pd.notna(x) else None for x in df['start_hour']],
        'end_h': [x if pd.notna(x) else None for x in df['end_hour']],
        'demand': df['totaldemand'].round(1).tolist(),
        'speed': df['avg_speed'].round(1).tolist(),
        'traveltime': df['traveltimes'].tolist(),  # not rounded -- feeds the OLS fit directly
    }

    payload = {
        'vds': vds,
        'label': STATION_LABELS[vds],
        'corridor': CORRIDORS[vds],
        'zeta_h_per_mi': round(60.0 / FF_SPEED_MPH[vds], 6),
        'ff_speed_mph': FF_SPEED_MPH[vds],
        'lane_count': LANE_COUNT[vds],
        'eligibility': eligibility,
        'daily_peaks': daily_peaks,
    }

    out_path = os.path.join(OUT_DIR, f'{vds}.json')
    with open(out_path, 'w') as f:
        json.dump(payload, f, separators=(',', ':'))
    return out_path, len(df), eligibility, n_dropped


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    meta = pd.read_csv(META_PATH, dtype={'ID': str})
    meta_idx = meta.set_index('ID')

    manifest = {'stations': [], 'den_threshold': DEN_THRESHOLD,
                'count_threshold_per_year': COUNT_PER_YEAR_THRESHOLD}
    total_bytes = 0

    for vds in STATIONS:
        if not os.path.exists(raw_path(vds)):
            print(f'[MISSING] {vds}: {raw_path(vds)} not found — skipped')
            continue
        out_path, n_rows, eligibility, n_dropped = export_station(vds)
        size = os.path.getsize(out_path)
        total_bytes += size

        row = meta_idx.loc[vds] if vds in meta_idx.index else None
        lat = float(row['Latitude']) if row is not None else None
        lon = float(row['Longitude']) if row is not None else None

        excluded = [p for p in ('AM', 'PM') if not eligibility[p]['passes']]
        manifest['stations'].append({
            'vds': vds,
            'label': STATION_LABELS[vds],
            'corridor': CORRIDORS[vds],
            'lat': lat, 'lon': lon,
            'file': f'{vds}.json',
            'n_rows': n_rows,
            'excluded_periods': excluded,
        })
        excl_note = f" [excluded: {', '.join(excluded)}]" if excluded else ""
        drop_note = f" ({n_dropped} malformed times dropped)" if n_dropped else ""
        print(f'{STATION_LABELS[vds]:12} ({vds})  {n_rows:5d} rows  '
              f'{size/1024:6.1f} KB{excl_note}{drop_note}')

    manifest_path = os.path.join(OUT_DIR, 'manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    total_bytes += os.path.getsize(manifest_path)

    print(f'\n{len(manifest["stations"])} stations exported. '
          f'Total data/ size: {total_bytes/1024:.1f} KB '
          f'(budget: 1024 KB — {"OK" if total_bytes < 1024*1024 else "OVER BUDGET"})')


if __name__ == '__main__':
    main()
