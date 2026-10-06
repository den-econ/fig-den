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

Charts are gridless. Every line gets a label at its last value in the
line's colour, and date x-axes get ticks anchored at the last observation;
see den.style(last_label=..., date_breaks=...) and den.finalize().
"""

import re

import matplotlib.artist as martist
import matplotlib.dates as mdates
import matplotlib.figure as mfigure
import matplotlib.pyplot as plt
import matplotlib.text as mtext
import matplotlib.ticker as mticker
import matplotlib.transforms as mtransforms
import seaborn as sns
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.font_manager import FontProperties

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
    "#4A6D7C",  # 7  slate blue   (extended)
    "#5B8A72",  # 8  muted teal   (extended)
    "#A8687A",  # 9  dusty rose   (extended)
    "#9F522C",  # 10 rust         (extended)
    "#F8E69B",  # 11 light gold   (extended)
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
SLATE_BLUE  = PALETTE[7]
MUTED_TEAL  = PALETTE[8]
DUSTY_ROSE  = PALETTE[9]
RUST        = PALETTE[10]
LIGHT_GOLD  = PALETTE[11]

# Sequential colormap (light gold → gold → dark brown)
CMAP_SEQ = LinearSegmentedColormap.from_list("den_seq", [LIGHT_GOLD, GOLD, DARK_BROWN])

# Diverging colormap (gold ← light gold → red)
CMAP_DIV = LinearSegmentedColormap.from_list("den_div", [GOLD, LIGHT_GOLD, RED])


def palette(n=None):
    """Return the first *n* DEN colours (default: all 12)."""
    if n is None:
        return list(PALETTE)
    return list(PALETTE[:n])


def color(i):
    """Return the *i*-th DEN palette colour (1-based, matching Stata den1–den12)."""
    if not 1 <= i <= len(PALETTE):
        raise ValueError(f"i must be between 1 and {len(PALETTE)}, got {i}")
    return PALETTE[i - 1]


def cmap(kind="sequential"):
    """Return a DEN colormap.  kind = 'sequential' | 'diverging'."""
    return CMAP_SEQ if kind == "sequential" else CMAP_DIV


# ---------------------------------------------------------------------------
# 2. GLOBAL STYLE
# ---------------------------------------------------------------------------

_STYLE_APPLIED = False

# Defaults for last-value labels and date ticks, set by style().
_AUTO = {"last_label": True, "date_breaks": True}


def style(font_scale=1.0, last_label=True, date_breaks=True):
    """Apply DEN house style globally.

    Call once at the top of your script / notebook.

    Parameters
    ----------
    font_scale : float
        Scale all fonts.
    last_label : bool, str, callable or dict
        Default for last-value labels on figures made with den.subplots,
        den.line* or saved with den.save. True labels the last value of each
        line; False turns labels off; a format string (``"{:,.0f}"``) or
        callable sets the number format; a dict passes label_last options.
    date_breaks : bool or str
        Default for date x-axes. True anchors ticks at the last observation
        with an automatic step; a string such as ``"1 year"`` fixes the
        step; False keeps matplotlib's date ticks.
    """
    global _STYLE_APPLIED
    _label_spec(last_label)                       # validate early
    _AUTO["last_label"] = last_label
    _AUTO["date_breaks"] = date_breaks

    sns.set_theme(
        style="ticks",
        font_scale=font_scale,
        rc={
            # Grid — none
            "axes.grid": False,
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


def subplots(nrows=1, ncols=1, figsize=None, *, last_label=None,
             date_breaks=None, **kwargs):
    """Create a figure + axes with sensible DEN defaults.

    Every axes gets last-value labels and last-anchored date ticks (see
    ``den.finalize`` for *last_label* and *date_breaks*).
    """
    _ensure_style()
    if figsize is None:
        w = 5.5 * ncols
        h = 4.5 * nrows
        figsize = (w, h)
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, **kwargs)
    finalize(axes, last_label=last_label, date_breaks=date_breaks)
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
    finalize(ax2)
    ax2.spines["right"].set_visible(True)
    if ylabel:
        ax2.set_ylabel(ylabel)
    return ax2


# ---------------------------------------------------------------------------
# 4. CHART FUNCTIONS
# ---------------------------------------------------------------------------


def line(ax, data, x, y, hue=None, *, marker="o", markersize=4,
         linewidth=2.5, colors=None, annotate_last=True, pct=False,
         date_breaks=None, legend=True, **kwargs):
    """Line chart on *ax*.

    Parameters
    ----------
    annotate_last : bool, str, callable or dict
        Label the last value of each line in its colour (default True).
        False turns labels off for this axes; a format string or callable
        sets the number format; a dict passes label_last options.
    pct : bool
        If True, append '%' to the default label.
    date_breaks : None, bool or str
        Last-anchored date ticks when x holds dates (see den.finalize).
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
    else:
        c = cols[0]
        ax.plot(data[x], data[y], color=c, linewidth=linewidth,
                marker=marker, markersize=markersize, **kwargs)

    _configure_labels(ax, annotate_last, pct=pct)
    finalize(ax, date_breaks=date_breaks)
    if legend and hue is not None:
        legend_top(ax)


