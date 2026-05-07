"""
tools/search.py
---------------
Web search tool using DuckDuckGo with Redis caching.
"""

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from cache.service import cached

_raw_search = DuckDuckGoSearchRun(region="us-en")


@tool
def search_tool(query: str) -> str:
    """
    Search the web for information. Use this when you need up-to-date facts.
    """
    return cached("search_tool", _raw_search.invoke, 7200, query)
