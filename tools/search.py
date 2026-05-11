"""
tools/search.py
---------------
Web search tool using DuckDuckGo with Redis caching.
"""

from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from cache.service import cached

# Max results of 3 is usually perfect for chatbots
_raw_search = TavilySearch(max_results=3)


@tool
def search_tool(query: str) -> str:
    """
    Search the web for information using Tavily. Use this when you need up-to-date facts.
    """
    def fetch_tavily(q):
        # Tavily returns a list of dictionaries; we cast it to string for the LLM
        results = _raw_search.invoke({"query": q})
        return str(results)
        
    return cached("search_tool", fetch_tavily, 7200, query)
