"""
visualizer.py: Generate and save matplotlib chart images for the report.

Called internally by reporter.py — not a direct CLI subcommand.

Charts produced
---------------
1. Category distribution bar chart   (category_dist.png)
2. Daily collection trend line chart (daily_trend.png)

Both PNG files are saved to the output/charts/ directory (created if absent).

Functions:
    plot_category_distribution() — bar chart: article count per category
    plot_daily_trend()           — line chart: articles collected per day
    generate_charts()            — convenience wrapper that calls both charts
"""

import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # non-interactive backend; must be set before pyplot import
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

# Output directory for chart PNG files
CHARTS_DIR = Path("output") / "charts"

# Colour palette cycling through a curated set
_PALETTE = [
    "#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3",
    "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD",
]


# ---------------------------------------------------------------------------
# Chart 1 — Category distribution
# ---------------------------------------------------------------------------

# Horizontal bar chart of article count per category → output/charts/category_dist.png
def plot_category_distribution(category_counts, *, output_dir=CHARTS_DIR):
    """Save a horizontal bar chart of article counts per category.
        → output/charts/category_dist.png
    Args:
        category_counts: List of (category_str, count_int) tuples,
                         ordered by count descending (from get_report_stats()).
        output_dir:      Directory to save the PNG. Created if absent.

    Returns:
        Path to the saved PNG file, or None if no data.
    """
    if not category_counts:
        logger.warning("visualizer: No category data — skipping category chart.")
        return None

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "category_dist.png"

    categories = [row[0] for row in category_counts]
    counts     = [row[1] for row in category_counts]

    bar_colors = [_PALETTE[i % len(_PALETTE)] for i in range(len(categories))]

    fig, ax = plt.subplots(figsize=(10, max(4, len(categories) * 0.55)))
    bars = ax.barh(categories[::-1], counts[::-1], color=bar_colors[::-1], edgecolor="white")

    # Value labels on bars
    for bar, val in zip(bars, counts[::-1]):
        ax.text(
            bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
            str(val), va="center", ha="left", fontsize=9, color="#333333"
        )

    ax.set_xlabel("Article Count", fontsize=11)
    ax.set_title("News Distribution by Category", fontsize=14, fontweight="bold", pad=12)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlim(0, max(counts) * 1.15)
    ax.tick_params(axis="y", labelsize=10)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    logger.info(f"visualizer: category chart saved -> {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Chart 2 — Daily collection trend
# ---------------------------------------------------------------------------

def plot_daily_trend(daily_counts, *, output_dir=CHARTS_DIR):
    """Save a line chart showing article collection counts per day.
        → output/charts/daily_trend.png
    Args:
        daily_counts: List of (date_str, count_int) tuples ordered by date
                      ascending (from get_report_stats()).
        output_dir:   Directory to save the PNG. Created if absent.

    Returns:
        Path to the saved PNG file, or None if no data.
    """
    if not daily_counts:
        logger.warning("visualizer: No daily data — skipping daily trend chart.")
        return None

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "daily_trend.png"

    dates  = [row[0] for row in daily_counts]
    counts = [row[1] for row in daily_counts]

    fig, ax = plt.subplots(figsize=(max(8, len(dates) * 0.6), 5))

    ax.plot(dates, counts, marker="o", linewidth=2,
            color="#4C72B0", markerfacecolor="#DD8452",
            markeredgecolor="white", markersize=7)
    ax.fill_between(dates, counts, alpha=0.12, color="#4C72B0")

    # Annotate each point
    for x, y in zip(dates, counts):
        ax.annotate(
            str(y), (x, y),
            textcoords="offset points", xytext=(0, 8),
            ha="center", fontsize=8, color="#333333"
        )

    ax.set_xlabel("Date", fontsize=11)
    ax.set_ylabel("Article Count", fontsize=11)
    ax.set_title("Daily Collection Trend", fontsize=14, fontweight="bold", pad=12)
    ax.spines[["top", "right"]].set_visible(False)

    if len(dates) > 7:
        plt.xticks(rotation=45, ha="right", fontsize=9)
    else:
        plt.xticks(fontsize=10)

    ax.set_ylim(0, max(counts) * 1.25)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    logger.info(f"visualizer: daily trend chart saved -> {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Convenience wrapper
# ---------------------------------------------------------------------------

def generate_charts(stats, *, output_dir=CHARTS_DIR):
    """Generate both charts and return their file paths.

    Args:
        stats:      The dict returned by database.get_report_stats().
        output_dir: Directory to save PNG files.

    Returns:
        dict with keys 'category_chart' and 'daily_chart',
        each value being a Path (or None if chart could not be generated).
    """
    category_path = plot_category_distribution(
        stats["category_counts"], output_dir=output_dir
    )
    daily_path = plot_daily_trend(
        stats["daily_counts"], output_dir=output_dir
    )

    return {
        "category_chart": category_path,
        "daily_chart": daily_path,
    }
