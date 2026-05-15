import pytest
from unittest.mock import MagicMock
from tools.scraper import _clean_markdown, cleanup_old_chunks, set_connection


# ---------------------------------------------------------------------------
# _clean_markdown — pure function tests (no DB, no mocks)
# ---------------------------------------------------------------------------

def test_markdown_cleaner_strips_images():
    """Verify that the markdown cleaner successfully removes image tags."""
    dirty_text = "Here is a picture: ![cute cat](https://example.com/cat.jpg)\nAnd here is text."
    cleaned = _clean_markdown(dirty_text)

    assert "cute cat" not in cleaned
    assert "https://example.com/cat.jpg" not in cleaned
    assert "Here is a picture:" in cleaned


def test_markdown_cleaner_strips_urls():
    """Verify that URLs are stripped but the anchor text remains."""
    dirty_text = "Please [click here](https://website.com) to read more."
    cleaned = _clean_markdown(dirty_text)

    assert "click here" in cleaned
    assert "https://website.com" not in cleaned


def test_markdown_cleaner_removes_orphaned_lines():
    """Verify that short lines (like nav bars) are removed, but headers stay."""
    dirty_text = (
        "Home | About | Contact\n"
        "# Main Article Title\n"
        "This is a long sentence that has more than four words in it."
    )
    cleaned = _clean_markdown(dirty_text)

    assert "Home | About | Contact" not in cleaned
    assert "# Main Article Title" in cleaned
    assert "This is a long sentence" in cleaned


# ---------------------------------------------------------------------------
# cleanup_old_chunks — mock pool tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=False)
def mock_scraper_pool():
    """Inject a mock pool into the scraper module and reset after the test."""
    pool = MagicMock()
    conn = MagicMock()
    cursor = MagicMock()

    conn.execute.return_value = cursor
    pool.connection.return_value.__enter__.return_value = conn

    set_connection(pool)
    yield pool, conn, cursor
    set_connection(None)   # reset so other tests aren't affected


def test_cleanup_old_chunks_returns_zero_when_no_pool():
    """cleanup_old_chunks should safely return 0 when pool is not injected."""
    set_connection(None)
    result = cleanup_old_chunks()
    assert result == 0


def test_cleanup_old_chunks_executes_correct_delete(mock_scraper_pool):
    pool, conn, cursor = mock_scraper_pool
    cursor.rowcount = 5   # simulate 5 rows deleted

    result = cleanup_old_chunks()

    conn.execute.assert_called_once()
    sql = conn.execute.call_args[0][0]

    # Must target only web_scrape rows, not pdf_upload
    assert "DELETE FROM document_chunks" in sql
    assert "source_type = 'web_scrape'" in sql
    assert "INTERVAL '30 days'" in sql

    conn.commit.assert_called_once()
    assert result == 5


def test_cleanup_old_chunks_returns_zero_when_nothing_to_delete(mock_scraper_pool):
    pool, conn, cursor = mock_scraper_pool
    cursor.rowcount = 0

    result = cleanup_old_chunks()

    assert result == 0
    conn.commit.assert_called_once()


def test_cleanup_old_chunks_handles_db_error(mock_scraper_pool):
    pool, conn, cursor = mock_scraper_pool
    conn.execute.side_effect = Exception("Connection reset by peer")

    result = cleanup_old_chunks()

    assert result == 0   # must not raise
