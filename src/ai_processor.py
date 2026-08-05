"""
ai_processor.py: Summarize and analyze clean news articles using the Gemini AI model.

Pipeline contract (enforced here):
  summarize / analyze may ONLY read from clean_news.
  If no clean data is found, both commands abort with a clear error message.
  Users must run 'python main.py clean' before these commands.

Functions:
    summarize_news(args) — send clean article content to AI and save summary
    analyze_news(args)   — batch-analyze clean articles and return trend insights
"""

import logging
from datetime import datetime, timezone
from google import genai

from .config import GEMINI_MODEL, validate_gemini_key
from .database import get_clean_news, update_clean_status, save_insight

logger = logging.getLogger(__name__)


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

    Reads only from clean_news. Aborts with a clear message if clean_news
    is empty (i.e. 'python main.py clean' has not been run yet).

    Per §4.4:
      - Supports --all, --id, --unsummarized selection options.
      - Already-summarized articles are skipped by default (via status filter).
      - On API failure: logs the error and skips the article.
      - On success: saves the summary and flips status to 'summarized'.
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
    print(f"[INFO] Summary target: {total} articles")

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
            "Please, summarize the following news article in 3~5 sentences. "
            "Include only the key facts and provide the summary without additional comments.\n\n"
            f"Title: {title}\n\n"
            f"Content:\n{text}"
        )

        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            summary = response.text.strip()
            update_clean_status(article_id, summary, status="summarized")

            original_len = len(text)
            summary_len = len(summary)
            print(f"[INFO] [{i}/{total}] ID={article_id} summary completed ({original_len} chars → {summary_len} chars)")
            logger.info(
                f"[{i}/{total}] ID={article_id} summarized "
                f"({original_len} chars → {summary_len} chars): {title[:60]}"
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

    try:
        client = _get_client()
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
