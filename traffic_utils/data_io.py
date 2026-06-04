import copy
import numpy as np
import os
import pandas as pd
import pickle


def rawdata_setting(full_path,VDS_num,file_name,lane_num):
    """
    Upload raw-data and standardize the settings
    """
    
    rawdata = pd.read_excel("%s/%s" % (full_path,file_name))

    
    rawdata.columns = ['time'] + [f'flow_{i}' for i in lane_num] + [f'speed_{i}' for i in lane_num]+ [f'occ_{i}' for i in lane_num] + ['length']
    # rawdata.columns = ['time'] + [f'flow_{i}' for i in lane_num] + [f'occ_{i}' for i in lane_num]

    rawdata['time'] = pd.to_datetime(rawdata['time'])
    # 'time_filter' is to convert the time to minutes.(ex. 02:30:30 -> 150.30min)
    rawdata['time_filter'] = rawdata['time'].dt.hour*60 + rawdata['time'].dt.minute + rawdata['time'].dt.second/60
    # rawdata['time_filter'] = rawdata['time'].dt.hour*100 + rawdata['time'].dt.minute
    rawdata['time_hour'] = rawdata['time'].dt.hour
    
    return rawdata

""" Sometimes, the rawdata interval is too short to see the stable traffic pattern, so rawdata is aggregated to specific time interval.
This function address calculating traffic state variables in every pre-determined aggregated time interval.


* "This is not equal to the 'Research_BPR_function_Develop.ipynb', because of rawdata['time_slot'] is different: it used the median value
Interpolate_missing(traffic, config) is also changed.
"""

def aggregate_rawdata_5min(rawdata, raw_timeframe, date, lane_num, VDS_num):
    
    # Pre-compute time_slot for all data to avoid doing it in the loop
    rawdata['time_slot'] = (np.floor(rawdata['time_filter'] / raw_timeframe)) * raw_timeframe + raw_timeframe/2
    
    # Initialize list to store each row's data for final DataFrame
    traffic_within_day = pd.DataFrame()
    plot_date = []
     
    # Operate on grouped DataFrame
    flow_set = [f'flow_{i}' for i in range(1,lane_num[-1]+1,1)]
    density_set = [f'density_{i}' for i in range(1,lane_num[-1]+1,1)]
    occ_set = [f'occ_{i}' for i in range(1,lane_num[-1]+1,1)]
    speed_set = [f'speed_{i}' for i in range(1,lane_num[-1]+1,1)]
    
    rawdata[flow_set] *= 60/raw_timeframe
    # Compute densities with shape alignment, then rename columns to density_*
    speeds = rawdata[speed_set].replace(0, np.nan)
    dens_values = rawdata[flow_set].to_numpy() / speeds.to_numpy()
    dens = pd.DataFrame(dens_values, index=rawdata.index, columns=density_set)
    
    # 4) Assign (now lengths match)
    rawdata[density_set] = dens

    rawdata['flow'] = rawdata[flow_set].mean(axis=1)
    rawdata['density'] = rawdata[density_set].mean(axis=1)
    rawdata['occ'] = rawdata[occ_set].mean(axis=1)
    rawdata['speed'] = rawdata['flow'] /  rawdata['density']
    rawdata['traveltime'] = 1/rawdata['speed'] * 60 

    traffic_within_day = rawdata
    plot_date = traffic_within_day['time_slot']
    
    # Save the data
    path_directory = f'./12 python file/{VDS_num}'
    os.makedirs(path_directory, exist_ok=True)

    with open(f'./12 python file/{VDS_num}/traffic_within_day_{date}_raw{raw_timeframe}min_{lane_num}.p', 'wb') as file:
        pickle.dump(traffic_within_day, file)

    with open(f'./12 python file/{VDS_num}/plot_date_{date}_raw{raw_timeframe}min.p', 'wb') as file:    
        pickle.dump(plot_date, file)
    
    return traffic_within_day, plot_date

# =====================
# Utility Functions
# =====================

def load_raw(file_name, config):
    """
    Load and standardize raw traffic data and gfactor for a given date file.
    Returns: rawdata (DataFrame), gfactor (DataFrame), date (str)
    """
    date = file_name[-11:-5]
    gfile = f"{config['path']}/11 Rawdata/gfactor/{config['VDS_num']}/gfactor_{date}.xlsx"
    # gfactor = pd.read_excel(gfile)
    rawdata = rawdata_setting(
        full_path=f"{config['path']}/11 Rawdata/{config['dir']}/{config['VDS_num']}",
        VDS_num=config['VDS_num'],
        file_name = file_name,
        lane_num=config['lane_num']
    )
    # return rawdata, gfactor, date
    return rawdata, date

