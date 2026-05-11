"""
tools/scraper.py
----------------
Web scraper tool using the Jina AI Reader API with Redis caching.
Converts any URL into clean Markdown for the LLM to read.
"""

import urllib.request
import urllib.error
from langchain_core.tools import tool
from cache.service import cached

def _fetch_jina_markdown(url: str) -> str:
    """Internal function to call Jina Reader API."""
    jina_url = f"https://r.jina.ai/{url}"
    
    # Use a standard user-agent so we don't get blocked by the API itself
    req = urllib.request.Request(
        jina_url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8')
    except urllib.error.URLError as e:
        return f"Error reading webpage: {str(e)}. The site might be down or blocking the request."
    except Exception as e:
        return f"An unexpected error occurred while reading the webpage: {str(e)}"

@tool
def read_webpage(url: str) -> str:
    """
    Reads the full text of a webpage and returns it as Markdown. 
    Use this when you need to understand the detailed content of a specific URL, 
    especially after finding a relevant link via a web search.
    """
    # Cache the result for 24 hours (86400 seconds)
    return cached("read_webpage", _fetch_jina_markdown, 86400, url)
