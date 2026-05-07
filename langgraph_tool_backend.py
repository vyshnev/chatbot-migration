"""
langgraph_tool_backend.py
--------------------------
Application startup and dependency wiring.

Responsibilities:
  1. Open two PostgreSQL connections (business logic + LangGraph checkpointer).
  2. Run business table migrations via core/database.py.
  3. Inject connections into every service that needs them.
  4. Compile the LangGraph agent with the PostgresSaver checkpointer.
"""

from langgraph.checkpoint.postgres import PostgresSaver

from core.config import DATABASE_URL
from core.database import get_connection, run_migrations
import memory.service as memory_service
import tools.memory_tools as memory_tools
import threads.service as threads_service
from agent.graph import llm, init_graph

# ---------------------------------------------------------------------------
# 1. Database — business connection + migrations
# ---------------------------------------------------------------------------
# Two separate connections avoid transaction conflicts between business logic
# (memory, threads) and LangGraph's internal checkpoint management.
business_conn = get_connection()
run_migrations(business_conn)

# ---------------------------------------------------------------------------
# 2. Dependency injection
# ---------------------------------------------------------------------------
memory_service.set_connection(business_conn)
memory_tools.set_connection(business_conn)
threads_service.set_connection(business_conn)
threads_service.set_llm(llm)

# ---------------------------------------------------------------------------
# 3. Compile agent graph with PostgresSaver
# ---------------------------------------------------------------------------
# A persistent connection is used (not a context manager) so the checkpointer
# stays alive for the full lifetime of the server process.
import psycopg
lg_conn = psycopg.connect(DATABASE_URL, autocommit=True)
checkpointer = PostgresSaver(lg_conn)
checkpointer.setup()   # Creates LangGraph tables: checkpoints, checkpoint_writes, checkpoint_blobs
chatbot = init_graph(checkpointer)