# ── combined-section CSV loader ─────────────────────────────────────────────
_section_cache: dict = {}


def load_section_combined(config, date: str):
    """
    Load daily traffic from a combined multi-day CSV with section-level data.

    Expected CSV columns:
        Route_ID, Direction, Section_ID, Date, Time_interval,
        Volume, Speed, Occ, Density

    Config keys used:
        - path / dir / VDS_num  : used to build file path
        - section_combined_params:
            - filename          : e.g. 'Detector.csv'  (default)
            - direction_filter  : 1 | 2 | None (aggregate both)
            - section_filter    : int | list[int] | None (all sections)
            - speed_unit        : 'kmh' | 'kph' | 'mph'  (default 'mph')
            - flow_col          : 'Volume'  (default)
            - speed_col         : 'Speed'   (default)
            - volume_to_flow    : multiplier for veh/interval → veh/hr
                                  auto=12 when data is veh/5min (default)
            - date_format       : '%Y%m%d' | '%y%m%d' (default '%Y%m%d')
    Returns:
        traffic (pd.DataFrame): same schema as aggregate_rawdata_5min output
        coverage_length       : placeholder = 1.0
    """
    import numpy as np
    from pathlib import Path

    scp = config.get('section_combined_params', {})
    vds = config['VDS_num']

    # ── file path ─────────────────────────────────────
    base = Path(config.get('path', config.get('file_path', '.')))
    fname = scp.get('filename', 'Detector.csv')
    # For per-section configs, keep the base VDS folder name (e.g. C1, not C1_S5)
    base_vds = config.get('base_vds', vds)
    fpath = base / '11 Rawdata' / config.get('dir', '5min') / base_vds / fname

    # ── cache once ────────────────────────────────────
    cache_key = str(fpath)
    if cache_key not in _section_cache:
        _section_cache[cache_key] = pd.read_csv(fpath)
    df_all = _section_cache[cache_key].copy()

    print(df_all.head())

    # ── filter ──────────────────────────────────────
    dformat = scp.get('date_format', '%Y%m%d')
    if dformat == '%Y%m%d' and len(str(date)) == 6:
        # date is YYMMDD, CSV stores YYYYMMDD → prepend century
        target_date = int('20' + str(date))
    else:
        target_date = int(date)
    df = df_all[df_all['Date'] == target_date].copy()

    direction = scp.get('direction_filter', None)
    if direction is not None:
        df = df[df['Direction'] == direction]

    sections = scp.get('section_filter', None)
    if sections is not None:
        if isinstance(sections, (int, np.integer)):
            sections = [int(sections)]
        df = df[df['Section_ID'].isin(sections)]

    if df.empty:
        print(f"[section_combined] No data for {vds} on {date}")
        return None, 1.0

    # ── unit conversions ─────────────────────────────
    speed_unit = scp.get('speed_unit', 'mph')   # 'mph' = native units (no conversion)
    vol_mult   = scp.get('volume_to_flow', 12)  # veh/5min → veh/hr

    # time_slot [minutes]  (interval 1 → 2.5 min, interval 288 → 1437.5 min)
    df['time_slot'] = (df['Time_interval'] - 1) * 5 + 2.5

    # Aggregate across sections if multiple
    grouped = df.groupby('time_slot').agg({
        'Volume': 'sum',              # total vehicles/5min
        'Speed':  'mean',             # arithmetic mean (user: no section length)
    }).reset_index()

    # Convert to pipeline units
    grouped['flow'] = grouped['Volume'] * vol_mult   # veh/hr
    if speed_unit in ('kmh', 'kph'):
        grouped['speed'] = grouped['Speed'] / 1.60934
        print(f"[section_combined] Speed converted km/h → mph ({vds}). "
              f"Adjust thresholds accordingly (e.g. 60 km/h ≈ 37.3 mph).")
    else:
        grouped['speed'] = grouped['Speed'].copy()

    grouped['density'] = grouped['flow'] / grouped['speed']
    grouped['traveltime'] = 60.0 / grouped['speed']
    grouped['occ'] = np.nan

    # Build standard traffic DataFrame
    traffic = grouped[['time_slot', 'flow', 'speed', 'density', 'occ', 'traveltime']].copy()
    # Properly parse YYMMDD date string to Timestamp
    if len(date) == 6:
        ts_date = pd.Timestamp('20' + date)
    else:
        ts_date = pd.Timestamp(date)
    traffic['time'] = ts_date + pd.to_timedelta(traffic['time_slot'], unit='m')

    return traffic, 1.0


