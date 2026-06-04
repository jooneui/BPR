"""Stage 1 plotting: Peak detection visualization.

Speed profiles, duration-vs-demand scatter, total-demand histograms, 
and PELT breakpoint visualization.
"""

import copy
import os
import matplotlib.pyplot as plt
import numpy as np

# cross-module imports
from .bpr_fitting import load_and_annotate, apply_filters


def speedprofile_plot(df, raw_timeframe, config, date):
    
    time_slot_hour = range(raw_timeframe, int(60*24/raw_timeframe) +1, raw_timeframe)
    
    # joon, pelt, RDP, derivative
    title_name = [f'Daily speed profile from multiple VDS (Date:{date})']   
    
    fig, ax1 = plt.subplots(figsize=(12, 5))

    ax1.set_xlabel('Time (Hours)',fontsize=16)
    ax1.set_ylabel('Speed (mph)',fontsize=16)
    ax1.set_title(title_name[0],fontsize=18)
    ax1.grid(True)
    ax1.set_xlim(0, 24+.1)
    ax1.set_xticks(np.arange(0, 25, 1))

    ax1.set_ylim(0,85)
    ax1.set_yticks(np.arange(0, 85 + 1, 10))  # Ticks at 0, 20, 40, 60, 80
    # Set y-axis tick label color
    # ax1.tick_params(axis='y', colors='green')
    # Set y-axis spine (axis line) color
    # ax1.spines['left'].set_color('green')

    colors = ['red','orange','green','blue','purple']
    
    for i, VDS  in enumerate(config['VDS_list']):
        df_per_VDS = df[i]
        df_per_VDS['time_slot_hour'] = df_per_VDS['time_slot'] / 60
        ax1.plot(df_per_VDS['time_slot_hour'], df_per_VDS['speed'], color=colors[i], linewidth=1.5, label=f'{i+1}th: {VDS}')
        ax1.legend(title="VDS", fontsize=10, loc="upper right")  # add legend inside plo
        
    fig.tight_layout()
    plt.savefig(f'./02 fig/17 Speedprofile/{config['VDS_list']}_{date}.png')
    # plt.show()  # Uncomment if you want to display the plot

from pathlib import Path
import pandas as pd
from functools import reduce



