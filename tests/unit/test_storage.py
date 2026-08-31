"""Sprint 6 — Object storage tests."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from app.services.object_storage import (
    LocalStorageProvider,
    StorageError,
    content_hash,
    guess_content_type,
    _key_for,
)


class TestContentHash:
    def test_stable_hash(self):
        assert content_hash(b"hello") == content_hash(b"hello")

    def test_different_inputs_different_hash(self):
        assert content_hash(b"hello") != content_hash(b"world")

    def test_hex_format(self):
        h = content_hash(b"test")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


class TestGuessContentType:
    def test_pdf(self):
        assert "application/pdf" in guess_content_type("doc.pdf")

    def test_json(self):
        assert guess_content_type("data.json") == "application/json"

    def test_unknown(self):
        assert guess_content_type("file.xyz123") == "application/octet-stream"

    def test_no_extension(self):
        assert guess_content_type("noext") == "application/octet-stream"


class TestKeyFor:
    def test_builds_key(self):
        key = _key_for("abc123def456", "report.pdf")
        assert key == "ab/abc123def456.pdf"

    def test_no_extension(self):
        key = _key_for("abc123def456", "noext")
        assert key == "ab/abc123def456"


class TestLocalStorageProvider:
    def test_save_and_load(self, tmp_path):
        provider = LocalStorageProvider(base_path=str(tmp_path))
        key = "test/file.txt"
        data = b"Hello, storage!"

        import asyncio
        url = asyncio.run(provider.save(key, data))
        assert url.endswith(key)

        loaded = asyncio.run(provider.load(key))
        assert loaded == data

    def test_exists(self, tmp_path):
        provider = LocalStorageProvider(base_path=str(tmp_path))
        asyncio = __import__("asyncio")
        asyncio.run(provider.save("exists/test.txt", b"data"))

        assert asyncio.run(provider.exists("exists/test.txt"))
        assert not asyncio.run(provider.exists("exists/missing.txt"))

    def test_delete(self, tmp_path):
        provider = LocalStorageProvider(base_path=str(tmp_path))
        asyncio = __import__("asyncio")
        asyncio.run(provider.save("del/test.txt", b"data"))
        assert asyncio.run(provider.exists("del/test.txt"))

        asyncio.run(provider.delete("del/test.txt"))
        assert not asyncio.run(provider.exists("del/test.txt"))

    def test_delete_missing_is_idempotent(self, tmp_path):
        provider = LocalStorageProvider(base_path=str(tmp_path))
        asyncio = __import__("asyncio")
        # Should not raise
        asyncio.run(provider.delete("missing/file.txt"))

    def test_path_traversal_blocked(self, tmp_path):
        provider = LocalStorageProvider(base_path=str(tmp_path))
        asyncio = __import__("asyncio")
        with pytest.raises(StorageError, match="traversal"):
            asyncio.run(provider.save("../../../etc/passwd", b"evil"))

    def test_presign_url_local(self, tmp_path):
        """Local storage returns the internal URL."""
        provider = LocalStorageProvider(base_path=str(tmp_path))
        asyncio = __import__("asyncio")
        asyncio.run(provider.save("url/test.txt", b"data"))
        url = asyncio.run(provider.presign_url("url/test.txt"))
        assert "url/test.txt" in url


class TestStorageFactory:
    def test_defaults_to_local(self):
        from app.core.config import settings
        original = settings.storage_backend
        settings.storage_backend = "filesystem"
        try:
            provider = __import__("app.services.object_storage", fromlist=["get_storage_provider"]).get_storage_provider()
            assert isinstance(provider, LocalStorageProvider)
        finally:
            settings.storage_backend = original

    def test_unknown_backend_falls_back_to_local(self):
        """Unknown backends gracefully fall back to local."""
        from app.core.config import settings
        original = settings.storage_backend
        settings.storage_backend = "unknown-backend"
        try:
            provider = __import__("app.services.object_storage", fromlist=["get_storage_provider"]).get_storage_provider()
            assert isinstance(provider, LocalStorageProvider)
        finally:
            settings.storage_backend = original
