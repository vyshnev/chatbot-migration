"""
tools/scraper.py
----------------
Web scraper tool with RAG (Retrieval-Augmented Generation) via pgvector.

Pipeline for read_webpage(url, query):
  1. Check document_chunks: is this URL already indexed?
     - HIT  → run cosine similarity search directly (zero Jina + embedding cost)
     - MISS → fetch via Jina → clean → chunk (600 tok / 100 overlap) → embed → store → search
  2. Return top-3 most relevant passages (~1,800 tokens max) instead of a
     raw 70,000-token page — eliminating 429 RateLimitError from the LLM.
"""

import re
import uuid
import json

import tiktoken
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Dependency-injected pool — set via set_connection() at startup
# ---------------------------------------------------------------------------
_pool = None


def set_connection(pool) -> None:
    """Inject the connection pool. Must be called before any tool is invoked."""
    global _pool
    _pool = pool


# ---------------------------------------------------------------------------
# Embeddings + text splitter — module-level singletons (created once)
# ---------------------------------------------------------------------------
_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
_enc = tiktoken.get_encoding("cl100k_base")


def _token_len(text: str) -> int:
    return len(_enc.encode(text))


_splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,       # ~600 tokens per chunk
    chunk_overlap=100,    # 100-token overlap prevents sentence boundary loss
    length_function=_token_len,
)

# ---------------------------------------------------------------------------
# Markdown cleaner
# ---------------------------------------------------------------------------
# Keep lines that contain currency symbols, percentages, or multi-digit
# numbers even if they are short (e.g. "$42.50", "4.2%", "Score: 87").
_DATA_PATTERN = re.compile(r'[$€£¥%]|\d{2,}')


def _clean_markdown(text: str) -> str:
    """
    Remove image tags, collapse link URLs to plain text, and drop short
    nav/footer noise. Does NOT truncate — RAG handles arbitrary lengths.
    """
    # 1. Remove image tags: ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)

    # 2. Strip URLs from links but keep the anchor text: [text](url) → text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # 3. Drop short orphaned lines (nav bars, footers, ad fragments)
    cleaned_lines = []
    for line in text.split('\n'):
        stripped = line.strip()
        if not stripped:
            continue
        # Always keep headers and list items
        if stripped.startswith(('#', '-', '*')):
            cleaned_lines.append(line)
            continue
        # Drop nav breadcrumbs like "Home | About | Contact" (not table rows)
        if ' | ' in stripped and not stripped.startswith('|'):
            continue
        # Keep lines with 2+ words OR lines with financial/statistical data
        if len(stripped.split()) >= 2 or _DATA_PATTERN.search(stripped):
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


# ---------------------------------------------------------------------------
# Jina AI Reader session with exponential-backoff retry
# 3 retries on 429/5xx: waits 1s, 2s, 4s before giving up.
# ---------------------------------------------------------------------------
_JINA_SESSION = requests.Session()
_JINA_SESSION.mount(
    "https://",
    HTTPAdapter(
        max_retries=Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
    ),
)
_JINA_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


# ---------------------------------------------------------------------------
# pgvector helpers
# ---------------------------------------------------------------------------

def _vec_str(embedding: list[float]) -> str:
    """Serialize a float list to a pgvector-compatible string literal."""
    return "[" + ",".join(str(x) for x in embedding) + "]"


def _url_already_indexed(url: str) -> bool:
    """Return True if at least one chunk for this URL exists in document_chunks."""
    if _pool is None:
        return False
    with _pool.connection() as conn:
        cursor = conn.execute(
            "SELECT 1 FROM document_chunks WHERE metadata->>'url' = %s LIMIT 1",
            (url,),
        )
        return cursor.fetchone() is not None


def _embed_and_store(url: str, chunks: list[str]) -> None:
    """Batch-embed chunks and insert them into document_chunks."""
    embeddings = _embeddings.embed_documents(chunks)
    with _pool.connection() as conn:
        for chunk_text, emb in zip(chunks, embeddings):
            conn.execute(
                """
                INSERT INTO document_chunks (id, source_type, content, metadata, embedding)
                VALUES (%s, 'web_scrape', %s, %s, %s::vector)
                """,
                (
                    str(uuid.uuid4()),
                    chunk_text,
                    json.dumps({"url": url}),
                    _vec_str(emb),
                ),
            )
        conn.commit()
    logger.info(f"Stored {len(chunks)} chunks for {url}")


