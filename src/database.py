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
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    """Create database tables if they do not exist."""
#    logger.debug(f"Initializing database at: {DATABASE_PATH}")
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
        insert_sql = "INSERT OR IGNORE"

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


def update_clean_status(article_id, summary, status="summarized"):
    """Update the summary text and status of a clean_news record after AI summarization.

    Args:
        article_id: The id of the clean_news row to update.
        summary:    The AI-generated summary text.
        status:     New status value; defaults to 'summarized'.
    """
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE clean_news
            SET summary = ?, status = ?
            WHERE id = ?
            """,
            (summary, status, article_id),
        )
        connection.commit()
#    logger.debug(f"Updated article id={article_id} status to '{status}'.")


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
        insight_id = cursor.lastrowid
#    logger.info(f"Saved AI insight record (id={insight_id}).")
    return insight_id


def get_raw_news():
    """Return all records from raw_news as a list of dicts."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM raw_news ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]


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
    conditions = []
    params = []

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
def get_report_stats():
    """Return a dict of aggregated statistics used by the report and visualizer.

    Keys returned
    -------------
    total_raw        : int   — total rows in raw_news
    total_clean      : int   — total rows in clean_news
    total_summarized : int   — clean_news rows with status='summarized'
    total_missing_content : int — clean_news rows where content IS NULL or ''
    category_counts  : list of (category, count) — clean_news grouped by category
    daily_counts     : list of (date, count)      — clean_news grouped by published date
    top_sources      : list of (source, count)    — Top-10 sources in clean_news
    """
    with get_connection() as connection:
        total_raw = connection.execute(
            "SELECT COUNT(*) FROM raw_news"
        ).fetchone()[0]

        total_clean = connection.execute(
            "SELECT COUNT(*) FROM clean_news"
        ).fetchone()[0]

        total_summarized = connection.execute(
            "SELECT COUNT(*) FROM clean_news WHERE status = 'summarized'"
        ).fetchone()[0]

        total_missing_content = connection.execute(
            "SELECT COUNT(*) FROM clean_news WHERE content IS NULL OR content = ''"
        ).fetchone()[0]

        category_rows = connection.execute(
            """
            SELECT COALESCE(NULLIF(category,''), '(none)') AS cat, COUNT(*) AS cnt
            FROM clean_news
            GROUP BY cat
            ORDER BY cnt DESC
            """
        ).fetchall()

        daily_rows = connection.execute(
            """
            SELECT SUBSTR(published_at, 1, 10) AS day, COUNT(*) AS cnt
            FROM clean_news
            WHERE published_at IS NOT NULL AND published_at != ''
            GROUP BY day
            ORDER BY day ASC
            """
        ).fetchall()

        source_rows = connection.execute(
            """
            SELECT COALESCE(NULLIF(source,''), '(unknown)') AS src, COUNT(*) AS cnt
            FROM clean_news
            GROUP BY src
            ORDER BY cnt DESC
            LIMIT 10
            """
        ).fetchall()

    return {
        "total_raw": total_raw,
        "total_clean": total_clean,
        "total_summarized": total_summarized,
        "total_missing_content": total_missing_content,
        "category_counts": [(r[0], r[1]) for r in category_rows],
        "daily_counts": [(r[0], r[1]) for r in daily_rows],
        "top_sources": [(r[0], r[1]) for r in source_rows],
    }