def get_unique_sections(config, vds: str):
    """
    Return sorted list of unique Section_IDs for a combined-section CSV.
    Respects direction_filter from config['section_combined_params'].
    """
    from pathlib import Path
    scp = config.get('section_combined_params', {})
    base = Path(config.get('path', config.get('file_path', '.')))
    fname = scp.get('filename', 'Detector.csv')
    fpath = base / '11 Rawdata' / config.get('dir', '5min') / vds / fname

    cache_key = str(fpath)
    if cache_key not in _section_cache:
        _section_cache[cache_key] = pd.read_csv(fpath)
    df_all = _section_cache[cache_key]
    df_all.columns = ['Route_ID', 'Direction', 'Section_ID', 'Date', 'Time_interval', 'Volume', 'Speed', 'Occ', 'Density']

    # Apply direction filter if present
    direction = scp.get('direction_filter', None)
    if direction is not None and 'Direction' in df_all.columns:
        df_all = df_all[df_all['Direction'] == direction]

    sections = sorted(df_all['Section_ID'].unique())

    # Apply explicit section filter if given
    explicit = scp.get('section_filter', None)
    if explicit is not None:
        if isinstance(explicit, (int, np.integer)):
            explicit = [int(explicit)]
        sections = [s for s in sections if s in explicit]

    return sections


def skip_if_missing(rawdata, config):
    """
    Check if rawdata exceeds missing_ratio threshold; skip if too many missing slots.
    """
    total_expected = (24 * 60) / config['raw_timeframe']

    for lane in config['lane_num']:
        col_name = f'flow_{lane}'
        # Count total zeros in this lane
        zero_count = (rawdata[col_name] == 0).sum()
        
        if zero_count > (total_expected * config['missing_ratio']):
            return True
    
    return False

def set_peak_period_save(config, set_peak_period):
    
    if config['spatial_scope'] == 'multi_vds':
        set_peak_period.to_csv(f"./04_peak_period_result/set_peak_period_{config['spatial_scope']}_{config['VDS_list']}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{config.get('method', config.get('speedbased_params', {}).get('method', 'RDP_v'))}_{config.get('congest_method', config.get('speedbased_params', {}).get('congest_method', 'speed-solely'))}.csv")
    else:
        set_peak_period.to_csv(f"./04_peak_period_result/set_peak_period_{config['spatial_scope']}_{config['VDS_num']}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{config.get('method', config.get('speedbased_params', {}).get('method', 'RDP_v'))}_{config.get('congest_method', config.get('speedbased_params', {}).get('congest_method', 'speed-solely'))}.csv")

