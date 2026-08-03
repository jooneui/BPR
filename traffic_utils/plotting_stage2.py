"""Stage 2 plotting: Recurrent analysis + Fundamental Diagram visualization.

FD composite figures, recurrent peak band drawing,
segment selection annotations, and common-point visualizations.
"""

import copy
import math
import os
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
from matplotlib.ticker import AutoMinorLocator
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import seaborn as sns
from .bpr_fitting import time_to_fractional_hour

DAY_ORDER = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

_FD_COLORS = {'AM': '#1f77b4', 'PM': '#d62728'}
_PERIOD_TO_AM_PM = {'morning-peak': 'AM', 'afternoon-peak': 'PM'}


def _compute_start_hour(df):
    if 'start_hour' in df.columns:
        return df
    df = df.copy()
    df['start_hour'] = df['start_time'].apply(time_to_fractional_hour)
    return df


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
    """Plot fundamental diagram scatter, split by AM/PM.

    Returns
    -------
    dict  {'AM': bool, 'PM': bool}
        True = period passes the density-threshold check and should proceed
        to recurrent classification and BPR; False = skip.
    """
    # ----------------------------
    # 1) Resolve X/Y column names
    # ----------------------------
    if variable == "qk":
        x_col, y_col = 'density', 'avg_flow'
    elif variable == "uq":
        x_col, y_col = 'avg_flow', 'avg_speed'
    else:
        raise ValueError(f"Unknown variable: {variable}")

    # ----------------------------
    # 2) AM/PM split + threshold
    # ----------------------------
    df_segment = _compute_start_hour(df_segment)
    df_segment = df_segment.copy()
    df_segment['_am_pm'] = df_segment['start_hour'].apply(
        lambda h: 'AM' if h < 12 else 'PM'
    )

    den_threshold = cfg.get('den_threshold', 40)
    vds_id = cfg.get('VDS_num', '?')

    # Sufficiency screening is purely rate-based: a period proceeds only if its
    # congested-point count per year of record reaches per_year_threshold.
    # Record length = number of distinct calendar days that actually carry data
    # (gaps excluded), so the bar scales with real coverage rather than the raw
    # first→last span.
    per_year_threshold = cfg.get('count_threshold_per_year', 50)
    record_years = 1.0
    if 'date' in df_segment.columns:
        # Strip the '.0' a float-typed date column produces, else every value
        # fails the '%y%m%d' parse and the record length falls back to 1 year.
        _d = pd.to_datetime(df_segment['date'].astype(str)
                            .str.replace(r'\.0$', '', regex=True).str.zfill(6),
                            format='%y%m%d', errors='coerce')
        if _d.notna().any():
            n_days = _d.dt.normalize().nunique()
            record_years = max(n_days / 365.25, 1e-9)

    skip_flags = {}
    fd_handles = []

    # ----------------------------
    # 3) Figure setup
    # ----------------------------
    plt.rcParams.update({
        "font.family": "STIXGeneral",
        "mathtext.fontset": "stix",
        "axes.unicode_minus": False,
    })

    fig, ax = plt.subplots(figsize=(8.4, 5.6), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    for period_label, color in _FD_COLORS.items():
        sub = df_segment[df_segment['_am_pm'] == period_label]
        if sub.empty:
            skip_flags[period_label] = False
            continue
        n_total = len(sub)
        n_over  = int((sub['density'] > den_threshold).sum())
        rate = n_over / record_years
        passes = rate >= per_year_threshold
        skip_flags[period_label] = passes

        lbl = (f"{period_label}  ({n_over} / {n_total} over {den_threshold}"
               f"; {rate:.0f}/yr)")
        ax.scatter(
            sub[x_col], sub[y_col],
            s=14, alpha=0.18, linewidths=0,
            color=color, rasterized=True,
        )
        fd_handles.append(mpatches.Patch(color=color, label=lbl))

        if not passes:
            print(
                f"[SKIP] VDS {vds_id} {period_label}: "
                f"{rate:.1f}/yr < {per_year_threshold}/yr required "
                f"({n_over} / {n_total} points over density {den_threshold}) "
                f"— will skip recurrent and BPR."
            )

    # ----------------------------
    # 4) Reference line q = v k
    # ----------------------------
    if variable == "qk":
        all_x = df_segment[x_col].dropna()
        if xlim is not None:
            xmin, xmax = xlim
        else:
            xmin = max(0, float(np.nanmin(all_x))) if len(all_x) else 0
            xmax = float(np.nanmax(all_x)) * 1.05 if len(all_x) else 1

        xs = np.linspace(xmin, xmax, 300)
        ref_line = ax.plot(
            xs, speed_thre * xs,
            linestyle="--",
            linewidth=2.6,
            color="black",
            label=rf"$q = {speed_thre}k$"
        )[0]

        all_handles = fd_handles + [ref_line]
        leg = ax.legend(
            handles=all_handles,
            loc="upper right",
            fontsize=14,
            frameon=True,
            fancybox=True,
            borderpad=0.6,
            handlelength=2.2,
        )
        leg.get_frame().set_alpha(0.95)
    else:
        if fd_handles:
            leg = ax.legend(
                handles=fd_handles,
                loc="upper right",
                fontsize=14,
                frameon=True,
                fancybox=True,
                borderpad=0.6,
            )
            leg.get_frame().set_alpha(0.95)

    # ----------------------------
    # 5) Labels, limits, title
    # ----------------------------
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
    # 6) Ticks + grid
    # ----------------------------
    ax.tick_params(axis="both", which="major", labelsize=18, length=6, width=1.2)
    ax.tick_params(axis="both", which="minor", length=3, width=1.0)

    ax.xaxis.set_minor_locator(AutoMinorLocator(5))
    ax.yaxis.set_minor_locator(AutoMinorLocator(5))

    ax.grid(True, which="major", alpha=0.22, linewidth=1.0)
    ax.grid(True, which="minor", alpha=0.10, linewidth=0.8)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.2)
    ax.spines["bottom"].set_linewidth(1.2)

    # ----------------------------
    # 7) Save
    # ----------------------------
    if save_name is None:
        os.makedirs(cfg["save_dir"], exist_ok=True)
        save_name = (
            f"{cfg['save_dir']}/FD_clean_{cfg['spatial_scope']}_"
            f"{cfg.get('VDS_num','multi')}_{variable}_"
            f"{cfg['temporal_scale']}_{cfg.get('period_filter','all')}_"
            f"{version_key}_{cfg['method']}"
        )

    fig.savefig(save_name + ".png", bbox_inches="tight")
    plt.close(fig)

    return skip_flags


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
        
        # ax.vlines(real_p['week_num'], real_p['start_hour'], real_p['end_hour'], color='lightgrey', alpha=0.8, linewidth=3)
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


