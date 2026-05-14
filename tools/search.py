"""
tools/search.py
---------------
Web search tool using Tavily with Redis caching.
"""

from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from cache.service import cached
from core.logger import get_logger

logger = get_logger(__name__)

# Max results of 3 is usually perfect for chatbots
_raw_search = TavilySearch(max_results=3)


def _format_results(results) -> str:
    """
    Extract only the fields the LLM needs (url + content) and format them
    as clean plain text. Avoids leaking Python dict syntax into the prompt,
    which wastes tokens and is harder for the model to parse.
    """
    try:
        items = results.get("results", []) if isinstance(results, dict) else results
        if not items:
            return "No search results found."
        return "\n\n".join(
            f"Source: {r.get('url', 'unknown')}\n{r.get('content', '').strip()}"
            for r in items
            if r.get("content")
        )
    except Exception as e:
        logger.error(f"Error formatting search results: {e}")
        return str(results)


@tool
def search_tool(query: str) -> str:
    """
    Search the web for current information using Tavily.
    Returns a list of sources with their content.
    Use this when you need up-to-date facts, news, or specific information.
    """
    def fetch_tavily(q):
        try:
            results = _raw_search.invoke({"query": q})
            return _format_results(results)
        except Exception as e:
            logger.error(f"Search failed for query '{q}': {e}")
            return f"Search unavailable: {e}"

    # Cache for 15 minutes — short enough to catch breaking news
    return cached("search_tool", fetch_tavily, 900, query)
