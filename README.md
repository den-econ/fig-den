# fig-den

**DEN (Dewan Ekonomi Nasional) house-style charting package for Python.**

A lightweight matplotlib/seaborn wrapper that applies DEN's official colour palette and chart style so every figure looks consistent and publication-ready.

## Installation

```bash
pip install git+https://github.com/den-econ/fig-den.git
```

### Dependencies

`matplotlib >= 3.5` · `seaborn >= 0.12` · `numpy >= 1.21` · `pandas >= 1.4`

All dependencies are installed automatically.

## Quick start

```python
import fig_den as den
import pandas as pd

# 1. Apply the DEN style (call once)
den.style()

# 2. Create a figure
fig, ax = den.subplots()

# 3. Plot
df = pd.DataFrame({
    "year": [2020, 2021, 2022, 2023, 2024],
    "growth": [2.1, 3.7, 5.3, 5.0, 5.2],
})
den.bar(ax, df, x="year", y="growth")
den.label(ax, title="GDP Growth", ylabel="%")

# 4. Save
den.save(fig, "growth.png")   # 300 dpi, tight bbox
```

## Default behaviour (v1.1)

After `den.style()`, charts made with fig-den:

1. **have no grid lines**, only the left and bottom axis lines;
2. **label the last value of each line** (largest x) in bold, in the line's
   colour. Labels that would overlap are pushed apart vertically, including
   labels of lines added with plain `ax.plot`;
3. **anchor date ticks at the last observation**: when x holds dates, the
   last tick is the last observation and the other ticks step backward
   from it (`Aug 2018, Aug 2020, …, Aug 2026`).

```python
import fig_den as den
import numpy as np
import pandas as pd

den.style()

dates = pd.date_range("2018-08-01", "2026-08-01", freq="MS")
df = pd.DataFrame({
    "date":   np.tile(dates, 2),
    "series": np.repeat(["Inflasi", "BI Rate"], len(dates)),
    "value":  np.concatenate([np.linspace(3, 2.5, len(dates)),
                              np.linspace(5, 4.75, len(dates))]),
})

fig, ax = den.subplots(figsize=(9, 5))
den.line(ax, df, x="date", y="value", hue="series", marker=None)
den.label(ax, title="Inflasi dan BI Rate", ylabel="%")
den.save(fig, "macro.png")
```

**Where the defaults apply.** Labels and date ticks are added by `den.subplots`, `den.twinx`, `den.line`, `den.line_multi`, `den.combo_bar_line` and `den.save`. For a figure made entirely with plain matplotlib or pandas and saved with `fig.savefig`, call `den.finalize(fig)` once. They are worked out when the figure is drawn, so lines added after the `den` call are included.

**Date ticks are only applied to date axes.** They need x values that matplotlib treats as dates (`datetime64`, `Timestamp`, `datetime`), with matplotlib's automatic date ticks still in place. Ticks are left unchanged for:
- numeric years (`year = 2015…2024`);
- categories (bar charts);
- pandas `df.plot()` with a `DatetimeIndex`, which uses pandas' own period ticks;
- any axis where you set your own locator.

For anchored ticks on a numeric year column, convert it first: `pd.to_datetime(df["year"], format="%Y")`.

### Last-value labels (`annotate_last` / `last_label`)

```python
# On (default): one decimal with thousands separator, bold, line colour
den.line(ax, df, x="date", y="value", hue="series")

# Append % to the default format
den.line(ax, df, x="date", y="value", hue="series", pct=True)          # "5.1%"

# Off for this chart
den.line(ax, df, x="date", y="value", hue="series", annotate_last=False)

# Number format: a format string or any callable
den.line(ax, df, x="date", y="value", hue="series", annotate_last="{:,.0f}")
den.line(ax, df, x="date", y="value", hue="series",
         annotate_last=lambda v: den.fmt_indo(v, 1))                   # "1.234,5"

# Full control (same options as den.label_last)
den.label_last(ax, fmt="{:.2f} pp", fontsize=11, fontweight="normal",
               color="grey", dodge=1.5)

# Plain matplotlib
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot(dates, np.linspace(3, 2.5, len(dates)))
den.finalize(fig)                         # or den.finalize(ax, last_label="{:.2f}")
```

