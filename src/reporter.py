"""
reporter.py: Generate a news analysis report combining statistics, charts, and AI insights.

Entry point for 'python main.py report'.

Pipeline:
  1. Fetch aggregated stats from the database (get_report_stats).
  2. Generate chart PNG files via visualizer.generate_charts().
  3. Fetch the latest AI insight result from the database (get_latest_insight).
  4. Assemble the report (console output + file saved in output/reports/).

Supported output formats: txt, md (markdown).

Functions:
    generate_report(args) — CLI entry point
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

from .database import get_report_stats, get_latest_insight, get_sentiment_stats
from .visualizer import generate_charts

logger = logging.getLogger(__name__)

REPORTS_DIR = Path("output") / "reports"



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _quality_metrics(stats):
    """Return quality metric lines as a list of strings.

    Metrics (satisfies §4.7: 2+ quality indicators):
      1. Summarization rate — % of clean articles that have been summarized.
      2. Content coverage   — % of clean articles that have a non-empty body.
    """
    total = stats["total_clean"]
    if total == 0:
        return ["  No clean articles found."]

    summarized_rate = stats["total_summarized"] / total * 100
    missing         = stats["total_missing_content"]
    coverage_rate   = (total - missing) / total * 100

    return [
        f"  Summarization rate : {stats['total_summarized']:>4} / {total} ({summarized_rate:.1f}%)",
        f"  Content coverage   : {total - missing:>4} / {total} ({coverage_rate:.1f}%)",
    ]


def _top_sources_block(stats, n=5):
    """Return formatted Top-N source lines (TOP N aggregate)."""
    sources = stats["top_sources"][:n]
    if not sources:
        return ["  No source data available."]
    lines = []
    for rank, (src, cnt) in enumerate(sources, start=1):
        lines.append(f"  {rank}. {src:<30} {cnt} articles")
    return lines


# Plain-text report assembly
def _build_report_lines(stats, chart_paths, insight, category=None, date_from=None, date_to=None):
    """Assemble the full report as a list of plain-text lines."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = []

    # Period display
    if date_from and date_to:
        period_str = f"{date_from} ~ {date_to}"
    elif date_from:
        period_str = f"From {date_from}"
    elif date_to:
        period_str = f"Until {date_to}"
    else:
        period_str = "All available data"

    # Category display
    category_str = category.capitalize() if category else "All categories"

    lines += [
        "=" * 60,
        "  AI NEWS ANALYZER — ANALYSIS REPORT",
        f"  Generated: {now}",
        f"  Period: {period_str}",
        f"  Category: {category_str}",
        "=" * 60,
        "",
    ]

    # --- Overview ---
    lines += [
        "[ OVERVIEW ]",
        f"  Raw articles collected : {stats['total_raw']}",
        f"  Clean articles stored  : {stats['total_clean']}",
        f"  Articles summarized    : {stats['total_summarized']}",
        "",
    ]

    # --- Quality Metrics (§4.7: 2+ indicators) ---
    lines += ["[ QUALITY METRICS ]"] + _quality_metrics(stats) + [""]

    # --- Top N Sources (§4.7: 1+ TOP N) ---
    lines += ["[ TOP 5 SOURCES ]"] + _top_sources_block(stats, n=5) + [""]

    # --- Category Distribution ---
    if stats["category_counts"]:
        lines.append("[ CATEGORY DISTRIBUTION ]")
        for cat, cnt in stats["category_counts"]:
            lines.append(f"  {cat:<20} {cnt} articles")
        lines.append("")

    # --- Sentiment Distribution ---
    if stats.get("sentiment_counts"):
        lines.append("[ SENTIMENT DISTRIBUTION ]")
        for sent, cnt in stats["sentiment_counts"]:
            lines.append(f"  {sent:<20} {cnt} articles")
        lines.append("")

    # --- Chart references ---
    lines.append("[ CHARTS ]")
    if chart_paths.get("category_chart"):
        lines.append(f"  Category distribution     : {chart_paths['category_chart']}")
    else:
        lines.append("  Category distribution     : (not generated — no data)")
    if chart_paths.get("daily_chart"):
        lines.append(f"  Daily trend               : {chart_paths['daily_chart']}")
    else:
        lines.append("  Daily trend               : (not generated — no data)")
    if chart_paths.get("sentiment_over_time_chart"):
        lines.append(f"  Sentiment over time       : {chart_paths['sentiment_over_time_chart']}")
    else:
        lines.append("  Sentiment over time       : (not generated — no data)")
    if chart_paths.get("sentiment_by_category_chart"):
        lines.append(f"  Sentiment by category     : {chart_paths['sentiment_by_category_chart']}")
    else:
        lines.append("  Sentiment by category     : (not generated — filtered or no data)")
    lines.append("")

    # --- AI Insight (§4.7: AI insight result) ---
    lines.append("[ AI INSIGHT ANALYSIS ]")
    if insight:
        lines += [
            f"  Analyzed at    : {insight.get('analyzed_at', 'N/A')}",
            f"  Articles used  : {insight.get('article_count', 'N/A')}",
            f"  Category filter: {insight.get('category') or 'all'}",
            f"  Date range     : {insight.get('date_from') or 'N/A'} ~ {insight.get('date_to') or 'N/A'}",
            "",
        ]
        lines += insight["result_text"].splitlines()
    else:
        lines.append(
            "  No AI insight found. Run 'python main.py analyze' first."
        )
    lines += ["", "=" * 60]

    return lines


