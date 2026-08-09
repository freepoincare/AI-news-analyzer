"""
visualizer.py: Generate and save matplotlib chart images for the report.

Called internally by reporter.py -- not a direct CLI subcommand.

Charts produced (combined into a single 2x2 grid image)
--------------------------------------------------------
1. Category distribution bar chart   (top-left)
2. Daily collection trend line chart (top-right)
3. Sentiment over time chart         (bottom-left)
4. Sentiment by category chart       (bottom-right)

The combined PNG is saved to the output/charts/ directory (created if absent)
with a timestamped filename: chart_{timestamp}.png

Functions:
    plot_category_distribution() -- draws category bar chart onto an Axes
    plot_daily_trend()           -- draws daily trend line chart onto an Axes
    plot_sentiment_over_time()   -- draws sentiment-over-time chart onto an Axes
    plot_sentiment_by_category() -- draws sentiment-by-category chart onto an Axes
    generate_charts()            -- combines all charts into one PNG and returns its path
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

_SENTIMENT_COLORS = {
    "positive": "#55A868",  # Green
    "neutral":  "#4C72B0",  # Blue
    "negative": "#C44E52",  # Red
    "none":     "#8C8C8C",  # Grey
}


# ---------------------------------------------------------------------------
# Chart 1 -- Category distribution
# ---------------------------------------------------------------------------

def plot_category_distribution(category_counts, *, ax=None):
    """Draw a horizontal bar chart of article counts per category onto ax.

    Args:
        category_counts: List of (category_str, count_int) tuples,
                         ordered by count descending (from get_report_stats()).
        ax:              A matplotlib Axes to draw into. If None, a standalone
                         figure is created (legacy / test usage).

    Returns:
        True if data was plotted, False if no data.
    """
    if not category_counts:
        logger.warning("visualizer: No category data -- skipping category chart.")
        if ax is not None:
            ax.set_visible(False)
        return False

    categories = [row[0] for row in category_counts]
    counts     = [row[1] for row in category_counts]
    bar_colors = [_PALETTE[i % len(_PALETTE)] for i in range(len(categories))]

    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(10, max(4, len(categories) * 0.55)))

    bars = ax.barh(categories[::-1], counts[::-1], color=bar_colors[::-1], edgecolor="white", alpha=0.85)

    # Value labels on bars
    for bar, val in zip(bars, counts[::-1]):
        ax.text(
            bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
            str(val), va="center", ha="left", fontsize=8, color="#333333"
        )

    ax.set_xlabel("Article Count", fontsize=12)
    ax.set_title("News Distribution by Category", fontsize=16, fontweight="bold", pad=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlim(0, max(counts) * 1.18)
    ax.tick_params(axis="y", labelsize=9)

    if standalone:
        fig.tight_layout()
        return fig

    return True


# ---------------------------------------------------------------------------
# Chart 2 -- Daily collection trend
# ---------------------------------------------------------------------------

def plot_daily_trend(daily_counts, *, ax=None):
    """Draw a line chart showing article collection counts per day onto ax.

    Args:
        daily_counts: List of (date_str, count_int) tuples ordered by date
                      ascending (from get_report_stats()).
        ax:           A matplotlib Axes to draw into. If None, a standalone
                      figure is created (legacy / test usage).

    Returns:
        True if data was plotted, False if no data.
    """
    if not daily_counts:
        logger.warning("visualizer: No daily data -- skipping daily trend chart.")
        if ax is not None:
            ax.set_visible(False)
        return False

    dates  = [row[0] for row in daily_counts]
    counts = [row[1] for row in daily_counts]

    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(max(8, len(dates) * 0.6), 5))

    ax.plot(dates, counts, marker="o", linewidth=2,
            color="#4C72B0", markerfacecolor="#DD8452",
            markeredgecolor="white", markersize=6)
    ax.fill_between(dates, counts, alpha=0.12, color="#4C72B0")

    # Annotate each point
    for x, y in zip(dates, counts):
        ax.annotate(
            str(y), (x, y),
            textcoords="offset points", xytext=(0, 7),
            ha="center", fontsize=7, color="#333333"
        )

    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Article Count", fontsize=12)
    ax.set_title("Daily Collection Trend", fontsize=16, fontweight="bold", pad=10)
    ax.spines[["top", "right"]].set_visible(False)

    if len(dates) > 7:
        ax.tick_params(axis="x", rotation=45, labelsize=8)
    else:
        ax.tick_params(axis="x", labelsize=9)

    ax.set_ylim(0, max(counts) * 1.25)

    if standalone:
        fig.tight_layout()
        return fig

    return True


# ---------------------------------------------------------------------------
# Chart 3 -- Sentiment over time
# ---------------------------------------------------------------------------

def plot_sentiment_over_time(sentiment_data, *, ax=None):
    """Draw a stacked area/bar chart for sentiment over time onto ax.

    Args:
        sentiment_data: List of dicts with keys date, positive, neutral, negative, none.
        ax:             A matplotlib Axes to draw into. If None, a standalone
                        figure is created (legacy / test usage).

    Returns:
        True if data was plotted, False if no data.
    """
    if not sentiment_data:
        logger.warning("visualizer: No sentiment time data -- skipping sentiment over time chart.")
        if ax is not None:
            ax.set_visible(False)
        return False

    dates = [row["date"] for row in sentiment_data]
    sentiments = ["positive", "neutral", "negative", "none"]
    labels = ["Positive", "Neutral", "Negative", "Unclassified"]
    colors = [_SENTIMENT_COLORS[s] for s in sentiments]

    standalone = ax is None
    if standalone:
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
            ax.bar(dates, vals, bottom=bottoms, label=label, color=color, edgecolor="white", alpha=0.85)
            bottoms = [b + v for b, v in zip(bottoms, vals)]

    ax.set_xlabel("Published Date", fontsize=12)
    ax.set_ylabel("Article Count", fontsize=12)
    ax.set_title("Sentiment Over Time", fontsize=16, fontweight="bold", pad=10)
    ax.spines[["top", "right"]].set_visible(False)

    if len(dates) > 7:
        ax.tick_params(axis="x", rotation=45, labelsize=8)
    else:
        ax.tick_params(axis="x", labelsize=9)

    ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="none", fontsize=8)

    if standalone:
        fig.tight_layout()
        return fig

    return True


# ---------------------------------------------------------------------------
# Chart 4 -- Sentiment by category
# ---------------------------------------------------------------------------

def plot_sentiment_by_category(sentiment_cat_data, *, ax=None):
    """Draw a stacked bar chart of sentiment by category onto ax.

    Args:
        sentiment_cat_data: List of dicts with keys category, positive, neutral, negative, none.
        ax:                 A matplotlib Axes to draw into. If None, a standalone
                            figure is created (legacy / test usage).

    Returns:
        True if data was plotted, False if no data.
    """
    if not sentiment_cat_data:
        logger.warning("visualizer: No sentiment category data -- skipping sentiment by category chart.")
        if ax is not None:
            ax.set_visible(False)
        return False

    categories = [row["category"] for row in sentiment_cat_data]
    sentiments = ["positive", "neutral", "negative", "none"]
    labels = ["Positive", "Neutral", "Negative", "Unclassified"]
    colors = [_SENTIMENT_COLORS[s] for s in sentiments]

    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(max(8, len(categories) * 0.8), 5))

    bottoms = [0] * len(categories)
    for s, label, color in zip(sentiments, labels, colors):
        vals = [row.get(s, 0) for row in sentiment_cat_data]
        ax.bar(categories, vals, bottom=bottoms, label=label, color=color, edgecolor="white", alpha=0.85)
        bottoms = [b + v for b, v in zip(bottoms, vals)]

    ax.set_xlabel("Category", fontsize=12)
    ax.set_ylabel("Article Count", fontsize=12)
    ax.set_title("Sentiment by Category", fontsize=16, fontweight="bold", pad=10)
    ax.spines[["top", "right"]].set_visible(False)

    if len(categories) > 5:
        ax.tick_params(axis="x", rotation=45, labelsize=8)
    else:
        ax.tick_params(axis="x", labelsize=9)

    ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="none", fontsize=8)

    if standalone:
        fig.tight_layout()
        return fig

    return True


# ---------------------------------------------------------------------------
# Combined 2x2 chart image
# ---------------------------------------------------------------------------

def generate_charts(stats, *, category=None, timestamp=None, output_dir=CHARTS_DIR):
    """Combine all four charts into a single 2x2 grid image and save it.

    Args:
        stats:      The dict returned by database.get_report_stats() & get_sentiment_stats().
        category:   Category filter specified in report subcommand (or None).
        timestamp:  Timestamp string (e.g. 20260808_234935) used in the filename.
                    If None, the filename defaults to chart.png for backwards compat.
        output_dir: Directory to save the PNG file.

    Returns:
        Path to the combined PNG file (or None if no charts were generated).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fname = f"chart_{timestamp}.png" if timestamp else "chart.png"
    out_path = output_dir / fname

    # Build the 2x2 figure
    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    fig.patch.set_facecolor("#FAFAFA")

    ax_cat   = axes[0][0]   # top-left:     Category distribution
    ax_daily = axes[0][1]   # top-right:    Daily trend
    ax_time  = axes[1][0]   # bottom-left:  Sentiment over time
    ax_scat  = axes[1][1]   # bottom-right: Sentiment by category

    any_plotted = False

    # Chart 1 -- Category distribution
    if plot_category_distribution(stats.get("category_counts", []), ax=ax_cat):
        any_plotted = True

    # Chart 2 -- Daily trend
    if plot_daily_trend(stats.get("daily_counts", []), ax=ax_daily):
        any_plotted = True

    # Chart 3 -- Sentiment over time
    if "sentiment_over_time" in stats:
        if plot_sentiment_over_time(stats["sentiment_over_time"], ax=ax_time):
            any_plotted = True
    else:
        ax_time.set_visible(False)

    # Chart 4 -- Sentiment by category
    # If --category is specified, skip the by category chart.
    if not category and "sentiment_by_category" in stats:
        if plot_sentiment_by_category(stats["sentiment_by_category"], ax=ax_scat):
            any_plotted = True
    else:
        ax_scat.set_visible(False)

    if not any_plotted:
        plt.close(fig)
        logger.warning("visualizer: No charts were generated -- no data available.")
        return None

    fig.suptitle("AI News Analyzer - Charts", fontsize=20, fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)

    logger.info(f"visualizer: combined chart saved -> {out_path}")
    return out_path