def line_multi(ax, data, x, y_cols, *, colors=None, marker="o",
               markersize=4, linewidth=2.5, annotate_last=True,
               pct=False, date_breaks=None, legend=True, **kwargs):
    """Plot multiple y columns against a shared x column.

    Useful when data is in wide format (each series is a column).
    *annotate_last*, *pct* and *date_breaks* work as in ``den.line``.
    """
    _ensure_style()
    cols = colors or palette()
    for i, col in enumerate(y_cols):
        c = cols[i % len(cols)]
        ax.plot(data[x], data[col], color=c, linewidth=linewidth,
                label=col, marker=marker, markersize=markersize, **kwargs)
    _configure_labels(ax, annotate_last, pct=pct)
    finalize(ax, date_breaks=date_breaks)
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
                   line_annotate_last=True, line_pct=False,
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
    line_annotate_last : bool, str, callable or dict
        Label the last value of each line (default True); see ``den.line``.
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
    _configure_labels(ax2, line_annotate_last, pct=line_pct)

    # --- Merged legend ---
    if legend:
        legend_merge(ax, ax2, ncol=legend_ncol)

    return ax2


def hline(ax, y=0, **kwargs):
    """Horizontal reference line (grey dashed by default)."""
    kwargs.setdefault("color", "gray")
    kwargs.setdefault("linestyle", "--")
    kwargs.setdefault("alpha", 0.5)
    kwargs.setdefault("gid", "_den_skip")
    ax.axhline(y=y, **kwargs)


def vline(ax, x, **kwargs):
    """Vertical reference line (red by default)."""
    kwargs.setdefault("color", "red")
    kwargs.setdefault("linestyle", "-")
    kwargs.setdefault("alpha", 0.5)
    kwargs.setdefault("linewidth", 1)
    kwargs.setdefault("gid", "_den_skip")
    ax.axvline(x=x, **kwargs)


# ---------------------------------------------------------------------------
# 5. ANNOTATION HELPERS
# ---------------------------------------------------------------------------


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
# 6. LAST-VALUE LABELS AND DATE TICKS
# ---------------------------------------------------------------------------
#
# Both are attached to an axes as invisible helper artists and resolved at
# draw time, so they see every line on the axes (including ones added with
# plain ax.plot after the fd call) and the final axis limits.

DEFAULT_FMT = "{:,.1f}"