`den.label_last(ax, ...)` options:

| Option | Default | Meaning |
|---|---|---|
| `fmt` | `"{:,.1f}"` | Format string or function turning the value into text |
| `dodge` | `True` | Push overlapping labels apart; a number scales the minimum gap (1 = one text line); `False` disables |
| `color` | `None` (line colour) | One fixed colour for all labels |
| `fontsize` | `None` (tick-label size) | Text size in points |
| `fontweight` | `"bold"` | Font weight |

Lines from `den.hline` / `den.vline`, `ax.axhline` / `ax.axvline` and marker-only plots are never labelled.

### Date ticks (`date_breaks`)

```python
den.line(ax, df, x="date", y="value", hue="series")                        # automatic step
den.line(ax, df, x="date", y="value", hue="series", date_breaks="1 year")  # Aug 2018, Aug 2019, …
den.line(ax, df, x="date", y="value", hue="series", date_breaks="6M")      # …, Feb 2026, Aug 2026
den.line(ax, df, x="date", y="value", hue="series", date_breaks=False)     # matplotlib default

# By hand, with your own anchor
ax.xaxis.set_major_locator(den.DateFromLastLocator(last="2026-08-01", by="2 years"))
ax.xaxis.set_major_formatter(den.DateFromLastFormatter())
```

Steps accept `"1 year"`, `"6 months"`, `"2 quarters"`, `"2 weeks"`, `"10 days"`, `"6 hours"` or the short forms `"1Y"`, `"6M"`, `"2Q"`, `"2W"`, `"10D"`, `"6H"`. Tick labels follow the step:
- `%Y` for yearly ticks on 1 January;
- `%b %Y` for monthly to yearly ticks;
- `%d %b %Y` for daily or weekly ticks.

Month-end data stays on month ends (31 Aug → 28 Feb → 31 Aug).

### Turning the defaults off

```python
den.style(last_label=False, date_breaks=False)        # for the whole session
fig, ax = den.subplots(last_label=False)              # for one figure
den.finalize(ax, last_label=False, date_breaks=False) # for one axes
den.save(fig, "out.png", auto=False)                  # don't apply defaults on save
```

## Line charts

### Long format (with `hue`)

When your data has one row per observation and a column that identifies each series, use `den.line` with `hue`:

```python
df_long = pd.DataFrame({
    "year":    [2020, 2021, 2022, 2023, 2024] * 2,
    "growth":  [2.1, 3.7, 5.3, 5.0, 5.2, 3.0, 4.1, 4.8, 4.5, 4.7],
    "country": ["Indonesia"] * 5 + ["Malaysia"] * 5,
})

fig, ax = den.subplots()
den.line(ax, df_long, x="year", y="growth", hue="country")
den.label(ax, title="GDP Growth Comparison", ylabel="%")
```

The `hue` column splits the data into one line per group, each assigned a colour from the DEN palette automatically. Use `colors=[den.GOLD, den.RED]` to override.

### Wide format (with `line_multi`)

When each series is its own column, use `den.line_multi`:

```python
df_wide = pd.DataFrame({
    "year":      [2020, 2021, 2022, 2023, 2024],
    "Indonesia": [2.1, 3.7, 5.3, 5.0, 5.2],
    "Malaysia":  [3.0, 4.1, 4.8, 4.5, 4.7],
})

fig, ax = den.subplots()
den.line_multi(ax, df_wide, x="year",
               y_cols=["Indonesia", "Malaysia"])
den.label(ax, title="GDP Growth Comparison", ylabel="%")
```

