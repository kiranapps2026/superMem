"""Sprint 6 — Object storage for large files.

The database stores metadata.  Large files (PDFs, images, CSV exports, etc.)
live in object storage.  This module provides a provider-agnostic interface
backed by the local filesystem by default; S3 and MinIO are additional
backends selected via configuration.

Never write a secret to disk or log.  Keys are loaded from settings only.
"""

from __future__ import annotations

import io
import mimetypes
import os
import shutil
import hashlib
from pathlib import Path
from typing import BinaryIO

from app.core.config import settings


class StorageError(Exception):
    """Raised when a storage operation fails."""


class StorageProvider:
    """Protocol-style base — all providers share these methods."""

    async def save(
        self,
        key: str,
        data: bytes | BinaryIO,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Store bytes under *key*.  Returns the resolved URL."""
        ...

    async def load(self, key: str) -> bytes:
        """Return the raw bytes for *key*.  Raises StorageError if missing."""
        ...

    async def delete(self, key: str) -> None:
        """Remove *key* from storage.  Idempotent (no error if missing)."""
        ...

    async def exists(self, key: str) -> bool:
        """Return True if *key* exists in storage."""
        ...

    async def presign_url(self, key: str, expires_seconds: int = 3600) -> str:
        """Return a time-limited download URL.  Must be overridden by cloud providers."""
        ...


class LocalStorageProvider(StorageProvider):
    """Filesystem-backed storage — the default.

    Files are stored under ``settings.storage_path`` with *key* used as the
    relative path.  The directory tree is created automatically.
    """

    def __init__(self, base_path: str | None = None) -> None:
        self._base = Path(base_path or settings.storage_path).resolve()
        self._base.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        """Resolve a key to a filesystem path, preventing path traversal."""
        # Normalise and reject traversal attempts
        resolved = (self._base / key).resolve()
        if not str(resolved).startswith(str(self._base)):
            raise StorageError(f"Path traversal detected: {key}")
        return resolved

    async def save(
        self,
        key: str,
        data: bytes | BinaryIO,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, bytes):
            path.write_bytes(data)
        else:
            with open(path, "wb") as f:
                shutil.copyfileobj(data, f)
        return self._url_for(key)

    async def load(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.exists():
            raise StorageError(f"Object not found: {key}")
        return path.read_bytes()

    async def delete(self, key: str) -> None:
        try:
            path = self._resolve(key)
            path.unlink(missing_ok=True)
        except OSError:
            pass

    async def exists(self, key: str) -> bool:
        return self._resolve(key).exists()

    async def presign_url(self, key: str, expires_seconds: int = 3600) -> str:
        return self._url_for(key)

    def _url_for(self, key: str) -> str:
        return f"/storage/{key}"


def _key_for(content_hash: str, filename: str) -> str:
    """Build a storage key from content hash + original filename."""
    ext = Path(filename).suffix or ""
    return f"{content_hash[:2]}/{content_hash}{ext}"


def content_hash(data: bytes) -> str:
    """SHA-256 hex digest used for dedup keys."""
    return hashlib.sha256(data).hexdigest()


def guess_content_type(filename: str) -> str:
    """Return MIME type from filename extension."""
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"


def get_storage_provider() -> StorageProvider:
    """Return the configured storage provider."""
    provider = settings.storage_backend.lower()
    if provider == "s3":
        from app.services.object_storage_s3 import S3StorageProvider
        return S3StorageProvider()
    if provider == "minio":
        from app.services.object_storage_minio import MinIOStorageProvider
        return MinIOStorageProvider()
    return LocalStorageProvider()
