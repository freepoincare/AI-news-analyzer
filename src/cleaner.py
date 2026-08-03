"""
cleaner.py: clean records and apply duplicate policy

One important detail: URL comparison alone may still miss duplicates because the same article can have:

https://example.com/news/article-123

versus:

https://www.example.com/news/article-123?utm_source=google

Therefore, in cleaner.py, you may later normalize URLs by removing tracking parameters and standardizing the hostname before comparing them.
"""


def clean_news(args):
    print(f"Cleaning news data with duplicate handling policy: {args.policy}...")
