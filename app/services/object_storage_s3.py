"""S3 storage provider stub for Sprint 6.

Requires: pip install boto3
Enabled via: storage_backend=s3 in settings.
"""

from __future__ import annotations

from typing import BinaryIO

from app.services.object_storage import StorageProvider, StorageError


class S3StorageProvider(StorageProvider):
    """AWS S3 storage provider.

    Configure via settings:
        storage_backend = "s3"
        s3_endpoint = "https://s3.amazonaws.com"  # or custom for S3-compatible
        s3_access_key = "..."
        s3_secret_key = "..."
        s3_bucket = "swarmvault-uploads"
        s3_region = "us-east-1"
    """

    def __init__(self) -> None:
        try:
            import boto3
            from botocore.exceptions import ClientError
            self._boto3 = boto3
            self._ClientError = ClientError
        except ImportError:
            raise StorageError("boto3 is required for S3 storage. Install: pip install boto3")

        self._bucket = settings.s3_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint or None,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        )

    async def save(self, key: str, data: bytes | BinaryIO, content_type: str | None = None,
                   metadata: dict[str, str] | None = None) -> str:
        extra = {}
        if content_type:
            extra["ContentType"] = content_type
        if metadata:
            extra["Metadata"] = metadata

        if isinstance(data, bytes):
            self._client.put_object(Bucket=self._bucket, Key=key, Body=data, **extra)
        else:
            self._client.upload_fileobj(data, self._bucket, key, ExtraArgs=extra)

        return f"s3://{self._bucket}/{key}"

    async def load(self, key: str) -> bytes:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
            return response["Body"].read()
        except self._ClientError as e:
            raise StorageError(f"S3 error: {e}")

    async def delete(self, key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
        except self._ClientError:
            pass

    async def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except self._ClientError:
            return False

    async def presign_url(self, key: str, expires_seconds: int = 3600) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_seconds,
        )
