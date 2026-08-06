"""
ai_processor.py: Summarize and analyze clean news articles using the Gemini AI model.

Pipeline contract (enforced here):
  summarize / analyze may ONLY read from clean_news.
  If no clean data is found, both commands abort with a clear error message.
  Users must run 'python main.py clean' before these commands.

Functions:
    summarize_news(args) — send clean article content to AI and save summary and sentiment analysis
    analyze_news(args)   — batch-analyze clean articles and return trend insights
"""

import json
import logging
from datetime import datetime, timezone
from google import genai
from enum import Enum
from pydantic import BaseModel

from .config import GEMINI_MODEL, validate_gemini_key
from .database import get_clean_news, update_clean_status, save_insight

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants & data models
# ---------------------------------------------------------------------------

ENFORCEMENT_PROMPT = (
    "\n\n[IMPORTANT] Your previous response was invalid. "
    "You MUST return ONLY valid JSON (no markdown, no code fences, no extra text). "
    "The JSON object must contain exactly two keys: "
    "\"summary\" (a string with a 3-5 sentence summary) and "
    "\"sentiment\" (a string that is exactly one of: \"positive\", \"neutral\", \"negative\"). "
    "Example: {\"summary\": \"...\", \"sentiment\": \"neutral\"}"
)

class Sentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"

    @classmethod
    def values(cls) -> set[str]:
        """Return a set of all valid sentiment string values."""
        return {member.value for member in cls}

class SummaryResult(BaseModel):
    summary: str
    sentiment: Sentiment

# ---------------------------------------------------------------------------
# Response validation
# ---------------------------------------------------------------------------

def _validate_ai_response(raw_text):
    """Validate the AI response and return (summary, sentiment) or raise ValueError.

    Checks performed:
        1. The output is valid JSON.
        2. It contains 'summary' and 'sentiment' keys with string values.
        3. The sentiment value is one of VALID_SENTIMENTS.

    Returns:
        A tuple (summary_str, sentiment_str) on success.

    Raises:
        ValueError with a descriptive message on any validation failure.
    """
    # (1) Check valid JSON
    try:
        data = json.loads(raw_text)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(f"Response is not valid JSON: {exc}")

    # (2) Check required keys exist and values are strings
    for key in ("summary", "sentiment"):
        if key not in data:
            raise ValueError(f"JSON is missing required key '{key}'")
        if not isinstance(data[key], str):
            raise ValueError(
                f"Value of '{key}' must be a string, got {type(data[key]).__name__}"
            )

    # (3) Check sentiment value is in VALID_SENTIMENTS
    if data["sentiment"] not in Sentiment.values():
        raise ValueError(
            f"Invalid sentiment '{data['sentiment']}'; "
            f"must be one of {Sentiment.values()}"
        )

    return data["summary"], data["sentiment"]

# ---------------------------------------------------------------------------
# Pipeline guard
# ---------------------------------------------------------------------------

def _require_clean_data(records, command_name):
    """Print an error and return False when no clean records are available.

    Args:
        records:      The list returned by get_clean_news().
        command_name: The CLI command name (used in the error message).

    Returns:
        True  — records exist; caller may proceed.
        False — no records; caller should return immediately.
    """
    if not records:
        print(
            f"[ERROR] No clean data found. "
            f"Please run 'python main.py clean' before running '{command_name}'."
        )
        logger.error(
            f"'{command_name}' aborted: clean_news table is empty. "
            f"Run 'python main.py clean' first."
        )
        return False
    return True


# ---------------------------------------------------------------------------
# summarize
# ---------------------------------------------------------------------------

