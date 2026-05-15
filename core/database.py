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
from core.logger import get_logger

logger = get_logger(__name__)


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

        # ── Core tables ────────────────────────────────────────────────────
        logger.info("Migration: ensuring core tables exist")

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

        # ── Incremental column migrations ──────────────────────────────────
        logger.info("Migration: applying incremental column patches")

        conn.execute("""
            ALTER TABLE thread_metadata
            ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """)

        conn.execute("""
            ALTER TABLE thread_metadata
            ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE
        """)

        # ── RAG: pgvector extension + document_chunks table ────────────────
        # CREATE EXTENSION requires superuser on self-hosted Postgres.
        # On Supabase the vector extension is pre-enabled; this is a no-op.
        # Wrapped in try/except so a permissions failure degrades gracefully
        # (basic chat still works) rather than crashing the server.
        try:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id          UUID PRIMARY KEY,
                    thread_id   TEXT,
                    source_type VARCHAR(50) NOT NULL,
                    content     TEXT NOT NULL,
                    metadata    JSONB,
                    embedding   vector(1536),
                    created_at  TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            # Fast URL lookup for deduplication — used on every read_webpage call
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_document_chunks_url
                ON document_chunks ((metadata->>'url'))
            """)
            # HNSW index for sub-millisecond approximate cosine similarity search
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
                ON document_chunks USING hnsw (embedding vector_cosine_ops)
            """)
            logger.info("Migration: pgvector + document_chunks ready")
        except Exception as e:
            logger.warning(
                f"Migration: pgvector setup skipped — {e}. "
                "RAG/web-scrape features will be unavailable. "
                "To fix: run  CREATE EXTENSION vector;  on your Postgres instance "
                "with a superuser account, then restart the server."
            )
            conn.rollback()

        conn.commit()
    logger.info("Migration: all migrations complete")
