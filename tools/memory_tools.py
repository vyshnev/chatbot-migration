"""
tools/memory_tools.py
---------------------
LangChain @tool wrappers for the user's long-term memory.

These tools are thin wrappers only — all SQL logic lives in memory/service.py.
The connection is initialised via set_connection(), called once from
langgraph_tool_backend.py after the database is ready.
"""

from langchain_core.tools import tool
import memory.service as memory_service


def set_connection(conn) -> None:
    """Propagate the database connection through to memory/service.py."""
    memory_service.set_connection(conn)


@tool
def save_memory(fact: str) -> str:
    """
    Save an important fact or preference about the user to long-term memory.
    CRITICAL WARNING: DO NOT use this tool if the user is changing or updating a fact you already know. You MUST use `update_memory` instead to prevent duplicates.
    CRITICAL: Always save ONE discrete, atomic piece of information per call. Do not save compound sentences.
    If you need to save multiple facts, call this tool multiple times in parallel.
    """
    return memory_service.save_fact(fact)


@tool
def forget_memory(memory_id: int) -> str:
    """
    Delete a specific fact from long-term memory using its ID.
    Use this when the user asks you to forget something or when a fact is no longer true.
    """
    return memory_service.forget_fact(memory_id)


@tool
def update_memory(old_memory_id: int, new_fact: str) -> str:
    """
    Update an existing fact in long-term memory.
    Use this when the user's new message updates or contradicts an existing memory.
    The `old_memory_id` MUST be the exact integer found inside the `[ID: X]` tag of the existing memory you are replacing.
    """
    return memory_service.update_fact(old_memory_id, new_fact)
