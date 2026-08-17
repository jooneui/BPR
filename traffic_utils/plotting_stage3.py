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
                          build_default_recurrent_output_tag_from_bpr,
                          build_bpr_input_path)
from .plotting_stage2 import _flatten_vds_labels


def _vds_label_dict(cfg):
    """Return {str(vds_id): label} whether VDS_label_list is a list, flat dict, or nested dict."""
    labels = cfg.get('VDS_label_list', [])
    if isinstance(labels, dict):
        return _flatten_vds_labels(labels)
    return {str(vds): lbl for vds, lbl in zip(cfg.get('VDS_list', []), labels)}


_BPR_SUPTITLE_BASE = 'Log-linearized BPR fits'

# Names the temporal unit that each BPR data point represents. 'hour' and
# 'hour_split' share a name: both cut the day into 24 clock-hour units and
# differ only in whether the unit carries an AM/PM period label.
_BPR_UNIT_NAME = {
    'hour':           'hourly unit',
    'hour_split':     'hourly unit',
    'peak':           'peak-hour unit',
    'speedbasedpeak': 'near-recurrent peak-period unit',
    'entireday':      'entire-day unit',
    'entireday_rec':  'entire-day unit (near-recurrent days only)',
}

# Axis limits for the paper figures: y is fixed, and x is data-driven on the
# left but capped on the right so panels share a common upper bound.
BPR_YLIM_DEFAULT = [-10, 4]
BPR_XLIM_RIGHT_DEFAULT = 10.0


def bpr_suptitle(cfg):
    """Return the BPR figure suptitle, naming cfg's temporal unit."""
    unit = _BPR_UNIT_NAME.get(cfg.get('temporal_scale'))
    return f'{_BPR_SUPTITLE_BASE} on the {unit}' if unit else _BPR_SUPTITLE_BASE


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


def plot_bpr_section_grid(
    cfg,
    version_key: str,
    nrows=3,
    ncols=2,
    xlim=None,
    ylim=None,
    suptitle=None,
    out_name=None,
    show_legend_only_first=False,
    font_add=5,
    font_scale=1.0,
    dpi=200,
):
    """
    BPR calibration plots arranged by corridor groups.
    font_scale multiplies every font size (panel titles, axis labels, ticks,
    legends, suptitle) — used to enlarge the paper figure.
    If 'corridor_groups' is in cfg, panels are laid out in per-corridor sub-grids
    composited vertically. Otherwise falls back to flat (nrows x ncols) pagination.
    Works correctly for section_combined when VDS_list = ['C1_S1', 'C1_S2', ...].
    ``suptitle=None`` derives the title from cfg's temporal unit via bpr_suptitle().
    """
    if suptitle is None:
        suptitle = bpr_suptitle(cfg)
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
                    dfg.to_csv(build_bpr_input_path(cfg_i, vds_id, per))
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
                        'MAE': np.nan if stats is None else stats['mae'],
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
                try:
                    plot_bpr_single_panel(
                        df_use=df_use, cfg=cfg_i, version_key=version_key,
                        xlim=use_xlim, ylim=ylim, ax=ax,
                        xcol=xcol, ycol=ycol,
                        show_legend=show_legend, font_add=font_add,
                    )
                except Exception as e:
                    print(f"  [BPR panel error] VDS {vds_id}: {e}")
                    ax.text(0.5, 0.5, f"Plot error\n{vds_id}",
                            ha='center', va='center', transform=ax.transAxes)
                tag = vds_label_map.get(str(vds_id), str(vds_id))
                ax.set_title(f"{tag}", fontsize=14 + font_add, pad=6)
                global_counter[0] += 1

            fig.suptitle(f"{suptitle} — {corridor_name}", fontsize=18 + font_add, y=1.05)
            fig.supxlabel(xlab, fontsize=14 + font_add)
            fig.supylabel(ylab, fontsize=14 + font_add)

            corridor_tag = corridor_name.replace(' ', '').replace('-', '')
            out_path = os.path.join(save_dir, f"BPR_{out_name}_{corridor_tag}.png")
            try:
                fig.savefig(out_path, dpi=dpi, bbox_inches='tight')
                saved_paths.append(out_path)
                print(f"Saved corridor {corridor_name}: {out_path}")
            except Exception as e:
                print(f"  [BPR save error] corridor {corridor_name}: {e}")
            finally:
                plt.close(fig)

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
                    dfg.to_csv(build_bpr_input_path(cfg_i, vds_id, per))
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
                        'MAE': np.nan if stats is None else stats['mae'],
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
                    show_legend=show_legend, font_add=font_add, font_scale=font_scale,
                )
                tag = vds_label_map.get(str(vds_id), str(vds_id))
                ax.set_title(f"{tag}", fontsize=(14 + font_add) * font_scale, pad=6)

            sup = suptitle if n_pages == 1 else f"{suptitle} (Page {page + 1}/{n_pages})"
            fig.suptitle(sup, fontsize=(18 + font_add) * font_scale, y=1.06)
            fig.supxlabel(xlab, fontsize=(14 + font_add) * font_scale)
            fig.supylabel(ylab, fontsize=(14 + font_add) * font_scale)

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
    suptitle=None,
    out_name=None,
    show_legend_only_first=False,
    font_add=5,
    dpi=200,
):
    """Legacy wrapper: 3×2 grid by default; cfg may override the layout.

    Set cfg['bpr_grid_nrows'] / cfg['bpr_grid_ncols'] to lay all stations out
    in a single grid instead (used for the paper figure).
    """
    plot_bpr_section_grid(
        cfg=cfg,
        version_key=version_key,
        nrows=cfg.get('bpr_grid_nrows', 3),
        ncols=cfg.get('bpr_grid_ncols', 2),
        xlim=xlim,
        ylim=ylim,
        suptitle=suptitle,
        out_name=out_name,
        show_legend_only_first=show_legend_only_first,
        font_add=font_add,
        font_scale=cfg.get('bpr_grid_font_scale', 1.0),
        dpi=dpi,
    )


