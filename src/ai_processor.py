from .config import GEMINI_API_KEY

if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY environment variable is not set")


def summarize_news(args):
    if args.all:
        print(f"Summarizing all available news articles (limit: {args.limit})...")
    elif args.id:
        print(f"Summarizing article with ID: {args.id}...")
    elif args.unsummarized:
        print(f"Summarizing unsummarized articles (limit: {args.limit})...")


def analyze_news(args):
    print(f"Analyzing news trends from {args.date_from} to {args.date_to} in category: {args.category}...")
