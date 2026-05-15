from fastapi.testclient import TestClient
from unittest.mock import patch
from server import app

client = TestClient(app)


@patch("server.get_all_threads")
def test_get_threads_endpoint(mock_get_all_threads):
    """Verify that the /threads endpoint returns a 200 OK and valid JSON format."""
    mock_get_all_threads.return_value = [{"id": "thread-123", "title": "Mock Thread", "is_pinned": False}]

    response = client.get("/threads")

    assert response.status_code == 200
    data = response.json()
    assert "threads" in data
    assert len(data["threads"]) == 1
    assert data["threads"][0]["id"] == "thread-123"


@patch("server.delete_thread")
def test_delete_thread_endpoint(mock_delete_thread):
    """Verify that deleting a thread returns a success message."""
    mock_delete_thread.return_value = True

    response = client.delete("/threads/test-thread-id")

    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Thread test-thread-id deleted"}


@patch("server.delete_thread")
def test_delete_thread_endpoint_failure(mock_delete_thread):
    """Verify that if the database deletion fails, a 500 error is thrown."""
    mock_delete_thread.return_value = False

    response = client.delete("/threads/test-thread-id")

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to delete thread"


@patch("server.pin_thread")
def test_pin_thread_endpoint(mock_pin_thread):
    """Verify PATCH /threads/{id}/pin toggles the pinned state."""
    mock_pin_thread.return_value = True

    response = client.patch("/threads/test-thread-id/pin", json={"pinned": True})

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_pin_thread.assert_called_once_with("test-thread-id", True)


@patch("server.pin_thread")
def test_pin_thread_endpoint_failure(mock_pin_thread):
    """Verify PATCH /threads/{id}/pin returns 500 when the DB call fails."""
    mock_pin_thread.return_value = False

    response = client.patch("/threads/test-thread-id/pin", json={"pinned": True})

    assert response.status_code == 500


@patch("server.rename_thread")
def test_rename_thread_endpoint(mock_rename_thread):
    """Verify PATCH /threads/{id}/rename updates the title."""
    mock_rename_thread.return_value = True

    response = client.patch("/threads/test-thread-id/rename", json={"title": "My New Title"})

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_rename_thread.assert_called_once_with("test-thread-id", "My New Title")


@patch("server.rename_thread")
def test_rename_thread_endpoint_failure(mock_rename_thread):
    """Verify PATCH /threads/{id}/rename returns 500 when the DB call fails."""
    mock_rename_thread.return_value = False

    response = client.patch("/threads/test-thread-id/rename", json={"title": "My New Title"})

    assert response.status_code == 500