def _search_chunks(url: str, query: str, top_k: int = 3) -> list[str]:
    """Return the top_k chunks most similar to query, scoped to this URL."""
    q_emb = _embeddings.embed_query(query)
    with _pool.connection() as conn:
        cursor = conn.execute(
            """
            SELECT content
            FROM   document_chunks
            WHERE  metadata->>'url' = %s
            ORDER  BY embedding <=> %s::vector
            LIMIT  %s
            """,
            (url, _vec_str(q_emb), top_k),
        )
        return [row[0] for row in cursor.fetchall()]


def cleanup_old_chunks() -> int:
    """
    Delete web_scrape chunks older than 30 days.
    PDF uploads (source_type='pdf_upload') are exempt — they are never auto-deleted.
    Returns the number of rows deleted.
    """
    if _pool is None:
        return 0
    try:
        with _pool.connection() as conn:
            result = conn.execute(
                """
                DELETE FROM document_chunks
                WHERE  source_type = 'web_scrape'
                AND    created_at  < NOW() - INTERVAL '30 days'
                """
            )
            conn.commit()
            deleted = result.rowcount
            if deleted:
                logger.info(f"TTL cleanup: removed {deleted} stale web_scrape chunk(s)")
            else:
                logger.info("TTL cleanup: no stale chunks found")
            return deleted
    except Exception as e:
        logger.error(f"TTL cleanup failed: {e}")
        return 0


# ---------------------------------------------------------------------------
# Jina fetch + index pipeline
# ---------------------------------------------------------------------------

def _fetch_and_index(url: str) -> None:
    """
    Fetch a URL via Jina, clean the Markdown, split into chunks,
    embed them, and persist to document_chunks.
    Raises on HTTP/network errors so the caller can surface them cleanly.
    """
    jina_url = f"https://r.jina.ai/{url}"
    response = _JINA_SESSION.get(jina_url, headers=_JINA_HEADERS, timeout=15)
    response.raise_for_status()

    markdown = _clean_markdown(response.text)
    chunks = _splitter.split_text(markdown)
    logger.info(f"Fetched {url}: {len(chunks)} chunks after splitting")

    if chunks:
        _embed_and_store(url, chunks)


# ---------------------------------------------------------------------------
# LangChain tool — public API
# ---------------------------------------------------------------------------

@tool
def read_webpage(url: str, query: str) -> str:
    """
    Fetches a webpage and returns the most relevant sections for your query
    using semantic vector search. Only the top 3 matching passages (~1,800 tokens)
    are returned, not the entire page.

    Args:
        url:   The full URL of the webpage to read.
        query: The specific question or topic you are looking for on this page.
               This is used internally to rank and select the most relevant passages.

    IMPORTANT: If this tool returns an error (e.g. "HTTP 403", "HTTP 451",
    "timed out", or "blocking the request"), do NOT fabricate information.
    Instead, try calling this tool again with the next best URL from your
    search results. Only if all URLs fail should you inform the user that
    the sources are currently unavailable and base your answer solely on
    the search snippets — making clear that the information may be incomplete.
    """
    try:
        if not _url_already_indexed(url):
            _fetch_and_index(url)
        else:
            logger.info(f"Cache HIT for {url} — skipping Jina, querying pgvector directly")

        chunks = _search_chunks(url, query)
        if not chunks:
            return "No relevant content found in this webpage for your query."

        return "\n\n---\n\n".join(chunks)

    except requests.HTTPError as e:
        logger.error(f"Jina HTTP error for {url}: {e}")
        return f"Error reading webpage: HTTP {e.response.status_code}. The site might be blocking the request."
    except requests.Timeout:
        logger.error(f"Jina timed out for {url}")
        return "Error reading webpage: The request timed out after 15 seconds."
    except Exception as e:
        logger.error(f"read_webpage failed for {url}: {e}")
        return f"Error reading webpage: {e}"
