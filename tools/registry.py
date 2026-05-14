"""
tools/registry.py
-----------------
Assembles all tools into a single list and binds them to the LLM.

This is the only file that server.py or agent/graph.py should ever import
tools from — they never import individual tools directly.
"""

from langchain_openai import ChatOpenAI

from tools.search import search_tool
from tools.calculator import calculator
from tools.stock import get_stock_price
from tools.memory_tools import save_memory, forget_memory, update_memory
from tools.scraper import read_webpage

# The canonical tool list for the entire application
ALL_TOOLS = [search_tool, get_stock_price, calculator, save_memory, forget_memory, update_memory, read_webpage]


def build_llm_with_tools(llm: ChatOpenAI) -> ChatOpenAI:
    """Bind all tools to the provided LLM instance. Called once at startup."""
    return llm.bind_tools(ALL_TOOLS)
