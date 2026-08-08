"""
cleaner.py: validate, normalize, enrich, and deduplicate raw news records.

Pipeline (called by 'python main.py clean --policy skip|upsert'):

Check if raw_news table is empty → abort with message
      │
      ▼
  raw_news table
      │
      ├── (1) validate required fields (title, url)
      ├── normalize text  (strip HTML tags, collapse whitespace)
      ├── normalize date  (parse to YYYY-MM-DD)
      ├── handle missing values
      └── (2) fetch full article body via newspaper4k
              │  (falls back to snippet if fetch fails or returns empty)
              ▼
  save_clean_news(policy) → clean_news table
        • 'skip'   = INSERT OR IGNORE  (keep existing record)
        • 'upsert' = INSERT OR REPLACE (overwrite existing record)

Note on URL deduplication:
  URL comparison alone may miss duplicates because the same article can appear as:
    https://example.com/news/article-123
    https://www.example.com/news/article-123?utm_source=google
  A future improvement could normalize URLs (strip tracking params, unify host)
  before comparing unique_guid values.
"""

import logging
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests
from bs4 import BeautifulSoup
from newspaper import Article, Config
from newspaper.article import ArticleException

from .collector import resolve_google_rss_link
from .database import get_raw_news, save_clean_news, get_existing_clean_guids

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


# ---------------------------------------------------------------------------
# Date normalization
# ---------------------------------------------------------------------------

_RELATIVE_DATE_RE = re.compile(r"\d+\s*(분|시간|일|주|개월|년)\s*전")  # 11시간 전, 1일 전, 2주 전, 3개월 전, 1년 전
_DOT_DATE_RE = re.compile(r"(\d{4})[.\-](\d{2})[.\-](\d{2})")


def _normalize_date(raw_date):
    """Parse raw_date into YYYY-MM-DD string. Returns None for empty input,
    original string if all parse attempts fail."""
    if not raw_date:
        return None

    raw_date = str(raw_date).strip()

    # ISO 8601: "2026-08-03T12:00:00Z" or "2026-08-03"
    try:
        dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        return dt.date().isoformat()
    except (ValueError, AttributeError):
        pass

    # RFC 2822: "Mon, 03 Aug 2026 12:00:00 +0000"
    try:
        dt = parsedate_to_datetime(raw_date)
        return dt.date().isoformat()
    except Exception:
        pass

    # Dot / dash format embedded in string: "2026.08.03." or "2026-08-03"
    m = _DOT_DATE_RE.search(raw_date)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # Korean relative date (e.g. "3시간 전", "1일 전") — use today as best-effort
    if _RELATIVE_DATE_RE.search(raw_date):
        return datetime.now(timezone.utc).date().isoformat()

    return raw_date  # give up; keep original so data is not silently lost


# ---------------------------------------------------------------------------
# Text normalization
# ---------------------------------------------------------------------------

def _strip_html(text):
    """Remove HTML tags from text."""
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _normalize_whitespace(text):
    """Collapse runs of whitespace into a single space."""
    return re.sub(r"\s+", " ", text or "").strip()


# ---------------------------------------------------------------------------
# Full-article content fetching
# ---------------------------------------------------------------------------

def _fetch_full_content(url, raw_content=""):
    """Download and parse the full article body using newspaper4k, BeautifulSoup fallback, or raw content.

    Returns the article text, or an empty string if the fetch fails
    (network error, paywall, bot-block, etc.).
    """
    # 1. First check if raw_content already contains full article text
    cleaned_raw = _strip_html(raw_content)
    if len(cleaned_raw) > 200:
        return cleaned_raw

    # 2. Try fetching with newspaper4k using realistic browser User-Agent
    try:
        config = Config()
        config.browser_user_agent = USER_AGENT
        config.request_timeout = 10

        article = Article(url, config=config)
        article.download()
        article.parse()
        text = article.text.strip()
        if text and len(text) > 100:
            return text
    except ArticleException as e:
        logger.warning(f"newspaper4k could not parse article at {url}: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error fetching full content for {url}: {e}")

    # 3. Fallback: direct HTTP GET + BeautifulSoup paragraph extraction
    try:
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            # Remove scripts, styles, header, footer, nav
            for tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
                tag.decompose()
            paragraphs = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 30]
            full_text = "\n\n".join(paragraphs)
            if len(full_text) > 100:
                return full_text
    except Exception as e:
        logger.warning(f"BeautifulSoup fallback failed for {url}: {e}")

    return cleaned_raw


