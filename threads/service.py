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

_conn = None
_llm: ChatOpenAI | None = None


def set_connection(conn) -> None:
    """Inject the shared database connection. Must be called before any function is used."""
    global _conn
    _conn = conn


def set_llm(llm: ChatOpenAI) -> None:
    """Inject the LLM instance used for title generation."""
    global _llm
    _llm = llm


def get_all_threads() -> list[dict]:
    """Return all threads ordered by most recently updated."""
    cursor = _conn.execute(
        "SELECT thread_id, title FROM thread_metadata ORDER BY last_updated DESC"
    )
    return [{"id": row[0], "title": row[1]} for row in cursor.fetchall()]


def save_title(thread_id: str, title: str) -> None:
    """Upsert a thread title and refresh the last_updated timestamp."""
    try:
        _conn.execute(
            """
            INSERT INTO thread_metadata (thread_id, title, last_updated)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (thread_id) DO UPDATE SET
                title=EXCLUDED.title,
                last_updated=CURRENT_TIMESTAMP
            """,
            (thread_id, title),
        )
        _conn.commit()
    except Exception as e:
        print(f"Error saving title: {e}")


def update_timestamp(thread_id: str) -> None:
    """Ensure a thread exists in metadata and refresh its timestamp."""
    try:
        _conn.execute(
            """
            INSERT INTO thread_metadata (thread_id, title, last_updated)
            VALUES (%s, 'New Chat', CURRENT_TIMESTAMP)
            ON CONFLICT (thread_id) DO UPDATE SET
                last_updated=CURRENT_TIMESTAMP
            """,
            (thread_id,),
        )
        _conn.commit()
    except Exception as e:
        print(f"Error updating timestamp: {e}")


def generate_title(message_content: str) -> str:
    """Use the LLM to produce a concise 3-5 word title for a conversation."""
    try:
        prompt = (
            f"Summarize this message into a concise 3-5 word title. "
            f"Do not use quotes. Message: {message_content}"
        )
        response = _llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"Error generating title: {e}")
        return "New Conversation"


def delete_thread(thread_id: str) -> bool:
    """Delete a thread and all its checkpointed state from the database."""
    try:
        _conn.execute("DELETE FROM thread_metadata WHERE thread_id = %s", (thread_id,))
        _conn.execute("DELETE FROM checkpoints WHERE thread_id = %s", (thread_id,))
        _conn.execute("DELETE FROM checkpoint_writes WHERE thread_id = %s", (thread_id,))
        _conn.execute("DELETE FROM checkpoint_blobs WHERE thread_id = %s", (thread_id,))
        _conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting thread: {e}")
        return False
