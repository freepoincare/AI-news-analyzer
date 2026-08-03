"""
collector: collect and normalize source data

collect_news()
      ├── get_news_via_rss()
      ├── get_news_via_api()
      └── get_news_via_crawler()
                │
                ▼
          common records
                │
                ▼
         save_raw_news()
                │
                ▼
       SQLite raw_news table

## 뉴스 수집 및 저장

- 외부 뉴스 API(또는 RSS)와 크롤링으로 뉴스 데이터를 수집하고, raw/clean 분리 저장이 동작한다.
- 중복 뉴스는 설정에 따라 `skip` 또는 `upsert` 처리된다.

* 다음 두 가지 방법을 모두 구현한다.

  - 방법 1: 공개 뉴스 API 또는 RSS 피드 활용
  - 방법 2: 뉴스 사이트 크롤링 (`BeautifulSoup` 또는 `Selenium` 활용)

* HTTP 요청 시 타임아웃 설정과 오류 처리를 구현한다.
* 수집된 원본 데이터는 수집 시각, 소스 정보, 수집 방법과 함께 raw 저장소에 저장된다.
"""

import logging
import re
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import quote_plus

from .database import save_raw_news
from .config import NEWS_API_KEY, RSS_URL, API_URL, CRAWLER_URL, LANGUAGE


_DATE_PATTERN = re.compile(r"\d{4}[.\-]\d{2}[.\-]\d{2}|\d+[분시일주개월년]+\s*전")


logger = logging.getLogger(__name__)


def _base_record(*, title, url, source, published_at, snippet, content, unique_guid, method, query, category, raw):
    """Create a common record schema for all news sources (RSS, API, Crawler)"""
    return {
        "title": title,
        "url": url,
        "source": source,
        "published_at": published_at,  # Preserve the original publication-date value. Date normalization is performed during the clean step.
        "snippet": snippet,
        "content": content,
        "unique_guid": unique_guid,
        "method": method,
        "query": query,
        "category": category,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "raw": raw,
    }


def resolve_google_rss_link(google_link):
    """Google RSS redirect URL into the actual publisher article URL.
    news.google.com/rss/articles/... → Resolve a Google News RSS URL to the article URL."""
    try:
        response = requests.head(google_link, allow_redirects=True, timeout=5)
        response.raise_for_status()  # HTTP errors (4xx, 5xx) are raised as an exception, then caught by the except block below.
        return response.url
    except requests.RequestException as e:  # some news servers(BBC, Reuters, etc.) reject HEAD request with 405. 'resolve' itself fails without GET fallback.
        logger.debug(f"HEAD request failed for {google_link}: {e}")

    try:
        response = requests.get(google_link, allow_redirects=True, timeout=5)
        response.raise_for_status()
        return response.url
    except requests.RequestException as e:
        logger.warning(
            f"Could not resolve Google RSS URL '{google_link}'. "
            f"Using the original URL instead: {e}"
        )
        return google_link


def normalize_rss_entry(entry, query, category):
    link = entry.get("link", "")
    resolved = resolve_google_rss_link(link) if "news.google.com" in link else link
    return _base_record(
        title=entry.get("title", ""),
        url=resolved,
        source=entry.get("source", {}).get("title", "Google News"),
        published_at=entry.get("published", ""),
        snippet=entry.get("summary", ""),
        content=entry.get("content", [{}])[0].get("value", ""),
        unique_guid=resolved,  # Resolve Google News RSS link to actual article URL
        method="rss",
        query=query,
        category=category,
        raw=dict(entry)  # Store the entire entry as raw data
    )


def normalize_api_article(article, query, category):
    return _base_record(
        title=article.get("title", ""),
        url=article.get("url", ""),
        source=article.get("source", {}).get("name", "Unknown"),
        published_at=article.get("publishedAt", ""),
        snippet=article.get("description", ""),
        content=article.get("content", ""),
        unique_guid=article.get("url", ""),  # Use URL as unique identifier
        method="api",
        query=query,
        category=category,
        raw=dict(article)  # Store the entire article as raw data
    )


def normalize_crawler_article(*, title, url, source, published_at, snippet, query, category, raw):
    return _base_record(
        title=title,
        url=url,
        source=source,
        published_at=published_at,
        snippet=snippet,
        content="",
        unique_guid=url,
        method="crawler",
        query=query,
        category=category,
        raw=raw,
    )