class _LastValueLabels(martist.Artist):
    """Label the last point (largest x) of every data line on an axes."""

    def __init__(self):
        super().__init__()
        self.set_zorder(3)
        self.set_clip_on(False)
        self.set_label("_den_last_labels")
        self.implicit = True
        self.configure({})

    def configure(self, opts):
        """Set options from a dict of label_last kwargs; None turns labels off."""
        self.set_visible(opts is not None)
        opts = opts or {}
        self.fmt = opts.get("fmt", DEFAULT_FMT)
        self.dodge = opts.get("dodge", True)
        self.color = opts.get("color")
        self.fontsize = opts.get("fontsize")
        self.fontweight = opts.get("fontweight", "bold")
        self.stale = True

    def _format(self, value):
        return self.fmt(value) if callable(self.fmt) else self.fmt.format(value)

    def _texts(self, renderer):
        ax = self.axes
        xmin, xmax = sorted(ax.get_xlim())
        points = []
        for ln in _data_lines(ax):
            xy = np.asarray(ln.get_xydata(), dtype=float)
            xy = xy[np.isfinite(xy).all(axis=1)]
            if len(xy) == 0:
                continue
            x, y = xy[np.argmax(xy[:, 0])]
            if not xmin <= x <= xmax:
                continue
            points.append((ln, y, ax.transData.transform((x, y))))
        if not points:
            return []

        size = self.fontsize or FontProperties(
            size=plt.rcParams["xtick.labelsize"]).get_size_in_points()
        ys = np.array([disp[1] for _, _, disp in points])
        if self.dodge:
            gap = renderer.points_to_pixels(size * 1.15)
            ys = _dodge_positions(ys, gap * (1 if self.dodge is True else float(self.dodge)))
        dx = renderer.points_to_pixels(4)

        texts = []
        for (ln, y, disp), y_pix in zip(points, ys):
            t = mtext.Text(disp[0] + dx, y_pix, self._format(y),
                           color=self.color or ln.get_color(), fontsize=size,
                           fontweight=self.fontweight, ha="left", va="center",
                           transform=mtransforms.IdentityTransform())
            t.set_figure(self.figure)
            texts.append(t)
        return texts

    @martist.allow_rasterization
    def draw(self, renderer):
        if self.get_visible():
            for t in self._texts(renderer):
                t.draw(renderer)
        self.stale = False

    def get_window_extent(self, renderer=None):
        if renderer is None:
            renderer = self.figure.canvas.get_renderer()
        boxes = [t.get_window_extent(renderer) for t in self._texts(renderer)]
        return mtransforms.Bbox.union(boxes) if boxes else mtransforms.Bbox.null()


class _DateTicksFromLast(martist.Artist):
    """Switch a date x-axis to DateFromLastLocator just before it is drawn."""

    def __init__(self):
        super().__init__()
        self.set_zorder(-1e9)   # drawn before the axis computes its ticks
        self.set_in_layout(False)
        self.set_label("_den_date_ticks")
        self.implicit = True
        self.by = None

    @martist.allow_rasterization
    def draw(self, renderer):
        if self.get_visible():
            date_ticks_from_last(self.axes, by=self.by)
        self.stale = False

    def get_window_extent(self, renderer=None):
        return mtransforms.Bbox.null()


def _data_lines(ax):
    """Lines drawn in data coordinates with a visible line, i.e. not
    axhline/axvline, reference lines from den.hline/vline, or marker-only."""
    return [
        ln for ln in ax.get_lines()
        if ln.get_visible()
        and ln.get_gid() != "_den_skip"
        and ln.get_transform() == ax.transData
        and ln.get_linestyle() not in ("None", "none", "", " ")
    ]


def _dodge_positions(y, gap):
    """Spread values so neighbours are at least *gap* apart. Overlapping
    labels are merged into clusters centred on the mean of their positions."""
    order = np.argsort(y)
    ys = np.asarray(y, dtype=float)[order]
    clusters = [[i] for i in range(len(ys))]

    def place(members):
        k = len(members)
        return ys[members].mean() + (np.arange(k) - (k - 1) / 2) * gap

    while True:
        pos = [place(c) for c in clusters]
        hit = next((i for i in range(len(clusters) - 1)
                    if pos[i][-1] + gap > pos[i + 1][0] + 1e-9), None)
        if hit is None:
            break
        clusters[hit] = clusters[hit] + clusters.pop(hit + 1)
    out = np.empty(len(ys))
    out[order] = np.concatenate([place(c) for c in clusters])
    return out


def _label_spec(spec, pct=False):
    """Normalise a last-label spec to label_last kwargs, or None for off."""
    if spec is None or spec is False:
        return None
    if spec is True:
        return {"fmt": DEFAULT_FMT + "%" if pct else DEFAULT_FMT}
    if isinstance(spec, str) or callable(spec):
        return {"fmt": spec}
    if isinstance(spec, dict):
        return dict(spec)
    raise TypeError("last_label must be True, False, a format string, "
                    "a callable, or a dict of label_last() options.")


