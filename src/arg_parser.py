import argparse
from .config import CATEGORIES
from .utils import validate_date

def parse_arguments():
    parser = argparse.ArgumentParser(description="AI News Trend and Insight Analysis Report Generator")

    subparsers = parser.add_subparsers(dest="command", required=True, help="Available subcommands")

    # fetch
    fetch_parser = subparsers.add_parser("fetch", help="Collect news articles from a source")
    fetch_parser.add_argument("--source", type=str.lower, required=True, choices=['rss', 'api', 'crawler'], help="The news source name to fetch articles from")
    fetch_parser.add_argument("--limit", type=int, default=10, help="Maximum number of articles to fetch (default: 10)")  # required=False is default -> optional, but writing '--limit' w/o value will raise an error.
    fetch_parser.add_argument("--category", type=str.lower, required=True, choices=CATEGORIES, help="News category to fetch articles from")
    fetch_parser.add_argument("--query", type=str, required=True, help="Search query for fetching news articles (limited to 500 characters)")
    fetch_parser.add_argument("--date-from", type=validate_date, help="Start date for fetching articles (YYYY-MM-DD)")
    fetch_parser.add_argument("--date-to", type=validate_date, help="End date for fetching articles (YYYY-MM-DD)")

    # clean
    clean_parser = subparsers.add_parser("clean", help="Clean and validate raw news data")
    clean_parser.add_argument("--policy", type=str.lower, choices=["skip", "upsert"], default="skip", help="Duplicate handling policy: 'skip' to ignore duplicates, 'upsert' to update existing records")

    # summarize
    summarize_parser = subparsers.add_parser("summarize", help="Summarize news articles (with full content, not snippet-only) using AI)")
    summarize_group = summarize_parser.add_mutually_exclusive_group(required=True)
    summarize_group.add_argument("--all", action="store_true", help="Summarize all available news") # store_true means that if the flag is present, it will be set to True; otherwise, it will be False
    summarize_group.add_argument("--id", type=int, help="ID of a specific article to summarize")    # including action="append" allows 'python main.py summarize --id 5 --id 10'; it will append the values to a list; otherwise, it will be a single value
    summarize_group.add_argument("--unsummarized", action="store_true", help="Summarize only articles that haven't been summarized yet")
    summarize_parser.add_argument("--limit", type=int, default=5, help="Maximum number of articles to summarize (default: 5)")
    summarize_parser.add_argument("--include-snippet", action="store_true", default=False, help="Include snippet-only articles in summarization (default: skip)")

    # analyze
    analyze_parser = subparsers.add_parser("analyze", help="Analyze news trends using AI")
    analyze_parser.add_argument("--date-from", type=validate_date, required=True, help="Start date of the articles (YYYY-MM-DD)")
    analyze_parser.add_argument("--date-to", type=validate_date, required=True, help="End date of the articles (YYYY-MM-DD)")
    analyze_parser.add_argument("--category", type=str.lower, required=True, choices=CATEGORIES, help="News category")

    # report
    report_parser = subparsers.add_parser("report", help="Generate a news analysis report")
    report_parser.add_argument("--format", type=str.lower, choices=["txt", "md"], default="md", help="Report output format (txt or md) (default: md)")
    report_parser.add_argument("--date-from", type=validate_date, help="Start date of the articles (YYYY-MM-DD)")
    report_parser.add_argument("--date-to", type=validate_date, help="End date of the articles (YYYY-MM-DD)")
    report_parser.add_argument("--category", type=str.lower, choices=CATEGORIES, help="News category")

    # export
    export_parser = subparsers.add_parser("export", help="Export news data to a file")
    export_parser.add_argument("--format", type=str.lower, choices=["csv", "jsonl", "xlsx"], required=True, help="Export file format (csv, jsonl, or xlsx)")
    export_parser.add_argument("--status", type=str.lower, choices=["all", "summarized", "unsummarized"], default="all", help="Filter news by summary status")

    # list: Show a list of news articles with filtering options
    list_parser = subparsers.add_parser("list", help="Show a list of news articles")
    list_parser.add_argument("--category", type=str.lower, choices=CATEGORIES, help="Filter articles by category")
    list_parser.add_argument("--date-from", type=validate_date, help="Filter articles from this date (YYYY-MM-DD)")
    list_parser.add_argument("--date-to", type=validate_date, help="Filter articles up to this date (YYYY-MM-DD)")
    list_parser.add_argument("--keyword", type=str.lower, help="Search articles by keyword")
    list_parser.add_argument("--page", type=int, default=1, help="Page number to display (default: 1)")
    list_parser.add_argument("--page-size", type=int, default=10, help="Number of articles per page (default: 10)")

    # show: Show details of a specific news article by its ID
    show_parser = subparsers.add_parser("show", help="Show details of a news article")
    show_parser.add_argument("--id", type=int, required=True, help="ID of the article to display")

    # category (not required): The category values can instead come from your SQLite database.
    # category_parser = subparsers.add_parser("category", help="Manage news categories")
    # category_group = category_parser.add_mutually_exclusive_group(required=True)
    # category_group.add_argument("--list", action="store_true", help="List all categories")
    # category_group.add_argument("--add", type=str, help="Add a new category")
    # category_group.add_argument("--remove", type=str, help="Remove an existing category")

    return parser.parse_args()  # args