"""Backward-compatibility redirect module.

This module no longer contains any functions. All former contents have
been redistributed to their logical homes:

- Stage 1 plotting   → plotting_stage1.py
- Stage 2 plotting   → plotting_stage2.py
- Stage 3 plotting   → plotting_stage3.py
- Legacy / dead code → _legacy.py (opt-in only)

If you imported from traffic_utils.plotting, update your imports to
use the new module names. For legacy code, use::

    from traffic_utils._legacy import *
"""


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
