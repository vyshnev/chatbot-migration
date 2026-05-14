"""
tools/scraper.py
----------------
Web scraper tool using the Jina AI Reader API with Redis caching.
Converts any URL into clean Markdown for the LLM to read.
"""

import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from langchain_core.tools import tool
from cache.service import cached
from core.logger import get_logger

logger = get_logger(__name__)

# Matches lines worth keeping even if they are short: currency symbols,
# percentage signs, or multi-digit numbers (e.g. $42.50, 4.2%, Score: 87).
# \d{2,} avoids preserving lone page-number digits like "1" or "2".
_DATA_PATTERN = re.compile(r'[$€£¥%]|\d{2,}')

def _clean_markdown(text: str) -> str:
    """Aggressively trims markdown to save LLM tokens."""
    # 1. Remove all image tags: ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)
    
    # 2. Strip URLs from links but keep the text: [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # 3. Remove short orphaned lines (nav bars, footers, ad text)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        # Keep headers and list items
        if stripped.startswith('#') or stripped.startswith('-') or stripped.startswith('*'):
            cleaned_lines.append(line)
        else:
        # Drop navigation bars — but only if the line does NOT start with '|'.
            # Markdown table rows always start with '|'; nav breadcrumbs never do.
            if " | " in stripped and not stripped.startswith("|"):
                continue
            # Keep lines with 2+ words, OR lines containing currency symbols,
            # percentages, or multi-digit numbers (e.g. $42.50, GDP: 4.2%, Score: 87).
            # Using \d{2,} instead of \d avoids keeping lone page-number digits (1, 2, 3).
            if len(stripped.split()) >= 2 or _DATA_PATTERN.search(stripped):
                cleaned_lines.append(line)

    cleaned_text = '\n'.join(cleaned_lines)
    
    # 4. Hard safety cap at 25,000 characters (~6,000 tokens) to guarantee no 429 error
    if len(cleaned_text) > 25000:
        cleaned_text = cleaned_text[:25000] + "\n\n...[CONTENT TRUNCATED FOR LENGTH]..."
        
    return cleaned_text

# ---------------------------------------------------------------------------
# HTTP session with automatic retry for Jina API transient failures.
# Retries up to 3 times on 429 / 5xx responses with exponential backoff
# (1s, 2s, 4s). Built on urllib3.Retry — no extra dependencies needed.
# ---------------------------------------------------------------------------
_JINA_SESSION = requests.Session()
_JINA_SESSION.mount(
    "https://",
    HTTPAdapter(
        max_retries=Retry(
            total=3,
            backoff_factor=1,                        # waits: 1s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
    ),
)
_JINA_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def _fetch_jina_markdown(url: str) -> str:
    """Fetch a URL via Jina Reader API and return cleaned Markdown."""
    jina_url = f"https://r.jina.ai/{url}"
    try:
        response = _JINA_SESSION.get(jina_url, headers=_JINA_HEADERS, timeout=15)
        response.raise_for_status()
        return _clean_markdown(response.text)
    except requests.HTTPError as e:
        logger.error(f"Jina API HTTP error for {url}: {e}")
        return f"Error reading webpage: HTTP {e.response.status_code}. The site might be blocking the request."
    except requests.Timeout:
        logger.error(f"Jina API timed out for {url}")
        return "Error reading webpage: The request timed out after 15 seconds."
    except requests.RequestException as e:
        logger.error(f"Jina API request failed for {url}: {e}")
        return f"Error reading webpage: {e}"

@tool
def read_webpage(url: str) -> str:
    """
    Reads the full text of a webpage and returns it as clean Markdown.
    Use this when you need to understand the detailed content of a specific URL,
    especially after finding a relevant link via a web search.

    IMPORTANT: If this tool returns an error (e.g. "HTTP 403", "HTTP 451",
    "timed out", or "blocking the request"), do NOT fabricate information.
    Instead, try calling this tool again with the next best URL from your
    search results. Only if all URLs fail should you inform the user that
    the sources are currently unavailable and base your answer solely on
    the search snippets — making clear that the information may be incomplete.
    """
    # Cache the result for 24 hours (86400 seconds)
    return cached("read_webpage", _fetch_jina_markdown, 86400, url)
