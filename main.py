import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="AI News Trend and Insight Analysis Report Generator")

    subparsers = parser.add_subparsers(dest="command", required=True, help="Available subcommands")

    # fetch
    fetch_parser = subparsers.add_parser("fetch", help="Collect news articles from a source")
    fetch_parser.add_argument("--source", type=str, required=True, choices=['google', 'naver'], help="The news source name to fetch articles from")
    fetch_parser.add_argument("--limit", type=int, default=10, help="Maximum number of articles to fetch (default: 10)")  # required=False is default -> optional, but writing '--limit' w/o value will raise an error.

    # clean
    clean_parser = subparsers.add_parser("clean", help="Clean and validate raw news data")
    clean_parser.add_argument("--policy", type=str, choices=["skip", "upsert"], default="skip", help="Duplicate handling policy: 'skip' to ignore duplicates, 'upsert' to update existing records")

    # summarize
    summarize_parser = subparsers.add_parser("summarize", help="Summarize news articles using AI")
    summarize_group = summarize_parser.add_mutually_exclusive_group(required=True)
    summarize_group.add_argument("--all", action="store_true", help="Summarize all available news") # store_true means that if the flag is present, it will be set to True; otherwise, it will be False
    summarize_group.add_argument("--id", type=int, help="ID of a specific article to summarize")    # including action="append" allows 'python main.py summarize --id 5 --id 10'; it will append the values to a list; otherwise, it will be a single value
    summarize_group.add_argument("--unsummarized", action="store_true", help="Summarize only articles that haven't been summarized yet")
    summarize_parser.add_argument("--limit", type=int, default=5, help="Maximum number of articles to summarize (default: 5)")

    # analyze
    analyze_parser = subparsers.add_parser("analyze", help="Analyze news trends using AI")
    analyze_parser.add_argument("--date-from", type=str, required=True, help="Start date of the articles (YYYY-MM-DD)")
    analyze_parser.add_argument("--date-to", type=str, required=True, help="End date of the articles (YYYY-MM-DD)")
    analyze_parser.add_argument("--category", type=str, required=True, help="News category")  # what categories are available? we can get them from the database or from the 'category' subcommand

    # report
    report_parser = subparsers.add_parser("report", help="Generate a news analysis report")
    report_parser.add_argument("--format", type=str, choices=["txt", "md"], default="md", help="Report output format (txt or md) (default: md)")

    # export
    export_parser = subparsers.add_parser("export", help="Export news data to a file")
    export_parser.add_argument("--format", type=str, choices=["csv", "jsonl", "xlsx"], required=True, help="Export file format (csv, jsonl, or xlsx)")
    export_parser.add_argument("--status", type=str, choices=["all", "summarized", "unsummarized"], default="all", help="Filter news by summary status")

    # list (bonus): Show a list of news articles with filtering options
    list_parser = subparsers.add_parser("list", help="Show a list of news articles")
    list_parser.add_argument("--category", type=str, help="Filter articles by category")
    list_parser.add_argument("--date-from", type=str, help="Filter articles from this date (YYYY-MM-DD)")
    list_parser.add_argument("--date-to", type=str, help="Filter articles up to this date (YYYY-MM-DD)")
    list_parser.add_argument("--keyword", type=str, help="Search articles by keyword")
    list_parser.add_argument("--page", type=int, default=1, help="Page number to display (default: 1)")
    list_parser.add_argument("--page-size", type=int, default=10, help="Number of articles per page (default: 10)")

    # show (bonus): Show details of a specific news article by its ID
    show_parser = subparsers.add_parser("show", help="Show details of a news article")
    show_parser.add_argument("--id", type=int, required=True, help="ID of the article to display")

    # category (not required): The category values can instead come from your SQLite database.
    category_parser = subparsers.add_parser("category", help="Manage news categories")
    category_group = category_parser.add_mutually_exclusive_group(required=True)
    category_group.add_argument("--list", action="store_true", help="List all categories")
    category_group.add_argument("--add", type=str, help="Add a new category")
    category_group.add_argument("--remove", type=str, help="Remove an existing category")

    return parser.parse_args()

def collect_news(args):
    print(f"Collecting up to {args.limit} articles from {args.source}...")

def clean_news(args):
    print(f"Cleaning news data with duplicate handling policy: {args.policy}...")

def summarize_news(args):
    if args.all:
        print(f"Summarizing all available news articles (limit: {args.limit})...")
    elif args.id:
        print(f"Summarizing article with ID: {args.id}...")
    elif args.unsummarized:
        print(f"Summarizing unsummarized articles (limit: {args.limit})...")

def analyze_news(args):
    print(f"Analyzing news trends from {args.date_from} to {args.date_to} in category: {args.category}...")

def generate_report(args):
    print(f"Generating news analysis report in {args.format} format...")

def export_news(args):
    print(f"Exporting news data in {args.format} format with status filter: {args.status}...")

def list_news(args):
    print(f"Listing news articles with filters - Category: {args.category}, Date From: {args.date_from}, Date To: {args.date_to}, Keyword: {args.keyword}, Page: {args.page}, Page Size: {args.page_size}...")

def show_news(args):
    print(f"Showing details for article with ID: {args.id}...")

def manage_categories(args):
    if args.list:
        print("Listing all categories...")
    elif args.add:
        print(f"Adding new category: {args.add}...")
    elif args.remove:
        print(f"Removing category: {args.remove}...")


def main():
    args = parse_arguments()

    commands = {
        "fetch": collect_news,
        "clean": clean_news,
        "summarize": summarize_news,
        "analyze": analyze_news,
        "report": generate_report,
        "export": export_news,
        "list": list_news,
        "show": show_news,
        "category": manage_categories
    }

    commands[args.command](args)
    
"""
    if args.command == "fetch":
        collect_news(args)
    elif args.command == "clean":
        clean_news(args)
    elif args.command == "summarize":
        summarize_news(args)
    elif args.command == "analyze":
        analyze_news(args)
    elif args.command == "report":
        generate_report(args)
    elif args.command == "export":
        export_news(args)
    elif args.command == "list":
        list_news(args)
    elif args.command == "show":
        show_news(args)
    elif args.command == "category":
        manage_categories(args)
    else:
        print("Unknown command. Use --help for available commands.")
"""


if __name__ == "__main__":
    main()