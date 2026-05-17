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
    """Verify that a missing thread returns a 404."""
    mock_delete_thread.return_value = False

    response = client.delete("/threads/test-thread-id")

    assert response.status_code == 404
    assert response.json()["detail"] == "Thread not found"


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
    """Verify PATCH /threads/{id}/pin returns 404 when no row is updated."""
    mock_pin_thread.return_value = False

    response = client.patch("/threads/test-thread-id/pin", json={"pinned": True})

    assert response.status_code == 404


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
    """Verify PATCH /threads/{id}/rename returns 404 when no row is updated."""
    mock_rename_thread.return_value = False

    response = client.patch("/threads/test-thread-id/rename", json={"title": "My New Title"})

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /upload
# ---------------------------------------------------------------------------

FAKE_PDF_BYTES = b"%PDF-1.4 minimal fake pdf content"


@patch("server.ingest_pdf")
def test_upload_endpoint_success(mock_ingest):
    """Verify a valid PDF upload returns 200 with filename and chunk count."""
    mock_ingest.return_value = {"status": "success", "chunks": 12, "filename": "report.pdf"}

    response = client.post(
        "/upload",
        data={"thread_id": "thread-abc"},
        files={"file": ("report.pdf", FAKE_PDF_BYTES, "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["chunks"] == 12
    assert body["filename"] == "report.pdf"
    mock_ingest.assert_called_once_with(FAKE_PDF_BYTES, "report.pdf", "thread-abc")


def test_upload_endpoint_wrong_file_type():
    """Verify that non-PDF files are rejected with 400."""
    response = client.post(
        "/upload",
        data={"thread_id": "thread-abc"},
        files={"file": ("notes.txt", b"plain text content", "text/plain")},
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_upload_endpoint_file_too_large():
    """Verify that files over 10 MB are rejected with 413."""
    big_content = b"x" * (11 * 1024 * 1024)   # 11 MB
    response = client.post(
        "/upload",
        data={"thread_id": "thread-abc"},
        files={"file": ("large.pdf", big_content, "application/pdf")},
    )
    assert response.status_code == 413
    assert "10 MB" in response.json()["detail"]


@patch("server.ingest_pdf")
def test_upload_endpoint_duplicate(mock_ingest):
    """Verify that uploading the same PDF twice returns a duplicate message."""
    mock_ingest.return_value = {"status": "duplicate", "chunks": 0}

    response = client.post(
        "/upload",
        data={"thread_id": "thread-abc"},
        files={"file": ("report.pdf", FAKE_PDF_BYTES, "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "duplicate"


@patch("server.ingest_pdf")
def test_upload_endpoint_empty_pdf(mock_ingest):
    """Verify that image-only PDFs (no extractable text) return 422."""
    mock_ingest.return_value = {"status": "empty", "chunks": 0}

    response = client.post(
        "/upload",
        data={"thread_id": "thread-abc"},
        files={"file": ("scanned.pdf", FAKE_PDF_BYTES, "application/pdf")},
    )

    assert response.status_code == 422


@patch("server.ingest_pdf", side_effect=Exception("DB is down"))
def test_upload_endpoint_ingest_failure(mock_ingest):
    """Verify that an unexpected ingest exception returns 500."""
    response = client.post(
        "/upload",
        data={"thread_id": "thread-abc"},
        files={"file": ("report.pdf", FAKE_PDF_BYTES, "application/pdf")},
    )
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# GET /threads/{id}/files
# ---------------------------------------------------------------------------

@patch("server.list_thread_files")
def test_get_thread_files_endpoint(mock_list_files):
    """Verify that the files endpoint returns a list of uploaded filenames."""
    mock_list_files.return_value = [
        {"filename": "report.pdf", "chunks": 42, "uploaded_at": "2025-05-15T10:00:00"},
    ]

    response = client.get("/threads/thread-abc/files")

    assert response.status_code == 200
    body = response.json()
    assert "files" in body
    assert body["files"][0]["filename"] == "report.pdf"
    mock_list_files.assert_called_once_with("thread-abc")
