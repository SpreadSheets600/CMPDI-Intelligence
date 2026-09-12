"""Chart rendering for reports. Deterministic matplotlib charts drawn from
the cleaned fact series, in one consistent visual style (coal/amber palette,
no chart junk), saved as PNGs ready for DOCX embedding."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402

COAL = "#d97706"
COAL_SOFT = "#f5b04c"
INK = "#1c1917"
MUTE = "#78716c"
GRID = "#e7e5e4"
SERIES = ["#d97706", "#292524", "#0f766e", "#57534e", "#a8a29e", "#0369a1"]

DPI = 150


def _style(ax, title: str, ylabel: str | None = None):
    ax.set_facecolor("white")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(GRID)
    ax.grid(axis="y", color=GRID, linewidth=0.8, alpha=0.9)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTE, labelsize=9)
    ax.set_title(title, fontsize=11.5, fontweight="bold", color=INK, loc="left", pad=12)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9.5, color=MUTE)


def _save(fig, path: Path) -> Path:
    fig.tight_layout()
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def chart_trend(table, path: Path, title: str, ylabel: str) -> Path:
    """Lines with markers: one series per entity across fiscal years."""
    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    for i, col in enumerate(table.columns):
        ax.plot(table.index, table[col], marker="o", markersize=4.5,
                linewidth=2.0, color=SERIES[i % len(SERIES)], label=str(col))
    _style(ax, title, ylabel)
    ax.legend(frameon=False, fontsize=9, loc="best")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    return _save(fig, path)


def chart_shares(latest_values: dict[str, float], path: Path, title: str) -> Path:
    """Horizontal bars with value + share labels, largest on top."""
    items = sorted(latest_values.items(), key=lambda kv: -kv[1])
    labels = [k for k, _ in items]
    values = [v for _, v in items]
    total = sum(values) or 1
    fig, ax = plt.subplots(figsize=(7.6, 0.62 * len(labels) + 1.6))
    y = range(len(labels))[::-1]
    bars = ax.barh(y, values, height=0.62, color=[COAL if i == 0 else COAL_SOFT for i in range(len(labels))])
    ax.set_yticks(list(y), labels)
    for bar, v in zip(bars, values):
        ax.text(bar.get_width() + total * 0.008, bar.get_y() + bar.get_height() / 2,
                f"{v:,.2f}  ({v / total * 100:.1f}%)", va="center", fontsize=9, color=INK)
    _style(ax, title)
    ax.grid(axis="x", color=GRID, linewidth=0.8, alpha=0.9)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, max(values) * 1.22)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    return _save(fig, path)


def chart_grouped(table, path: Path, title: str, ylabel: str,
                  labels: tuple[str, str] | None = None) -> Path:
    """Grouped bars by fiscal year for two metrics (e.g. production vs offtake)."""
    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    n = table.shape[1]
    width = 0.8 / max(n, 1)
    x = range(len(table.index))
    for i, col in enumerate(table.columns):
        offset = (i - (n - 1) / 2) * width
        ax.bar([xi + offset for xi in x], table[col], width=width,
               color=SERIES[i % len(SERIES)], label=str(labels[i] if labels and i < len(labels) else col))
    ax.set_xticks(list(x), table.index)
    _style(ax, title, ylabel)
    ax.legend(frameon=False, fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    return _save(fig, path)
