"""
Save and retrieve data
creating the SQLite database and tables
inserting raw news records
retrieving raw records for the clean step
inserting/updating clean records
querying data later for summarization, analysis, reports, and export

database.py
    ├── initialize_database()
    ├── save_raw_news()
    ├── get_raw_news()
    ├── save_clean_news()
    ├── update_clean_status()
    ├── save_insight()
    ├── get_clean_news()
    └── query_news()

"""

import json
import logging
import sqlite3
from pathlib import Path

from .config import CONFIG

logger = logging.getLogger(__name__)


DATABASE_PATH = Path(CONFIG["database"]["path"])


def get_connection():
    """Create and return a SQLite database connection."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)     # creates the database file if it does not exist
    connection.row_factory = sqlite3.Row            # allow to access columns by name. row["title"] instead of row[1]
    return connection


def initialize_database():
    """Create database tables if they do not exist. (like preparing an empty warehouse before storing products)"""
#    logger.debug(f"Initializing database at: {DATABASE_PATH}")
    # opens the database safely and when this block finishes, the connection is automatically closed.
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS raw_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                title TEXT,
                url TEXT,
                source TEXT,
                published_at TEXT,
                snippet TEXT,
                content TEXT,
                category TEXT,

                unique_guid TEXT,
                method TEXT,
                query TEXT,
                collected_at TEXT,

                raw_data TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS clean_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                title TEXT NOT NULL,
                url TEXT,
                source TEXT,
                published_at TEXT,
                snippet TEXT,
                content TEXT,
                category TEXT,

                unique_guid TEXT UNIQUE,
                method TEXT,
                query TEXT,
                collected_at TEXT,

                summary TEXT,
                sentiment TEXT,
                status TEXT DEFAULT 'unsummarized'
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                analyzed_at TEXT NOT NULL,
                category TEXT,
                date_from TEXT,
                date_to TEXT,
                article_count INTEGER,

                result_text TEXT NOT NULL
            )
            """
        )
        connection.commit()

        # Todo: check why this is needed.
        # --- migrate: add sentiment column if missing (for existing DBs) ---
        cols = {
            row[1]
            for row in connection.execute("PRAGMA table_info(clean_news)").fetchall()
        }
        if "sentiment" not in cols:
            connection.execute("ALTER TABLE clean_news ADD COLUMN sentiment TEXT")
            connection.commit()
            logger.info("Migration: added 'sentiment' column to clean_news.")
#    logger.info("Database tables initialized successfully.")


def save_raw_news(records):
    """Save collected news records to the raw_news table (plain INSERT, no deduplication).

    Raw storage is an unfiltered archive. Deduplication is handled later
    by save_clean_news() during the 'clean' step.
    """
    with get_connection() as connection:
        for record in records:
            raw_value = record["raw"]
            if not isinstance(raw_value, str):
                raw_value = json.dumps(raw_value, ensure_ascii=False)

            connection.execute(
                """
                INSERT INTO raw_news (
                    title,
                    url,
                    source,
                    published_at,
                    snippet,
                    content,
                    category,
                    unique_guid,
                    method,
                    query,
                    collected_at,
                    raw_data
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["title"],
                    record["url"],
                    record["source"],
                    record["published_at"],
                    record["snippet"],
                    record["content"],
                    record.get("category", ""),
                    record["unique_guid"],
                    record["method"],
                    record["query"],
                    record["collected_at"],
                    raw_value,
                )
            )
        connection.commit()
    logger.info(f"Saved {len(records)} raw news record(s) to database.")


def save_clean_news(records, policy="skip"):
    """Promote cleaned records into the clean_news table.

    Args:
        records: List of cleaned record dicts (same schema as raw, but
                 with normalised fields).
        policy:  'skip'   – INSERT OR IGNORE: keep existing row untouched.
                 'upsert' – INSERT OR REPLACE: overwrite existing row.
    """
    if policy == "upsert":
        insert_sql = "INSERT OR REPLACE"
    else:  # default: skip
        insert_sql = "INSERT OR IGNORE"    # if duplicate GUID exists, SQLite ignores it

    with get_connection() as connection:
        for record in records:
            connection.execute(
                f"""
                {insert_sql} INTO clean_news (
                    title,
                    url,
                    source,
                    published_at,
                    snippet,
                    content,
                    category,
                    unique_guid,
                    method,
                    query,
                    collected_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["title"],
                    record["url"],
                    record["source"],
                    record["published_at"],
                    record["snippet"],
                    record["content"],
                    record.get("category", ""),
                    record["unique_guid"],
                    record["method"],
                    record["query"],
                    record["collected_at"],
                )
            )
        connection.commit()
#    logger.info(f"Promoted {len(records)} clean news record(s) to database (policy='{policy}').")


