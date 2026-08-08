import logging
import math
from src.logging_config import setup_logging
from src.config import load_config
from src.arg_parser import parse_arguments
from src.collector import collect_news
from src.cleaner import clean_news
from src.ai_processor import summarize_news, analyze_news
from src.reporter import generate_report
from src.exporter import export_news
from src.database import initialize_database, get_clean_news, get_clean_news_count


logger = logging.getLogger(__name__)


def list_news(args):
    page = max(1, args.page)
    page_size = max(1, args.page_size)
    offset = (page - 1) * page_size

    total_count = get_clean_news_count(
        category=args.category,
        date_from=args.date_from,
        date_to=args.date_to,
        keyword=args.keyword
    )
    
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

    articles = get_clean_news(
        category=args.category,
        date_from=args.date_from,
        date_to=args.date_to,
        keyword=args.keyword,
        order_by="id ASC",
        limit=page_size,
        offset=offset
    )

    filters_applied = []
    if args.category:
        filters_applied.append(f"Category: {args.category}")
    if args.date_from:
        filters_applied.append(f"Date From: {args.date_from}")
    if args.date_to:
        filters_applied.append(f"Date To: {args.date_to}")
    if args.keyword:
        filters_applied.append(f"Keyword: '{args.keyword}'")

    filter_str = f" [{', '.join(filters_applied)}]" if filters_applied else ""

    print("=" * 80)
    print(f" News List (Page {page}/{total_pages}, Total: {total_count} articles){filter_str}")
    print("=" * 80)

    if not articles:
        print("No articles found matching the criteria.")
        print("=" * 80)
        return

    for idx, article in enumerate(articles, start=offset + 1):
        published = article.get("published_at") or "N/A"
        category = article.get("category") or "N/A"
        source = article.get("source") or "N/A"
        status = article.get("status") or "unsummarized"
        
        print(f"[{article['id']}] {article['title']}")
        print(f"    Date: {published} | Category: {category} | Source: {source} | Status: {status}")
        if article.get("snippet"):
            snippet = article['snippet'][:120] + "..." if len(article['snippet']) > 120 else article['snippet']
            print(f"    Snippet: {snippet}")
        print("-" * 80)


def show_news_detail(args):
    articles = get_clean_news(article_id=args.id)
    if not articles:
        logger.error(f"Error: Article with ID {args.id} not found.")
        return

    article = articles[0]
    print("=" * 80)
    print(f" Article Details (ID: {article['id']})")
    print("=" * 80)
    print(f"Title       : {article.get('title', 'N/A')}")
    print(f"Category    : {article.get('category', 'N/A')}")
    print(f"Source      : {article.get('source', 'N/A')}")
    print(f"Published   : {article.get('published_at', 'N/A')}")
    print(f"URL         : {article.get('url', 'N/A')}")
    print(f"Status      : {article.get('status', 'unsummarized')}")
    if article.get("sentiment"):
        print(f"Sentiment   : {article['sentiment']}")
    print("-" * 80)

    if article.get("snippet"):
        print(f"[Snippet]\n{article['snippet']}\n")
    if article.get("summary"):
        print(f"[AI Summary]\n{article['summary']}\n")
    if article.get("content"):
        print(f"[Content]\n{article['content']}")
    elif not article.get("summary") and not article.get("snippet"):
        print("(No additional content available)")
    print("=" * 80)


def main():
    config = load_config() # Load config.json first
    setup_logging(config)  # Configure logging once when the program starts
    initialize_database()
    args = parse_arguments()
    commands = {
        "fetch": collect_news,
        "clean": clean_news,
        "summarize": summarize_news,
        "analyze": analyze_news,
        "report": generate_report,
        "export": export_news,
        "list": list_news,
        "show": show_news_detail,
    }
    commands[args.command](args)  # Execute the corresponding function based on the command


if __name__ == "__main__":
    main()