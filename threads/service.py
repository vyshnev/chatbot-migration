"""
threads/service.py
------------------
All thread management logic: CRUD on thread_metadata, title generation.

server.py imports exclusively from this module — it no longer imports
anything from langgraph_tool_backend.py except `chatbot` (the compiled graph).

Both the database connection and the LLM are injected at startup via
set_connection() and set_llm(), following the same pattern used in
memory/service.py to avoid circular imports until core/database.py
is extracted in Step 7.
"""

from langchain_openai import ChatOpenAI
from core.logger import get_logger

logger = get_logger(__name__)

_pool = None
_llm: ChatOpenAI | None = None


def set_connection(pool) -> None:
    """Inject the connection pool. Must be called before any function is used."""
    global _pool
    _pool = pool


def set_llm(llm: ChatOpenAI) -> None:
    """Inject the LLM instance used for title generation."""
    global _llm
    _llm = llm


def get_all_threads() -> list[dict]:
    """Return all threads — pinned first, then ordered by most recently updated."""
    with _pool.connection() as conn:
        cursor = conn.execute(
            """SELECT thread_id, title, is_pinned
               FROM thread_metadata
               ORDER BY is_pinned DESC, last_updated DESC"""
        )
        return [
            {"id": row[0], "title": row[1], "is_pinned": row[2]}
            for row in cursor.fetchall()
        ]


def save_title(thread_id: str, title: str) -> None:
    """Upsert a thread title and refresh the last_updated timestamp."""
    try:
        with _pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO thread_metadata (thread_id, title, last_updated)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (thread_id) DO UPDATE SET
                    title=EXCLUDED.title,
                    last_updated=CURRENT_TIMESTAMP
                """,
                (thread_id, title),
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Error saving title: {e}")


def update_timestamp(thread_id: str) -> None:
    """Ensure a thread exists in metadata and refresh its timestamp."""
    try:
        with _pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO thread_metadata (thread_id, title, last_updated)
                VALUES (%s, 'New Chat', CURRENT_TIMESTAMP)
                ON CONFLICT (thread_id) DO UPDATE SET
                    last_updated=CURRENT_TIMESTAMP
                """,
                (thread_id,),
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Error updating timestamp: {e}")


def pin_thread(thread_id: str, pinned: bool) -> bool:
    """Set or clear the pinned flag for a thread."""
    try:
        with _pool.connection() as conn:
            conn.execute(
                "UPDATE thread_metadata SET is_pinned = %s WHERE thread_id = %s",
                (pinned, thread_id),
            )
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error pinning thread {thread_id}: {e}")
        return False


def rename_thread(thread_id: str, title: str) -> bool:
    """Update the title of a thread."""
    try:
        with _pool.connection() as conn:
            conn.execute(
                "UPDATE thread_metadata SET title = %s WHERE thread_id = %s",
                (title, thread_id),
            )
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error renaming thread {thread_id}: {e}")
        return False


def generate_title(message_content: str) -> str:
    """Use the LLM to produce a concise 1-4 word title for a conversation."""
    try:
        prompt = (
            f"Summarize this message into a concise 1-4 word title. "
            f"Do not use quotes. Message: {message_content}"
        )
        response = _llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        logger.error(f"Error generating title: {e}")
        return "New Conversation"


def delete_thread(thread_id: str) -> bool:
    """Delete a thread and all its checkpointed state from the database."""
    try:
        with _pool.connection() as conn:
            conn.execute("DELETE FROM thread_metadata WHERE thread_id = %s", (thread_id,))
            conn.execute("DELETE FROM checkpoints WHERE thread_id = %s", (thread_id,))
            conn.execute("DELETE FROM checkpoint_writes WHERE thread_id = %s", (thread_id,))
            conn.execute("DELETE FROM checkpoint_blobs WHERE thread_id = %s", (thread_id,))
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error deleting thread: {e}")
        return False