# Markdown report assembly with tables and image embeds
def _build_markdown_lines(stats, chart_paths, insight, category=None, date_from=None, date_to=None):
    """Assemble the full report as markdown lines."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = []

    # Period display
    if date_from and date_to:
        period_str = f"{date_from} ~ {date_to}"
    elif date_from:
        period_str = f"From {date_from}"
    elif date_to:
        period_str = f"Until {date_to}"
    else:
        period_str = "All available data"

    # Category display
    category_str = category.capitalize() if category else "All categories"

    lines += [
        "# AI News Analyzer — Analysis Report",
        "",
        f"Period: {period_str}",
        f"Category: {category_str}",
        f"**Generated:** {now}",
        "",
        "---",
        "",
    ]

    # --- Overview ---
    lines += [
        "## Overview",
        "",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Raw articles collected | {stats['total_raw']} |",
        f"| Clean articles stored  | {stats['total_clean']} |",
        f"| Articles summarized    | {stats['total_summarized']} |",
        "",
    ]

    # --- Quality Metrics ---
    total = stats["total_clean"]
    if total > 0:
        summarized_rate = stats["total_summarized"] / total * 100
        missing         = stats["total_missing_content"]
        coverage_rate   = (total - missing) / total * 100
        lines += [
            "## Quality Metrics",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Summarization rate | {stats['total_summarized']} / {total} ({summarized_rate:.1f}%) |",
            f"| Content coverage   | {total - missing} / {total} ({coverage_rate:.1f}%) |",
            "",
        ]

    # --- Top N Sources ---
    lines += ["## Top 5 Sources", ""]
    sources = stats["top_sources"][:5]
    if sources:
        lines.append("| Rank | Source | Articles |")
        lines.append("|------|--------|----------|")
        for rank, (src, cnt) in enumerate(sources, start=1):
            lines.append(f"| {rank} | {src} | {cnt} |")
    else:
        lines.append("_No source data available._")
    lines.append("")

    # --- Category Distribution ---
    if stats["category_counts"]:
        lines += ["## Category Distribution", ""]
        lines.append("| Category | Articles |")
        lines.append("|----------|----------|")
        for cat, cnt in stats["category_counts"]:
            lines.append(f"| {cat} | {cnt} |")
        lines.append("")

    # --- Sentiment Distribution ---
    if stats.get("sentiment_counts"):
        lines += ["## Sentiment Distribution", ""]
        lines.append("| Sentiment | Articles |")
        lines.append("|-----------|----------|")
        for sent, cnt in stats["sentiment_counts"]:
            lines.append(f"| {sent} | {cnt} |")
        lines.append("")

    # --- Charts ---
    lines += ["## Charts", ""]
    if chart_paths.get("category_chart"):
        rel = Path(chart_paths["category_chart"])
        lines.append(f"![Category Distribution]({rel})")
    else:
        lines.append("_Category distribution chart not generated (no data)._")
    lines.append("")
    if chart_paths.get("daily_chart"):
        rel = Path(chart_paths["daily_chart"])
        lines.append(f"![Daily Trend]({rel})")
    else:
        lines.append("_Daily trend chart not generated (no data)._")
    lines.append("")
    if chart_paths.get("sentiment_over_time_chart"):
        rel = Path(chart_paths["sentiment_over_time_chart"])
        lines.append(f"![Sentiment Over Time]({rel})")
    else:
        lines.append("_Sentiment over time chart not generated (no data)._")
    lines.append("")
    if chart_paths.get("sentiment_by_category_chart"):
        rel = Path(chart_paths["sentiment_by_category_chart"])
        lines.append(f"![Sentiment By Category]({rel})")
    elif not category:
        lines.append("_Sentiment by category chart not generated (no data)._")
    lines.append("")

    # --- AI Insight ---
    lines += ["## AI Insight Analysis", ""]
    if insight:
        lines += [
            f"- **Analyzed at:** {insight.get('analyzed_at', 'N/A')}",
            f"- **Articles used:** {insight.get('article_count', 'N/A')}",
            f"- **Category filter:** {insight.get('category') or 'all'}",
            f"- **Date range:** {insight.get('date_from') or 'N/A'} ~ {insight.get('date_to') or 'N/A'}",
            "",
        ]
        lines += insight["result_text"].splitlines()
    else:
        lines.append(
            "> No AI insight found. Run `python main.py analyze` first."
        )
    lines.append("")

    return lines


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def generate_report(args):
    """CLI entry point for 'python main.py report  # md (default)' or
                           'python main.py report --format txt'.
    [collects stats] → [generates charts] → [loads AI insight] → [prints + saves file]
    Args:
        args.format: 'txt' or 'md' (default 'md').
        args.category: Optional category filter string.
        args.date_from: Optional start date filter (YYYY-MM-DD).
        args.date_to: Optional end date filter (YYYY-MM-DD).
    """
    fmt = getattr(args, "format", "md")
    category = getattr(args, "category", None)
    date_from = getattr(args, "date_from", None)
    date_to = getattr(args, "date_to", None)

    logger.info("Collecting statistics...")
    stats = get_report_stats(category=category, date_from=date_from, date_to=date_to)

    if stats["total_clean"] == 0:
        logger.error("No clean data found matching the specified filters. "
                     "Please run 'python main.py clean' or adjust your filter parameters.")
        return

    # Collect sentiment stats
    sentiment_stats = get_sentiment_stats(category=category, date_from=date_from, date_to=date_to)
    stats.update(sentiment_stats)

    logger.info("Generating charts...")
    chart_paths = generate_charts(stats, category=category)

    if chart_paths["category_chart"]:
        logger.info(f"Category chart saved: {chart_paths['category_chart']}")
    if chart_paths["daily_chart"]:
        logger.info(f"Daily trend chart saved: {chart_paths['daily_chart']}")
    if chart_paths.get("sentiment_over_time_chart"):
        logger.info(f"Sentiment over time chart saved: {chart_paths['sentiment_over_time_chart']}")
    if chart_paths.get("sentiment_by_category_chart"):
        logger.info(f"Sentiment by category chart saved: {chart_paths['sentiment_by_category_chart']}")

    logger.info("Loading latest AI insight...")
    insight = get_latest_insight()
    if not insight:
        logger.warning("No AI insight found. Run 'python main.py analyze' first.")

    # --- Build report content ---
    if fmt == "md":
        lines = _build_markdown_lines(stats, chart_paths, insight, category=category, date_from=date_from, date_to=date_to)
        ext = "md"
    else:
        lines = _build_report_lines(stats, chart_paths, insight, category=category, date_from=date_from, date_to=date_to)
        ext = "txt"

    report_text = "\n".join(lines)

    # --- Console output ---
    logger.info("\n" + report_text)

    # --- Save to file ---
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = REPORTS_DIR / f"report_{timestamp}.{ext}"
    out_path.write_text(report_text, encoding="utf-8")

    logger.info(f"report: saved to {out_path} (format={fmt})")