def compute_bpr_ff_speed_thresholds(cfg: dict) -> dict:
    """
    Compute flow-weighted harmonic mean free-flow speed for each VDS using
    0-3am and 22-24 off-peak intervals across the entire dataset.
    
    Returns {vds_id: rounded_integer_speed} for pasting into MASTER_CONFIG['bpr_ff_speed_threshold'].
    
    Formula: v_ff = sum(q_i) / sum(q_i / v_i)   [flow-weighted harmonic mean]
    
    When data_format='section_combined' and VDS_list contains base names like 'C1',
    this function auto-expands to per-section VDS names (e.g., 'C1_S1_D1') and
    computes thresholds for each section individually. Returns both per-section
    and base-VDS entries.
    
    Usage:
        thresholds = compute_bpr_ff_speed_thresholds(MASTER_CONFIG)
        for k, v in thresholds.items():
            print(f"    '{k}': {v},")
        # Then paste into MASTER_CONFIG['bpr_ff_speed_threshold']
    """
    from pathlib import Path
    import pandas as pd
    import numpy as np
    
    # Auto-expand section_combined base VDS names into per-section names
    vds_list_expanded = []
    if cfg.get('data_format') == 'section_combined' and cfg.get('spatial_scope') == 'single':
        for base_vds in cfg.get('VDS_list', []):
            sections = get_unique_sections(cfg, base_vds)
            scp = cfg.get('section_combined_params', {})
            direction = scp.get('direction_filter')
            dir_suffix = f"_D{direction}" if direction is not None else ""
            if sections:
                for sec_id in sections:
                    sec_name = f"{base_vds}_S{int(sec_id)}{dir_suffix}"
                    vds_list_expanded.append(sec_name)
            else:
                vds_list_expanded.append(base_vds)
    else:
        vds_list_expanded = list(cfg.get('VDS_list', []))
    
    base_path = Path(cfg.get('path', cfg.get('file_path', '.'))) / '11 Rawdata'
    results = {}
    
    for vds in vds_list_expanded:
        all_offpeak = []
        
        if cfg.get('data_format') == 'section_combined':
            # Load from combined CSV
            scp = cfg.get('section_combined_params', {})
            base_vds = cfg.get('base_vds', vds.split('_')[0] if '_' in vds else vds)
            fname = scp.get('filename', 'Detector.csv')
            fpath = base_path / cfg.get('dir', '5min') / base_vds / fname
            
            if not fpath.exists():
                print(f"[compute_bpr_ff] File not found: {fpath}, skipping {vds}")
                continue
                
            df_all = pd.read_csv(fpath, header=None, names=['Route_ID','Direction','Section_ID','Date','Time_interval','Volume','Speed','Occ','Density'])
            
            # Apply direction filter
            direction = scp.get('direction_filter')
            if direction is not None and 'Direction' in df_all.columns:
                df_all = df_all[df_all['Direction'] == direction]
            
            # For per-section VDS names like C1_S1_D1, filter by section
            import re
            m = re.search(r'_S(\d+)', vds)
            if m:
                sec_id = int(m.group(1))
                if 'Section_ID' in df_all.columns:
                    df_all = df_all[df_all['Section_ID'] == sec_id]
            
            # unit conversion (same as load_section_combined)
            speed_unit = scp.get('speed_unit', 'mph')
            vol_mult = scp.get('volume_to_flow', 12)
            df_all['time_slot'] = (df_all['Time_interval'] - 1) * 5 + 2.5
            df_all['flow'] = df_all['Volume'] * vol_mult
            if speed_unit in ('kmh', 'kph'):
                df_all['speed'] = df_all['Speed'] / 1.60934
            else:
                df_all['speed'] = df_all['Speed']
            
            # Filter to off-peak hours
            mask = ((df_all['time_slot'] >= 0) & (df_all['time_slot'] < 180)) | \
                   ((df_all['time_slot'] >= 1320) & (df_all['time_slot'] <= 1440))
            offpeak = df_all[mask]
            all_offpeak.append(offpeak[['flow', 'speed']].copy())
            
        else:
            # Legacy per-day files (.csv or .xlsx)
            data_dir = base_path / cfg.get('dir', '5min') / vds
            file_list = [f for f in data_dir.iterdir() if f.is_file() and f.suffix in ('.csv', '.txt', '.xlsx')]
            
            for fname in sorted(file_list):
                try:
                    if fname.suffix == '.xlsx':
                        df = pd.read_excel(fname)
                    else:
                        df = pd.read_csv(fname)
                    
                    # Build time_slot from date/timestamp column
                    if 'time_slot' not in df.columns:
                        if 'date' in df.columns:
                            df['time_slot'] = pd.to_datetime(df['date']).dt.hour * 60 + pd.to_datetime(df['date']).dt.minute
                        elif 'Time' in df.columns:
                            df['time_slot'] = pd.to_datetime(df['Time']).dt.hour * 60 + pd.to_datetime(df['Time']).dt.minute
                        elif 'interval' in df.columns:
                            df['time_slot'] = (df['interval'] - 1) * cfg.get('raw_timeframe', 5) + cfg.get('raw_timeframe', 5) / 2
                        else:
                            # Assume rows are 5-min intervals in order
                            df['time_slot'] = df.index * 5 + 2.5
                    
                    # Aggregate lane-level flow and speed to section-level
                    flow_cols = [c for c in df.columns if c.startswith('flow_')]
                    speed_cols = [c for c in df.columns if c.startswith('speed_')]
                    
                    if flow_cols and speed_cols:
                        # Total flow = sum across lanes
                        df['flow'] = df[flow_cols].sum(axis=1)
                        # Flow-weighted harmonic mean speed across lanes
                        # v = sum(flow_i) / sum(flow_i / speed_i)
                        numer = df[flow_cols].sum(axis=1)
                        denom = pd.Series(0.0, index=df.index)
                        for fc, sc in zip(flow_cols, speed_cols):
                            s = df[sc].replace(0, np.nan)
                            denom += df[fc] / s
                        df['speed'] = numer / denom
                    else:
                        flow_col = 'flow' if 'flow' in df.columns else 'Flow'
                        speed_col = 'speed' if 'speed' in df.columns else 'Speed'
                        df['flow'] = df[flow_col]
                        df['speed'] = df[speed_col]
                    
                    mask = ((df['time_slot'] >= 0) & (df['time_slot'] < 180)) | \
                           ((df['time_slot'] >= 1320) & (df['time_slot'] <= 1440))
                    offpeak = df[mask]
                    if not offpeak.empty:
                        valid = offpeak.dropna(subset=['flow', 'speed'])
                        valid = valid[valid['speed'] > 0]
                        if not valid.empty:
                            all_offpeak.append(valid[['flow', 'speed']].copy())
                except Exception as e:
                    print(f"[compute_bpr_ff] Error reading {fname}: {e}")
                    continue
        
        if not all_offpeak:
            print(f"[compute_bpr_ff] No off-peak data for {vds}, using default 55")
            results[vds] = 55
            continue
            
        combined = pd.concat(all_offpeak, ignore_index=True)
        combined = combined.dropna(subset=['flow', 'speed'])
        combined = combined[combined['speed'] > 0]
        
        if combined.empty:
            print(f"[compute_bpr_ff] No valid off-peak data for {vds}, using default 55")
            results[vds] = 55
            continue
        
        # Flow-weighted harmonic mean
        ff_speed = combined['flow'].sum() / (combined['flow'] / combined['speed']).sum()
        results[vds] = int(round(ff_speed))
        print(f"[compute_bpr_ff] {vds}: flow-weighted harmonic mean speed = {ff_speed:.2f} → threshold = {results[vds]}")
    
    return results


