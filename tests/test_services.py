import pytest
from unittest.mock import MagicMock
from threads.service import set_connection, get_all_threads, save_title, delete_thread

@pytest.fixture
def mock_pool():
    """Create a mock psycopg connection pool."""
    pool = MagicMock()
    # The pool.connection() is used as a context manager: with pool.connection() as conn:
    conn = MagicMock()
    cursor = MagicMock()
    
    # conn.execute() returns the cursor
    conn.execute.return_value = cursor
    
    # Set up the context manager to yield the connection
    pool.connection.return_value.__enter__.return_value = conn
    
    # Inject the mock pool into the service
    set_connection(pool)
    
    return pool, conn, cursor

def test_get_all_threads(mock_pool):
    pool, conn, cursor = mock_pool
    
    # Mock the database returning two rows
    cursor.fetchall.return_value = [
        ("thread-123", "First Chat"),
        ("thread-456", "Second Chat")
    ]
    
    result = get_all_threads()
    
    # Verify the SQL was executed
    conn.execute.assert_called_once()
    assert "SELECT thread_id, title" in conn.execute.call_args[0][0]
    
    # Verify the service parsed the rows into dictionaries correctly
    assert len(result) == 2
    assert result[0] == {"id": "thread-123", "title": "First Chat"}
    assert result[1] == {"id": "thread-456", "title": "Second Chat"}

def test_delete_thread(mock_pool):
    pool, conn, cursor = mock_pool
    
    result = delete_thread("thread-999")
    
    # Verify it executed 4 DELETE statements and 1 commit
    assert conn.execute.call_count == 4
    
    # Check that all checkpoints were deleted
    calls = conn.execute.call_args_list
    assert "DELETE FROM thread_metadata" in calls[0][0][0]
    assert "DELETE FROM checkpoints" in calls[1][0][0]
    assert "DELETE FROM checkpoint_writes" in calls[2][0][0]
    assert "DELETE FROM checkpoint_blobs" in calls[3][0][0]
    
    # Verify the ID was passed to all of them
    assert calls[0][0][1] == ("thread-999",)
    
    conn.commit.assert_called_once()
    assert result is True
