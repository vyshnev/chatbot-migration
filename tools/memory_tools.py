"""
tools/memory_tools.py
---------------------
LangChain tools for reading and writing the user's long-term memory.

Because the database connection (conn) is owned by langgraph_tool_backend.py
until Step 7 (core/database.py), we use a module-level initialiser pattern
to receive the connection without creating a circular import.

Usage (called once from langgraph_tool_backend.py after conn is created):
    import tools.memory_tools as memory_tools
    memory_tools.set_connection(conn)
"""

from langchain_core.tools import tool

_conn = None


def set_connection(conn) -> None:
    """Inject the shared SQLite connection. Must be called before any tool is invoked."""
    global _conn
    _conn = conn


@tool
def save_memory(fact: str) -> str:
    """
    Save an important fact or preference about the user to long-term memory.
    CRITICAL WARNING: DO NOT use this tool if the user is changing or updating a fact you already know. You MUST use `update_memory` instead to prevent duplicates.
    CRITICAL: Always save ONE discrete, atomic piece of information per call. Do not save compound sentences.
    If you need to save multiple facts, call this tool multiple times in parallel.
    """
    try:
        cursor = _conn.execute("INSERT OR IGNORE INTO user_memory (fact) VALUES (?)", (fact,))
        _conn.commit()
        if cursor.rowcount == 0:
            return "Already remembered."
        return "Fact remembered."
    except Exception as e:
        return f"Error saving memory: {e}"


@tool
def forget_memory(memory_id: int) -> str:
    """
    Delete a specific fact from long-term memory using its ID.
    Use this when the user asks you to forget something or when a fact is no longer true.
    """
    try:
        cursor = _conn.execute("DELETE FROM user_memory WHERE id = ?", (memory_id,))
        _conn.commit()
        if cursor.rowcount == 0:
            return f"No memory found with ID {memory_id}."
        return "Memory forgotten."
    except Exception as e:
        return f"Error forgetting memory: {e}"


@tool
def update_memory(old_memory_id: int, new_fact: str) -> str:
    """
    Update an existing fact in long-term memory.
    Use this when the user's new message updates or contradicts an existing memory.
    The `old_memory_id` MUST be the exact integer found inside the `[ID: X]` tag of the existing memory you are replacing.
    """
    try:
        cursor = _conn.execute(
            "UPDATE user_memory SET fact = ?, created_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_fact, old_memory_id),
        )
        _conn.commit()
        if cursor.rowcount == 0:
            return f"No memory found with ID {old_memory_id}."
        return "Memory updated successfully."
    except Exception as e:
        return f"Error updating memory: {e}"
