"""Sprint 6 — Object storage API for large file uploads.

Endpoints:
  POST   /api/v1/storage/upload    upload a file
  GET    /api/v1/storage/{key}     download (presigned URL)
  DELETE /api/v1/storage/{key}     delete
  GET    /api/v1/storage/          list files for workspace
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.middleware.tenancy import TenantContext, get_tenant_context
from app.services.object_storage import get_storage_provider, content_hash, guess_content_type


router = APIRouter(prefix="/storage", tags=["storage"])


class UploadResponse(BaseModel):
    key: str
    url: str
    size: int
    content_type: str
    sha256: str


class FileListResponse(BaseModel):
    items: list[dict]
    total: int


@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    tc: Annotated[TenantContext, Depends(get_tenant_context)] = ...,
):
    """Upload a file to object storage.

    The key is derived from the file content hash for deduplication.
    Files are scoped to the workspace.
    """
    storage = get_storage_provider()

    # Read file content
    content = await file.read()
    size = len(content)
    sha = hashlib.sha256(content).hexdigest()

    # Build storage key: workspace-scoped + content hash
    ext = Path(file.filename or "file").suffix or ""
    key = f"{tc.workspace_id}/{sha[:8]}{ext}"

    # Determine content type
    ctype = file.content_type or guess_content_type(file.filename or "file")

    # Store (dedup handled by provider if supported)
    url = await storage.save(key, content, content_type=ctype, metadata={
        "workspace_id": tc.workspace_id,
        "original_name": file.filename or "unknown",
    })

    return UploadResponse(
        key=key,
        url=url,
        size=size,
        content_type=ctype,
        sha256=sha,
    )


@router.get("/{key:path}", response_model=dict)
async def get_file_info(key: str):
    """Get a presigned URL for a file."""
    storage = get_storage_provider()
    if not await storage.exists(key):
        raise HTTPException(status_code=404, detail="File not found")
    url = await storage.presign_url(key)
    return {"key": key, "url": url}


@router.delete("/{key:path}", status_code=204)
async def delete_file(key: str):
    """Delete a file from storage."""
    storage = get_storage_provider()
    await storage.delete(key)
    return None
