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

from .database import get_report_stats, get_matching_insight, get_sentiment_stats
from .visualizer import generate_charts
from .utils import format_date_only, format_datetime_utc

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
def _build_report_lines(stats, combined_chart, insight, category=None, date_from=None, date_to=None):
    """Assemble the full report as a list of plain-text lines.

    Args:
        combined_chart: Path to the single combined chart PNG (or None).
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = []

    # Format dates to YYYY-MM-DD only
    d_from = format_date_only(date_from)
    d_to = format_date_only(date_to)

    # Period display
    if d_from and d_to:
        period_str = f"{d_from} ~ {d_to}"
    elif d_from:
        period_str = f"From {d_from}"
    elif d_to:
        period_str = f"Until {d_to}"
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

    # --- Quality Metrics ---
    lines += ["[ QUALITY METRICS ]"] + _quality_metrics(stats) + [""]

    # --- Top N Sources ---
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

    # --- Chart reference (single combined image) ---
    lines.append("[ CHARTS ]")
    if combined_chart:
        lines.append(f"  Combined chart (2x2)      : {combined_chart}")
    else:
        lines.append("  Combined chart            : (not generated — no data)")
    lines.append("")

    # --- AI Insight ---
    lines.append("[ AI INSIGHT ANALYSIS ]")
    if insight:
        analyzed_at_str = format_datetime_utc(insight.get('analyzed_at'))
        insight_from = format_date_only(insight.get('date_from')) or 'N/A'
        insight_to = format_date_only(insight.get('date_to')) or 'N/A'
        lines += [
            f"  Analyzed at    : {analyzed_at_str}",
            f"  Articles used  : {insight.get('article_count', 'N/A')}",
            f"  Category filter: {insight.get('category') or 'all'}",
            f"  Date range     : {insight_from} ~ {insight_to}",
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
def _build_markdown_lines(stats, combined_chart, insight, category=None, date_from=None, date_to=None):
    """Assemble the full report as markdown lines.

    Args:
        combined_chart: Path to the single combined chart PNG (or None).
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = []

    # Format dates to YYYY-MM-DD only
    d_from = format_date_only(date_from)
    d_to = format_date_only(date_to)

    # Period display
    if d_from and d_to:
        period_str = f"{d_from} ~ {d_to}"
    elif d_from:
        period_str = f"From {d_from}"
    elif d_to:
        period_str = f"Until {d_to}"
    else:
        period_str = "All available data"

    # Category display
    category_str = category.capitalize() if category else "All categories"

    lines += [
        "# AI News Analyzer - Analysis Report",
        "",
        f"* Generated: {now}",
        f"* Period: {period_str}",
        f"* Category: {category_str}",
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

    # --- Charts (single combined 2x2 image) ---
    lines += ["## Charts", ""]
    if combined_chart:
        chart_name = Path(combined_chart).name
        lines.append(f"![AI News Analyzer Charts](../charts/{chart_name})")
    else:
        lines.append("_Charts not generated (no data)._")
    lines.append("")

    # --- AI Insight ---
    lines += ["## AI Insight Analysis", ""]
    if insight:
        analyzed_at_str = format_datetime_utc(insight.get('analyzed_at'))
        insight_from = format_date_only(insight.get('date_from')) or 'N/A'
        insight_to = format_date_only(insight.get('date_to')) or 'N/A'
        lines += [
            f"- Analyzed at: {analyzed_at_str}",
            f"- Articles used: {insight.get('article_count', 'N/A')}",
            f"- Category filter: {insight.get('category') or 'all'}",
            f"- Date range: {insight_from} ~ {insight_to}",
            "",
        ]
        lines += insight["result_text"].splitlines()
    else:
        lines.append("> No AI insight found. Run `python main.py analyze` first.")
    lines.append("")

    return lines


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def generate_report(args):
    """CLI entry point for 'python main.py report'.
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

    # Generate a single timestamp shared by both the report file and the chart image.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info("Generating charts...")
    combined_chart = generate_charts(stats, category=category, timestamp=timestamp)

    if combined_chart:
        logger.info(f"Combined chart saved: {combined_chart}")
    else:
        logger.warning("No chart was generated (no data).")

    logger.info("Loading matching AI insight for requested scope...")
    insight = get_matching_insight(category=category, date_from=date_from, date_to=date_to)
    if not insight:
        scope_parts = []
        if category:
            scope_parts.append(f"category='{category}'")
        if date_from or date_to:
            d_from = format_date_only(date_from) or "start"
            d_to = format_date_only(date_to) or "end"
            scope_parts.append(f"period={d_from}~{d_to}")

        if scope_parts:
            scope_str = " with " + " and ".join(scope_parts)
        else:
            scope_str = " with matching category or period filters"

        logger.warning(
            f"No AI insight found matching the requested scope ({scope_str.strip()}). "
            f"Please run 'python main.py analyze'{scope_str} for AI insights."
        )

    # --- Build report content ---
    if fmt == "md":
        lines = _build_markdown_lines(stats, combined_chart, insight, category=category, date_from=date_from, date_to=date_to)
        ext = "md"
    else:
        lines = _build_report_lines(stats, combined_chart, insight, category=category, date_from=date_from, date_to=date_to)
        ext = "txt"

    report_text = "\n".join(lines)

    # --- Console output ---
    print("=" * 80)
    print(report_text)
    print("=" * 80)

    # --- Save to file ---
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"report_{timestamp}.{ext}"
    out_path.write_text(report_text, encoding="utf-8")

    logger.info(f"report: saved to {out_path} (format={fmt})")


