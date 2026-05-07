"""
memory/service.py
-----------------
Pure SQL functions for reading and writing the user's long-term memory table.

This module is intentionally free of LangChain / LangGraph imports so that:
  - It can be unit-tested without booting the LLM or the graph.
  - A future REST endpoint (/memories) can call it directly.
  - tools/memory_tools.py remains a thin @tool wrapper with no raw SQL.

The connection is injected via set_connection() once at startup, using the
same pattern as tools/memory_tools.py to avoid circular imports until
core/database.py is extracted in Step 7.
"""

_conn = None


def set_connection(conn) -> None:
    """Inject the shared database connection. Must be called before any function is used."""
    global _conn
    _conn = conn


def get_all_memories() -> str:
    """
    Return all stored memory facts as a formatted string for injection into the system prompt.
    Returns an empty string if no memories exist.
    """
    try:
        cursor = _conn.execute(
            "SELECT id, fact, date(created_at) FROM user_memory ORDER BY created_at ASC"
        )
        facts = [
            f"- [ID: {row[0]}] {row[1]} (Saved: {row[2]})"
            for row in cursor.fetchall()
        ]
        if facts:
            return "\n".join(facts)
    except Exception as e:
        print(f"Error retrieving memories: {e}")
    return ""


def save_fact(fact: str) -> str:
    """Insert a new fact into user_memory. Returns a status string."""
    try:
        cursor = _conn.execute(
            "INSERT OR IGNORE INTO user_memory (fact) VALUES (?)", (fact,)
        )
        _conn.commit()
        return "Already remembered." if cursor.rowcount == 0 else "Fact remembered."
    except Exception as e:
        return f"Error saving memory: {e}"


def update_fact(memory_id: int, new_fact: str) -> str:
    """Update an existing fact by ID. Returns a status string."""
    try:
        cursor = _conn.execute(
            "UPDATE user_memory SET fact = ?, created_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_fact, memory_id),
        )
        _conn.commit()
        if cursor.rowcount == 0:
            return f"No memory found with ID {memory_id}."
        return "Memory updated successfully."
    except Exception as e:
        return f"Error updating memory: {e}"


def forget_fact(memory_id: int) -> str:
    """Delete a fact by ID. Returns a status string."""
    try:
        cursor = _conn.execute(
            "DELETE FROM user_memory WHERE id = ?", (memory_id,)
        )
        _conn.commit()
        if cursor.rowcount == 0:
            return f"No memory found with ID {memory_id}."
        return "Memory forgotten."
    except Exception as e:
        return f"Error forgetting memory: {e}"
