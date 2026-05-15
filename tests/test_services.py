import pytest
from unittest.mock import MagicMock
from threads.service import set_connection, get_all_threads, save_title, delete_thread, pin_thread, rename_thread

@pytest.fixture
def mock_pool():
    """Create a mock psycopg connection pool."""
    pool = MagicMock()
    conn = MagicMock()
    cursor = MagicMock()

    conn.execute.return_value = cursor
    pool.connection.return_value.__enter__.return_value = conn
    set_connection(pool)

    return pool, conn, cursor


def test_get_all_threads(mock_pool):
    pool, conn, cursor = mock_pool

    # Mock the database returning two rows — now includes is_pinned column
    cursor.fetchall.return_value = [
        ("thread-123", "First Chat", True),
        ("thread-456", "Second Chat", False),
    ]

    result = get_all_threads()

    conn.execute.assert_called_once()
    assert "SELECT thread_id, title" in conn.execute.call_args[0][0]

    assert len(result) == 2
    assert result[0] == {"id": "thread-123", "title": "First Chat", "is_pinned": True}
    assert result[1] == {"id": "thread-456", "title": "Second Chat", "is_pinned": False}


def test_delete_thread(mock_pool):
    pool, conn, cursor = mock_pool

    result = delete_thread("thread-999")

    # Verify it executed 4 DELETE statements
    assert conn.execute.call_count == 4

    calls = conn.execute.call_args_list
    assert "DELETE FROM thread_metadata" in calls[0][0][0]
    assert "DELETE FROM checkpoints" in calls[1][0][0]
    assert "DELETE FROM checkpoint_writes" in calls[2][0][0]
    assert "DELETE FROM checkpoint_blobs" in calls[3][0][0]
    assert calls[0][0][1] == ("thread-999",)

    conn.commit.assert_called_once()
    assert result is True


def test_pin_thread(mock_pool):
    pool, conn, cursor = mock_pool

    result = pin_thread("thread-123", True)

    conn.execute.assert_called_once()
    sql = conn.execute.call_args[0][0]
    assert "UPDATE thread_metadata" in sql
    assert "is_pinned" in sql
    assert conn.execute.call_args[0][1] == (True, "thread-123")
    conn.commit.assert_called_once()
    assert result is True


def test_unpin_thread(mock_pool):
    pool, conn, cursor = mock_pool

    result = pin_thread("thread-123", False)

    assert conn.execute.call_args[0][1] == (False, "thread-123")
    assert result is True


def test_rename_thread(mock_pool):
    pool, conn, cursor = mock_pool

    result = rename_thread("thread-123", "My New Title")

    conn.execute.assert_called_once()
    sql = conn.execute.call_args[0][0]
    assert "UPDATE thread_metadata" in sql
    assert "title" in sql
    assert conn.execute.call_args[0][1] == ("My New Title", "thread-123")
    conn.commit.assert_called_once()
    assert result is True


def test_rename_thread_db_error(mock_pool):
    pool, conn, cursor = mock_pool
    conn.execute.side_effect = Exception("DB connection lost")

    result = rename_thread("thread-123", "New Title")

    assert result is False
