import logging
import feedparser
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


"""
## 뉴스 수집 및 저장

- 외부 뉴스 API(또는 RSS)와 크롤링으로 뉴스 데이터를 수집하고, raw/clean 분리 저장이 동작한다.
- 중복 뉴스는 설정에 따라 `skip` 또는 `upsert` 처리된다.

* 다음 두 가지 방법을 모두 구현한다.

  - 방법 1: 공개 뉴스 API 또는 RSS 피드 활용
  - 방법 2: 뉴스 사이트 크롤링 (`BeautifulSoup` 또는 `Selenium` 활용)

* HTTP 요청 시 타임아웃 설정과 오류 처리를 구현한다.
* 수집된 원본 데이터는 수집 시각, 소스 정보, 수집 방법과 함께 raw 저장소에 저장된다.
"""


def get_news_via_rss(args_query, args_limit):
    query = quote_plus(args_query)
    rss_url = (
        f"https://news.google.com/rss/search?q={query}"
        "&hl=en-US&gl=US&ceid=US:en"
    )
    feed = feedparser.parse(rss_url)

    for idx, entry in enumerate(feed.entries[:args_limit], start=1):
        print(f"[{idx}] {entry.title}")
        print(f"Published: {entry.published}")
        print(f"Link: {entry.link}\n")

    return feed.entries

def get_news_via_api(args_query, args_limit):
    # Placeholder for API-based news fetching logic
    # Implement the actual API request and response handling here
    print(f"Fetching news via API for query: {args_query} with limit: {args_limit}")
    return []  # Return a list of articles

def get_news_via_crawler(args_query, args_limit):
    # Placeholder for web crawling logic
    # Implement the actual crawling and parsing logic here
    print(f"Fetching news via crawler for query: {args_query} with limit: {args_limit}")
    return []  # Return a list of articles


def collect_news(args):
    
    logger.info(f"[INFO] News collection started: source={args.source}, limit={args.limit}")

    try:
        if args.source == "rss":
            articles = get_news_via_rss(args.query, args.limit)
        elif args.source == "api":
            articles = get_news_via_api(args.query, args.limit)
        elif args.source == "crawler":
            articles = get_news_via_crawler(args.query, args.limit)
        else:  # parse_arguments() already restricts the choices, but this is a safeguard.
            logger.error(f"Unknown news source: {args.source}")
            return

        logger.info(f"News collection completed: {len(articles)} articles success")
        # how do I check how many articles were failed? I can check the response from the API or the crawler, but for RSS, it will just return whatever is available. I can log the number of articles fetched and compare it to the requested limit.

    except TimeoutError:
        logger.warning("News API request timed out")

    except Exception as e:
        logger.error(f"News collection failed: {e}")