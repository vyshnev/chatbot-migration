"""
core/database.py
----------------
PostgreSQL connection factory and business table migrations.

This is the single place that knows how to connect to the database and
ensure the schema is correct. All other modules receive a connection via
dependency injection — they never import from this file directly.
"""

import psycopg
from core.config import DATABASE_URL


def get_connection() -> psycopg.Connection:
    """Open and return a new PostgreSQL connection."""
    return psycopg.connect(DATABASE_URL)


def run_migrations(conn: psycopg.Connection) -> None:
    """
    Create business tables and run any pending schema migrations.
    Safe to call on every startup — all statements are idempotent.
    """
    # thread_metadata: tracks sidebar history, titles, and sort order
    conn.execute("""
        CREATE TABLE IF NOT EXISTS thread_metadata (
            thread_id TEXT PRIMARY KEY,
            title TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # user_memory: long-term facts the AI remembers about the user
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_memory (
            id SERIAL PRIMARY KEY,
            fact TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migration: add last_updated if not present (safe for existing databases)
    conn.execute("""
        ALTER TABLE thread_metadata
        ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """)

    conn.commit()
