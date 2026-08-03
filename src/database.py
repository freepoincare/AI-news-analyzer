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

                unique_guid TEXT,
                method TEXT,
                query TEXT,
                collected_at TEXT,

                raw_data TEXT NOT NULL
            )
            """
        )
        connection.commit()


def save_raw_news(records):
    """Save collected news records to the raw_news table."""

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
                    unique_guid,
                    method,
                    query,
                    collected_at,
                    raw_data
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
                )
                """,
                (
                    record["title"],
                    record["url"],
                    record["source"],
                    record["published_at"],
                    record["snippet"],
                    record["content"],
                    record["unique_guid"],
                    record["method"],
                    record["query"],
                    record["collected_at"],
                    raw_value,
                )
            )
        connection.commit()