def _resolve_speed_threshold(speed_thre, vds_id, cfg=None):
    """Resolve speed threshold for a VDS, with fallback to base VDS prefix.

    For section-combined names like 'C1_S1_D1', tries:
      1. speed_thre['C1_S1_D1']  (per-section, user-specified)
      2. speed_thre['C1']        (base VDS, user-specified)
      3. 55                       (hard default)
    """
    if isinstance(speed_thre, dict):
        if vds_id in speed_thre:
            return speed_thre[vds_id]
        # Fallback: try base VDS prefix (e.g. 'C1' from 'C1_S1_D1')
        base = vds_id.split('_')[0] if '_' in vds_id else vds_id
        if base in speed_thre:
            return speed_thre[base]
        return 55  # default
    return speed_thre  # scalar


def plot_fd_all_in_one_png(
    cfg, variable, version_key, speed_thre, xlim, ylim,
    title_suffix="", out_name="FD_all_in_one"
):
    """
    Generate individual FD PNGs per VDS, then stitch into one composite figure.
    If 'corridor_groups' is defined in cfg, panels are arranged in per-corridor
    sub-grids composited vertically. Otherwise falls back to flat N-column grid.
    """
    pass  # all helpers defined in this module

    # --- 1) generate individual PNGs using your existing pipeline ---

    vds_ids = cfg["VDS_list"]
    vds_label_map = _vds_label_dict(cfg)
    vds_labels = [vds_label_map[vid] for vid in vds_ids]
    N = len(vds_ids)

    os.makedirs(cfg["save_dir"], exist_ok=True)

    cfg_i = cfg.copy()

    png_paths = []
    png_map = {}    # vds_id -> png_path for corridor lookup
    skip_map = {}   # vds_id -> {'AM': bool, 'PM': bool}

    for vds_id, vds_lab in zip(vds_ids, vds_labels):
        cfg_i["VDS_num"] = vds_id
        cfg_i["VDS_label"] = vds_lab

        print(cfg_i["VDS_num"])
        fn_segment = (
            f"./04_peak_period_result/c_daily_traffic_segment_{cfg_i['spatial_scope']}_"
            f"{cfg_i['VDS_num']}_{cfg_i['temporal_scale']}_{cfg_i['aggregate_timeframe']}_"
            f"{cfg_i['method']}_{cfg_i['congest_method']}.csv"
        )
        fn_division = (
            f"./04_peak_period_result/c_daily_traffic_division_{cfg_i['spatial_scope']}_"
            f"{cfg_i['VDS_num']}_{cfg_i['temporal_scale']}_{cfg_i['aggregate_timeframe']}_"
            f"{cfg_i['method']}_{cfg_i['congest_method']}.csv"
        )

        df_segment = pd.read_csv(fn_segment)
        df_division = pd.read_csv(fn_division)

        # special filter for VDS 1205541
        if cfg_i.get("spatial_scope") == "single" and str(cfg_i.get("VDS_num")) == "1205541":
            df_segment['month'] = df_segment['date'].astype(str).str[:4]
            df_segment = df_segment[~df_segment["month"].isin(["2401", "2402", "2403"])]

        save_base = f"{cfg_i['save_dir']}/FD_{vds_lab}_{vds_id}_{variable}"
        flags = plot_linear_by_group_FD(
            df_segment=df_segment,
            df_division=df_division,
            variable=variable,
            cfg=cfg_i,
            version_key=version_key,
            speed_thre=_resolve_speed_threshold(speed_thre, vds_id, cfg_i),
            xlim=xlim,
            ylim=ylim,
            title_suffix=title_suffix,
            save_name=save_base
        )
        skip_map[str(vds_id)] = flags

        png_path = save_base + ".png"
        png_paths.append(png_path)
        png_map[vds_id] = png_path

    # --- 2) stitch them into one PNG ---
    max_ncols = cfg.get('corridor_grid_ncols', 3)
    corridor_groups = _resolve_corridor_groups(cfg)
    has_corridor_groups = cfg.get('corridor_groups') is not None

    if variable == "qk":
        var_title = r"$k-q$"
        xlab = r"$k \,	\text{(vpmpl)}$"
        ylab = r"$q \, 	\text{(vphpl)}$"
    elif variable == "uq":
        var_title = r"$q-z$"
        xlab = r"$q \,	\text{(vphpl)}$"
        ylab = r"$z \, 	\text{(min}/	\text{mile)}$"

    if has_corridor_groups:
        # --- One figure per corridor, saved as separate file ---
        corridor_out_paths = []
        for corridor_name, vds_ids_in_group in corridor_groups:
            n = len(vds_ids_in_group)
            g_ncols = min(n, max_ncols)
            g_nrows = math.ceil(n / g_ncols)

            fig = plt.figure(figsize=(6 * g_ncols, 5 * g_nrows), dpi=300)
            gs = GridSpec(g_nrows, g_ncols, figure=fig, wspace=0.04, hspace=0.08)

            positions = [(i // g_ncols, i % g_ncols) for i in range(n)]
            used = set(positions)

            for j, vds_id in enumerate(vds_ids_in_group):
                r, c = positions[j]
                ax = fig.add_subplot(gs[r, c])
                path = png_map.get(vds_id)
                if path and os.path.exists(path):
                    img = mpimg.imread(path)
                    ax.imshow(img)
                else:
                    ax.text(0.5, 0.5, f"Missing\n{vds_id}", ha='center', va='center')
                ax.axis("off")

            # fill remaining cells if grid is not full
            for r in range(g_nrows):
                for c in range(g_ncols):
                    if (r, c) not in used:
                        fig.add_subplot(gs[r, c]).axis("off")

            fig.suptitle(f"{var_title} — {corridor_name}", fontsize=24, y=0.93)
            fig.supxlabel(xlab, fontsize=22, y=0.07)
            fig.supylabel(ylab, fontsize=22, x=0.09)

            corridor_tag = corridor_name.replace(' ', '').replace('-', '')
            out_png = f"{cfg['save_dir']}/{out_name}_{variable}_{cfg['temporal_scale']}_{corridor_tag}.png"
            fig.savefig(out_png, bbox_inches="tight")
            plt.close(fig)
            corridor_out_paths.append(out_png)
            print(f"Saved corridor {corridor_name}: {out_png}")

        out_png = corridor_out_paths[-1] if corridor_out_paths else None
    else:
        # --- Original flat grid layout ---
        ncols_fd = min(N, max_ncols)
        nrows_fd = math.ceil(N / ncols_fd)
        fig = plt.figure(figsize=(6 * ncols_fd, 5 * nrows_fd), dpi=300)
        gs = GridSpec(nrows_fd, ncols_fd, figure=fig, wspace=0.04, hspace=0.08)

        positions = [(i // ncols_fd, i % ncols_fd) for i in range(N)]
        used = set(positions)

        for path, (r, c) in zip(png_paths, positions):
            ax = fig.add_subplot(gs[r, c])
            img = mpimg.imread(path)
            ax.imshow(img)
            ax.axis("off")

        for r in range(nrows_fd):
            for c in range(ncols_fd):
                if (r, c) not in used:
                    fig.add_subplot(gs[r, c]).axis("off")

        out_png = f"{cfg['save_dir']}/{out_name}_{variable}_{cfg['temporal_scale']}.png"

        fig.supxlabel(xlab, fontsize=22, y=0.07)
        fig.supylabel(ylab, fontsize=22, x=0.11)

        if cfg['temporal_scale'] == 'hour':
            sup_title = f"Traffic State Relationship under Hourly Aggregation: {var_title} Relationship"
        elif cfg['temporal_scale'] == 'speedbasedpeak':
            sup_title = f"Traffic State Relationship under Segment-Level Aggregation: {var_title} Relationship"
        else:
            sup_title = f"Traffic State Relationship: {var_title} Relationship"

        fig.suptitle(sup_title, fontsize=24, y=0.93)

        fig.savefig(out_png, bbox_inches="tight")
        plt.close(fig)

        print("Saved:", out_png)
    return out_png, skip_map