def _configure_labels(ax, spec, *, pct=False, implicit=False):
    """Attach or update the last-value labels of *ax*.

    An implicit request (den defaults) never overrides an existing setting.
    A plain ``True`` keeps an explicit custom setting made earlier.
    """
    art = getattr(ax, "_den_labels", None)
    if art is not None and (implicit or (spec is True and not pct and not art.implicit)):
        return art
    if art is None:
        art = _LastValueLabels()
        ax.add_artist(art)
        ax._den_labels = art
    art.configure(_label_spec(spec, pct))
    art.implicit = implicit or (spec is True and not pct)
    return art


def _configure_dates(ax, spec, *, implicit=False):
    """Attach or update automatic last-observation date ticks on *ax*."""
    art = getattr(ax, "_den_dates", None)
    if art is not None and implicit:
        return art
    if art is None:
        art = _DateTicksFromLast()
        ax.add_artist(art)
        ax._den_dates = art
    if not (spec is True or spec is False or isinstance(spec, str)):
        raise TypeError('date_breaks must be True, False, or a step such as "1 year".')
    art.set_visible(spec is not False)
    art.by = spec if isinstance(spec, str) else None
    art.implicit = implicit
    return art


def label_last(ax, fmt=DEFAULT_FMT, *, dodge=True, color=None, fontsize=None,
               fontweight="bold"):
    """Label the last value of every line on *ax*, in the line's colour.

    Labels are placed when the figure is drawn, so lines added afterwards
    are labelled too and labels can be kept apart.

    Parameters
    ----------
    fmt : str or callable
        Format string (``"{:,.1f}"``) or function turning the value into text.
    dodge : bool or float
        Push overlapping labels apart vertically. A number scales the
        minimum gap (1 = one line of text). False disables it.
    color : str or None
        Fixed colour for all labels. None uses each line's colour.
    fontsize : float or None
        Text size in points. None matches the tick labels.
    fontweight : str
        Font weight (default ``"bold"``).
    """
    opts = dict(fmt=fmt, dodge=dodge, color=color, fontsize=fontsize,
                fontweight=fontweight)
    return _configure_labels(ax, opts)


class DateFromLastLocator(mticker.Locator):
    """Date ticks whose last tick is the last observation.

    The remaining ticks step backward from it at a regular interval.

    Parameters
    ----------
    last : datetime-like or None
        Anchor date. None uses the largest x of the lines on the axes.
    by : str or None
        Step, e.g. ``"1 year"``, ``"6 months"``, ``"3M"``, ``"2 weeks"``.
        None picks a step giving at most *n* ticks.
    n : int
        Maximum number of ticks when *by* is None.
    """

    def __init__(self, last=None, by=None, n=6):
        self.last = last
        self.by = by
        self.n = n

    def __call__(self):
        vmin, vmax = self.axis.get_view_interval()
        return self.tick_values(vmin, vmax)

    def _last_num(self, vmax):
        if self.last is not None:
            return mdates.date2num(pd.Timestamp(self.last))
        ax = self.axis.axes
        xs = [np.nanmax(np.asarray(ln.get_xydata(), dtype=float)[:, 0])
              for ln in _data_lines(ax) if len(ln.get_xdata())]
        xs = [x for x in xs if np.isfinite(x)]
        return max(xs) if xs else self.axis.get_data_interval()[1]

    def tick_values(self, vmin, vmax):
        vmin, vmax = sorted((vmin, vmax))
        last_num = min(self._last_num(vmax), vmax)
        if not np.isfinite(last_num) or last_num <= vmin:
            return np.array([last_num])
        first = _num2ts(vmin)
        last = _num2ts(last_num)
        k, unit = _parse_step(self.by) if self.by else _auto_step(first, last, self.n)
        month_end = unit in ("years", "months") and last.is_month_end
        ticks = []
        for i in range(1000):
            t = last - pd.DateOffset(**{unit: k * i})
            if month_end:
                t = t + pd.offsets.MonthEnd(0)
            if t < first:
                break
            ticks.append(t)
        return mdates.date2num(sorted(ticks))


