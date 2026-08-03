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
    ├── get_clean_news()
    └── query_news()

"""

import json
import sqlite3
from pathlib import Path

from .config import CONFIG


DATABASE_PATH = Path(CONFIG["database"]["path"])


def get_connection():
    """Create and return a SQLite database connection."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)     # creates the database file if it does not exist
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    """Create database tables if they do not exist."""

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
        connection.commit()


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