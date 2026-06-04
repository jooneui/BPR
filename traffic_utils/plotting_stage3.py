"""Stage 3 plotting: BPR fitting visualization.

FD scatter with BPR fit lines, BPR section grids,
and BPR single panels.
"""

import copy
import math
import os
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
from matplotlib.ticker import AutoMinorLocator

from .bpr_fitting import (fit_bpr_ols_stats, prepare_bpr_dataframe,
                          LINEAR_REGISTRY_BPR,
                          build_default_recurrent_output_tag_from_bpr)


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


