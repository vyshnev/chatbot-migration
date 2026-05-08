"""
core/database.py
----------------
PostgreSQL connection factory and business table migrations.

This is the single place that knows how to connect to the database and
ensure the schema is correct. All other modules receive a pool via
dependency injection — they never import from this file directly.
"""

import psycopg
from psycopg_pool import ConnectionPool
from core.config import DATABASE_URL


def create_pool(min_size: int = 1, max_size: int = 5) -> ConnectionPool:
    """
    Create and return a connection pool for business table queries.
    The pool automatically recycles stale connections and reconnects on failure,
    preventing the 500 errors that occur when a long-running server's single
    persistent connection goes stale.
    """
    return ConnectionPool(
        DATABASE_URL,
        min_size=min_size,
        max_size=max_size,
        open=True,          # Open the pool immediately at startup
    )


def run_migrations(pool: ConnectionPool) -> None:
    """
    Create business tables and run any pending schema migrations.
    Safe to call on every startup — all statements are idempotent.
    """
    with pool.connection() as conn:
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

