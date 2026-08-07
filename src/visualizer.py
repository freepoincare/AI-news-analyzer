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

def generate_charts(stats, *, category=None, output_dir=CHARTS_DIR):
    """Generate charts and return their file paths.

    Args:
        stats:      The dict returned by database.get_report_stats() & get_sentiment_stats().
        category:   Category filter specified in report subcommand (or None).
        output_dir: Directory to save PNG files.

    Returns:
        dict with keys 'category_chart', 'daily_chart', 'sentiment_over_time_chart',
        and 'sentiment_by_category_chart', each value being a Path (or None if not generated).
    """
    category_path = plot_category_distribution(
        stats["category_counts"], output_dir=output_dir
    )
    daily_path = plot_daily_trend(
        stats["daily_counts"], output_dir=output_dir
    )

    sentiment_time_path = None
    sentiment_cat_path = None

    if "sentiment_over_time" in stats:
        sentiment_time_path = plot_sentiment_over_time(
            stats["sentiment_over_time"], output_dir=output_dir
        )

    # Condition: If --category is specified, generate only "Sentiment over time" chart.
    # If no category is specified, generate both sentiment charts.
    if not category and "sentiment_by_category" in stats:
        sentiment_cat_path = plot_sentiment_by_category(
            stats["sentiment_by_category"], output_dir=output_dir
        )

    return {
        "category_chart": category_path,
        "daily_chart": daily_path,
        "sentiment_over_time_chart": sentiment_time_path,
        "sentiment_by_category_chart": sentiment_cat_path,
    }


# ---------------------------------------------------------------------------
# Chart 3 — Sentiment over time
# ---------------------------------------------------------------------------

_SENTIMENT_COLORS = {
    "positive": "#55A868",  # Green
    "neutral":  "#4C72B0",  # Blue
    "negative": "#C44E52",  # Red
    "none":     "#8C8C8C",  # Grey
}

def plot_sentiment_over_time(sentiment_data, *, output_dir=CHARTS_DIR):
    """Save a stacked area chart (> 5 dates) or stacked bar chart (<= 5 dates) for sentiment over time.
        → output/charts/sentiment_over_time.png

    Args:
        sentiment_data: List of dicts with keys 'date', 'positive', 'neutral', 'negative', 'none'.
        output_dir:     Directory to save the PNG.

    Returns:
        Path to saved PNG file, or None if no data.
    """
    if not sentiment_data:
        logger.warning("visualizer: No sentiment time data — skipping sentiment over time chart.")
        return None

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "sentiment_over_time.png"

    dates = [row["date"] for row in sentiment_data]
    sentiments = ["positive", "neutral", "negative", "none"]
    labels = ["Positive", "Neutral", "Negative", "Unclassified"]
    colors = [_SENTIMENT_COLORS[s] for s in sentiments]

    fig, ax = plt.subplots(figsize=(max(8, len(dates) * 0.6), 5))

    num_dates = len(dates)

    if num_dates > 5:
        # Stacked area chart
        y_series = [[row.get(s, 0) for row in sentiment_data] for s in sentiments]
        ax.stackplot(dates, *y_series, labels=labels, colors=colors, alpha=0.85)
    else:
        # Stacked bar chart
        bottoms = [0] * num_dates
        for s, label, color in zip(sentiments, labels, colors):
            vals = [row.get(s, 0) for row in sentiment_data]
            ax.bar(dates, vals, bottom=bottoms, label=label, color=color, edgecolor="white")
            bottoms = [b + v for b, v in zip(bottoms, vals)]

    ax.set_xlabel("Date", fontsize=11)
    ax.set_ylabel("Article Count", fontsize=11)
    ax.set_title("Sentiment Over Time", fontsize=14, fontweight="bold", pad=12)
    ax.spines[["top", "right"]].set_visible(False)

    if len(dates) > 7:
        plt.xticks(rotation=45, ha="right", fontsize=9)
    else:
        plt.xticks(fontsize=10)

    ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="none", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    logger.info(f"visualizer: sentiment over time chart saved -> {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Chart 4 — Sentiment by category
# ---------------------------------------------------------------------------

def plot_sentiment_by_category(sentiment_cat_data, *, output_dir=CHARTS_DIR):
    """Save a stacked bar chart of sentiment by category.
        → output/charts/sentiment_by_category.png

    Args:
        sentiment_cat_data: List of dicts with keys 'category', 'positive', 'neutral', 'negative', 'none'.
        output_dir:         Directory to save the PNG.

    Returns:
        Path to saved PNG file, or None if no data.
    """
    if not sentiment_cat_data:
        logger.warning("visualizer: No sentiment category data — skipping sentiment by category chart.")
        return None

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "sentiment_by_category.png"

    categories = [row["category"] for row in sentiment_cat_data]
    sentiments = ["positive", "neutral", "negative", "none"]
    labels = ["Positive", "Neutral", "Negative", "Unclassified"]
    colors = [_SENTIMENT_COLORS[s] for s in sentiments]

    fig, ax = plt.subplots(figsize=(max(8, len(categories) * 0.8), 5))

    bottoms = [0] * len(categories)
    for s, label, color in zip(sentiments, labels, colors):
        vals = [row.get(s, 0) for row in sentiment_cat_data]
        ax.bar(categories, vals, bottom=bottoms, label=label, color=color, edgecolor="white")
        bottoms = [b + v for b, v in zip(bottoms, vals)]

    ax.set_xlabel("Category", fontsize=11)
    ax.set_ylabel("Article Count", fontsize=11)
    ax.set_title("Sentiment by Category", fontsize=14, fontweight="bold", pad=12)
    ax.spines[["top", "right"]].set_visible(False)

    if len(categories) > 5:
        plt.xticks(rotation=45, ha="right", fontsize=9)
    else:
        plt.xticks(fontsize=10)

    ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="none", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    logger.info(f"visualizer: sentiment by category chart saved -> {out_path}")
    return out_path