def update_clean_status(article_id, summary, status="summarized", sentiment=None):
    """Update the summary text, sentiment, and status of a clean_news record after AI summarization.

    Args:
        article_id: The id of the clean_news row to update.
        summary:    The AI-generated summary text.
        status:     New status value; defaults to 'summarized'.
        sentiment:  Sentiment classification ('positive', 'neutral', or 'negative').
    """
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE clean_news
            SET summary = ?, sentiment = ?, status = ?
            WHERE id = ?
            """,
            (summary, sentiment, status, article_id),
        )
        connection.commit()
#    logger.debug(f"Updated article id={article_id} status to '{status}', sentiment='{sentiment}'.")


def save_insight(analyzed_at, article_count, result_text,
                 category=None, date_from=None, date_to=None):
    """Persist an AI insight-analysis result to the insights table.

    Args:
        analyzed_at:   ISO-format timestamp of when the analysis ran.
        article_count: Number of articles that were analysed.
        result_text:   The full AI-generated analysis text.
        category:      Category filter used for this analysis (or None).
        date_from:     Start of the date range filter (or None).
        date_to:       End of the date range filter (or None).

    Returns:
        The row id of the newly inserted insight record.
    """
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO insights (
                analyzed_at,
                category,
                date_from,
                date_to,
                article_count,
                result_text
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (analyzed_at, category, date_from, date_to, article_count, result_text),
        )
        connection.commit()
        insight_id = cursor.lastrowid   # returns the ID of the newly inserted insight
    return insight_id


def get_raw_news():
    """Return all records from raw_news as a list of dicts."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM raw_news ORDER BY id"
        ).fetchall()        # get all rows
        return [dict(row) for row in rows]      # converts sqlite3.Row into a normal Python dictionary


