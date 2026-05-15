"""
agent/graph.py
--------------
LangGraph state definition, node functions, and compiled chatbot graph.

This module owns:
  - ChatState: the typed graph state
  - chat_node: the LLM inference node
  - tool_node: the tool execution node
  - chatbot: the compiled, checkpointed graph (imported by server.py)

The checkpointer (SqliteSaver) is injected at startup via init_graph(),
called from langgraph_tool_backend.py after the database is ready.
"""

from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from core.config import LLM_MODEL
from core.logger import get_logger
from tools.registry import ALL_TOOLS, build_llm_with_tools
import memory.service as memory_service
from agent.prompts import build_system_prompt

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------
# One instance is created here and reused everywhere:
#   - llm_with_tools  → used by chat_node for inference
#   - llm             → exported to threads_service for title generation
llm = ChatOpenAI(streaming=True, model=LLM_MODEL)
llm_with_tools = build_llm_with_tools(llm)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------
def chat_node(state: ChatState):
    """LLM node: injects memories into the system prompt, then invokes the LLM."""
    messages = state["messages"]
    memories = memory_service.get_all_memories()
    system_prompt = build_system_prompt(memories)

    memory_count = len([m for m in memories.split('\n') if m.strip()]) if memories else 0
    logger.debug(f"chat_node: {len(messages)} message(s) in state, {memory_count} memory fact(s) injected")

    messages_to_invoke = [SystemMessage(content=system_prompt)] + messages
    response = llm_with_tools.invoke(messages_to_invoke)
    return {"messages": [response]}

tool_node = ToolNode(ALL_TOOLS)

# ---------------------------------------------------------------------------
# Graph — compiled lazily via init_graph() so the checkpointer can be injected
# ---------------------------------------------------------------------------
chatbot = None


def init_graph(checkpointer):
    """
    Compile and store the graph with the provided checkpointer.
    Must be called once at startup after the database connection is ready.
    """
    global chatbot
    graph = StateGraph(ChatState)
    graph.add_node("chat_node", chat_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node", tools_condition)
    graph.add_edge("tools", "chat_node")
    chatbot = graph.compile(checkpointer=checkpointer)
    return chatbot