def plot_bpr_grid_vdslist(
    cfg,
    version_key: str,
    ncols=3,
    xlim=None,
    ylim=None,
    suptitle=None,
    out_name=None,
    font_add=5,
    dpi=200,
):
    """VDS-list-driven BPR grid: one panel per VDS in ``cfg['VDS_list']`` order,
    AM (blue) and PM (orange) fits overlaid per panel with the eqn + R^2 legend.

    Columns are fixed at ``ncols`` (default 3); rows = ceil(n / ncols). Ignores
    ``corridor_groups`` so the layout follows VDS_list, not corridors. Produces a
    single figure (no pagination). Matches the style of bpr_grid_recurrent.png.
    """
    cfg_flat = copy.deepcopy(cfg)
    cfg_flat.pop('corridor_groups', None)   # force flat / VDS_list layout
    n = len(cfg_flat.get('VDS_list', []))
    nrows = max(1, math.ceil(n / ncols))
    cfg_flat['bpr_grid_nrows'] = nrows
    cfg_flat['bpr_grid_ncols'] = ncols
    if out_name is None:
        out_name = build_default_recurrent_output_tag_from_bpr(cfg_flat)
    out_name = f"{out_name}_vdsgrid"
    return plot_bpr_section_grid(
        cfg=cfg_flat,
        version_key=version_key,
        nrows=nrows,
        ncols=ncols,
        xlim=xlim,
        ylim=ylim,
        suptitle=suptitle,
        out_name=out_name,
        font_add=font_add,
        font_scale=cfg_flat.get('bpr_grid_font_scale', 1.0),
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
    font_scale=1.0,
):
    if ax is None:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 1, figsize=(6, 4))

    TICK = (12 + font_add) * font_scale
    LEG = (8 + font_add) * font_scale
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
        # Match fit_bpr_ols_stats: a period is calibrated only with >= 5
        # observations. Skipping smaller series keeps the figure consistent
        # with the summary table, which reports these as excluded.
        if len(dfg) < 5:
            continue

        x = dfg[xcol].to_numpy()
        y = dfg[ycol].to_numpy()
        # Fix the colour by period so it is stable regardless of which periods
        # a panel happens to contain: AM blue, PM orange (off-peak/other blue).
        period_color = {'morning-peak': '#1f77b4',
                        'afternoon-peak': '#ff7f0e'}.get(gname, '#1f77b4')
        sc = ax.scatter(x, y, s=55, alpha=0.55, edgecolors='none', label=gname, color=period_color)
        pretty = ('AM' if gname == 'morning-peak' else 'PM' if gname == 'afternoon-peak' else 'OLS-fit' if gname == 'off-peak' else gname)

        if len(dfg) >= 2 and np.nanmax(x) > np.nanmin(x):
            X = sm.add_constant(x)
            model = sm.OLS(y, X).fit()
            a, b = model.params[0], model.params[1]
            r2 = model.rsquared
            xx = np.linspace(np.nanmin(x), np.nanmax(x), 100)
            yy = a + b * xx
            ln, = ax.plot(xx, yy, linewidth=3, color=period_color)
            labels.append(rf"{pretty}: $y={a:.2f}+{b:.2f}x$, $R^2$={r2:.3f}")
            handles.append(ln)
        else:
            labels.append(f"{pretty}: n={len(dfg)}")
            handles.append(sc)

    # Per-VDS override wins over both the caller's xlim and the data-driven
    # default: cfg['bpr_xlim_by_vds'] = {vds_id: [lo, hi]}. Keyed by temporal
    # scale first if the mapping is nested, so each unit can differ.
    _by_vds = cfg.get('bpr_xlim_by_vds') or {}
    if _by_vds and cfg.get('temporal_scale') in _by_vds:
        _by_vds = _by_vds[cfg['temporal_scale']]
    _override = _by_vds.get(str(cfg.get('VDS_num', '')))
    if _override is not None:
        xlim = list(_override)

    if xlim is None:
        import math
        x_data = df_use[xcol].replace([np.inf, -np.inf], np.nan).dropna()
        if not x_data.empty:
            x_min = float(x_data.min())
            x_max = float(x_data.max())
            pad = float(cfg.get('bpr_xlim_pad', 0.0))   # widen each end
            # Cap the right edge so every panel ends at the same demand, while
            # the left edge still follows the data.
            right = cfg.get('bpr_xlim_right', BPR_XLIM_RIGHT_DEFAULT)
            lo = math.floor(x_min / 0.3) * 0.3 - pad
            hi = math.ceil(x_max / 0.3) * 0.3 + pad
            # Only honour the shared cap when it actually sits right of the data.
            # Units with larger demand (entireday: ln N ~ 11-12) would otherwise
            # get an inverted axis and an empty-looking panel.
            if right is not None and float(right) > lo:
                hi = float(right)
            xlim = [lo, hi]
    if ylim is None:
        ylim = cfg.get('bpr_ylim', BPR_YLIM_DEFAULT)
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