def get_clean_news(*, article_id=None, status=None, category=None,
                   date_from=None, date_to=None, limit=None):
    """Query clean_news with optional filters and return a list of dicts.

    Args:
        article_id: Return only the record with this ID.
        status:     Filter by 'summarized' or 'unsummarized'. None = all.
        category:   Filter by category string.
        date_from:  Include records where published_at >= date_from (YYYY-MM-DD).
        date_to:    Include records where published_at <= date_to (YYYY-MM-DD).
        limit:      Maximum number of records to return.
    """
    conditions = []     # collect WHERE condition
    params = []         # collect corresponding values using ? placeholder to avoid SQL injection

    if article_id is not None:
        conditions.append("id = ?")
        params.append(article_id)
    if status:
        conditions.append("status = ?")
        params.append(status)
    if category:
        conditions.append("category = ?")
        params.append(category)
    if date_from:
        conditions.append("published_at >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("published_at <= ?")
        params.append(date_to)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else ""

    sql = f"SELECT * FROM clean_news {where_clause} ORDER BY published_at DESC {limit_clause}"

    with get_connection() as connection:
        rows = connection.execute(sql, params).fetchall()
        return [dict(row) for row in rows]


# fetches the most recent AI analysis result
def get_latest_insight():
    """Return the most recently saved insight record as a dict, or None."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM insights ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


# single-pass aggregation of all stats needed
def get_report_stats(category=None, date_from=None, date_to=None):
    """Return a dict of aggregated statistics used by the report and visualizer.

    Keys returned
    -------------
    total_raw        : int   — total rows in raw_news
    total_clean      : int   — clean_news rows matching filters
    total_summarized : int   — clean_news rows matching filters with status='summarized'
    total_missing_content : int — clean_news rows matching filters where content IS NULL or ''
    category_counts  : list of (category, count)  — clean_news grouped by category matching filters
    daily_counts     : list of (date, count)      — clean_news grouped by published date matching filters
    top_sources      : list of (source, count)    — Top-10 sources in clean_news matching filters
    sentiment_counts : list of (sentiment, count) — clean_news grouped by sentiment matching filters
    """
    conditions = []
    params = []

    if category:
        conditions.append("category = ?")
        params.append(category)
        raw_category_cond = "category = ?"
    else:
        raw_category_cond = None

    if date_from:
        conditions.append("published_at >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("published_at <= ?")
        params.append(date_to)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Build WHERE clause for raw_news (using published_at or created_at if needed, but here raw_news has published_at and category)
    raw_conditions = []
    raw_params = []

    if category:
        raw_conditions.append("category = ?")
        raw_params.append(category)    
    if date_from:
        raw_conditions.append("published_at >= ?")
        raw_params.append(date_from)
    if date_to:
        raw_conditions.append("published_at <= ?")
        raw_params.append(date_to)

    raw_where_clause = f"WHERE {' AND '.join(raw_conditions)}" if raw_conditions else ""

    with get_connection() as connection:
        total_raw = connection.execute(
            f"SELECT COUNT(*) FROM raw_news {raw_where_clause}", raw_params
        ).fetchone()[0]

        total_clean = connection.execute(
            f"SELECT COUNT(*) FROM clean_news {where_clause}", params
        ).fetchone()[0]

        sum_conds = list(conditions) + ["status = 'summarized'"]
        sum_where = f"WHERE {' AND '.join(sum_conds)}"
        total_summarized = connection.execute(
            f"SELECT COUNT(*) FROM clean_news {sum_where}", params
        ).fetchone()[0]

        missing_conds = list(conditions) + ["(content IS NULL OR content = '')"]
        missing_where = f"WHERE {' AND '.join(missing_conds)}"
        total_missing_content = connection.execute(
            f"SELECT COUNT(*) FROM clean_news {missing_where}", params
        ).fetchone()[0]

        category_rows = connection.execute(
            f"""
            SELECT COALESCE(NULLIF(category,''), '(none)') AS cat, COUNT(*) AS cnt
            FROM clean_news
            {where_clause}
            GROUP BY cat
            ORDER BY cnt DESC
            """,
            params
        ).fetchall()

        daily_conds = list(conditions) + ["published_at IS NOT NULL", "published_at != ''"]
        daily_where = f"WHERE {' AND '.join(daily_conds)}"
        daily_rows = connection.execute(
            f"""
            SELECT SUBSTR(published_at, 1, 10) AS day, COUNT(*) AS cnt
            FROM clean_news
            {daily_where}
            GROUP BY day
            ORDER BY day ASC
            """,
            params
        ).fetchall()

        source_rows = connection.execute(
            f"""
            SELECT COALESCE(NULLIF(source,''), '(unknown)') AS src, COUNT(*) AS cnt
            FROM clean_news
            {where_clause}
            GROUP BY src
            ORDER BY cnt DESC
            LIMIT 10
            """,
            params
        ).fetchall()

        sentiment_rows = connection.execute(
            f"""
            SELECT COALESCE(NULLIF(sentiment,''), '(none)') AS sent, COUNT(*) AS cnt
            FROM clean_news
            {where_clause}
            GROUP BY sent
            ORDER BY cnt DESC
            """,
            params
        ).fetchall()

    return {
        "total_raw": total_raw,
        "total_clean": total_clean,
        "total_summarized": total_summarized,
        "total_missing_content": total_missing_content,
        "category_counts": [(r[0], r[1]) for r in category_rows],
        "daily_counts": [(r[0], r[1]) for r in daily_rows],
        "top_sources": [(r[0], r[1]) for r in source_rows],
        "sentiment_counts": [(r[0], r[1]) for r in sentiment_rows],
    }


def get_sentiment_stats(category=None, date_from=None, date_to=None):
    """Return aggregated sentiment statistics for visualization.

    Returns:
        dict containing:
            - sentiment_over_time: list of dicts with 'date' and counts for 'positive', 'neutral', 'negative', 'none' (or unclassified)
            - sentiment_by_category: list of dicts with 'category' and counts for 'positive', 'neutral', 'negative', 'none'
    """
    conditions = []
    params = []

    if category:
        conditions.append("category = ?")
        params.append(category)
    if date_from:
        conditions.append("published_at >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("published_at <= ?")
        params.append(date_to)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    time_conds = list(conditions) + ["published_at IS NOT NULL", "published_at != ''"]
    time_where = f"WHERE {' AND '.join(time_conds)}"

    with get_connection() as connection:
        # Sentiment over time grouped by date (SUBSTR(published_at, 1, 10))
        time_rows = connection.execute(
            f"""
            SELECT SUBSTR(published_at, 1, 10) AS day,
                   LOWER(COALESCE(NULLIF(sentiment, ''), 'none')) AS sent,
                   COUNT(*) AS cnt
            FROM clean_news
            {time_where}
            GROUP BY day, sent
            ORDER BY day ASC
            """,
            params
        ).fetchall()

        # Sentiment by category grouped by category
        cat_rows = connection.execute(
            f"""
            SELECT COALESCE(NULLIF(category, ''), '(none)') AS cat,
                   LOWER(COALESCE(NULLIF(sentiment, ''), 'none')) AS sent,
                   COUNT(*) AS cnt
            FROM clean_news
            {where_clause}
            GROUP BY cat, sent
            ORDER BY cat ASC
            """,
            params
        ).fetchall()

    # Structure sentiment_over_time
    # { date: { 'positive': int, 'neutral': int, 'negative': int, 'none': int } }
    time_dict = {}
    for r in time_rows:
        day, sent, cnt = r[0], r[1], r[2]
        if day not in time_dict:
            time_dict[day] = {"positive": 0, "neutral": 0, "negative": 0, "none": 0}
        if sent in time_dict[day]:
            time_dict[day][sent] += cnt
        else:
            time_dict[day]["none"] += cnt

    sentiment_over_time = [
        {"date": day, **counts} for day, counts in time_dict.items()
    ]

    # Structure sentiment_by_category
    cat_dict = {}
    for r in cat_rows:
        cat, sent, cnt = r[0], r[1], r[2]
        if cat not in cat_dict:
            cat_dict[cat] = {"positive": 0, "neutral": 0, "negative": 0, "none": 0}
        if sent in cat_dict[cat]:
            cat_dict[cat][sent] += cnt
        else:
            cat_dict[cat]["none"] += cnt

    sentiment_by_category = [
        {"category": cat, **counts} for cat, counts in cat_dict.items()
    ]

    return {
        "sentiment_over_time": sentiment_over_time,
        "sentiment_by_category": sentiment_by_category,
    }