class DateFromLastFormatter(mticker.Formatter):
    """Tick labels matched to the tick spacing: %Y, %b %Y, %d %b %Y."""

    fmt = "%b %Y"

    def format_ticks(self, values):
        dates = [_num2ts(v) for v in values]
        spacing = np.median(np.diff(values)) if len(values) > 1 else 365
        if spacing >= 360 and all(d.month == 1 and d.day == 1 for d in dates):
            self.fmt = "%Y"
        elif spacing >= 28:
            self.fmt = "%b %Y"
        elif spacing >= 1:
            self.fmt = "%d %b %Y"
        else:
            self.fmt = "%d %b %H:%M"
        return [d.strftime(self.fmt) for d in dates]

    def __call__(self, x, pos=None):
        return _num2ts(x).strftime(self.fmt)


def _num2ts(x):
    return pd.Timestamp(mdates.num2date(x)).tz_localize(None)


# Steps tried in order; the first giving fewer than n intervals is used.
_STEPS = [
    (1, "seconds", 1 / 86400), (15, "seconds", 15 / 86400), (1, "minutes", 1 / 1440),
    (15, "minutes", 15 / 1440), (1, "hours", 1 / 24), (3, "hours", 3 / 24),
    (6, "hours", 6 / 24), (12, "hours", 12 / 24), (1, "days", 1), (2, "days", 2),
    (1, "weeks", 7), (2, "weeks", 14), (1, "months", 30.44), (2, "months", 60.88),
    (3, "months", 91.31), (6, "months", 182.62), (1, "years", 365.25),
    (2, "years", 730.5), (5, "years", 1826.25), (10, "years", 3652.5),
    (20, "years", 7305), (25, "years", 9131.25), (50, "years", 18262.5),
    (100, "years", 36525),
]

_UNITS = {
    "years": ("y", "yr", "yrs", "year", "years", "a", "ye"),
    "quarters": ("q", "qtr", "quarter", "quarters", "qe"),
    "months": ("m", "mo", "mon", "month", "months", "me"),
    "weeks": ("w", "wk", "week", "weeks"),
    "days": ("d", "day", "days"),
    "hours": ("h", "hr", "hour", "hours"),
    "minutes": ("min", "mins", "minute", "minutes", "t"),
    "seconds": ("s", "sec", "secs", "second", "seconds"),
}


def _parse_step(by):
    """'6 months' / '6M' / '1 year' / '2Q' -> (k, DateOffset unit)."""
    m = re.fullmatch(r"\s*(\d*)\s*([A-Za-z]+)\s*", str(by))
    if m:
        k = int(m.group(1) or 1)
        word = m.group(2).lower()
        for unit, names in _UNITS.items():
            if word in names:
                return (3 * k, "months") if unit == "quarters" else (k, unit)
    raise ValueError(f"Unrecognised date step {by!r}; use e.g. '1 year', '6 months', '3M'.")


def _auto_step(first, last, n):
    span = (last - first) / pd.Timedelta(days=1)
    for k, unit, days in _STEPS:
        if span / days < n:
            return k, unit
    return _STEPS[-1][:2]


def _is_date_axis(axis):
    conv = axis.get_converter() if hasattr(axis, "get_converter") else axis.converter
    if conv is None or type(conv).__name__ == "PeriodConverter":
        return False
    date_types = tuple(c for c in (mdates.DateConverter, mdates.ConciseDateConverter,
                                   getattr(mdates, "_SwitchableDateConverter", None))
                       if c is not None)
    return isinstance(conv, date_types)


def date_ticks_from_last(ax, by=None, last=None):
    """Anchor the x ticks of a date axis at the last observation.

    Does nothing (and returns False) unless the x axis holds dates and still
    uses matplotlib's automatic date ticks. Numeric years, categories,
    pandas period plots and axes with your own locator are left unchanged.

    Parameters
    ----------
    by : str or None
        Step such as ``"1 year"``, ``"6 months"``, ``"3M"``. None = automatic.
    last : datetime-like or None
        Anchor date. None uses the largest x of the lines on the axes.
    """
    axis = ax.xaxis
    current = axis.get_major_locator()
    if isinstance(current, DateFromLastLocator):
        current.by, current.last = by, last
        return True
    if not _is_date_axis(axis) or not isinstance(current, mdates.AutoDateLocator):
        return False
    axis.set_major_locator(DateFromLastLocator(last=last, by=by))
    axis.set_major_formatter(DateFromLastFormatter())
    axis.set_minor_locator(mticker.NullLocator())
    return True


