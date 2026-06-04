from scipy import stats
import copy
import math
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
import matplotlib.image as mpimg
import numpy as np
import os
import pandas as pd
import seaborn as sns
import statsmodels.api as sm

# cross-module imports
from .bpr_fitting import fit_bpr_ols_stats, prepare_bpr_dataframe, LINEAR_REGISTRY_BPR, build_default_recurrent_output_tag_from_bpr

DAY_ORDER = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']



def generate_config_name(config):
    # Extract the shortest_interval parameters
    m_rm = config['recurrent_method']
    si = config['recurrent_method_params'][m_rm]
    
    # Helper to format the percentile (0.9 -> 90)
    def fmt_q(val):
        return int(val * 100) if val is not None else ""

    #reucrrent_method
    
    if (m_rm == 'shortest_interval'):
        # Build parts for morning
        m_sel = si['selector_by_period']['morning-peak']
        m_sq = f"s{fmt_q(si['start_q_by_period']['morning-peak'])}"
        m_eq = f"e{fmt_q(si['end_q_by_period']['morning-peak'])}"
        
        # Build parts for afternoon
        a_sel = si['selector_by_period']['afternoon-peak']
        a_eq = fmt_q(si['end_q_by_period']['afternoon-peak'])
    elif (m_rm == 'simpleband'):
        # Build parts for morning
        m_sel = si['selector_by_period']['morning-peak']
        m_sq = f"s{si['start_bandwidth_minutes_by_period']['morning-peak']}"
        m_eq = f"s{si['end_bandwidth_minutes_by_period']['morning-peak']}"
        
        # Build parts for afternoon
        a_sel = si['selector_by_period']['afternoon-peak']
        a_eq = f"s{si['end_bandwidth_minutes_by_period']['afternoon-peak']}"
    elif (m_rm == 'RDP_v'):
        # Build parts for morning
        m_sel = si['selector_by_period']['morning-peak']
        m_sq = f"s{si['epsilon_start_by_period']['morning-peak']}_s{si['epsilon_end_by_period']['morning-peak']}"
        
        # Build parts for afternoon
        a_sel = si['selector_by_period']['afternoon-peak']
        a_eq = f"s{si['epsilon_start_by_period']['afternoon-peak']}_s{si['epsilon_end_by_period']['afternoon-peak']}"

    # Construct the final string
    name = (
        f"{m_rm}_"
        f"morning_{m_sel}_{m_sq}_"
        f"afternoon_{a_sel}{a_eq}"
    )
    
    return name


def _flatten_vds_labels(labels):
    """Accept nested {corridor: {vds: label}} or flat {vds: label}; always return flat {vds: label}."""
    flat = {}
    for key, val in labels.items():
        if isinstance(val, dict):
            flat.update(val)
        else:
            flat[key] = val
    return flat


def _vds_label_dict(cfg):
    """Return {str(vds_id): label} whether VDS_label_list is a list, flat dict, or nested dict."""
    labels = cfg.get('VDS_label_list', [])
    if isinstance(labels, dict):
        return _flatten_vds_labels(labels)
    return {str(vds): lbl for vds, lbl in zip(cfg.get('VDS_list', []), labels)}


def _resolve_corridor_groups(cfg):
    """
    Return ordered list of (corridor_name, [vds_ids]) tuples.
    If 'corridor_groups' is defined in cfg, use it.
    Otherwise, fall back to one group per VDS in VDS_list.
    """
    groups = cfg.get('corridor_groups', None)
    if groups:
        return list(groups.items())
    # fallback: each VDS in its own group
    return [(str(v), [v]) for v in cfg.get('VDS_list', [])]


def _build_corridor_suffix(cfg):
    """Build a file-name suffix from corridor group names, e.g. '_SR91_I5SB_I5NB_I10W'."""
    groups = _resolve_corridor_groups(cfg)
    if len(groups) == 1 and groups[0][0] == str(cfg.get('VDS_list', [''])[0]):
        # fallback mode — no corridor_groups defined
        return _build_vds_range_suffix(cfg.get('VDS_list', []))
    return '_' + '_'.join(name.replace(' ', '').replace('-', '') for name, _ in groups)


"""
This is the plot of average flow and speed over time for every day.
"""

def plot_within_flowspeed_day(traffic_day, plot_date, directory, file_name, VDS_num, Day, aggregate_timeframe, date, lane_num):
    # 1st Plot: Time vs Traffic Flow and Avg Speed
    fig, ax = plt.subplots(1,1, figsize=(9,6))
    fig.suptitle(f'Traffic State within a Day using {directory} data(Date: {file_name[8:-5]}({Day}))',fontsize=18)
    ax.plot(plot_date, traffic_day['flow'], color='tab:blue')
    
    # Configure x-axis ticks and labels
    x_ticks = range(0, 1500, 60)
    x_labels = range(0, 25, 1)
    ax.set_xticks(ticks=x_ticks, labels=x_labels, fontsize=10)
    ax.locator_params(axis='x', nbins=25)
    
    # Set plot title and labels
    ax.set_title(f'Average Flow and Speed over time (aggregated by every {aggregate_timeframe} min)',fontsize=13)
    ax.set_ylabel('Flow rates (vphpl)', color='tab:blue', fontsize=12)
    ax.tick_params(axis='y',labelcolor='tab:blue')
    ax.set_xlabel('Time (hr)', fontsize=12)
    ax.set_ylim(0,2500)
    ax.set_yticks(range(0,2600,200))
    
    # Create a twinx axis for the second line plot on the same subplot
    ax2 = ax.twinx()
    ax2.plot(plot_date, traffic_day['speed'], color='tab:red')
    ax2.set_ylabel('Average Speed (mph)', color='tab:red', fontsize=12)
    ax2.tick_params(axis='y',labelcolor='tab:red')
    ax2.set_ylim(0,120)
    ax2.set_yticks(range(0,130,10))

    ax.grid(True)

    directory_path = f"./02 fig/15 Unit time_flowspeed_all/{VDS_num}"
    # Create the directory
    os.makedirs(directory_path, exist_ok=True)

    plt.savefig(f'{directory_path}/{date}_{lane_num}.png')
    plt.close()

