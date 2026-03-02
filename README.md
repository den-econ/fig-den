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

## API reference

### Style & figure

| Function | Description |
|---|---|
| `den.style(font_scale=1.0)` | Apply DEN house style globally. Call once at the top of your script or notebook. |
| `den.subplots(nrows, ncols, figsize)` | Create a figure + axes with DEN defaults. |

### Charts

| Function | Description |
|---|---|
| `den.line(ax, data, x, y, hue)` | Line chart. Supports `annotate_last` and `pct` options. |
| `den.line_multi(ax, data, x, y_cols)` | Multi-line chart from wide-format data (each series is a column). |
| `den.bar(ax, data, x, y)` | Simple bar chart with optional value annotations. |
| `den.stacked_bar(ax, data, x, y_cols)` | Stacked bar chart with optional percentage labels. |
| `den.grouped_bar(ax, data, x, y_cols)` | Side-by-side grouped bar chart. |

### Annotations & helpers

| Function | Description |
|---|---|
| `den.hline(ax, y=0)` | Horizontal reference line (grey dashed). |
| `den.vline(ax, x)` | Vertical reference line (red). |
| `den.annotate_bars(ax, bars, values)` | Add value labels on top of bar patches. |
| `den.label(ax, title, xlabel, ylabel, subtitle)` | Set common labels on an axes. |
| `den.legend_top(ax)` | Place legend centered above the plot. |
| `den.legend_right(ax)` | Place legend to the right of the plot. |

### Axis formatting

| Function | Description |
|---|---|
| `den.fmt_billion(ax)` | Format ticks as billions (÷ 1e9). |
| `den.fmt_million(ax)` | Format ticks as millions (÷ 1e6). |
| `den.fmt_pct(ax)` | Append `%` to tick labels. |
| `den.fmt_indo(value)` | Indonesian number format (e.g. `1.234.567,89`). |

### Colours

```python
den.PALETTE          # full 9-colour list
den.PALETTE_2        # gold + brown
den.PALETTE_4        # gold, brown, red, tan
den.GOLD, den.BROWN, den.RED, den.TAN, den.GREY  # individual colours
den.palette(n)       # first n colours
den.cmap("sequential")   # gold → brown → red
den.cmap("diverging")    # gold ← tan → red
```

## License

DEN License — see [LICENSE](LICENSE) for details.