def finalize(fig_or_ax=None, last_label=None, date_breaks=None):
    """Apply DEN last-value labels and date ticks to a figure or axes.

    ``den.subplots``, ``den.line`` and ``den.save`` already do this; call
    it for figures made with plain matplotlib/pandas and saved elsewhere.

    Parameters
    ----------
    fig_or_ax : Figure, Axes, array of Axes, or None (current figure)
    last_label : None, bool, str, callable or dict
        None keeps any existing setting and otherwise uses the default from
        ``den.style()``. True/False turn labels on/off; a format string or
        callable sets the number format; a dict passes label_last options.
    date_breaks : None, bool or str
        None keeps any existing setting and otherwise uses the default.
        True/False turn last-anchored date ticks on/off; a string such as
        ``"1 year"`` fixes the step.
    """
    if fig_or_ax is None:
        fig_or_ax = plt.gcf()
    if isinstance(fig_or_ax, mfigure.FigureBase):
        axes = fig_or_ax.axes
    else:
        axes = np.atleast_1d(fig_or_ax).ravel()
    for ax in axes:
        if last_label is None:
            _configure_labels(ax, _AUTO["last_label"], implicit=True)
        else:
            _configure_labels(ax, last_label)
        if date_breaks is None:
            _configure_dates(ax, _AUTO["date_breaks"], implicit=True)
        else:
            _configure_dates(ax, date_breaks)
    return fig_or_ax


# ---------------------------------------------------------------------------
# 7. LEGEND HELPERS
# ---------------------------------------------------------------------------


class _TitleAboveLegend(martist.Artist):
    """Lift the axes title above a legend placed on top of the axes.

    The legend's height is only known once it is laid out, so the title
    offset is set at draw time, before the title itself is drawn.
    """

    def __init__(self):
        super().__init__()
        self.set_zorder(-1e9)
        self.set_in_layout(False)

    @martist.allow_rasterization
    def draw(self, renderer):
        ax = self.axes
        leg = ax.get_legend()
        if leg is not None and leg.get_visible():
            gap = renderer.points_to_pixels(plt.rcParams["axes.titlepad"])
            lift = max(leg.get_window_extent(renderer).y1 - ax.bbox.y1, 0) + gap
            ax._set_title_offset_trans(lift * 72 / self.figure.dpi)
        self.stale = False

    def get_window_extent(self, renderer=None):
        return mtransforms.Bbox.null()


def _place_legend_on_top(ax, ncol, kwargs, handles=None, labels=None):
    kwargs.setdefault("bbox_to_anchor", (0.5, 1.02))
    kwargs.setdefault("loc", "lower center")
    kwargs.setdefault("frameon", False)
    if handles is None:
        ax.legend(ncol=ncol, **kwargs)
    else:
        ax.legend(handles, labels, ncol=ncol, **kwargs)
    if getattr(ax, "_den_title_lift", None) is None:
        ax._den_title_lift = _TitleAboveLegend()
        ax.add_artist(ax._den_title_lift)


def legend_top(ax, ncol=4, **kwargs):
    """Place legend centered above the plot area, below the title."""
    _place_legend_on_top(ax, ncol, kwargs)


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
    _place_legend_on_top(target, ncol, kwargs, handles, labels)


# ---------------------------------------------------------------------------
# 8. AXIS FORMATTING
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
# 9. LABEL HELPERS
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
# 10. SAVE
# ---------------------------------------------------------------------------


def save(fig_or_path, path=None, dpi=300, *, auto=True, **kwargs):
    """Save figure to disk.

    Accepts either:
        den.save(fig, "output.png")
        den.save("output.png")          # saves current figure

    With *auto* (default), axes that have no DEN label/date-tick setting yet
    get the defaults from ``den.style()`` (see ``den.finalize``).
    """
    kwargs.setdefault("bbox_inches", "tight")
    if isinstance(fig_or_path, str):
        # Called as den.save("path.png")
        fig, path = plt.gcf(), fig_or_path
    else:
        fig = fig_or_path
    if auto:
        finalize(fig)
    fig.savefig(path, dpi=dpi, **kwargs)
