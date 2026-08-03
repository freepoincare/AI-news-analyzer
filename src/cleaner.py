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

from newspaper import Article
from newspaper.article import ArticleException

from .database import get_raw_news, save_clean_news

logger = logging.getLogger(__name__)


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

def _fetch_full_content(url):
    """Download and parse the full article body using newspaper4k.

    Returns the article text, or an empty string if the fetch fails
    (network error, paywall, bot-block, etc.).
    """
    try:
        article = Article(url, request_timeout=10)
        article.download()
        article.parse()
        return article.text.strip()
    except ArticleException as e:
        logger.warning(f"newspaper4k could not parse article at {url}: {e}")
        return ""
    except Exception as e:
        logger.warning(f"Unexpected error fetching full content for {url}: {e}")
        return ""


# ---------------------------------------------------------------------------
# Record-level validation and cleaning
# ---------------------------------------------------------------------------

def _validate(record):
    """Return True if the record has the minimum required fields."""
    return bool(record.get("title", "").strip()) and bool(record.get("url", "").strip())


def _clean_record(raw):
    """Normalize and enrich a single raw record.

    Returns a cleaned dict ready for save_clean_news(), or None if the
    record fails validation.
    """

    # (1) Validate required fields (title, url)
    if not _validate(raw):
        logger.warning(
            f"Skipping raw record id={raw.get('id')} — "
            f"missing required field (title or url)."
        )
        return None

    url = raw["url"].strip()

    # (2) Fetch full article body; fall back to snippet when unavailable
    logger.info(f"Fetching full content: {url}")
    content = _fetch_full_content(url)
    if not content:
        logger.warning(
            f"No full content retrieved for {url}. "
            f"Using snippet as fallback."
        )
        content = _strip_html(raw.get("snippet", ""))  # fallback

    return {
        "title":        _normalize_whitespace(raw["title"]),
        "url":          url,
        "source":       _normalize_whitespace(raw.get("source", "")),
        "published_at": _normalize_date(raw.get("published_at")),
        "snippet":      _normalize_whitespace(_strip_html(raw.get("snippet", ""))),
        "content":      _normalize_whitespace(content),
        "category":     raw.get("category", ""),
        "unique_guid":  raw.get("unique_guid", url),
        "method":       raw.get("method", ""),
        "query":        raw.get("query", ""),
        "collected_at": raw.get("collected_at", ""),
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
        print(
            "[WARNING] No raw data found. "
            "Please run 'python main.py fetch ...' first."
        )
        logger.warning("Clean step aborted: raw_news table is empty.")
        return

    logger.info(f"Processing {len(raw_records)} raw records...")

    cleaned = []
    skipped = 0

    for raw in raw_records:
        result = _clean_record(raw)
        if result:
            cleaned.append(result)
        else:
            skipped += 1

    if not cleaned:
        print(
            "[WARNING] No records passed validation. "
            "Nothing was saved to clean storage."
        )
        logger.warning("Clean step: all records failed validation.")
        return

    save_clean_news(cleaned, policy=policy)

    summary = (
        f"{len(cleaned)} article(s) saved to clean storage "
        f"(policy={policy}), {skipped} skipped."
    )
    logger.info(f"Clean step completed: {summary}")
    print(f"[INFO] Clean completed: {summary}")
