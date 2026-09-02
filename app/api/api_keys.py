"""Sprint 6 — API key management for MCP server registration.

Endpoints:
  POST   /api/v1/api-keys/           create a key (returns it once)
  GET    /api/v1/api-keys/           list keys (masked)
  DELETE /api/v1/api-keys/{key_id}   revoke a key
  POST   /api/v1/api-keys/{key_id}/rotate  rotate (create new, revoke old)

Keys are scoped to a workspace and can carry optional metadata (server name,
description, allowed tools).  The key hash is stored; the raw key is returned
exactly once at creation time and is never logged.
"""

from __future__ import annotations

import secrets
import hashlib
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.middleware.tenancy import TenantContext, get_tenant_context
from app.middleware.rbac import require_min_role
from app.models import ApiKey
from app.schemas import ApiKeyOut
from app.services.audit import (
    AuditService,
    API_KEY_CREATED,
    API_KEY_REVOKED,
    API_KEY_ROTATED,
    RESULT_SUCCESS,
    RESULT_FAILURE,
)

_audit = AuditService()


router = APIRouter(prefix="/api-keys", tags=["api-keys"])


# ── Schemas ────────────────────────────────────────────────────────────


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Human-readable name")
    description: str | None = Field(None, max_length=500)
    expires_at: datetime | None = Field(None, description="ISO-8601 expiry; null = never")
    metadata: dict[str, str] | None = Field(None, description="Arbitrary key-value metadata")


class ApiKeyCreateResponse(BaseModel):
    """Returns the full key on creation — the only time it's visible."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    key_prefix: str
    created_at: datetime
    expires_at: datetime | None = None
    key_extra: dict[str, str] | None = None
    raw_key: str


class ApiKeyRotateResponse(BaseModel):
    """Rotation returns both the new key and a confirmation."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    key_prefix: str
    raw_key: str  # new key, only time visible
    rotated_at: datetime


# ── Helpers ───────────────────────────────────────────────────────────


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _prefix(raw: str, length: int = 8) -> str:
    return raw[:length]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _generate_key() -> str:
    """Generate a 32-character hex API key."""
    return secrets.token_hex(32)


# ── CRUD ──────────────────────────────────────────────────────────────


@router.post("/", response_model=ApiKeyCreateResponse, status_code=201)
async def create_api_key(
    data: ApiKeyCreate,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_min_role("admin")),
):
    """Create a new API key for the current workspace."""
    raw_key = _generate_key()
    key_hash = _hash_key(raw_key)

    key = ApiKey(
        workspace_id=tc.workspace_id,
        user_id=tc.user_id,
        name=data.name,
        key_hash=key_hash,
        key_prefix=_prefix(raw_key),
        description=data.description,
        expires_at=data.expires_at,
        key_extra=data.metadata,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)

    _audit.emit(
        event_type=API_KEY_CREATED,
        result_status=RESULT_SUCCESS,
        principal_id=tc.user_id,
        principal_type="user",
        resource_type="api_key",
        resource_id=str(key.id),
        action="create",
        tenant_id=tc.tenant_id,
        workspace_id=tc.workspace_id,
        request_id=getattr(tc, "request_id", None),
        metadata={"key_prefix": key.key_prefix, "key_name": key.name},
    )

    return ApiKeyCreateResponse(
        id=key.id,
        name=key.name,
        description=key.description,
        key_prefix=key.key_prefix,
        created_at=key.created_at,
        expires_at=key.expires_at,
        key_extra=dict(key.key_extra) if key.key_extra else None,
        raw_key=raw_key,
    )


@router.get("/", response_model=list[ApiKeyOut])
async def list_api_keys(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """List all API keys for the current workspace (keys are never returned)."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.workspace_id == tc.workspace_id,
            ApiKey.revoked_at.is_(None),
        ).order_by(ApiKey.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/{key_id}", status_code=204)
async def revoke_api_key(
    key_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_min_role("admin")),
):
    """Revoke an API key immediately."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.workspace_id == tc.workspace_id,
        )
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    key.revoked_at = _now()
    await db.commit()

    _audit.emit(
        event_type=API_KEY_REVOKED,
        result_status=RESULT_SUCCESS,
        principal_id=tc.user_id,
        principal_type="user",
        resource_type="api_key",
        resource_id=str(key.id),
        action="revoke",
        tenant_id=tc.tenant_id,
        workspace_id=tc.workspace_id,
        request_id=getattr(tc, "request_id", None),
        metadata={"key_prefix": key.key_prefix},
    )
    return None


@router.post("/{key_id}/rotate", response_model=ApiKeyRotateResponse)
async def rotate_api_key(
    key_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_min_role("admin")),
):
    """Rotate an API key: creates a new one with the same metadata and revokes the old."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.workspace_id == tc.workspace_id,
        )
    )
    old_key = result.scalar_one_or_none()
    if not old_key:
        raise HTTPException(status_code=404, detail="API key not found")

    new_raw = _generate_key()
    new_key = ApiKey(
        workspace_id=old_key.workspace_id,
        user_id=old_key.user_id,
        name=old_key.name,
        key_hash=_hash_key(new_raw),
        key_prefix=_prefix(new_raw),
        description=old_key.description,
        expires_at=old_key.expires_at,
        key_extra=old_key.key_extra,
    )
    old_key.revoked_at = _now()
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)

    _audit.emit(
        event_type=API_KEY_ROTATED,
        result_status=RESULT_SUCCESS,
        principal_id=tc.user_id,
        principal_type="user",
        resource_type="api_key",
        resource_id=str(new_key.id),
        action="rotate",
        tenant_id=tc.tenant_id,
        workspace_id=tc.workspace_id,
        request_id=getattr(tc, "request_id", None),
        metadata={"old_key_prefix": old_key.key_prefix, "new_key_prefix": new_key.key_prefix},
    )

    return ApiKeyRotateResponse(
        id=new_key.id,
        name=new_key.name,
        key_prefix=new_key.key_prefix,
        raw_key=new_raw,
        rotated_at=_now(),
    )


# ── Authentication by API key ─────────────────────────────────────────


async def authenticate_api_key(raw_key: str, db: AsyncSession) -> ApiKey | None:
    """Look up an API key by its raw value.  Returns None if invalid."""
    key_hash = _hash_key(raw_key)
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.key_hash == key_hash,
            ApiKey.revoked_at.is_(None),
        )
    )
    key = result.scalar_one_or_none()
    if key and key.expires_at and key.expires_at < _now():
        return None
    return key