def get_news_via_rss(query_text, limit, category):
    encoded = quote_plus(query_text)
    rss_url = f"{RSS_URL}?q={encoded}&hl=en-US&gl=US&ceid=US:en"
    response = requests.get(rss_url, timeout=10)    # requests controls the timeout
    response.raise_for_status()                     # handles HTTP errors (4xx, 5xx) in the calling function
    feed = feedparser.parse(response.content)       # parses the downloaded RSS content; feed object contains feed.feed and feed.entries
    return [normalize_rss_entry(entry, query_text, category) for entry in feed.entries[:limit]]


def get_news_via_api(query_text, limit, category, date_from=None, date_to=None):

    # only raising error when using API (thus, inside this fct), because RSS and Crawler do not require API keys.
    if not NEWS_API_KEY:
        raise EnvironmentError("NEWS_API_KEY environment variable is not set")

    params = {
        "q": query_text,        # q: max length 500 chars
        "apiKey": NEWS_API_KEY,
        "sortBy": "popularity", # popularity: articles from popular sources and publishers come first.
        "language": LANGUAGE,
        "pageSize": limit,       # pageSize: when omitted, default 100, max 100
    }

    if date_from:
        params["from"] = date_from
    if date_to:
        params["to"] = date_to

    response = requests.get(API_URL, params=params, timeout=10)
    response.raise_for_status()  # Raise an HTTPError for 4xx and 5xx responses. collect_news() catches and logs the exception..
    data = response.json()
    articles = data.get("articles", [])

    return [normalize_api_article(a, query_text, category) for a in articles]


def get_news_via_crawler(query_text, limit, category):
    query = quote_plus(query_text)
    url = f"{CRAWLER_URL}?where=news&query={query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=10)

    response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes, which we can catch and log as an error in the calling function.

    soup = BeautifulSoup(response.text, "html.parser")
    news_items = soup.select(".news_area")
    articles = []

    for item in news_items[:limit]:
        title_tag = item.select_one(".news_tit")
        if not title_tag:
            continue  # Skip if title tag is not found, as it's essential for identifying the article.

        source_tag = item.select_one(".info.press")
        snippet_tag = item.select_one(".dsc_wrap")
        info_tags = item.select(".info_group .info")
        info_texts = [tag.get_text(strip=True) for tag in info_tags]

        published_at = None
        for text in info_texts:
            if _DATE_PATTERN.search(text):  # Check if the text matches a date pattern (e.g., "2023.08.15.")
                published_at = text
                break

        articles.append(normalize_crawler_article(
            title=title_tag.get_text(strip=True),
            url=title_tag["href"],
            source=(source_tag.get_text(strip=True) if source_tag else "Naver News"),
            published_at=published_at,
            snippet=(snippet_tag.get_text(" ", strip=True) if snippet_tag else ""),
            query=query_text,
            category=category,
            raw=item.prettify()  # Store the entire HTML of the news item
        ))

    return articles


def collect_news(args):
    
    logger.info(f"News collection started: source={args.source}, limit={args.limit}")

    try:
        if args.source == "rss":
            articles = get_news_via_rss(args.query, args.limit, args.category)
        elif args.source == "api":
            articles = get_news_via_api(
                args.query,
                args.limit,
                args.category,
                getattr(args, "date_from", None),
                getattr(args, "date_to", None),
            )
        elif args.source == "crawler":
            articles = get_news_via_crawler(args.query, args.limit, args.category)
        else:  # parse_arguments() already restricts the choices, but this is a safeguard.
            logger.error(f"Unknown news source: {args.source}")
            return
        # For empty articles, for now, I'll just log a warning.
        if not articles:
            logger.warning("No articles were collected. Please check the query and source.")
            return

        save_raw_news(articles)
        logger.info(f"News collection completed: {len(articles)} articles collected and saved to raw storage.")
 
    except requests.exceptions.Timeout:
        logger.warning(f"News request timed out: source={args.source}")

    except requests.exceptions.RequestException as e:
        logger.error(f"News request failed: source={args.source}, error={e}")

    except Exception:
        logger.exception(f"Unexpected error during news collection: source={args.source}")