# ---------------------------------------------------------------------------
# Record-level validation and cleaning
# ---------------------------------------------------------------------------

def _validate(record):
    """Return True if the record has the minimum required fields."""
    return bool(record.get("title", "").strip()) and bool(record.get("url", "").strip())


def _clean_record(raw):
    """Normalize and enrich a single raw record.

    Returns a cleaned dict ready for save_clean_news(), or None if the
    record fails validation or has empty content and snippet.
    """

    # (1) Validate required fields (title, url)
    if not _validate(raw):
        logger.warning(
            f"Skipping raw record id={raw.get('id')} — "
            f"missing required field (title or url)."
        )
        return None

    url = raw["url"].strip()
    fetch_url = resolve_google_rss_link(url) if "news.google.com" in url else url

    snippet = _normalize_whitespace(_strip_html(raw.get("snippet", "")))

    # (2) Fetch full article body; fall back to snippet when unavailable
    logger.info(f"Fetching full content: {fetch_url}")
    full_content = _fetch_full_content(fetch_url, raw_content=raw.get("content", ""))
    
    if full_content:
        content = _normalize_whitespace(full_content)
        content_source = "full"
    elif snippet:
        logger.warning(
            f"No full content retrieved for {fetch_url}. "
            f"Using snippet as fallback."
        )
        content = snippet
        content_source = "snippet"
    else:
        logger.warning(
            f"Skipping raw record id={raw.get('id')} — "
            f"both snippet and content are empty."
        )
        return None

    raw_guid = raw.get("unique_guid", url)
    unique_guid = fetch_url if "news.google.com" in raw_guid else raw_guid

    return {
        "title":          _normalize_whitespace(raw["title"]),
        "url":            fetch_url if fetch_url else url,
        "source":         _normalize_whitespace(raw.get("source", "")),
        "published_at":   _normalize_date(raw.get("published_at")),
        "snippet":        snippet,
        "content":        content,
        "content_source": content_source,
        "category":       raw.get("category", ""),
        "unique_guid":    unique_guid,
        "method":         raw.get("method", ""),
        "query":          raw.get("query", ""),
        "collected_at":   raw.get("collected_at", ""),
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def clean_news(args):
    """Entry point for 'python main.py clean --policy skip|upsert'."""

    policy = args.policy  # 'skip' or 'upsert', validated by argparse

    logger.info(f"Clean step started (policy={policy}).")

    raw_records = get_raw_news()
    if not raw_records:
        logger.warning(
            "Clean step aborted: raw_news table is empty. "
            "Please run 'python main.py fetch ...' first."
        )
        return

    logger.info(f"Processing {len(raw_records)} raw records...")

    existing_guids = set()
    if policy == "skip":
        existing_guids = get_existing_clean_guids()

    cleaned = []
    skipped = 0

    for raw in raw_records:
        guid = raw.get("unique_guid") or raw.get("url", "").strip()
        if policy == "skip" and guid in existing_guids:
            logger.info(f"Skipping article processing (already in clean storage): {guid}")
            skipped += 1
            continue

        result = _clean_record(raw)
        if result:
            cleaned.append(result)
        else:
            skipped += 1

    if not cleaned:
        if skipped > 0:
            print(f"[INFO] All {skipped} record(s) were already present in clean storage or skipped.")
        logger.warning("Clean step: no new valid records to save to clean storage.")
        return

    save_clean_news(cleaned, policy=policy)

    summary = (
        f"{len(cleaned)} article(s) saved to clean storage "
        f"(policy={policy}), {skipped} skipped."
    )
    logger.info(f"Clean step completed: {summary}")
