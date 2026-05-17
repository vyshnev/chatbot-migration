"""
langgraph_tool_backend.py
-------------------------
Application startup and dependency wiring.

Importing this module is intentionally side-effect free. Call init_backend()
from FastAPI lifespan startup to open pools, run migrations, inject service
dependencies, and compile the LangGraph agent.
"""

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

from core.config import DATABASE_URL
from core.database import create_pool, run_migrations
import memory.service as memory_service
import tools.memory_tools as memory_tools
import threads.service as threads_service
import tools.scraper as scraper_tools
import tools.document_rag as document_rag
from agent.graph import llm, init_graph

business_pool = None
lg_pool = None
checkpointer = None
chatbot = None
vector_ready = False


def init_backend() -> None:
    """Open pools, run migrations, inject dependencies, and compile the graph."""
    global business_pool, lg_pool, checkpointer, chatbot, vector_ready

    if chatbot is not None:
        return

    # Keep business queries and LangGraph checkpoint writes on separate pools.
    business_pool = create_pool()
    vector_ready = run_migrations(business_pool)

    memory_service.set_connection(business_pool)
    memory_tools.set_connection(business_pool)
    threads_service.set_connection(business_pool)
    threads_service.set_llm(llm)
    scraper_tools.set_connection(business_pool)
    scraper_tools.set_vector_available(vector_ready)
    document_rag.set_connection(business_pool)
    document_rag.set_vector_available(vector_ready)

    lg_pool = ConnectionPool(
        DATABASE_URL,
        min_size=1,
        max_size=5,
        open=True,
        kwargs={"autocommit": True},
    )
    checkpointer = PostgresSaver(lg_pool)
    checkpointer.setup()
    chatbot = init_graph(checkpointer)


def shutdown_backend() -> None:
    """Close database pools if they were opened."""
    global business_pool, lg_pool, checkpointer, chatbot, vector_ready

    if business_pool is not None:
        business_pool.close()
    if lg_pool is not None:
        lg_pool.close()

    business_pool = None
    lg_pool = None
    checkpointer = None
    chatbot = None
    vector_ready = False
