"""
langgraph_tool_backend.py
--------------------------
Application startup and dependency wiring.

Responsibilities:
  1. Open two PostgreSQL connection pools (business logic + LangGraph checkpointer).
  2. Run business table migrations via core/database.py.
  3. Inject pools into every service that needs them.
  4. Compile the LangGraph agent with the PostgresSaver checkpointer.
"""

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

from core.config import DATABASE_URL
from core.database import create_pool, run_migrations
import memory.service as memory_service
import tools.memory_tools as memory_tools
import threads.service as threads_service
from agent.graph import llm, init_graph

# ---------------------------------------------------------------------------
# 1. Database — business pool + migrations
# ---------------------------------------------------------------------------
# Two separate pools avoid transaction conflicts between business logic
# (memory, threads) and LangGraph's internal checkpoint management.
business_pool = create_pool()
run_migrations(business_pool)

# ---------------------------------------------------------------------------
# 2. Dependency injection
# ---------------------------------------------------------------------------
memory_service.set_connection(business_pool)
memory_tools.set_connection(business_pool)
threads_service.set_connection(business_pool)
threads_service.set_llm(llm)

# ---------------------------------------------------------------------------
# 3. Compile agent graph with PostgresSaver (pool-backed)
# ---------------------------------------------------------------------------
# Using a ConnectionPool instead of a bare psycopg.connect() means the
# checkpointer will automatically recover from database restarts without
# requiring a full server restart.
lg_pool = ConnectionPool(
    DATABASE_URL,
    min_size=1,
    max_size=5,
    open=True,
    kwargs={"autocommit": True},
)
checkpointer = PostgresSaver(lg_pool)
checkpointer.setup()   # Creates LangGraph tables: checkpoints, checkpoint_writes, checkpoint_blobs
chatbot = init_graph(checkpointer)