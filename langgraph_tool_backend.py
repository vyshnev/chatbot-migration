"""
langgraph_tool_backend.py
--------------------------
Application startup and dependency wiring.

This file is now a thin orchestrator. Its only responsibilities are:
  1. Connect to the database and run schema migrations.
  2. Inject the connection into every service that needs it.
  3. Compile the LangGraph agent with the checkpointer.

No business logic lives here. It is imported by server.py solely to trigger
this startup sequence and to expose `chatbot` for the chat endpoint.
"""

import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

from core.config import DB_PATH
import memory.service as memory_service
import tools.memory_tools as memory_tools
import threads.service as threads_service
from agent.graph import llm, init_graph

# ---------------------------------------------------------------------------
# 1. Database — connect and run migrations
# ---------------------------------------------------------------------------
conn = sqlite3.connect(database=DB_PATH, check_same_thread=False)

conn.execute("""
    CREATE TABLE IF NOT EXISTS thread_metadata (
        thread_id TEXT PRIMARY KEY,
        title TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

conn.execute("""
    CREATE TABLE IF NOT EXISTS user_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fact TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Migration: add last_updated column to existing databases
try:
    conn.execute(
        "ALTER TABLE thread_metadata ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    )
except sqlite3.OperationalError:
    pass  # Column already exists

# Backfill: ensure all checkpointed threads appear in thread_metadata
conn.execute("""
    INSERT OR IGNORE INTO thread_metadata (thread_id, title, last_updated)
    SELECT DISTINCT thread_id, 'New Chat', CURRENT_TIMESTAMP FROM checkpoints
""")
conn.commit()

# ---------------------------------------------------------------------------
# 2. Dependency injection
# ---------------------------------------------------------------------------
memory_service.set_connection(conn)
memory_tools.set_connection(conn)
threads_service.set_connection(conn)
threads_service.set_llm(llm)

# ---------------------------------------------------------------------------
# 3. Compile agent graph
# ---------------------------------------------------------------------------
checkpointer = SqliteSaver(conn=conn)
chatbot = init_graph(checkpointer)