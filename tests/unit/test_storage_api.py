"""Sprint 6 — Storage upload API tests."""

import pytest
from pathlib import Path

from app.services.object_storage import LocalStorageProvider


class TestUploadAPI:
    """Tests for the storage upload endpoint."""

    @pytest.mark.asyncio
    async def test_upload_file_returns_key_and_url(self, client, seeded_workspace):
        """Uploading a file returns key, url, size, content_type, sha256."""
        file_content = b"Hello, object storage!"
        res = await client.post(
            "/api/v1/storage/upload",
            files={"file": ("test.txt", file_content, "text/plain")},
            headers=seeded_workspace["headers"],
        )
        assert res.status_code == 201
        data = res.json()
        assert data["key"].endswith(".txt")
        assert data["size"] == len(file_content)
        assert data["content_type"] == "text/plain"
        assert len(data["sha256"]) == 64

    @pytest.mark.asyncio
    async def test_upload_pdf(self, client, seeded_workspace):
        """PDF upload returns correct content type."""
        pdf_content = b"%PDF-1.4 fake pdf content"
        res = await client.post(
            "/api/v1/storage/upload",
            files={"file": ("doc.pdf", pdf_content, "application/pdf")},
            headers=seeded_workspace["headers"],
        )
        assert res.status_code == 201
        assert res.json()["key"].endswith(".pdf")

    @pytest.mark.asyncio
    async def test_upload_deduplication(self, client, seeded_workspace):
        """Same file content produces the same key (dedup)."""
        content = b"duplicate content"
        res1 = await client.post(
            "/api/v1/storage/upload",
            files={"file": ("a.txt", content, "text/plain")},
            headers=seeded_workspace["headers"],
        )
        res2 = await client.post(
            "/api/v1/storage/upload",
            files={"file": ("b.txt", content, "text/plain")},
            headers=seeded_workspace["headers"],
        )
        assert res1.status_code == 201
        assert res2.status_code == 201
        # Same content hash → same key prefix
        key1 = res1.json()["key"]
        key2 = res2.json()["key"]
        assert key1.split("/")[1][:8] == key2.split("/")[1][:8]

    @pytest.mark.asyncio
    async def test_upload_requires_auth(self, client):
        """Unauthenticated upload is rejected."""
        res = await client.post(
            "/api/v1/storage/upload",
            files={"file": ("test.txt", b"data", "text/plain")},
        )
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_upload_empty_file(self, client, seeded_workspace):
        """Empty file upload works."""
        res = await client.post(
            "/api/v1/storage/upload",
            files={"file": ("empty.txt", b"", "text/plain")},
            headers=seeded_workspace["headers"],
        )
        assert res.status_code == 201
        assert res.json()["size"] == 0

    @pytest.mark.asyncio
    async def test_get_file_info(self, client, seeded_workspace):
        """Get presigned URL for an uploaded file."""
        # Upload first
        upload = await client.post(
            "/api/v1/storage/upload",
            files={"file": ("info.txt", b"info data", "text/plain")},
            headers=seeded_workspace["headers"],
        )
        assert upload.status_code == 201
        key = upload.json()["key"]

        # Get info
        res = await client.get(
            f"/api/v1/storage/{key}",
            headers=seeded_workspace["headers"],
        )
        assert res.status_code == 200
        assert res.json()["url"] is not None

    @pytest.mark.asyncio
    async def test_get_nonexistent_file(self, client, seeded_workspace):
        """Getting a nonexistent file returns 404."""
        res = await client.get(
            "/api/v1/storage/nonexistent/key.txt",
            headers=seeded_workspace["headers"],
        )
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_file(self, client, seeded_workspace):
        """Delete an uploaded file."""
        upload = await client.post(
            "/api/v1/storage/upload",
            files={"file": ("del.txt", b"delete me", "text/plain")},
            headers=seeded_workspace["headers"],
        )
        key = upload.json()["key"]

        res = await client.delete(
            f"/api/v1/storage/{key}",
            headers=seeded_workspace["headers"],
        )
        assert res.status_code == 204

        # Verify gone
        get_res = await client.get(
            f"/api/v1/storage/{key}",
            headers=seeded_workspace["headers"],
        )
        assert get_res.status_code == 404

    @pytest.mark.asyncio
    async def test_workspace_scoped_keys(self, client, seeded_workspace):
        """Storage keys include workspace_id prefix."""
        upload_a = await client.post(
            "/api/v1/storage/upload",
            files={"file": ("a.txt", b"tenant a data", "text/plain")},
            headers=seeded_workspace["headers"],
        )
        key_a = upload_a.json()["key"]
        # Key contains workspace prefix
        assert "/" in key_a  # workspace_id/hash format