Column names become the legend labels. Both functions label the last value of each line by default (`annotate_last=False` turns this off) and accept `pct=True` to append `%` to those labels; see [Last-value labels](#last-value-labels-annotate_last--last_label).

## API reference

### Style & figure

| Function | Description |
|---|---|
| `den.style(font_scale=1.0, last_label=True, date_breaks=True)` | Apply DEN house style globally and set the label/date-tick defaults. Call once at the top of your script or notebook. |
| `den.subplots(nrows, ncols, figsize)` | Create a figure + axes with DEN defaults. |

### Charts

| Function | Description |
|---|---|
| `den.line(ax, data, x, y, hue)` | Line chart. Supports `annotate_last`, `pct` and `date_breaks` options. |
| `den.line_multi(ax, data, x, y_cols)` | Multi-line chart from wide-format data (each series is a column). |
| `den.bar(ax, data, x, y)` | Simple bar chart with optional value annotations. |
| `den.stacked_bar(ax, data, x, y_cols)` | Stacked bar chart with optional percentage labels. |
| `den.grouped_bar(ax, data, x, y_cols)` | Side-by-side grouped bar chart. Returns `x_pos` for alignment with secondary axes. |
| `den.combo_bar_line(ax, data, x, bar_cols, line_cols)` | Grouped bars + line(s) on secondary y-axis. Returns `ax2` for further formatting. |

### Annotations & helpers

| Function | Description |
|---|---|
| `den.hline(ax, y=0)` | Horizontal reference line (grey dashed). |
| `den.vline(ax, x)` | Vertical reference line (red). |
| `den.annotate_bars(ax, bars, values)` | Add value labels on top of bar patches. |
| `den.label(ax, title, xlabel, ylabel, subtitle)` | Set common labels on an axes. |
| `den.legend_top(ax)` | Place legend centered above the plot. |
| `den.legend_right(ax)` | Place legend to the right of the plot. |
| `den.legend_merge(*axes)` | Combine legend handles from multiple axes into one. |
| `den.twinx(ax)` | Create a DEN-styled secondary y-axis (right side). |
| `den.label_last(ax, fmt)` | Label the last value of every line on an axes, in the line's colour. |
| `den.finalize(fig_or_ax, last_label, date_breaks)` | Apply last-value labels and date ticks to a plain matplotlib/pandas figure, or change them. |
| `den.date_ticks_from_last(ax, by)` | Anchor the ticks of a date x-axis at the last observation (no-op for non-date axes). |
| `den.DateFromLastLocator` / `den.DateFromLastFormatter` | The locator and formatter behind it, for manual use. |

### Axis formatting

| Function | Description |
|---|---|
| `den.fmt_billion(ax)` | Format ticks as billions (÷ 1e9). |
| `den.fmt_million(ax)` | Format ticks as millions (÷ 1e6). |
| `den.fmt_pct(ax)` | Append `%` to tick labels. |
| `den.fmt_indo(value)` | Indonesian number format (e.g. `1.234.567,89`). |

## Dual-axis combo charts

Use `combo_bar_line` when you need grouped bars on the left axis and line(s) on the right axis — a common layout for comparing levels (e.g. production) against a rate (e.g. utilisation).

### Quick way — `combo_bar_line`

```python
import fig_den as den
import pandas as pd

den.style()

df = pd.DataFrame({
    "Tahun": [2018, 2019, 2020, 2021, 2022, 2023, 2024],
    "Kapasitas":  [110, 112, 117, 117, 117, 120, 119.3],
    "Produksi":   [72,  73,  60,  63,  63,  67,  67.8],
    "Konsumsi":   [69,  69,  60,  63,  63,  67,  56.5],
    "Utilisasi":  [65,  65,  51,  54,  54,  56,  56.5],
})

fig, ax = den.subplots(figsize=(12, 6))

ax2 = den.combo_bar_line(
    ax, df, "Tahun",
    bar_cols=["Kapasitas", "Produksi", "Konsumsi"],
    line_cols=["Utilisasi"],
    line_colors=[den.GREY],
    ylabel_left="Juta Ton",
    bar_annotate=False,
    line_annotate_last=True,
    line_pct=True,
)

# Format and adjust the secondary axis
den.fmt_pct(ax2)
ax2.set_ylim(40, 80)

den.label(ax, title="Ikhtisar Kinerja Industri Semen Indonesia")
den.save(fig, "semen.png")
```

The function handles x-position alignment, z-ordering (line on top of bars), and legend merging automatically. It returns `ax2` (the right-side axes) so you can set limits, format ticks, or add further annotations.

**Key parameters:**

| Parameter | Default | Description |
|---|---|---|
| `bar_colors` / `line_colors` | DEN palette | Override colours for each series group. |
| `bar_width` | `0.35` | Width of each bar. |
| `bar_annotate` / `bar_fmt` | `True` / `"{:.1f}"` | Show values on top of bars. |
| `line_annotate_last` / `line_pct` | `True` / `False` | Bold label at the last point; append `%`. |
| `ylabel_left` / `ylabel_right` | `""` | Axis labels. |
| `legend` / `legend_ncol` | `True` / `4` | Show merged legend above the chart. |

### Composable way — `twinx` + `legend_merge`

For layouts that don't fit the standard combo pattern, use the building blocks directly:

```python
fig, ax = den.subplots()

# Bars on the primary axis
x_pos = den.grouped_bar(ax, df, "Tahun",
                        ["Kapasitas", "Produksi", "Konsumsi"],
                        legend=False)

# Line on the secondary axis, aligned to the same x positions
ax2 = den.twinx(ax, ylabel="Utilisasi (%)")
ax2.plot(x_pos, df["Utilisasi"], color=den.GREY,
         marker="o", label="Utilisasi")

# Merge legends from both axes
den.legend_merge(ax, ax2)

den.fmt_pct(ax2)
```

`grouped_bar` returns `x_pos` (an integer array `[0, 1, 2, …]`) so the line aligns with the bar positions. `twinx` creates a secondary axis with the right spine visible and grid disabled (to avoid double-gridlines). `legend_merge` collects handles from all axes into a single legend above the chart.

### Colours

Pick colours by position (1-based, matching Stata `den1`–`den12`) or by name:

```python
den.color(1)         # "#EEC051" (gold)
den.color(3)         # "#C00000" (red)

den.GOLD             # "#EEC051"  — by name
den.DARK_BROWN       # "#845B24"
den.RED              # "#C00000"
```

Use in any matplotlib/seaborn call:

```python
ax.scatter(x, y, color=den.color(1))             # gold markers
ax.plot(x, y, color=den.color(3))                 # red line

# Two groups with specific colours
ax.scatter(x1, y1, color=den.color(1), label="A")
ax.scatter(x2, y2, color=den.color(3), label="B")
```

Full palette access:

```python
den.PALETTE          # full 12-colour list
den.PALETTE_2        # gold + dark brown
den.PALETTE_4        # gold, dark brown, red, bright gold
den.palette(n)       # first n colours
den.cmap("sequential")   # light gold → gold → dark brown
den.cmap("diverging")    # gold ← light gold → red
```

All named constants:

| Position | Constant | Hex |
|----------|----------|-----|
| 1 | `den.GOLD` | `#EEC051` |
| 2 | `den.DARK_BROWN` | `#845B24` |
| 3 | `den.RED` | `#C00000` |
| 4 | `den.BRIGHT_GOLD` | `#FFC000` |
| 5 | `den.TAN` | `#A19574` |
| 6 | `den.GREY` | `#3A3A3A` |
| 7 | `den.DEEP_AMBER` | `#935200` |
| 8 | `den.SLATE_BLUE` | `#4A6D7C` |
| 9 | `den.MUTED_TEAL` | `#5B8A72` |
| 10 | `den.DUSTY_ROSE` | `#A8687A` |
| 11 | `den.RUST` | `#9F522C` |
| 12 | `den.LIGHT_GOLD` | `#F8E69B` |

## License

DEN License — see [LICENSE](LICENSE) for details.