"""
This is the plot of average flow and speed over time for every day.
"""

def plot_within_densityspeed_day(traffic_day, plot_date, directory, file_name, VDS_num, Day, aggregate_timeframe, date, lane_num):
    # 1st Plot: Time vs Traffic Flow and Avg Speed
    fig, ax = plt.subplots(1,1, figsize=(9,6))
    fig.suptitle(f'Traffic State within a Day using {directory} data(Date: {file_name[8:-5]}({Day}))',fontsize=18)
    ax.plot(plot_date, traffic_day['density'], color='tab:blue')
    
    # Configure x-axis ticks and labels
    x_ticks = range(0, 1500, 60)
    x_labels = range(0, 25, 1)
    ax.set_xticks(ticks=x_ticks, labels=x_labels, fontsize=10)
    ax.locator_params(axis='x', nbins=25)
    
    # Set plot title and labels
    ax.set_title(f'Average Flow and Speed over time (aggregated by every {aggregate_timeframe} min)',fontsize=13)
    ax.set_ylabel('Densities (vpmpl)', color='tab:blue', fontsize=12)
    ax.tick_params(axis='y',labelcolor='tab:blue')
    ax.set_xlabel('Time (hr)', fontsize=12)
    ax.set_ylim(0,80)
    ax.set_yticks(range(0,85,5))
    
    # Create a twinx axis for the second line plot on the same subplot
    ax2 = ax.twinx()
    ax2.plot(plot_date, traffic_day['speed'], color='tab:red')
    ax2.set_ylabel('Average Speed (mph)', color='tab:red', fontsize=12)
    ax2.tick_params(axis='y',labelcolor='tab:red')
    ax2.set_ylim(0,120)
    ax2.set_yticks(range(0,130,10))

    ax.grid(True)

    directory_path = f"./02 fig/15 Unit time_densityspeed_all/{VDS_num}"
    # Create the directory
    os.makedirs(directory_path, exist_ok=True)

    plt.savefig(f'{directory_path}/{date}_{lane_num}.png')
    plt.close()

import matplotlib.pyplot as plt
import numpy as np

def PELT_plot(df, bkpts, date, VDS_num, aggregate_timeframe, peak_list, method, penalty):
    # Set global aesthetic parameters for a "clean" look
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
    
    time_slot_hour = df['time_slot'] / 60
    
    title_name = {
        'RDP': 'RDP-Based Congested Periods Detection',
        'RDP_v': 'RDP_v_Based Congested Periods Detection',
        'pelt': 'PELT-Based Congested Periods Detection',
        'joon': 'Speed Threshold-Based Congested Periods Detection',
        'pelt_directpeak': 'PELT-Based Directly Congested Periods Detection',
    }
    
    # Increase DPI for higher quality and set a clean background
    fig, ax1 = plt.subplots(figsize=(9, 4), dpi=100)
    
    date_v2 = f'{date[4:6]}/{date[6:8]}/20{date[2:4]}' # Adjusted for consistent formatting
    
    # Title and Labels
    ax1.set_title(f'{title_name[method]}\n(VDS: {VDS_num}, Date: {date_v2})', 
                  fontsize=18, fontweight='bold', pad=20)
    ax1.set_xlabel('Time (Hours)', fontsize=14, labelpad=10)
    ax1.set_ylabel('Speed (mph)', fontsize=14, color='#2E7D32', fontweight='bold')
    
    # 1. Primary Plot: Speed (Left Axis)
    ax1.plot(time_slot_hour, df['speed'], color='#4CAF50', linewidth=1.8, label='Speed', alpha=0.9)
    ax1.set_ylim(0, 85)
    ax1.set_xlim(0, 24)
    ax1.set_xticks(np.arange(0, 25, 1))
    ax1.tick_params(axis='y', colors='#2E7D32')
    
    # Subtle Speed Threshold (e.g., 60mph) for context
    ax1.axhline(50, color='#D84315', linestyle=':', linewidth=1.5, alpha=0.8)
    
    # # 2. Secondary Plot: Cumulative Speed (Right Axis)
    ax2 = ax1.twinx()
    time_slot_hour_re = [0] + time_slot_hour.to_list()
    cumsum_speed_re = [0] + df['cumsum_speed'].to_list()
    
    # Use a subtle fill for cumulative speed to avoid cluttering lines
    ax2.fill_between(time_slot_hour_re, cumsum_speed_re, color='#1976D2', alpha=0.1)
    ax2.plot(time_slot_hour_re, cumsum_speed_re, color='#1976D2', linewidth=1.5, alpha=0.7, label='Cumulative Speed')
    
    ax2.set_ylabel('Cumulative Speed (miles)', fontsize=14, color='#1565C0', fontweight='bold', labelpad=10)
    ax2.set_ylim(0, 1600)
    ax2.tick_params(axis='y', colors='#1565C0')
    
    # 3. Changepoints and Peak Periods
    # Changepoints (PELT results) – black dashed lines
    for i, bkpt in enumerate(bkpts):
        label = 'Changepoints' if i == 0 else ""
        ax1.axvline(x=time_slot_hour[bkpt], color='black', linestyle='--', linewidth=1.2, alpha=0.8, label=label)

    # Peak-period boundaries and shaded regions
    for i, element in enumerate(peak_list):
        if element['idx'] > 0:
            s_hours, s_minutes = map(int, element['start'].split(':'))
            s_total = s_hours + s_minutes/60 - 5/60
            e_hours, e_minutes = map(int, element['end'].split(':'))
            e_total = e_hours + e_minutes/60
            
            # Shade the congested period (opaque red)
            label_span = 'Congested period' if i == 0 else ""
            ax1.axvspan(s_total, e_total, color='red', alpha=0.15, label=label_span)
            
            # Boundary lines (red dashed)
            label_line = 'Congested periods boundary' if i == 0 else ""
            ax1.axvline(x=s_total, color='red', linestyle='--', linewidth=2, label=label_line)
            ax1.axvline(x=e_total, color='red', linestyle='--', linewidth=2)

    # Styling and Legend
    ax1.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.4)
    ax1.spines['left'].set_color('#2E7D32')
    ax2.spines['right'].set_color('#1565C0')
    
    # Combined Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    # Unique labels only
    by_label = dict(zip(labels1 + labels2, lines1 + lines2))
    # by_label = dict(zip(labels1, lines1))
    ax1.legend(by_label.values(), by_label.keys(), loc='upper left', fontsize=11, frameon=True, shadow=True)

    plt.tight_layout()
    
    # Save with proper metadata
    save_path = f'./02 fig/16 PELT/{VDS_num}/{VDS_num}_{date}_{aggregate_timeframe}_{method}_{penalty}.png'
    plt.savefig(save_path, bbox_inches='tight')
    plt.show()