def plot_duration_vs_demand_single_panel(
    df_use,
    cfg,
    ax=None,
    xcol="totaldemand",
    duration_col="duration",
    period_col="period",
    periods=("morning-peak", "afternoon-peak"),
    dt_min=5,                # if duration is in # of 5-min bins
    duration_unit="auto",    # "auto" | "bins" | "minutes"
    show_legend=True,
    font_add=5,
    xlim=None,
    ylim=None,
):
    """
    Scatter: duration (y) vs totaldemand (x), overlaid by period (Mor/Aft).

    - df_use is your filtered congested-period observation table.
    - duration_unit:
        * "bins": convert duration -> minutes using dt_min
        * "minutes": use as-is
        * "auto": infer; if max(duration) <= 288, treat as bins (typical max # of 5-min bins in a day)
    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(6, 4))

    TICK = 12 + font_add
    LEG = 9 + font_add
    ax.minorticks_on()
    ax.grid(True, which="major", linestyle="--", linewidth=1.0, alpha=0.35)
    ax.grid(True, which="minor", linestyle="-", linewidth=0.6, alpha=0.15)

    # basic checks
    needed = {xcol, duration_col, period_col}
    missing = needed - set(df_use.columns)
    if missing:
        ax.text(0.5, 0.5, f"Missing columns: {missing}", ha="center", va="center", transform=ax.transAxes)
        return ax

    # infer duration unit
    dur = df_use[duration_col].dropna()
    if duration_unit == "auto":
        # Heuristic: <= 288 usually means "number of 5-min bins" (24*60/5)
        duration_unit_use = "bins" if (len(dur) and dur.max() <= 288) else "minutes"
    else:
        duration_unit_use = duration_unit

    def _dur_to_minutes(s):
        return s * dt_min if duration_unit_use == "bins" else s

    handles, labels = [], []
    for per in periods:
        dfg = df_use[df_use[period_col] == per].copy()
        dfg = dfg[[xcol, duration_col]].dropna()
        if dfg.empty:
            continue

        x = dfg[xcol].to_numpy()
        y = _dur_to_minutes(dfg[duration_col]).to_numpy()

        sc = ax.scatter(x, y, s=55, alpha=0.55, edgecolors="none")
        pretty = "Mor" if per == "morning-peak" else ("Aft" if per == "afternoon-peak" else per)

        # store one handle for legend (scatter)
        handles.append(sc)
        labels.append(pretty)

    if show_legend and handles:
        ax.legend(handles, labels, loc="upper left", fontsize=LEG, frameon=True)

    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)

    ax.tick_params(axis="both", labelsize=TICK, width=1.8, length=6)
    for s in ax.spines.values():
        s.set_linewidth(1.8)

    return ax



# ============================================
# B) 3x3 wrapper: duration vs demand (mirrors your BPR layout)
# ============================================


def plot_duration_demand_all_in_one_png_3x3(
    cfg,
    out_name="Duration_vs_Demand_ALL_3x3",
    periods=("morning-peak", "afternoon-peak"),
    dt_min=5,
    duration_unit="auto",
    xlim=None,
    ylim=None,
    font_add=5,
    dpi=200,
):
    """
    Creates a single 3x3 PNG:
      row1: VDS 1-①, VDS 1-②, blank
      row2: VDS 2-①, VDS 2-②, VDS 2-③
      row3: VDS 2-④, VDS 2-⑤, blank
    with Mor/Aft overlaid in each panel.
    """
    vds_list = cfg.get("VDS_list", [])
    _lbl = cfg.get("VDS_label_list", [])
    vds_label_map = _lbl if isinstance(_lbl, dict) else {str(v): l for v, l in zip(cfg.get("VDS_list", []), _lbl)}

    if len(vds_list) != 7:
        print(f"[Warning] Expected 7 VDS in cfg['VDS_list'], got {len(vds_list)}. Will plot what is available.")

    positions = [(0,0),(0,1),
                 (1,0),(1,1),(1,2),
                 (2,0),(2,1)]  # (0,2) and (2,2) blank

    fig, axs = plt.subplots(3, 3, figsize=(16, 14), constrained_layout=True)

    # hide all
    for ax in axs.ravel():
        ax.set_visible(False)

    for i, vds_id in enumerate(vds_list):
        if i >= len(positions):
            break
        r, c = positions[i]
        ax = axs[r, c]
        ax.set_visible(True)

        cfg_i = copy.deepcopy(cfg)
        cfg_i["VDS_num"] = vds_id
        cfg_i["VDS_list"] = vds_id  # keep your convention

        # ---- your pipeline ----
        df_all = load_and_annotate(cfg_i)

        if cfg_i.get("spatial_scope") == "single" and str(cfg_i.get("VDS_num")) == "1205541":
            if "month" in df_all.columns:
                df_all = df_all[~df_all["month"].isin(["2401", "2402", "2403", "2404"])]

        df_use = apply_filters(df_all, cfg_i)

        # panel plot
        show_legend = (i == 0)  # legend only on first to keep it clean
        plot_duration_vs_demand_single_panel(
            df_use=df_use,
            cfg=cfg_i,
            ax=ax,
            periods=periods,
            dt_min=dt_min,
            duration_unit=duration_unit,
            show_legend=show_legend,
            font_add=font_add,
            xlim=xlim,
            ylim=ylim,
        )

        tag = vds_label_map.get(str(vds_id), str(vds_id))
        ax.set_title(f"VDS {tag}", fontsize=16 + font_add, pad=8)

    fig.suptitle("Congested-period Duration vs Total Demand", fontsize=20 + font_add, y=1.05)
    fig.supxlabel(r"Total demand $Q$ (vehicles)", fontsize=16 + font_add)
    fig.supylabel("Congested duration (minutes)", fontsize=16 + font_add)

    save_dir = cfg.get("save_dir", ".")
    os.makedirs(save_dir, exist_ok=True)
    out_path = os.path.join(save_dir, f"{out_name}.png")
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.show()

    print(f"Saved: {out_path}")
    return out_path




import os
import copy
import numpy as np
import matplotlib.pyplot as plt



def plot_totaldemand_histogram_single_panel(
    df_use,
    ax,
    xcol="totaldemand",
    period_col="period",
    periods=("morning-peak", "afternoon-peak"),
    bins=30,
    density=True,
    font_add=5,
    show_legend=True,
):
    TICK = 12 + font_add
    LEG = 10 + font_add

    # styling
    ax.minorticks_on()
    ax.grid(True, which="major", linestyle="--", linewidth=1.0, alpha=0.35)
    ax.grid(True, which="minor", linestyle="-", linewidth=0.6, alpha=0.15)
    ax.set_ylim(0, 0.001)
    ax.set_xlim(0, 10000)

    handles, labels = [], []
    for per in periods:
        s = df_use.loc[df_use[period_col] == per, xcol].dropna()
        if s.empty:
            continue

        lab = "Mor" if per == "morning-peak" else ("Aft" if per == "afternoon-peak" else per)

        # use common bin edges per panel (stable overlay)
        # -> compute edges from the pooled data in this panel
    pooled = df_use.loc[df_use[period_col].isin(periods), xcol].dropna()
    if pooled.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        return

    edges = np.histogram_bin_edges(pooled.to_numpy(), bins=bins)

   # split data explicitly
    mor = df_use.loc[df_use[period_col] == "morning-peak", xcol].dropna().to_numpy()
    aft = df_use.loc[df_use[period_col] == "afternoon-peak", xcol].dropna().to_numpy()
    
    # Morning: filled histogram
    if mor.size:
        ax.hist(
            mor,
            bins=edges,
            density=density,
            histtype = "step",
            linewidth=2.5,
            label="Mor",
        )
    
    # Afternoon: outline-only histogram
    if aft.size:
        ax.hist(
            aft,
            bins=edges,
            density=density,
            histtype="step",
            linewidth=2.5,
            label="Aft",
        )
    if show_legend:
        ax.legend(loc="upper right", fontsize=LEG, frameon=True)
    

    ax.tick_params(axis="both", labelsize=TICK, width=1.8, length=6)
    for sp in ax.spines.values():
        sp.set_linewidth(1.8)




def plot_totaldemand_histogram_all_in_one_png_3x3(
    cfg,
    out_name="TotalDemand_Hist_ALL_3x3",
    periods=("morning-peak", "afternoon-peak"),
    bins=30,
    density=True,
    font_add=5,
    dpi=200,
):
    """
    Same 3x3 layout as your BPR plots:
      row1: VDS 1-①, VDS 1-②, blank
      row2: VDS 2-①, VDS 2-②, VDS 2-③
      row3: VDS 2-④, VDS 2-⑤, blank
    Each panel overlays Mor/Aft histograms of totaldemand.
    """
    vds_list = cfg.get("VDS_list", [])
    _lbl = cfg.get("VDS_label_list", [])
    vds_label_map = _lbl if isinstance(_lbl, dict) else {str(v): l for v, l in zip(cfg.get("VDS_list", []), _lbl)}

    positions = [(0,0),(0,1),
                 (1,0),(1,1),(1,2),
                 (2,0),(2,1)]  # (0,2), (2,2) blank

    fig, axs = plt.subplots(3, 3, figsize=(16, 14), constrained_layout=True)
    for ax in axs.ravel():
        ax.set_visible(False)

    for i, vds_id in enumerate(vds_list):
        if i >= len(positions):
            break
        r, c = positions[i]
        ax = axs[r, c]
        ax.set_visible(True)

        cfg_i = copy.deepcopy(cfg)
        cfg_i["VDS_num"] = vds_id
        cfg_i["VDS_list"] = vds_id

        df_all = load_and_annotate(cfg_i)

        # your special exclusion
        if cfg_i.get("spatial_scope") == "single" and str(cfg_i.get("VDS_num")) == "1205541":
            if "month" in df_all.columns:
                df_all = df_all[~df_all["month"].isin(["2401","2402","2403","2404"])]

        df_use = apply_filters(df_all, cfg_i)

        # show_legend = (i == 0)  # only first panel
        show_legend = True
        plot_totaldemand_histogram_single_panel(
            df_use=df_use,
            ax=ax,
            xcol="totaldemand",
            period_col="period",
            periods=periods,
            bins=bins,
            density=density,
            font_add=font_add,
            show_legend=show_legend,
        )

        tag = vds_label_map.get(str(vds_id), str(vds_id))
        ax.set_title(f"VDS {tag}", fontsize=16 + font_add, pad=8)

    fig.suptitle("Total Demand Histogram", fontsize=20 + font_add, y=1.05)
    fig.supxlabel("Total demand $Q$ (vehicles)", fontsize=16 + font_add)
    fig.supylabel("Relative frequency" if density else "Count", fontsize=16 + font_add)

    save_dir = cfg.get("save_dir", ".")
    os.makedirs(save_dir, exist_ok=True)
    out_path = os.path.join(save_dir, f"{out_name}.png")
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.show()

    print(f"Saved: {out_path}")
    return out_path


