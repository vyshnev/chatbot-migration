"""
tools/scraper.py
----------------
Web scraper tool using the Jina AI Reader API with Redis caching.
Converts any URL into clean Markdown for the LLM to read.
"""

import urllib.request
import urllib.error
import re
from langchain_core.tools import tool
from cache.service import cached

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
            # Drop obvious navigation bars
            if " | " in stripped:
                continue
            # Keep lines that have 3 or more words
            if len(stripped.split()) >= 3:
                cleaned_lines.append(line)
            
    cleaned_text = '\n'.join(cleaned_lines)
    
    # 4. Hard safety cap at 25,000 characters (~6,000 tokens) to guarantee no 429 error
    if len(cleaned_text) > 25000:
        cleaned_text = cleaned_text[:25000] + "\n\n...[CONTENT TRUNCATED FOR LENGTH]..."
        
    return cleaned_text

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
            raw_md = response.read().decode('utf-8')
            return _clean_markdown(raw_md)
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