def PELT_plot_all(df, date, VDS_num, aggregate_timeframe, peak_list_PELT, peak_list_RDP, peak_list_PELT_direct, purpose):
# def PELT_plot_all(df, bkpts, date, VDS_num, aggregate_timeframe, peak_list_PELT, method):
    
    time_slot_hour = df['time_slot'] / 60
    date_v2 = f'{date[2:4]}/{date[4:6]}/20{date[0:2]}'
    
    # joon, pelt, RDP, derivative
    title_name = {'RDP':f'Congestion Period Detection from PELT and RDP (VDS: {VDS_num}, Date: {date_v2})', 
                  'PELT_direct': f'Comparison of Proposed and Previous Approaches (VDS: {VDS_num}, Date: {date_v2})'}

    label_name = {'RDP':['PELT-detected congestion boundaries', 'RDP-detected congestion boundaries'],
                  'PELT_direct': ['Proposed method: congested period boundary','Previous method: congested period boundary']}
    
    fig, ax1 = plt.subplots(figsize=(12, 5))

    
    # Left axis: Changepoints (as vertical lines)
    ax1.set_xlabel('Time (Hours)',fontsize=16)
    ax1.set_ylabel('Speed (mph)',fontsize=16, color = 'green')
    ax1.set_title(title_name[purpose],fontsize=18)
    ax1.grid(True)
    ax1.set_xlim(0, 24+.1)
    ax1.set_xticks(np.arange(0, 25, 1))

    # Plot peak/off-peaks
    select_date_PELT = peak_list_PELT.loc[(peak_list_PELT['date'] == int(date)),'peak_list'].iloc[0]
    select_date_RDP = peak_list_RDP.loc[(peak_list_RDP['date'] == int(date)),'peak_list'].iloc[0]
    # select_date_PELT_direct = peak_list_PELT_direct.loc[(peak_list_PELT_direct['date'] == int(date)),'peak_list'].iloc[0]

    if purpose == 'RDP':
        select_date_purpose = select_date_RDP
    elif purpose == 'PELT_direct':
        select_date_purpose = select_date_PELT_direct

    
    for element in select_date_PELT:
        if len(element) == 0:
            continue
        
        if element['idx'] > 0:
            s_hours, s_minutes = map(int, element['start'].split(':'))
            s_total_hours = s_hours + s_minutes/60
            # label = 'PELT congested boundary' if element['idx'] == 1 else ''
            label = label_name[purpose][0] if element['idx'] == 1 else ''
            ax1.axvline(x=s_total_hours, color='red', linewidth=2.5, linestyle='-', label=label)

            e_hours, e_minutes = map(int, element['end'].split(':'))
            e_total_hours = e_hours + e_minutes/60
            # label = 'Peak-Periods' if element['idx'] == 1 else ''
            ax1.axvline(x=e_total_hours, color='red', linewidth=2.5, linestyle='-')
            
    
    for element in select_date_purpose:    
        if len(element) == 0:
            continue
        
        if element['idx'] > 0:
            s_hours, s_minutes = map(int, element['start'].split(':'))
            s_total_hours = s_hours + s_minutes/60
            label = label_name[purpose][1] if element['idx'] == 1 else ''
            ax1.axvline(x=s_total_hours, color='purple', linewidth=2.5, linestyle='--', label=label)

            e_hours, e_minutes = map(int, element['end'].split(':'))
            e_total_hours = e_hours + e_minutes/60
            # label = 'Peak-Periods' if element['idx'] == 1 else ''
            ax1.axvline(x=e_total_hours, color='purple', linewidth=2.5, linestyle='--')
            

    # Right axis: Cumulative speed pattern
    ax1.plot(time_slot_hour, df['speed'], color='green', linewidth=1, label='Speed')
    ax1.set_ylim(0,85)
    ax1.set_yticks(np.arange(0, 85 + 1, 10))  # Ticks at 0, 20, 40, 60, 80
    # Set y-axis tick label color
    ax1.tick_params(axis='y', colors='black')
    # Set y-axis spine (axis line) color
    ax1.spines['left'].set_color('green')

    time_slot_hour_re = [0] + time_slot_hour.to_list()
    cumsum_speed_re = [0] + df['cumsum_speed'].to_list()

    ax2 = ax1.twinx()
    ax2.plot(time_slot_hour_re, cumsum_speed_re, color='blue', linewidth=1, label='Cumulative speed')
    ax2.set_ylabel('Cumulative Speed (miles)',fontsize=16, color='blue')
    ax2.set_ylim(0, 1600)
    ax2.set_yticks(np.arange(0, 1600 + 1, 200)) 
    # Set y-axis tick label color
    ax2.tick_params(axis='y', colors='blue')
    # Set y-axis spine (axis line) color
    ax2.spines['right'].set_color('blue')

    # Handle legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left',fontsize=15)

    fig.tight_layout()
    plt.savefig(f'./02 fig/16 PELT/All_{purpose}_{VDS_num}_{date}_{aggregate_timeframe}.png')
    # plt.show()  # Uncomment if you want to display the plot

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