def summarize_news(args):
    """Entry point for 'python main.py summarize'.

    Reads only from clean_news. Aborts with a message if clean_news is empty
    (i.e. 'python main.py clean' has not been run yet).

      - Supports --all, --id, --unsummarized selection options
      - Supports --limit for batch processing.
      - Already-summarized articles are skipped by default (via status filter).
      - On API failure: logs the error and skips the article.
      - On success: saves the summary + sentiment and flips status to 'summarized'.
    """
    # --- resolve which records to process ---
    if args.id:
        records = get_clean_news(article_id=args.id)
    elif args.unsummarized:
        records = get_clean_news(status="unsummarized", limit=args.limit)
    else:  # --all
        records = get_clean_news(limit=args.limit)

    # --- pipeline guard: refuse to proceed without clean data ---
    if not _require_clean_data(records, "summarize"):
        return

    total = len(records)
    logger.info(f"summarize: {total} record(s) queued for summarization.")

    api_key = validate_gemini_key()
    success_count = 0
    fail_count = 0

    for i, record in enumerate(records, start=1):
        article_id = record["id"]
        title = record["title"]
        text = record["content"] if record["content"] else record["snippet"]

        if not text:
            logger.warning(f"[{i}/{total}] ID={article_id} no content, skipping.")
            fail_count += 1
            continue

        prompt = (
            "Please analyze the following news article (available at the end)."
            "Return ONLY valid JSON."
            "Do not include markdown, explanations, or code fences."
            "The JSON must have exactly this structure:"
            "{"
            "  \"summary\": \"3-5 sentence summary\","
            "  \"sentiment\": \"positive | neutral | negative\""
            "}"
            "Instructions:"
            "  - The summary should be 3-5 concise sentences."
            "  - Include only the key facts."
            "  - The sentiment must be exactly one of:"
            "    \"positive\", \"neutral\", or \"negative\"."
            "\n---\n"
            "Article:\n"
            "Title:\n"
            f"{title}\n"
            "Content:\n"
            f"{text}\n"
            "\n---\n"
        )

        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": SummaryResult,
                },
            )
            raw_text = response.text.strip()

            # --- validate response; retry once on failure ---
            try:
                summary_text, sentiment_value = _validate_ai_response(raw_text)
            except ValueError as ve:
                logger.warning(
                    f"[{i}/{total}] ID={article_id} first response invalid ({ve}), retrying..."
                )
                retry_prompt = prompt + ENFORCEMENT_PROMPT
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=retry_prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": SummaryResult,
                    },
                )
                raw_text = response.text.strip()
                # validate again — let ValueError propagate to outer except on second failure
                summary_text, sentiment_value = _validate_ai_response(raw_text)

            update_clean_status(
                article_id,
                summary_text,
                status="summarized",
                sentiment=sentiment_value,
            )

            original_len = len(text)
            summary_len = len(summary_text)
            print(
                f"[INFO] [{i}/{total}] ID={article_id} summary completed "
                f"({original_len} chars → {summary_len} chars), "
                f"sentiment={sentiment_value}"
            )
            logger.info(
                f"[{i}/{total}] ID={article_id} summarized "
                f"({original_len} chars → {summary_len} chars), "
                f"sentiment={sentiment_value}: {title[:60]}"
            )
            success_count += 1

        except Exception as exc:
            logger.error(f"[{i}/{total}] ID={article_id} summary failed: {exc}")
            print(f"[WARNING] [{i}/{total}] ID={article_id} summary failed, skipping: {exc}")
            fail_count += 1

    print(f"[INFO] Summary completed: {success_count} succeeded, {fail_count} failed")
    logger.info(f"summarize finished: {success_count} succeeded, {fail_count} failed.")


# ---------------------------------------------------------------------------
# analyze
# ---------------------------------------------------------------------------

def analyze_news(args):
    """Entry point for 'python main.py analyze'.

    Reads only from clean_news. Aborts with a clear message if no matching
    clean records exist for the given filters.

    Per §4.5:
      - Filters by date range and/or category.
      - Sends combined article text to the Gemini API.
      - Analysis covers at least 4 items: Key Trends, Core Keywords,
        Commonalities / Differences, Implications.
      - Persists the result to the insights table for later report use.
      - Prints the structured result to the console.
    """
    records = get_clean_news(
        category=args.category,
        date_from=args.date_from,
        date_to=args.date_to,
    )

    # --- pipeline guard: refuse to proceed without clean data ---
    if not _require_clean_data(records, "analyze"):
        return

    total = len(records)
    logger.info(f"analyze: {total} record(s) queued for analysis.")
    print(f"[INFO] Analysis target: {total} articles")
    print("[INFO] Requesting AI analysis...")

    # --- build combined article text for the prompt ---
    article_blocks = []
    for idx, record in enumerate(records, start=1):
        text = record["content"] if record["content"] else record["snippet"]
        block = (
            f"[Article: {idx}]\n"
            f"Title: {record['title']}\n"
            f"Date: {record.get('published_at', 'Unknown')}\n"
            f"Content: {text[:800] if text else '(No content)'}"
        )
        article_blocks.append(block)

    combined_text = "\n\n".join(article_blocks)

    prompt = (
        "The following is a list of news articles. Please provide a comprehensive insight analysis based on the four items below.\n\n"
        "1. [Key Trends] — Describe 2~4 key trends commonly appearing in the articles\n"
        "2. [Core Keywords] — List frequently appearing or important keywords, separated by commas (5~10 items)\n"
        "3. [Commonalities / Differences] — Briefly compare the main commonalities and differences among the articles\n"
        "4. [Implications] — Describe the implications of these articles in 2~3 sentences\n\n"
        "Use the exact section titles and fill in only the content. Omit unnecessary introductions or concluding remarks.\n\n"
        f"--- News Articles ({total} articles) ---\n\n"
        f"{combined_text}"
    )

    api_key = validate_gemini_key()

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        result_text = response.text.strip()

    except Exception as exc:
        logger.error(f"analyze: Gemini API call failed: {exc}")
        print(f"[ERROR] AI analysis failed: {exc}")
        return

    print("[INFO] Analysis completed\n")

    # --- console output ---
    print("=" * 40)
    print("  AI Insight Analysis Results")
    print("=" * 40)
    print(result_text)
    print("=" * 40)

    # --- persist to insights table ---
    analyzed_at = datetime.now(timezone.utc).isoformat()
    insight_id = save_insight(
        analyzed_at=analyzed_at,
        article_count=total,
        result_text=result_text,
        category=getattr(args, "category", None),
        date_from=getattr(args, "date_from", None),
        date_to=getattr(args, "date_to", None),
    )

    logger.info(
        f"analyze finished: insight saved (id={insight_id}), "
        f"category={getattr(args, 'category', None)}, "
        f"date_from={getattr(args, 'date_from', None)}, "
        f"date_to={getattr(args, 'date_to', None)}, "
        f"articles={total}."
    )
    print(f"\n[INFO] Analysis results have been saved. (insight id={insight_id})")
