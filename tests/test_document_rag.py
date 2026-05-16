import json
import hashlib
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from tools.document_rag import (
    ingest_pdf,
    search_thread_documents,
    list_thread_files,
    set_connection,
    _is_already_ingested,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_pool(fetchone_return=None, fetchall_return=None, rowcount=0):
    pool = MagicMock()
    conn = MagicMock()
    cursor = MagicMock()

    cursor.fetchone.return_value = fetchone_return
    cursor.fetchall.return_value = fetchall_return or []
    cursor.rowcount = rowcount

    conn.execute.return_value = cursor
    pool.connection.return_value.__enter__.return_value = conn
    return pool, conn, cursor


@pytest.fixture(autouse=True)
def reset_pool():
    """Ensure the module pool is reset between tests."""
    set_connection(None)
    yield
    set_connection(None)


# ---------------------------------------------------------------------------
# _is_already_ingested
# ---------------------------------------------------------------------------

def test_is_already_ingested_returns_false_when_no_pool():
    set_connection(None)
    assert _is_already_ingested("abc123", "thread-1") is False


def test_is_already_ingested_returns_true_when_row_found():
    pool, conn, cursor = _make_mock_pool(fetchone_return=(1,))
    set_connection(pool)
    assert _is_already_ingested("abc123", "thread-1") is True


def test_is_already_ingested_returns_false_when_no_row():
    pool, conn, cursor = _make_mock_pool(fetchone_return=None)
    set_connection(pool)
    assert _is_already_ingested("abc123", "thread-1") is False


# ---------------------------------------------------------------------------
# ingest_pdf
# ---------------------------------------------------------------------------

MINIMAL_PDF_TEXT = "This is a test document with enough content to chunk properly."


@patch("tools.document_rag._is_already_ingested", return_value=True)
def test_ingest_pdf_returns_duplicate_when_hash_exists(mock_dedup):
    result = ingest_pdf(b"%PDF-1.4 fake", "report.pdf", "thread-1")
    assert result["status"] == "duplicate"
    assert result["chunks"] == 0


@patch("tools.document_rag._is_already_ingested", return_value=False)
@patch("tools.document_rag._embeddings")
@patch("tools.document_rag.fitz")
def test_ingest_pdf_success(mock_fitz, mock_embeddings, mock_dedup):
    # Simulate PyMuPDF returning one page of text
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_page.get_text.return_value = MINIMAL_PDF_TEXT * 5   # enough text to produce a chunk
    mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
    mock_fitz.open.return_value = mock_doc

    # Simulate embeddings returning a 1536-dim vector
    mock_embeddings.embed_documents.return_value = [[0.1] * 1536]

    pool, conn, cursor = _make_mock_pool()
    set_connection(pool)

    result = ingest_pdf(b"%PDF-1.4 fake", "report.pdf", "thread-1")

    assert result["status"] == "success"
    assert result["chunks"] >= 1
    assert result["filename"] == "report.pdf"
    conn.commit.assert_called_once()


@patch("tools.document_rag._is_already_ingested", return_value=False)
@patch("tools.document_rag.fitz")
def test_ingest_pdf_empty_returns_empty_status(mock_fitz, mock_dedup):
    # Simulate PDF with no extractable text (image-only)
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_page.get_text.return_value = "   "   # whitespace only
    mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
    mock_fitz.open.return_value = mock_doc

    result = ingest_pdf(b"%PDF-1.4 fake", "scanned.pdf", "thread-1")

    assert result["status"] == "empty"
    assert result["chunks"] == 0


# ---------------------------------------------------------------------------
# search_thread_documents
# ---------------------------------------------------------------------------

def test_search_returns_empty_string_when_no_pool():
    set_connection(None)
    result = search_thread_documents("thread-1", "what is the revenue?")
    assert result == ""


def test_search_returns_empty_string_when_no_uploads():
    pool, conn, cursor = _make_mock_pool(fetchone_return=(0,))   # COUNT = 0
    set_connection(pool)

    result = search_thread_documents("thread-1", "any query")

    assert result == ""
    # Should NOT call embed (short-circuit after COUNT check)
    # We verify by checking no further DB calls were made beyond the COUNT
    assert conn.execute.call_count == 1


@patch("tools.document_rag._embeddings")
def test_search_returns_formatted_chunks(mock_embeddings):
    # First DB call: COUNT returns 2 (thread has uploads)
    # Second DB call: similarity search returns 2 rows
    pool = MagicMock()
    conn = MagicMock()

    count_cursor = MagicMock()
    count_cursor.fetchone.return_value = (2,)

    search_cursor = MagicMock()
    search_cursor.fetchall.return_value = [
        ("Chunk A text", "report.pdf"),
        ("Chunk B text", "report.pdf"),
    ]

    conn.execute.side_effect = [count_cursor, search_cursor]
    pool.connection.return_value.__enter__.return_value = conn

    mock_embeddings.embed_query.return_value = [0.1] * 1536
    set_connection(pool)

    result = search_thread_documents("thread-1", "what is the revenue?")

    assert "[From: report.pdf]" in result
    assert "Chunk A text" in result
    assert "Chunk B text" in result
    assert "---" in result   # separator between chunks


@patch("tools.document_rag._embeddings")
def test_search_returns_empty_on_db_error(mock_embeddings):
    pool, conn, cursor = _make_mock_pool(fetchone_return=(5,))
    conn.execute.side_effect = Exception("DB connection lost")
    set_connection(pool)

    result = search_thread_documents("thread-1", "query")

    assert result == ""   # must not raise


# ---------------------------------------------------------------------------
# list_thread_files
# ---------------------------------------------------------------------------

def test_list_thread_files_returns_empty_when_no_pool():
    set_connection(None)
    assert list_thread_files("thread-1") == []


def test_list_thread_files_returns_formatted_list():
    from datetime import datetime
    ts = datetime(2025, 5, 15, 10, 0, 0)

    pool, conn, cursor = _make_mock_pool(
        fetchall_return=[("report.pdf", 42, ts), ("slides.pdf", 18, ts)]
    )
    set_connection(pool)

    result = list_thread_files("thread-1")

    assert len(result) == 2
    assert result[0] == {"filename": "report.pdf", "chunks": 42, "uploaded_at": ts.isoformat()}
    assert result[1]["filename"] == "slides.pdf"


def test_list_thread_files_returns_empty_on_db_error():
    pool, conn, cursor = _make_mock_pool()
    conn.execute.side_effect = Exception("timeout")
    set_connection(pool)

    result = list_thread_files("thread-1")
    assert result == []
