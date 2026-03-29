"""
fig_den — Dewan Ekonomi Nasional (DEN) charting package for Python.

A matplotlib/seaborn wrapper that applies DEN's house style to charts.

Usage:
    import fig_den as den

    den.style()                        # apply DEN style globally
    fig, ax = den.subplots()           # create a figure
    den.line(ax, df, x, y, hue)        # line chart
    den.bar(ax, df, x, y)              # bar chart
    den.save(fig, "output.png")        # save at 300 dpi
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

# ---------------------------------------------------------------------------
# 1. COLOR PALETTES
# ---------------------------------------------------------------------------

# Full DEN palette (12 colours, v1.0)
PALETTE = [
    "#EEC051",  # 0  gold         (core)
    "#845B24",  # 1  dark brown   (core)
    "#C00000",  # 2  red          (core)
    "#FFC000",  # 3  bright gold  (standard)
    "#A19574",  # 4  tan          (standard)
    "#3A3A3A",  # 5  dark grey    (standard)
    "#935200",  # 6  deep amber   (standard)
    "#F8E69B",  # 7  light gold   (extended)
    "#C3986D",  # 8  warm sand    (extended)
    "#B58B80",  # 9  rose brown   (extended)
    "#9F522C",  # 10 rust         (extended)
    "#8B8679",  # 11 olive tan    (extended)
]

# Handy sub-palettes
PALETTE_2 = PALETTE[:2]        # gold + dark brown  (most common pair)
PALETTE_4 = PALETTE[:4]        # gold, dark brown, red, bright gold
PALETTE_6 = PALETTE[:6]
GOLD        = PALETTE[0]
DARK_BROWN  = PALETTE[1]
BROWN       = PALETTE[1]       # backwards-compatible alias
RED         = PALETTE[2]
BRIGHT_GOLD = PALETTE[3]
TAN         = PALETTE[4]
GREY        = PALETTE[5]
DEEP_AMBER  = PALETTE[6]
LIGHT_GOLD  = PALETTE[7]

# Sequential colormap (light gold → gold → dark brown)
CMAP_SEQ = LinearSegmentedColormap.from_list("den_seq", [LIGHT_GOLD, GOLD, DARK_BROWN])

# Diverging colormap (gold ← light gold → red)
CMAP_DIV = LinearSegmentedColormap.from_list("den_div", [GOLD, LIGHT_GOLD, RED])


def palette(n=None):
    """Return the first *n* DEN colours (default: all 12)."""
    if n is None:
        return list(PALETTE)
    return list(PALETTE[:n])


def cmap(kind="sequential"):
    """Return a DEN colormap.  kind = 'sequential' | 'diverging'."""
    return CMAP_SEQ if kind == "sequential" else CMAP_DIV


# ---------------------------------------------------------------------------
# 2. GLOBAL STYLE
# ---------------------------------------------------------------------------

_STYLE_APPLIED = False


def style(font_scale=1.0):
    """Apply DEN house style globally.

    Call once at the top of your script / notebook.
    """
    global _STYLE_APPLIED

    sns.set_theme(
        style="whitegrid",
        font_scale=font_scale,
        rc={
            # Grid
            "axes.grid": True,
            "grid.alpha": 0.3,
            "grid.linestyle": "-",
            # Spines — only bottom
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": True,
            "axes.spines.bottom": True,
            # Figure
            "figure.figsize": (10, 6),
            "figure.dpi": 100,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            # Font
            "font.family": "sans-serif",
            "axes.titleweight": "bold",
            "axes.titlesize": 13,
            "axes.labelsize": 12,
            # Legend
            "legend.frameon": False,
            "legend.fontsize": 10,
        },
    )
    sns.set_palette(sns.color_palette(PALETTE))
    _STYLE_APPLIED = True


def _ensure_style():
    if not _STYLE_APPLIED:
        style()


# ---------------------------------------------------------------------------
# 3. FIGURE / AXES HELPERS
# ---------------------------------------------------------------------------


def subplots(nrows=1, ncols=1, figsize=None, **kwargs):
    """Create a figure + axes with sensible DEN defaults."""
    _ensure_style()
    if figsize is None:
        w = 5.5 * ncols
        h = 4.5 * nrows
        figsize = (w, h)
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, **kwargs)
    return fig, axes


def twinx(ax, *, ylabel="", grid=False):
    """Create a DEN-styled secondary y-axis (right side).

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The primary axes to twin.
    ylabel : str
        Label for the right y-axis.
    grid : bool
        Whether to show grid on the secondary axis.
        Default False to avoid double-gridlines.

    Returns
    -------
    ax2 : matplotlib.axes.Axes
        The new secondary axes sharing the same x-axis.
    """
    ax2 = ax.twinx()
    ax2.grid(grid)
    ax2.spines["right"].set_visible(True)
    if ylabel:
        ax2.set_ylabel(ylabel)
    return ax2


# ---------------------------------------------------------------------------
# 4. CHART FUNCTIONS
# ---------------------------------------------------------------------------


def line(ax, data, x, y, hue=None, *, marker="o", markersize=4,
         linewidth=2.5, colors=None, annotate_last=False, pct=False,
         legend=True, **kwargs):
    """Line chart on *ax*.

    Parameters
    ----------
    annotate_last : bool
        If True, add a bold label at the last data point of each line.
    pct : bool
        If True, append '%' to the annotation.
    """
    _ensure_style()
    cols = colors or palette()

    if hue is not None:
        groups = data[hue].unique()
        for i, grp in enumerate(groups):
            sub = data[data[hue] == grp]
            c = cols[i % len(cols)]
            ax.plot(sub[x], sub[y], color=c, linewidth=linewidth,
                    label=grp, marker=marker, markersize=markersize, **kwargs)
            if annotate_last:
                _annotate_end(ax, sub[x], sub[y], c, pct=pct)
    else:
        c = cols[0]
        ax.plot(data[x], data[y], color=c, linewidth=linewidth,
                marker=marker, markersize=markersize, **kwargs)
        if annotate_last:
            _annotate_end(ax, data[x], data[y], c, pct=pct)

    if legend and hue is not None:
        legend_top(ax)


def line_multi(ax, data, x, y_cols, *, colors=None, marker="o",
               markersize=4, linewidth=2.5, annotate_last=False,
               pct=False, legend=True, **kwargs):
    """Plot multiple y columns against a shared x column.

    Useful when data is in wide format (each series is a column).
    """
    _ensure_style()
    cols = colors or palette()
    for i, col in enumerate(y_cols):
        c = cols[i % len(cols)]
        ax.plot(data[x], data[col], color=c, linewidth=linewidth,
                label=col, marker=marker, markersize=markersize, **kwargs)
        if annotate_last:
            _annotate_end(ax, data[x], data[col], c, pct=pct)
    if legend:
        legend_top(ax)


def bar(ax, data, x, y, *, colors=None, width=0.6, annotate=True,
        fmt="{:.1f}", **kwargs):
    """Simple (unstacked) bar chart.

    Parameters
    ----------
    annotate : bool
        If True, place the value on top of each bar.
    fmt : str
        Format string for annotations.
    """
    _ensure_style()
    cols = colors or palette()
    c = cols[0] if isinstance(cols, list) else cols
    bars = ax.bar(data[x].astype(str), data[y], color=c, width=width, **kwargs)
    if annotate:
        for b, val in zip(bars, data[y]):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(),
                    fmt.format(val), ha="center", va="bottom",
                    fontsize=9, fontweight="bold")
    return bars


def stacked_bar(ax, data, x, y_cols, *, colors=None, annotate_pct=True,
                legend=True, **kwargs):
    """Stacked bar chart from wide-format data.

    Parameters
    ----------
    data : DataFrame
        Index or column *x* holds categories, *y_cols* are the stacks.
    annotate_pct : bool
        Show percentage share inside each segment.
    """
    _ensure_style()
    cols = colors or palette()
    bottom = np.zeros(len(data))
    x_vals = data[x].astype(str) if x in data.columns else data.index.astype(str)
    x_pos = np.arange(len(x_vals))

    for i, col in enumerate(y_cols):
        c = cols[i % len(cols)]
        vals = data[col].values.astype(float)
        ax.bar(x_pos, vals, bottom=bottom, color=c, label=col, **kwargs)

        if annotate_pct:
            totals = data[y_cols].sum(axis=1).values.astype(float)
            for j in range(len(vals)):
                if totals[j] > 0 and vals[j] > 0:
                    pct = vals[j] / totals[j] * 100
                    ax.text(x_pos[j], bottom[j] + vals[j] / 2,
                            f"{pct:.1f}%", ha="center", va="center",
                            color="white", fontsize=8, fontweight="bold")
        bottom += vals

    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_vals)
    if legend:
        legend_top(ax)


def grouped_bar(ax, data, x, y_cols, *, colors=None, width=0.35,
                annotate=True, fmt="{:.1f}", legend=True, **kwargs):
    """Side-by-side grouped bar chart.

    Parameters
    ----------
    data : DataFrame
        *x* column for categories, *y_cols* for each group.
    """
    _ensure_style()
    cols = colors or palette()
    x_vals = data[x]
    x_pos = np.arange(len(x_vals))
    n = len(y_cols)
    offsets = np.linspace(-(n - 1) / 2 * width, (n - 1) / 2 * width, n)

    for i, col in enumerate(y_cols):
        c = cols[i % len(cols)]
        vals = data[col].values.astype(float)
        bars = ax.bar(x_pos + offsets[i], vals, width=width, color=c,
                      label=col, **kwargs)
        if annotate:
            for b, val in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, b.get_height(),
                        fmt.format(val), ha="center", va="bottom",
                        fontsize=8, fontweight="bold")

    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_vals)
    if legend:
        legend_top(ax)
    return x_pos


def combo_bar_line(ax, data, x, bar_cols, line_cols, *,
                   bar_colors=None, line_colors=None,
                   bar_width=0.35, bar_annotate=True, bar_fmt="{:.1f}",
                   line_marker="o", line_markersize=4, line_linewidth=2.5,
                   line_annotate_last=False, line_pct=False,
                   ylabel_left="", ylabel_right="",
                   legend=True, legend_ncol=4):
    """Grouped bars on primary y-axis + line(s) on secondary y-axis.

    Parameters
    ----------
    ax : Axes
        Primary axes (left y-axis, used for bars).
    data : DataFrame
        Wide-format data.
    x : str
        Column name for the shared x-axis (categories).
    bar_cols : list of str
        Column names for grouped bar series.
    line_cols : list of str
        Column names for line series on secondary y-axis.
    bar_colors, line_colors : list or None
        Colours for each series.  Defaults to DEN palette.
    bar_width : float
        Width of each bar group member.
    bar_annotate : bool
        Annotate bar values.
    bar_fmt : str
        Format string for bar annotations.
    line_marker, line_markersize, line_linewidth
        Line styling options.
    line_annotate_last : bool
        Add bold label at the last data point of each line.
    line_pct : bool
        If True, append '%' to line annotations.
    ylabel_left, ylabel_right : str
        Labels for left and right y-axes.
    legend : bool
        Show merged legend above the chart.
    legend_ncol : int
        Number of legend columns.

    Returns
    -------
    ax2 : Axes
        The secondary axes (right y-axis), for further formatting.
    """
    _ensure_style()
    b_cols = bar_colors or palette()
    l_cols = line_colors or palette(len(bar_cols) + len(line_cols))[len(bar_cols):]

    x_vals = data[x]
    x_pos = np.arange(len(x_vals))

    # --- Grouped bars on primary axis ---
    n = len(bar_cols)
    offsets = np.linspace(-(n - 1) / 2 * bar_width,
                          (n - 1) / 2 * bar_width, n)

    for i, col in enumerate(bar_cols):
        c = b_cols[i % len(b_cols)]
        vals = data[col].values.astype(float)
        bars = ax.bar(x_pos + offsets[i], vals, width=bar_width,
                      color=c, label=col)
        if bar_annotate:
            for b, val in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, b.get_height(),
                        bar_fmt.format(val), ha="center", va="bottom",
                        fontsize=8, fontweight="bold")

    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_vals)
    if ylabel_left:
        ax.set_ylabel(ylabel_left)

    # --- Line(s) on secondary axis ---
    ax2 = twinx(ax, ylabel=ylabel_right)

    # Ensure line renders on top of bars
    ax2.set_zorder(ax.get_zorder() + 1)
    ax.patch.set_visible(False)

    for i, col in enumerate(line_cols):
        c = l_cols[i % len(l_cols)]
        vals = data[col].values.astype(float)
        ax2.plot(x_pos, vals, color=c, linewidth=line_linewidth,
                 marker=line_marker, markersize=line_markersize, label=col)
        if line_annotate_last:
            last_val = vals[-1]
            lbl = f"{last_val:.1f}%" if line_pct else f"{last_val:.1f}"
            ax2.annotate(
                lbl, xy=(x_pos[-1], last_val),
                xytext=(x_pos[-1] + 0.3, last_val),
                fontsize=10, color=c, fontweight="bold",
                verticalalignment="center",
            )

    # --- Merged legend ---
    if legend:
        legend_merge(ax, ax2, ncol=legend_ncol)

    return ax2


def hline(ax, y=0, **kwargs):
    """Horizontal reference line (grey dashed by default)."""
    kwargs.setdefault("color", "gray")
    kwargs.setdefault("linestyle", "--")
    kwargs.setdefault("alpha", 0.5)
    ax.axhline(y=y, **kwargs)


def vline(ax, x, **kwargs):
    """Vertical reference line (red by default)."""
    kwargs.setdefault("color", "red")
    kwargs.setdefault("linestyle", "-")
    kwargs.setdefault("alpha", 0.5)
    kwargs.setdefault("linewidth", 1)
    ax.axvline(x=x, **kwargs)


# ---------------------------------------------------------------------------
# 5. ANNOTATION HELPERS
# ---------------------------------------------------------------------------


def _annotate_end(ax, xs, ys, color, pct=False):
    """Bold label at the last data point of a series."""
    last_x = xs.iloc[-1]
    last_y = ys.iloc[-1]
    label = f"{last_y:.1f}%" if pct else f"{last_y:.1f}"
    ax.annotate(
        label,
        xy=(last_x, last_y),
        xytext=(last_x + 0.3, last_y),
        fontsize=10,
        color=color,
        fontweight="bold",
        verticalalignment="center",
    )


def annotate_bars(ax, bars, values, fmt="{:.1f}", offset=(0, 5), **kwargs):
    """Add value labels on top of bar patches."""
    kwargs.setdefault("ha", "center")
    kwargs.setdefault("va", "bottom")
    kwargs.setdefault("fontsize", 9)
    kwargs.setdefault("fontweight", "bold")
    for b, val in zip(bars, values):
        ax.annotate(
            fmt.format(val),
            xy=(b.get_x() + b.get_width() / 2, b.get_height()),
            xytext=offset,
            textcoords="offset points",
            **kwargs,
        )


# ---------------------------------------------------------------------------
# 6. LEGEND HELPERS
# ---------------------------------------------------------------------------


def legend_top(ax, ncol=4, **kwargs):
    """Place legend centered above the plot area."""
    kwargs.setdefault("bbox_to_anchor", (0.5, 1.12))
    kwargs.setdefault("loc", "upper center")
    kwargs.setdefault("frameon", False)
    ax.legend(ncol=ncol, **kwargs)


def legend_right(ax, **kwargs):
    """Place legend to the right of the plot area."""
    kwargs.setdefault("bbox_to_anchor", (1, 1))
    kwargs.setdefault("loc", "upper left")
    kwargs.setdefault("frameon", False)
    ax.legend(**kwargs)


def legend_merge(*axes, ax=None, ncol=4, **kwargs):
    """Combine legend handles from multiple axes into a single legend.

    Parameters
    ----------
    *axes : Axes
        Two or more axes whose legend handles should be merged.
    ax : Axes or None
        The axes on which to place the merged legend.
        Defaults to the first axes passed.
    ncol : int
        Number of legend columns.
    """
    handles, labels = [], []
    for a in axes:
        h, l = a.get_legend_handles_labels()
        handles.extend(h)
        labels.extend(l)
        if a.get_legend() is not None:
            a.get_legend().remove()
    target = ax or axes[0]
    kwargs.setdefault("bbox_to_anchor", (0.5, 1.12))
    kwargs.setdefault("loc", "upper center")
    kwargs.setdefault("frameon", False)
    target.legend(handles, labels, ncol=ncol, **kwargs)


# ---------------------------------------------------------------------------
# 7. AXIS FORMATTING
# ---------------------------------------------------------------------------


def fmt_billion(ax, axis="y", decimals=1):
    """Format axis ticks as billions (÷ 1e9)."""
    formatter = mticker.FuncFormatter(
        lambda x, _: f"{x / 1e9:.{decimals}f}"
    )
    if axis in ("y", "both"):
        ax.yaxis.set_major_formatter(formatter)
    if axis in ("x", "both"):
        ax.xaxis.set_major_formatter(formatter)


def fmt_million(ax, axis="y", decimals=1):
    """Format axis ticks as millions (÷ 1e6)."""
    formatter = mticker.FuncFormatter(
        lambda x, _: f"{x / 1e6:.{decimals}f}"
    )
    if axis in ("y", "both"):
        ax.yaxis.set_major_formatter(formatter)
    if axis in ("x", "both"):
        ax.xaxis.set_major_formatter(formatter)


def fmt_pct(ax, axis="y", decimals=1):
    """Format axis ticks with a % suffix."""
    formatter = mticker.FuncFormatter(
        lambda x, _: f"{x:.{decimals}f}%"
    )
    if axis in ("y", "both"):
        ax.yaxis.set_major_formatter(formatter)
    if axis in ("x", "both"):
        ax.xaxis.set_major_formatter(formatter)


def fmt_indo(value, decimals=2):
    """Format a number Indonesian-style (dot for thousands, comma for decimal).

    Example: 1234567.89 → '1.234.567,89'
    """
    s = f"{value:,.{decimals}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------------------
# 8. LABEL HELPERS
# ---------------------------------------------------------------------------


def label(ax, *, title=None, xlabel="", ylabel="", subtitle=None):
    """Set common labels on an axes."""
    if title:
        ax.set_title(title, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if subtitle:
        ax.text(0.02, 0.98, subtitle, transform=ax.transAxes,
                fontsize=12, fontweight="bold", verticalalignment="top")


# ---------------------------------------------------------------------------
# 9. SAVE
# ---------------------------------------------------------------------------


def save(fig_or_path, path=None, dpi=300, **kwargs):
    """Save figure to disk.

    Accepts either:
        den.save(fig, "output.png")
        den.save("output.png")          # saves current figure
    """
    kwargs.setdefault("bbox_inches", "tight")
    if isinstance(fig_or_path, str):
        # Called as den.save("path.png")
        plt.savefig(fig_or_path, dpi=dpi, **kwargs)
    else:
        fig_or_path.savefig(path, dpi=dpi, **kwargs)
