"""MinIO storage provider stub for Sprint 6.

Requires: pip install minio
Enabled via: storage_backend=minio in settings.
"""

from __future__ import annotations

from typing import BinaryIO

from app.services.object_storage import StorageProvider, StorageError


class MinIOStorageProvider(StorageProvider):
    """MinIO-compatible storage provider.

    Configure via settings:
        storage_backend = "minio"
        s3_endpoint = "http://localhost:9000"
        s3_access_key = "..."
        s3_secret_key = "..."
        s3_bucket = "swarmvault-uploads"
        s3_region = "us-east-1"
    """

    def __init__(self) -> None:
        try:
            from minio import Minio
            self._Minio = Minio
        except ImportError:
            raise StorageError("minio is required. Install: pip install minio")

        self._bucket = settings.s3_bucket
        self._client = Minio(
            settings.s3_endpoint.replace("http://", "").replace("https://", ""),
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            secure=settings.s3_endpoint.startswith("https"),
            region=settings.s3_region,
        )

        # Ensure bucket exists
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

    async def save(self, key: str, data: bytes | BinaryIO, content_type: str | None = None,
                   metadata: dict[str, str] | None = None) -> str:
        if isinstance(data, bytes):
            self._client.put_object(
                self._bucket, key, data, length=len(data),
                content_type=content_type or "application/octet-stream",
                metadata=metadata or {},
            )
        else:
            self._client.put_object(
                self._bucket, key, data, length=-1,
                content_type=content_type or "application/octet-stream",
                metadata=metadata or {},
            )
        return f"minio://{self._bucket}/{key}"

    async def load(self, key: str) -> bytes:
        try:
            response = self._client.get_object(self._bucket, key)
            return response.read()
        except Exception as e:
            raise StorageError(f"MinIO error: {e}")

    async def delete(self, key: str) -> None:
        try:
            self._client.remove_object(self._bucket, key)
        except Exception:
            pass

    async def exists(self, key: str) -> bool:
        try:
            self._client.stat_object(self._bucket, key)
            return True
        except Exception:
            return False

    async def presign_url(self, key: str, expires_seconds: int = 3600) -> str:
        return self._client.presigned_get_object(
            self._bucket, key, expires=expires_seconds
        )
