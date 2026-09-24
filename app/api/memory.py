"""Memory API — CRUD, search, and project-scoped derived knowledge.

Architecture (Sprint 8):
  HTTP Request
    ↓
  Router (validation, auth, response formatting)
    ↓
  MemoryService (business logic, policy, persistence, audit)
    ↓
  PostgreSQL (source of truth)

The router delegates all business logic to MemoryService.
Direct SQLAlchemy access is limited to the MemoryService itself.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.middleware.tenancy import TenantContext, get_tenant_context
from app.middleware.rbac import require_min_role
from app.models import Memory
from app.schemas import MemoryCreate, MemoryUpdate, MemoryOut, MemorySearchRequest
from app.services.policy.dependencies import require_policy
from app.services.memory import MemoryService, MemoryRecord

# Singleton MemoryService — initialized at startup
_memory_service: MemoryService | None = None


def get_memory_service() -> MemoryService:
    """Return the singleton MemoryService, creating it if needed."""
    global _memory_service
    if _memory_service is None:
        from app.services.audit.service import AuditService
        _audit = AuditService()
        _audit.register_db_sink()
        _memory_service = MemoryService(audit_service=_audit)
    return _memory_service


router = APIRouter(prefix="/memory", tags=["memory"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _record_to_response(record: MemoryRecord, model: Memory) -> dict:
    """Convert a MemoryRecord + ORM model to MemoryOut-compatible dict."""
    return {
        "id": model.id,
        "workspace_id": model.workspace_id,
        "user_id": model.user_id,
        "agent_id": model.agent_id,
        "run_id": model.run_id,
        "project_id": model.project_id,
        "memory_type": model.memory_type,
        "content": model.content,
        "extra_metadata": model.extra_metadata,
        "temporal_status": model.temporal_status,
        "confidence": model.confidence,
        "authority": model.authority,
        "deleted_at": model.deleted_at,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


# ── CRUD ────────────────────────────────────────────────────────────────


@router.post("/", response_model=MemoryOut, status_code=201)
async def create_memory(
    data: MemoryCreate,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_policy("memory", "write")),
    ms: MemoryService = Depends(get_memory_service),
):
    """Create a new memory in the workspace.

    Delegates to MemoryService which handles:
      - policy authorization
      - provenance attachment
      - PostgreSQL persistence
      - audit event emission
    """
    request_id = getattr(tc, "_request_id", None) if hasattr(tc, "_request_id") else None

    record = MemoryRecord(
        memory_type=data.memory_type,
        scope="USER",
        tenant_id=tc.tenant_id,  # P0 fix: set tenant for isolation
        workspace_id=tc.workspace_id,
        user_id=tc.user_id,
        agent_id=data.agent_id,
        run_id=data.run_id,
        project_id=data.project_id,
        content=data.content,
        user_metadata=data.extra_metadata or {},  # FIX: preserve user metadata
    )

    # Write through MemoryService (persists to PostgreSQL)
    await ms.write(
        record,
        principal_id=tc.user_id,
        principal_type="user",
        session=db,
        provenance={"source": "api", "source_id": request_id, "method": "api_create"},
    )

    # Fetch the persisted ORM model for response
    result = await db.execute(
        select(Memory).where(
            Memory.id == record.memory_id,
            Memory.workspace_id == tc.workspace_id,  # P0 fix: defense-in-depth
        )
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=500, detail="Memory created but not retrievable")
    await db.commit()
    return _record_to_response(record, model)


@router.get("/", response_model=list[MemoryOut])
async def list_memories(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    memory_type: str | None = Query(None),
    project_id: str | None = Query(None),
    temporal_status: str | None = Query(None),
    include_deleted: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    ms: MemoryService = Depends(get_memory_service),
):
    """List memories for the current user in the workspace."""
    query = select(Memory).where(
        Memory.tenant_id == tc.tenant_id,
        Memory.workspace_id == tc.workspace_id,
        Memory.user_id == tc.user_id,
    )
    if memory_type:
        query = query.where(Memory.memory_type == memory_type)
    if project_id:
        query = query.where(Memory.project_id == project_id)
    if temporal_status:
        query = query.where(Memory.temporal_status == temporal_status)
    if not include_deleted:
        query = query.where(Memory.deleted_at.is_(None))
    query = query.order_by(Memory.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{memory_id}", response_model=MemoryOut)
async def get_memory(
    memory_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    ms: MemoryService = Depends(get_memory_service),
):
    """Get a specific memory by ID through MemoryService."""
    record = await ms.read(
        memory_id,
        principal_id=tc.user_id,
        principal_type="user",
        tenant_id=tc.tenant_id,
        session=db,
    )
    if not record:
        raise HTTPException(status_code=404, detail="Memory not found")

    # Fetch the ORM model for response formatting
    result = await db.execute(
        select(Memory).where(
            Memory.id == memory_id,
            Memory.workspace_id == tc.workspace_id,  # P0 fix: enforce workspace isolation
        )
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Memory not found")
    return _record_to_response(record, model)


@router.patch("/{memory_id}", response_model=MemoryOut)
async def update_memory(
    memory_id: str,
    data: MemoryUpdate,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_min_role("member")),
    ms: MemoryService = Depends(get_memory_service),
):
    """Update a memory. Requires member role.

    Delegates update to MemoryService.
    """
    updates = {}
    if data.content is not None:
        updates["content"] = data.content
    if data.memory_type is not None:
        updates["memory_type"] = data.memory_type
    if data.project_id is not None:
        updates["project_id"] = data.project_id
    if data.temporal_status is not None:
        updates["temporal_status"] = data.temporal_status

    record = await ms.update(
        memory_id,
        principal_id=tc.user_id,
        updates=updates,
        session=db,
        caller_tenant_id=tc.tenant_id,
    )
    if not record:
        raise HTTPException(status_code=404, detail="Memory not found")

    # Fetch updated ORM model for response
    result = await db.execute(
        select(Memory).where(
            Memory.id == memory_id,
            Memory.workspace_id == tc.workspace_id,
        )
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Memory not found")
    return _record_to_response(record, model)


@router.delete("/{memory_id}", status_code=204)
async def delete_memory(
    memory_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_min_role("owner")),
    __: None = Depends(require_policy("memory", "delete")),
    ms: MemoryService = Depends(get_memory_service),
):
    """Soft-delete a memory. Requires owner role.

    Delegates deletion to MemoryService.
    """
    deleted = await ms.delete(
        memory_id,
        principal_id=tc.user_id,
        session=db,
        caller_tenant_id=tc.tenant_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    await db.commit()
    return None


@router.post("/search", response_model=list[MemoryOut])
async def search_memories(
    data: MemorySearchRequest,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    ms: MemoryService = Depends(get_memory_service),
):
    """Full-text search across user's memories.

    Uses MemoryService for policy + audit, returns ORM models directly
    to avoid N+1 queries.
    """
    records = await ms.search(
        data.query,
        principal_id=tc.user_id,
        principal_type="user",
        memory_type=data.memory_type,
        workspace_id=tc.workspace_id,
        user_id=tc.user_id,
        limit=data.limit,
        session=db,
    )

    # Get the IDs of found records
    found_ids = [r.memory_id for r in records]
    if not found_ids:
        return []

    # Single query to get ORM models for response serialization
    result = await db.execute(
        select(Memory).where(
            Memory.id.in_(found_ids),
            Memory.workspace_id == tc.workspace_id,
            Memory.user_id == tc.user_id,
        )
    )
    # Preserve search order
    db_models = {m.id: m for m in result.scalars().all()}
    return [db_models[rid] for rid in found_ids if rid in db_models]