def c_daily_traffic_save(config, results, criterion): 
    
    c_daily_traffic = pd.DataFrame({'date': results['date'], 'dayofweek': results["dayofweek"],'division': results[criterion], 'period':results['period'], 'duration':results['duration'], 'start_time': results['start'], 'end_time': results['end'],'totaldemand': results["total_demand"], 'avg_flow': results['avg_flow'], 'traveltimes': results["traveltime"], 'avg_speed':results["avg_speed"], 'density':results["density"], 'avg_occ':results["avg_occ"]})
    c_daily_traffic['year'] = c_daily_traffic['date'].astype(int)//10000 + 2000

    if config['spatial_scope'] == 'multi_vds':
        c_daily_traffic.to_csv(f"./04_peak_period_result/c_daily_traffic_{criterion}_{config['spatial_scope']}_{config['VDS_list']}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{config.get('method', config.get('speedbased_params', {}).get('method', 'RDP_v'))}_{config.get('congest_method', config.get('speedbased_params', {}).get('congest_method', 'speed-solely'))}.csv")
    else:
        c_daily_traffic.to_csv(f"./04_peak_period_result/c_daily_traffic_{criterion}_{config['spatial_scope']}_{config['VDS_num']}_{config['temporal_scale']}_{config['aggregate_timeframe']}_{config.get('method', config.get('speedbased_params', {}).get('method', 'RDP_v'))}_{config.get('congest_method', config.get('speedbased_params', {}).get('congest_method', 'speed-solely'))}.csv")


# ═══════════════════════════════════════════════════════════
# Moved from _helpers.py (OneDrive file download utility)
# ═══════════════════════════════════════════════════════════
import subprocess
import time

def _ensure_local(path: str, retries: int = 5, delay: float = 3.0) -> str:
    """Force-download an OneDrive Files-On-Demand file before reading.

    On macOS with OneDrive, files can be 'cloud-only' — present in directory
    listings but not physically on disk.  This function tries multiple
    strategies to make the file local before raising an error.
    """
    import subprocess

    for attempt in range(retries):
        # Strategy 1: Try opening the file (triggers OneDrive on-demand download)
        try:
            with open(path, 'rb') as f:
                f.read(1)
            return path  # file is local now
        except FileNotFoundError:
            if attempt < retries - 1:
                print(f"  OneDrive file not local yet, retrying ({attempt+1}/{retries})..."
                      f" path={os.path.basename(path)}")
                # Strategy 2: Use 'brctl download' to force OneDrive to pin file locally
                try:
                    subprocess.run(['brctl', 'download', path],
                                   capture_output=True, timeout=10)
                except Exception:
                    pass
                # Strategy 3: Touch the file to trigger eviction-clearing
                try:
                    import pathlib
                    pathlib.Path(path).touch()
                except Exception:
                    pass
                time.sleep(delay)
            else:
                raise
    return path

