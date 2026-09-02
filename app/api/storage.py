"""Sprint 7 — Secure object storage API.

All endpoints are workspace-scoped with RBAC enforcement.
Files are keyed by workspace + content hash to prevent cross-workspace access.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.core.config import settings
from app.db import get_db
from app.middleware.tenancy import TenantContext, get_tenant_context
from app.middleware.rbac import require_min_role
from app.services.object_storage import get_storage_provider, content_hash, guess_content_type


router = APIRouter(prefix="/storage", tags=["storage"])

# Max upload size: 50 MB
_MAX_UPLOAD_BYTES = 50 * 1024 * 1024


class UploadResponse(BaseModel):
    key: str
    url: str
    size: int
    content_type: str
    sha256: str


class FileListResponse(BaseModel):
    items: list[dict]
    total: int


def _check_key_workspace(key: str, workspace_id: str) -> None:
    """Verify a storage key belongs to the given workspace.

    Returns 404 for non-matching keys to prevent information leakage
    about which workspaces have files.
    """
    if not key or ".." in key or key.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid storage key")
    expected_prefix = f"{workspace_id}/"
    if not key.startswith(expected_prefix):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")


@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    tc: Annotated[TenantContext, Depends(get_tenant_context)] = ...,
    _: None = Depends(require_min_role("member")),
):
    """Upload a file to object storage.

    Files are workspace-scoped and deduplicated by content hash.
    Max file size: 50 MB.
    """
    storage = get_storage_provider()

    # Check Content-Length header first (if provided)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {_MAX_UPLOAD_BYTES // (1024*1024)} MB",
        )

    # Read file content with streaming size check
    content = await file.read()
    total_size = len(content)
    if total_size > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {_MAX_UPLOAD_BYTES // (1024*1024)} MB",
        )

    sha = hashlib.sha256(content).hexdigest()

    # Build storage key: workspace-scoped + content hash
    ext = Path(file.filename or "file").suffix or ""
    key = f"{tc.workspace_id}/{sha[:8]}{ext}"

    # Determine content type
    ctype = file.content_type or guess_content_type(file.filename or "file")

    # Store
    url = await storage.save(key, content, content_type=ctype, metadata={
        "workspace_id": tc.workspace_id,
        "original_name": file.filename or "unknown",
    })

    return UploadResponse(
        key=key,
        url=url,
        size=len(content),
        content_type=ctype,
        sha256=sha,
    )


@router.get("/{key:path}", response_model=dict)
async def get_file_info(
    key: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    request: Request,
):
    """Get a presigned URL for a file.

    The file must belong to the caller's workspace.
    """
    _check_key_workspace(key, tc.workspace_id)
    storage = get_storage_provider()
    if not await storage.exists(key):
        raise HTTPException(status_code=404, detail="File not found")
    url = await storage.presign_url(key)
    return {"key": key, "url": url}


@router.delete("/{key:path}", status_code=204)
async def delete_file(
    key: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    _: None = Depends(require_min_role("admin")),
):
    """Delete a file from storage.

    The file must belong to the caller's workspace.
    Requires admin role.
    """
    _check_key_workspace(key, tc.workspace_id)
    storage = get_storage_provider()
    if not await storage.exists(key):
        raise HTTPException(status_code=404, detail="File not found")
    await storage.delete(key)
    return None
