"""
tools/document_rag.py
---------------------
Thread-scoped PDF ingestion and retrieval for the RAG pipeline.

Responsibilities:
  - ingest_pdf():              Parse → chunk → embed → store (source_type='pdf_upload')
  - search_thread_documents(): Similarity search scoped to one thread's uploads
  - set_connection():          Pool injection (same pattern as all other services)

This module is intentionally separate from tools/scraper.py:
  - scraper.py  handles web pages (tool-triggered, LLM decides when to call)
  - document_rag.py handles uploaded files (auto-injected on every message in
    a thread that has uploads — the LLM never needs to invoke a tool for this)

Both share the same document_chunks table and embedding model.
"""

import hashlib
import json
import uuid

import fitz  # PyMuPDF
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.logger import get_logger
from tools.vector_utils import to_pgvector_literal

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Shared infrastructure (same model as scraper.py for cross-table consistency)
# ---------------------------------------------------------------------------
_pool = None
_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)


def set_connection(pool) -> None:
    """Inject the connection pool. Must be called once at startup."""
    global _pool
    _pool = pool


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _is_already_ingested(file_hash: str, thread_id: str) -> bool:
    """Return True if a file with this exact hash is already stored for this thread."""
    if not _pool:
        return False
    try:
        with _pool.connection() as conn:
            cursor = conn.execute(
                """
                SELECT 1 FROM document_chunks
                WHERE thread_id = %s
                  AND source_type = 'pdf_upload'
                  AND metadata->>'file_hash' = %s
                LIMIT 1
                """,
                (thread_id, file_hash),
            )
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Dedup check failed: {e}")
        return False


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------

def ingest_pdf(file_bytes: bytes, filename: str, thread_id: str) -> dict:
    """
    Parse a PDF, chunk it, embed it, and store in document_chunks.

    Returns:
        {"status": "success", "chunks": N, "filename": filename}
        {"status": "duplicate", "chunks": 0}
        {"status": "empty", "chunks": 0}
    """
    # 1. Hash for deduplication (SHA-256 of raw bytes)
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    if _is_already_ingested(file_hash, thread_id):
        logger.info(f"ingest_pdf: duplicate detected for '{filename}' in thread {thread_id}")
        return {"status": "duplicate", "chunks": 0}

    # 2. Extract text with PyMuPDF
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages_text = [page.get_text() for page in doc]
        doc.close()
    except Exception as e:
        logger.error(f"ingest_pdf: PyMuPDF failed for '{filename}': {e}")
        raise

    full_text = "\n\n".join(pages_text).strip()
    if not full_text:
        logger.warning(f"ingest_pdf: '{filename}' contains no extractable text (image-only PDF?)")
        return {"status": "empty", "chunks": 0}

    # 3. Chunk
    chunks = _splitter.split_text(full_text)
    logger.info(f"ingest_pdf: '{filename}' → {len(chunks)} chunks")

    # 4. Embed all chunks in a single API call (batch)
    embeddings = _embeddings.embed_documents(chunks)

    # 5. Store
    metadata_base = {"filename": filename, "file_hash": file_hash}
    with _pool.connection() as conn:
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            conn.execute(
                """
                INSERT INTO document_chunks
                    (id, thread_id, source_type, content, metadata, embedding)
                VALUES (%s, %s, 'pdf_upload', %s, %s, %s::vector)
                """,
                (
                    str(uuid.uuid4()),
                    thread_id,
                    chunk,
                    json.dumps({**metadata_base, "chunk_index": i}),
                    to_pgvector_literal(embedding),
                ),
            )
        conn.commit()

    logger.info(f"ingest_pdf: stored {len(chunks)} chunks for '{filename}' in thread {thread_id}")
    return {"status": "success", "chunks": len(chunks), "filename": filename}


# ---------------------------------------------------------------------------
# Retrieval — called automatically by chat_node on every message
# ---------------------------------------------------------------------------

def search_thread_documents(thread_id: str, query: str, top_k: int = 3) -> str:
    """
    Semantic search over PDF chunks belonging to this thread.

    Returns a formatted string of top-K relevant passages ready to inject
    into the system prompt, or an empty string if:
      - the pool is not set
      - this thread has no uploaded documents
      - any error occurs (never raises — must not crash a chat turn)
    """
    if not _pool:
        return ""
    try:
        # Fast COUNT check — skip embedding cost if no uploads exist
        with _pool.connection() as conn:
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM document_chunks
                WHERE thread_id = %s AND source_type = 'pdf_upload'
                """,
                (thread_id,),
            )
            if cursor.fetchone()[0] == 0:
                return ""

        # Embed the user's query
        query_embedding = _embeddings.embed_query(query)

        # Cosine similarity search scoped to this thread's PDF chunks
        with _pool.connection() as conn:
            cursor = conn.execute(
                """
                SELECT content, metadata->>'filename' AS filename
                FROM document_chunks
                WHERE thread_id = %s AND source_type = 'pdf_upload'
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (thread_id, to_pgvector_literal(query_embedding), top_k),
            )
            rows = cursor.fetchall()

        if not rows:
            return ""

        chunks = [f"[From: {row[1]}]\n{row[0]}" for row in rows]
        return "\n\n---\n\n".join(chunks)

    except Exception as e:
        logger.error(f"search_thread_documents failed for thread {thread_id}: {e}")
        return ""


# ---------------------------------------------------------------------------
# File listing — used by GET /threads/{id}/files
# ---------------------------------------------------------------------------

def list_thread_files(thread_id: str) -> list[dict]:
    """
    Return distinct filenames uploaded to this thread with their chunk counts.
    Returns [] on any error.
    """
    if not _pool:
        return []
    try:
        with _pool.connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    metadata->>'filename'  AS filename,
                    COUNT(*)               AS chunk_count,
                    MAX(created_at)        AS uploaded_at
                FROM document_chunks
                WHERE thread_id = %s AND source_type = 'pdf_upload'
                GROUP BY metadata->>'filename'
                ORDER BY MAX(created_at) DESC
                """,
                (thread_id,),
            )
            return [
                {
                    "filename": row[0],
                    "chunks": row[1],
                    "uploaded_at": row[2].isoformat() if row[2] else None,
                }
                for row in cursor.fetchall()
            ]
    except Exception as e:
        logger.error(f"list_thread_files failed for thread {thread_id}: {e}")
        return []