def plot_linear_by_group_FD(
    df_segment,
    df_division,              # kept for compatibility (not used)
    variable: str,
    cfg: dict,
    version_key: str,
    speed_thre: float,
    xlim=None,
    ylim=None,
    title_suffix: str = "",
    save_name=None,
):
    # ----------------------------
    # 1) Transform
    # ----------------------------
    print(df_segment.head())
    if variable == "qk":
        X = df_segment['density']
        Y = df_segment['avg_flow']
        Z = X/Y*60
        # Z.to_csv(f"{save_name}_{variable}.csv")
        
    elif variable == "uq":
        X = df_segment['avg_flow']
        Y = df_segment['avg_speed']
        Z = 1/Y*X*60
        # Z.to_csv(f"{save_name}_{variable}.csv")
        
    # ----------------------------
    # 2) Figure setup (beautified)
    # ----------------------------
    plt.rcParams.update({
        "font.family": "STIXGeneral",
        "mathtext.fontset": "stix",
        "axes.unicode_minus": False,
    })
    
    fig, ax = plt.subplots(figsize=(8.4, 5.6), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # Scatter: smaller, softer, cleaner
    ax.scatter(
        X, Y,
        s=14,                 # a bit smaller
        alpha=0.18,           # softer cloud
        linewidths=0,
        rasterized=True
    )

    # ----------------------------
    # 3) Reference line q = v k
    # ----------------------------
    if variable == "qk":  
        if xlim is not None:
            xmin, xmax = xlim
        else:
            xmin = max(0, float(np.nanmin(X)))
            xmax = float(np.nanmax(X)) * 1.05
    
        xs = np.linspace(xmin, xmax, 300)
        ax.plot(
            xs, speed_thre * xs,
            linestyle="--",
            linewidth=2.6,        # slightly thicker
            color="black",
            label=rf"$q = {speed_thre}k$"
        )
    
        # Legend: slightly rounded, nicer spacing
        leg = ax.legend(
            loc="upper right",
            fontsize=25,
            frameon=True,
            fancybox=True,
            borderpad=0.6,
            handlelength=2.2
        )
        leg.get_frame().set_alpha(0.95)

    # ----------------------------
    # 4) Labels, limits, title
    # ----------------------------
    # ax.set_xlabel(xlab, fontsize=25, labelpad=10)
    # ax.set_ylabel(ylab, fontsize=25, labelpad=10)

    if xlim is not None:
        ax.set_xlim(*xlim)
    if ylim is not None:
        ax.set_ylim(*ylim)

    if cfg.get("spatial_scope") == "single":
        ttl = f"{cfg.get('VDS_label', '')}"
    else:
        ttl = "Multiple VDS"
    if title_suffix:
        ttl += f" {title_suffix}"

    ax.set_title(ttl, fontsize=30, pad=14)

    # ----------------------------
    # 5) Ticks + grid (more “publication”)
    # ----------------------------
    ax.tick_params(axis="both", which="major", labelsize=18, length=6, width=1.2)
    ax.tick_params(axis="both", which="minor", length=3, width=1.0)

    ax.xaxis.set_minor_locator(AutoMinorLocator(5))
    ax.yaxis.set_minor_locator(AutoMinorLocator(5))

    # Softer grid: minor very light, major light
    ax.grid(True, which="major", alpha=0.22, linewidth=1.0)
    ax.grid(True, which="minor", alpha=0.10, linewidth=0.8)

    # Clean spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.2)
    ax.spines["bottom"].set_linewidth(1.2)



    # ----------------------------
    # 6) Save (PNG + PDF)
    # ----------------------------
    if save_name is None:
        os.makedirs(cfg["save_dir"], exist_ok=True)
        save_name = (
            f"{cfg['save_dir']}/FD_clean_{cfg['spatial_scope']}_"
            f"{cfg.get('VDS_num','multi')}_{variable}_"
            f"{cfg['temporal_scale']}_{cfg['period_filter']}_"
            f"{version_key}_{cfg['method']}"
        )

    fig.savefig(save_name + ".png", bbox_inches="tight")  # best for papers
    plt.close(fig)


## Code part for plotting the fixed bands on the facet plot

import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd


def draw_fixed_band(ax, meta):
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
        handles.append(Line2D([0], [0], color='orange', linewidth=6, alpha=0.2))
        labels.append(label)

    return handles, labels


def annotate_segment_selection_for_plot(df_peaks, cfg, recurrent_col, selected_col='segment_selected'):
    out = df_peaks.copy()
    out[selected_col] = False

    if out.empty or recurrent_col not in out.columns:
        return out

    min_weeks_map = cfg.get('segment_min_weeks_by_period', {'morning-peak': 2, 'afternoon-peak': 2})
    rec_mask = (out['is_peak'] == 1) & out[recurrent_col].fillna(False)
    rec_idx = out.index[rec_mask]
    if len(rec_idx) == 0:
        return out

    work = out.loc[rec_idx].copy()
    work = work.sort_values(['dayofweek', 'period', 'week_num', 'date_dt'])
    work['segment_selected'] = False
    work['segment_id_plot'] = np.nan
    work['segment_n_weeks_plot'] = np.nan

    for (day, period), grp in work.groupby(['dayofweek', 'period'], sort=False, dropna=False):
        grp = grp.sort_values(['week_num', 'date_dt']).copy()
        grp['segment_id_plot'] = (grp['week_num'].diff().fillna(1).ne(1)).cumsum() + 1
        seg_sizes = grp.groupby('segment_id_plot')['week_num'].transform('size')
        grp['segment_n_weeks_plot'] = seg_sizes
        min_weeks = int(min_weeks_map.get(period, 1))
        grp['segment_selected'] = seg_sizes >= min_weeks
        work.loc[grp.index, ['segment_selected', 'segment_id_plot', 'segment_n_weeks_plot']] = grp[['segment_selected', 'segment_id_plot', 'segment_n_weeks_plot']]

    out.loc[work.index, ['segment_selected', 'segment_id_plot', 'segment_n_weeks_plot']] = work[['segment_selected', 'segment_id_plot', 'segment_n_weeks_plot']]
    return out


def plot_common_points(ax, data, recurrent_col, excluded_col, selected_col='segment_selected',
                     merge_excluded_to_not_selected=False):
    """Plot recurrent, excluded, and non-peak points on a facet axis.

    For segmentation-based methods (RDP_v, PELT), set
    ``merge_excluded_to_not_selected=True`` so that peaks in excluded
    segments appear as dark-orange "Not Selected" circles instead of
    crimson "Non-Recurrent" diamonds.  In these methods the segmentation
    itself decides which peaks are selected, so the two-layer
    (recurrent_band + segment_selected) split produces almost no
    "Not Selected" points.  Merging gives a meaningful visual distinction.

    Parameters
    ----------
    merge_excluded_to_not_selected : bool
        If True, excluded-band peaks are drawn as dark-orange circles
        ("Recurrent Peaks (Not Selected)") instead of crimson diamonds.
    """

    print("data", data.shape[0])
    real_p = data[data['is_peak'] == 1]
    rec_p = real_p[real_p[recurrent_col]]
    exc_p = real_p[real_p[excluded_col]]
    non_real_p = data[data['is_peak'] == -5]

    if merge_excluded_to_not_selected:
        # For RDP_v / PELT: segmentation already decided selection.
        # Show ALL recurrent peaks as teal "Selected", and ALL excluded
        # peaks as dark-orange "Non-Recurrent Peaks".
        rec_selected = rec_p
        nonrec_p = exc_p                # excluded → dark orange, labeled "Non-Recurrent"
        show_not_selected_legend = False  # hide "Recurrent Peaks (Not Selected)" from legend
    else:
        # For simpleband / shortest-interval: apply secondary
        # segment_selected filter on top of the band assignment.
        nonrec_p = exc_p                  # crimson diamonds
        if selected_col in rec_p.columns:
            rec_selected = rec_p[rec_p[selected_col].fillna(False)]
            rec_not_selected = rec_p[~rec_p[selected_col].fillna(False)]
        else:
            rec_selected = rec_p
            rec_not_selected = rec_p.iloc[0:0]


    if (len(real_p) != 0):
        
        ax.vlines(real_p['week_num'], real_p['start_hour'], real_p['end_hour'], color='lightgrey', alpha=0.8, linewidth=3)
        ax.scatter(rec_selected['week_num'], rec_selected['start_hour'], color='teal', s=40, zorder=5)
        ax.scatter(rec_selected['week_num'], rec_selected['end_hour'], color='teal', s=40, zorder=5)

        if merge_excluded_to_not_selected:
        
            ax.scatter(nonrec_p['week_num'], nonrec_p['start_hour'], color='darkorange', s=40, zorder=5)
            ax.scatter(nonrec_p['week_num'], nonrec_p['end_hour'], color='darkorange', s=40, zorder=5)
        else:
            ax.scatter(rec_not_selected['week_num'], rec_not_selected['start_hour'], color='darkorange', s=40, zorder=5)
            ax.scatter(rec_not_selected['week_num'], rec_not_selected['end_hour'], color='darkorange', s=40, zorder=5)
            ax.scatter(nonrec_p['week_num'], nonrec_p['start_hour'], color='crimson', marker='D', s=35, zorder=5)
            ax.scatter(nonrec_p['week_num'], nonrec_p['end_hour'], color='crimson', marker='D', s=35, zorder=5)

    ax.scatter(non_real_p['week_num'], non_real_p['end_hour'], color='lightgrey', marker='x', s=35, zorder=5)

    handles = [
        Line2D([0], [0], color='teal', marker='o', linestyle='None', markersize=7, label='Recurrent Peaks (Selected)'),
        Line2D([0], [0], color='darkorange', marker='o', linestyle='None', markersize=7,
               label='Non-Recurrent Peaks' if merge_excluded_to_not_selected else 'Recurrent Peaks (Not Selected)'),
        Line2D([0], [0], color='crimson', marker='D', linestyle='None', markersize=6, label='Non-Recurrent Peaks'),
        Line2D([0], [0], color='lightgrey', marker='x', linestyle='None', markersize=6, label='No Peak Detected'),
    ]
    # For RDP_v/PELT: hide redundant legend entries
    if merge_excluded_to_not_selected:
        handles = [handles[0], handles[1], handles[3]]  # Selected, Non-Recurrent, No Peak
    labels = [h.get_label() for h in handles]
    return handles, labels


def plot_start_end_boxplots(df_peaks, save_path=None, vds_id=None, cfg=None, showfliers=True, figsize=(14, 10)):
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

    fig.suptitle(f"Distribution of Peak Start and End Times by Day of Week (VDS: {_vds_label_dict(cfg).get(str(vds_id), str(vds_id))})", fontsize=16, y=1.02)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def _resolve_hist_bin_size(period, bin_size, cfg=None):
    if isinstance(bin_size, dict):
        value = bin_size.get(period)
        return float(value) if value is not None else 0.5
    if bin_size is not None:
        return float(bin_size)
    cfg = cfg or {}
    params = cfg.get('recurrent_method_params', {}).get('simpleband', {})
    start_bw = params.get('start_bandwidth_minutes_by_period', {}).get('morning-peak', 30)
    end_bw = params.get('end_bandwidth_minutes_by_period', {}).get('afternoon-peak', 30)
    if period == 'morning-peak':
        return float(start_bw) / 60.0
    return float(end_bw) / 60.0


def plot_start_end_histograms(df_peaks, bin_size=None, save_path=None, vds_id=None, cfg=None, figsize=(14, 20)):
    plot_df = df_peaks.copy()
    plot_df['dayofweek'] = pd.Categorical(plot_df['dayofweek'], categories=DAY_ORDER, ordered=True)

    g = sns.FacetGrid(
        plot_df,
        row='dayofweek',
        col='period',
        col_order=['morning-peak', 'afternoon-peak'],
        sharey=False,
        sharex=False,
        height=2.5,
        aspect=2.8,
    )

    def draw_dual_hist(data, **kwargs):
        if data.empty:
            return
        period = data['period'].iloc[0]
        if period == 'morning-peak':
            x_range = (0, 12)
        else:
            x_range = (12, 24)
        local_bin_size = _resolve_hist_bin_size(period, bin_size, cfg)
        bins = np.arange(x_range[0], x_range[1] + local_bin_size, local_bin_size)

        sns.histplot(data=data, x='start_hour', bins=bins, color='#4C72B0', alpha=0.55, label='Start Hour', edgecolor='white', linewidth=0.5)
        sns.histplot(data=data, x='end_hour', bins=bins, color='#C44E52', alpha=0.55, label='End Hour', edgecolor='white', linewidth=0.5)

        ax = plt.gca()
        ax.set_xlim(x_range)
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax.xaxis.set_major_locator(ticker.MultipleLocator(1))

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


def _build_vds_range_suffix(vds_list):
    """
    Auto-generate a file-name suffix from a list of VDS IDs like
    ['C1_S1_D1','C1_S2_D1',...]  ->  '_S1-6_D1'
    Falls back to listing individual IDs if no clear pattern.
    """
    if not vds_list:
        return ""
    import re
    secs, dirs = [], []
    for v in vds_list:
        m = re.search(r'_S(\d+)', str(v))
        d = re.search(r'_D(\d+)', str(v))
        secs.append(int(m.group(1)) if m else None)
        dirs.append(int(d.group(1)) if d else None)

    uniq_dirs = sorted(set([d for d in dirs if d is not None]))
    dir_part = f"_D{uniq_dirs[0]}" if len(uniq_dirs) == 1 and uniq_dirs[0] is not None else ""

    clean_secs = [s for s in secs if s is not None]
    if not clean_secs:
        return ""
    if len(clean_secs) == 1:
        sec_part = f"_S{clean_secs[0]}"
    elif max(clean_secs) - min(clean_secs) == len(clean_secs) - 1:
        sec_part = f"_S{min(clean_secs)}-{max(clean_secs)}"
    else:
        sec_part = "_S" + "+".join(str(s) for s in clean_secs)

    return sec_part + dir_part


# 2) 3x3 wrapper (plot_bpr_all_in_one_png_3*3)
# =========================
def plot_bpr_section_grid(
    cfg,
    version_key: str,
    nrows=3,
    ncols=2,
    xlim=None,
    ylim=None,
    suptitle='Segment-Level Log-',
    out_name=None,
    show_legend_only_first=False,
    font_add=5,
    dpi=200,
):
    """
    BPR calibration plots arranged by corridor groups.
    If 'corridor_groups' is in cfg, panels are laid out in per-corridor sub-grids
    composited vertically. Otherwise falls back to flat (nrows x ncols) pagination.
    Works correctly for section_combined when VDS_list = ['C1_S1', 'C1_S2', ...].
    """
    if out_name is None:
        out_name = build_default_recurrent_output_tag_from_bpr(cfg)
    vds_list = cfg.get('VDS_list', [])
    vds_label_map = _vds_label_dict(cfg)
    xlim_list = xlim if (isinstance(xlim, list) and xlim and (
        isinstance(xlim[0], list) or xlim[0] is None
    )) else [xlim]
    periods_for_table = cfg['period_include'][cfg['temporal_scale']]

    assert version_key in LINEAR_REGISTRY_BPR, f"Unknown version_key: {version_key}"
    trans = LINEAR_REGISTRY_BPR[version_key]
    xcol, ycol, xlab, ylab = trans()

    save_dir = cfg.get('save_dir', '.')
    os.makedirs(save_dir, exist_ok=True)

    corridor_groups = _resolve_corridor_groups(cfg)
    max_ncols = cfg.get('corridor_grid_ncols', 3)

    # ------------------------------------------------------------------
    # Collect all data + stats first (independent of layout)
    # ------------------------------------------------------------------
    panel_data = {}   # vds_id -> (df_use, cfg_i) or None
    panel_idx = 0     # global counter for xlim_list
    for vds_id in vds_list:
        cfg_i = copy.deepcopy(cfg)
        cfg_i['VDS_num'] = vds_id
        try:
            df_use = prepare_bpr_dataframe(cfg_i)
            panel_data[vds_id] = (df_use, cfg_i)
        except Exception as e:
            print(f"[BPR grid] Failed to load data for {vds_id}: {e}")
            panel_data[vds_id] = None

    all_table_rows = []
    saved_paths = []

    global_counter = [0]  # mutable counter shared across corridors

    # ------------------------------------------------------------------
    # Branch: corridor-mode (one file per corridor) vs flat pagination
    # ------------------------------------------------------------------
    has_corridor_groups = cfg.get('corridor_groups') is not None

    if has_corridor_groups:
        # --- One figure per corridor, saved as separate file ---
        for corridor_name, vds_ids_in_group in corridor_groups:
            n = len(vds_ids_in_group)
            g_ncols = min(n, max_ncols)
            g_nrows = math.ceil(n / g_ncols)

            fig, axs = plt.subplots(g_nrows, g_ncols,
                                      figsize=(7 * g_ncols, 6 * g_nrows),
                                      constrained_layout=True)
            if g_nrows * g_ncols == 1:
                axs = np.array([axs])
            else:
                for ax in axs.ravel():
                    ax.set_visible(False)

            for j, vds_id in enumerate(vds_ids_in_group):
                r = j // g_ncols
                c = j % g_ncols
                ax = axs[r, c] if g_nrows > 1 else axs[c]
                ax.set_visible(True)

                data = panel_data.get(vds_id)
                if data is None:
                    ax.text(0.5, 0.5, f"Error loading\n{vds_id}",
                             ha='center', va='center', transform=ax.transAxes)
                    ax.set_title(str(vds_id), fontsize=12 + font_add, pad=4)
                    global_counter[0] += 1
                    continue

                df_use, cfg_i = data

                for per in periods_for_table:
                    dfg = df_use[df_use['period'] == per].copy()
                    dfg.to_csv(f"BPR_input_{vds_id}_{per}.csv")
                    stats = fit_bpr_ols_stats(dfg, xcol, ycol)
                    peak_label = ('AM' if per == 'morning-peak' else
                                  'PM' if per == 'afternoon-peak' else
                                  'Entireday' if per == 'off-peak' else per)
                    all_table_rows.append({
                        'VDS': vds_label_map.get(str(vds_id), str(vds_id)),
                        'Peak-period': str(peak_label),
                        'N': 0 if stats is None else stats['n'],
                        r'$log\tilde{\alpha}$': np.nan if stats is None else stats['ln_tilde_alpha'],
                        't-statistic (tilde_alpha)': np.nan if stats is None else stats['alpha_t'],
                        'p-value (tilde_alpha)': np.nan if stats is None else stats['alpha_p'],
                        r'$N_0$': np.nan if stats is None else stats['N_0'],
                        r'$\beta$': np.nan if stats is None else stats['beta'],
                        't-statistic (beta)': np.nan if stats is None else stats['beta_t'],
                        'p-value (beta)': np.nan if stats is None else stats['beta_p'],
                        'R-square': np.nan if stats is None else stats['r2'],
                        'jb_stat': np.nan if stats is None else stats['jb_stat'],
                        'jb_p': np.nan if stats is None else stats['jb_p'],
                        'reset_stat': np.nan if stats is None else stats['reset_stat'],
                        'reset_p': np.nan if stats is None else stats['reset_p'],
                        'link_t': np.nan if stats is None else stats['link_t'],
                        'link_p': np.nan if stats is None else stats['link_p'],
                        'median': np.nan if stats is None else stats['median'],
                        'mean': np.nan if stats is None else stats['mean'],
                    })

                show_legend = not (show_legend_only_first and global_counter[0] != 0)
                use_xlim = xlim_list[global_counter[0]] if len(xlim_list) > 1 else xlim_list[0]
                plot_bpr_single_panel(
                    df_use=df_use, cfg=cfg_i, version_key=version_key,
                    xlim=use_xlim, ylim=ylim, ax=ax,
                    xcol=xcol, ycol=ycol,
                    show_legend=show_legend, font_add=font_add,
                )
                tag = vds_label_map.get(str(vds_id), str(vds_id))
                ax.set_title(f"{tag}", fontsize=14 + font_add, pad=6)
                global_counter[0] += 1

            fig.suptitle(f"{suptitle} — {corridor_name}", fontsize=18 + font_add, y=1.05)
            fig.supxlabel(xlab, fontsize=14 + font_add)
            fig.supylabel(ylab, fontsize=14 + font_add)

            corridor_tag = corridor_name.replace(' ', '').replace('-', '')
            out_path = os.path.join(save_dir, f"BPR_{out_name}_{corridor_tag}.png")
            fig.savefig(out_path, dpi=dpi, bbox_inches='tight')
            plt.close(fig)
            saved_paths.append(out_path)
            print(f"Saved corridor {corridor_name}: {out_path}")

    else:
        # --- Original flat pagination mode (no corridor_groups) ---
        panels_per_fig = nrows * ncols
        n_pages = math.ceil(len(vds_list) / panels_per_fig)

        for page in range(n_pages):
            start = page * panels_per_fig
            end   = min(start + panels_per_fig, len(vds_list))
            page_vds = vds_list[start:end]

            fig, axs = plt.subplots(nrows, ncols, figsize=(7 * ncols, 6 * nrows), constrained_layout=True)
            if panels_per_fig == 1:
                axs = np.array([axs])
            for ax in axs.ravel():
                ax.set_visible(False)

            for i, vds_id in enumerate(page_vds):
                r = i // ncols
                c = i % ncols
                ax = axs[r, c] if nrows > 1 else axs[c]
                ax.set_visible(True)

                data = panel_data.get(vds_id)
                if data is None:
                    ax.text(0.5, 0.5, f"Error loading\n{vds_id}",
                             ha='center', va='center', transform=ax.transAxes)
                    continue
                df_use, cfg_i = data

                for per in periods_for_table:
                    dfg = df_use[df_use['period'] == per].copy()
                    dfg.to_csv(f"BPR_input_{vds_id}_{per}.csv")
                    stats = fit_bpr_ols_stats(dfg, xcol, ycol)
                    peak_label = ('AM' if per == 'morning-peak' else
                                  'PM' if per == 'afternoon-peak' else
                                  'Entireday' if per == 'off-peak' else per)
                    all_table_rows.append({
                        'VDS': vds_label_map.get(str(vds_id), str(vds_id)),
                        'Peak-period': str(peak_label),
                        'N': 0 if stats is None else stats['n'],
                        r'$log\tilde{\alpha}$': np.nan if stats is None else stats['ln_tilde_alpha'],
                        't-statistic (tilde_alpha)': np.nan if stats is None else stats['alpha_t'],
                        'p-value (tilde_alpha)': np.nan if stats is None else stats['alpha_p'],
                        r'$N_0$': np.nan if stats is None else stats['N_0'],
                        r'$\beta$': np.nan if stats is None else stats['beta'],
                        't-statistic (beta)': np.nan if stats is None else stats['beta_t'],
                        'p-value (beta)': np.nan if stats is None else stats['beta_p'],
                        'R-square': np.nan if stats is None else stats['r2'],
                        'jb_stat': np.nan if stats is None else stats['jb_stat'],
                        'jb_p': np.nan if stats is None else stats['jb_p'],
                        'reset_stat': np.nan if stats is None else stats['reset_stat'],
                        'reset_p': np.nan if stats is None else stats['reset_p'],
                        'link_t': np.nan if stats is None else stats['link_t'],
                        'link_p': np.nan if stats is None else stats['link_p'],
                        'median': np.nan if stats is None else stats['median'],
                        'mean': np.nan if stats is None else stats['mean'],
                    })

                show_legend = not (show_legend_only_first and (start + i) != 0)
                use_xlim = xlim_list[start + i] if len(xlim_list) > 1 else xlim_list[0]
                plot_bpr_single_panel(
                    df_use=df_use, cfg=cfg_i, version_key=version_key,
                    xlim=use_xlim, ylim=ylim, ax=ax,
                    xcol=xcol, ycol=ycol,
                    show_legend=show_legend, font_add=font_add,
                )
                tag = vds_label_map.get(str(vds_id), str(vds_id))
                ax.set_title(f"{tag}", fontsize=14 + font_add, pad=6)

            fig.suptitle(f"{suptitle} (Page {page + 1}/{n_pages})", fontsize=18 + font_add, y=1.02)
            fig.supxlabel(xlab, fontsize=14 + font_add)
            fig.supylabel(ylab, fontsize=14 + font_add)

            range_suffix = _build_vds_range_suffix(page_vds)
            page_suffix = f"_page{page + 1}" if n_pages > 1 else ""
            out_path = os.path.join(save_dir, f"BPR_{out_name}{range_suffix}{page_suffix}.png")
            fig.savefig(out_path, dpi=dpi, bbox_inches='tight')
            plt.show()
            saved_paths.append(out_path)
            print(f"Saved page {page + 1}/{n_pages}: {out_path}")

    # ------------------------------------------------------------------
    # Save parameter table
    # ------------------------------------------------------------------
    df_params = pd.DataFrame(all_table_rows)
    if has_corridor_groups:
        table_suffix = _build_corridor_suffix(cfg)
    else:
        table_suffix = _build_vds_range_suffix(vds_list)
    out_table_csv = os.path.join(save_dir, f"BPR_{out_name}{table_suffix}.csv")
    df_params.to_csv(out_table_csv, index=False)
    print('Saved parameter table:', out_table_csv)
    print(df_params)
    return saved_paths


def plot_bpr_all_in_one_png_3x3(
    cfg,
    version_key: str,
    xlim=None,
    ylim=None,
    var_list=None,
    suptitle='Segment-Level Log-',
    out_name=None,
    show_legend_only_first=False,
    font_add=5,
    dpi=200,
):
    """Legacy wrapper: fixed 3×2 grid for up to 6 VDS."""
    plot_bpr_section_grid(
        cfg=cfg,
        version_key=version_key,
        nrows=3,
        ncols=2,
        xlim=xlim,
        ylim=ylim,
        suptitle=suptitle,
        out_name=out_name,
        show_legend_only_first=show_legend_only_first,
        font_add=font_add,
        dpi=dpi,
    )


# plot_bpr_single_panel

import numpy as np
import statsmodels.api as sm
from statsmodels.stats.stattools import jarque_bera


def plot_bpr_single_panel(
    df_use,
    cfg,
    version_key,
    xlim=None,
    ylim=None,
    ax=None,
    xcol=None,
    ycol=None,
    show_legend=True,
    font_add=None,
):
    if ax is None:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 1, figsize=(6, 4))

    TICK = 12 + font_add
    LEG = 8 + font_add
    ax.minorticks_on()
    ax.grid(True, which='major', linestyle='--', linewidth=1.0, alpha=0.35)
    ax.grid(True, which='minor', linestyle='-', linewidth=0.6, alpha=0.15)

    if cfg['temporal_scale'] == 'speedbasedpeak':
        periods = ['morning-peak', 'afternoon-peak']
    else:
        periods = cfg['period_include'][cfg['temporal_scale']]
        if isinstance(periods, str):
            periods = [periods]

    handles, labels = [], []
    for gname in periods:
        dfg = df_use[df_use['period'] == gname].copy()
        dfg = dfg[[xcol, ycol]].replace([np.inf, -np.inf], np.nan).dropna()
        if dfg.empty:
            continue

        x = dfg[xcol].to_numpy()
        y = dfg[ycol].to_numpy()
        sc = ax.scatter(x, y, s=55, alpha=0.55, edgecolors='none', label=gname)
        pretty = ('AM' if gname == 'morning-peak' else 'PM' if gname == 'afternoon-peak' else 'OLS-fit' if gname == 'off-peak' else gname)

        if len(dfg) >= 2 and np.nanmax(x) > np.nanmin(x):
            X = sm.add_constant(x)
            model = sm.OLS(y, X).fit()
            a, b = model.params[0], model.params[1]
            r2 = model.rsquared
            xx = np.linspace(np.nanmin(x), np.nanmax(x), 100)
            yy = a + b * xx
            ln, = ax.plot(xx, yy, linewidth=3, color=sc.get_facecolor()[0])
            labels.append(rf"{pretty}: $y={a:.2f}+{b:.2f}x$, $R^2$={r2:.3f}")
            handles.append(ln)
        else:
            labels.append(f"{pretty}: n={len(dfg)}")
            handles.append(sc)

    if xlim is None:
        import math
        x_data = df_use[xcol].replace([np.inf, -np.inf], np.nan).dropna()
        if not x_data.empty:
            x_min = float(x_data.min())
            x_max = float(x_data.max())
            xlim = [
                math.floor(x_min / 0.3) * 0.3,
                math.ceil(x_max / 0.3) * 0.3,
            ]
    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)

    ax.tick_params(axis='both', labelsize=TICK, width=1.8, length=6)
    for s in ax.spines.values():
        s.set_linewidth(1.8)

    if show_legend and handles:
        ax.legend(handles, labels, loc='upper left', fontsize=LEG, frameon=True)
    return ax
