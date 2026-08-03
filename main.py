import logging
from src.arg_parser import parse_arguments
from src.collector import collect_news
from src.cleaner import clean_news
#from src.ai_processor import summarize_news, analyze_news
from src.reporter import generate_report
from src.exporter import export_news
from src.database import initialize_database


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    filename="app.log",
    encoding="utf-8"
)


def list_news(args):
    print(f"Listing news articles with filters - Category: {args.category}, Date From: {args.date_from}, Date To: {args.date_to}, Keyword: {args.keyword}, Page: {args.page}, Page Size: {args.page_size}...")

def show_news(args):
    print(f"Showing details for article with ID: {args.id}...")



def main():
    initialize_database()
    args = parse_arguments()

    commands = {
        "fetch": collect_news,
        "clean": clean_news,
        #"summarize": summarize_news,
        #"analyze": analyze_news,
        "report": generate_report,
        "export": export_news,
        "list": list_news,
        "show": show_news,
        # "category": manage_categories
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