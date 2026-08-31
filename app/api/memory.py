"""Memory API — CRUD, search, and project-scoped derived knowledge."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.middleware.tenancy import TenantContext, get_tenant_context
from app.models import Memory
from app.schemas import MemoryCreate, MemoryUpdate, MemoryOut, MemorySearchRequest


router = APIRouter(prefix="/memory", tags=["memory"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── CRUD ────────────────────────────────────────────────────────────────


@router.post("/", response_model=MemoryOut, status_code=201)
async def create_memory(
    data: MemoryCreate,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Create a new memory in the workspace."""
    memory = Memory(
        workspace_id=tc.workspace_id,
        user_id=tc.user_id,
        agent_id=data.agent_id,
        run_id=data.run_id,
        project_id=data.project_id,
        memory_type=data.memory_type,
        content=data.content,
        extra_metadata=data.extra_metadata,
    )
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    return memory


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
):
    """List memories for the current user in the workspace."""
    query = select(Memory).where(
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
):
    """Get a specific memory by ID."""
    result = await db.execute(
        select(Memory).where(
            Memory.id == memory_id,
            Memory.workspace_id == tc.workspace_id,
            Memory.user_id == tc.user_id,
            Memory.deleted_at.is_(None),
        )
    )
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@router.patch("/{memory_id}", response_model=MemoryOut)
async def update_memory(
    memory_id: str,
    data: MemoryUpdate,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Update a memory (content, type, project, temporal status)."""
    result = await db.execute(
        select(Memory).where(
            Memory.id == memory_id,
            Memory.workspace_id == tc.workspace_id,
            Memory.user_id == tc.user_id,
            Memory.deleted_at.is_(None),
        )
    )
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    if data.content is not None:
        memory.content = data.content
    if data.memory_type is not None:
        memory.memory_type = data.memory_type
    if data.project_id is not None:
        memory.project_id = data.project_id
    if data.temporal_status is not None:
        memory.temporal_status = data.temporal_status
    memory.updated_at = _now()
    await db.commit()
    await db.refresh(memory)
    return memory


@router.delete("/{memory_id}", status_code=204)
async def delete_memory(
    memory_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a memory."""
    result = await db.execute(
        select(Memory).where(
            Memory.id == memory_id,
            Memory.workspace_id == tc.workspace_id,
            Memory.user_id == tc.user_id,
            Memory.deleted_at.is_(None),
        )
    )
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    memory.deleted_at = _now()
    await db.commit()


@router.post("/search", response_model=list[MemoryOut])
async def search_memories(
    data: MemorySearchRequest,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Full-text search across user's memories."""
    query = select(Memory).where(
        Memory.workspace_id == tc.workspace_id,
        Memory.user_id == tc.user_id,
        Memory.deleted_at.is_(None),
        Memory.content.ilike(f"%{data.query}%"),
    )
    if data.memory_type:
        query = query.where(Memory.memory_type == data.memory_type)
    query = query.order_by(Memory.created_at.desc()).limit(data.limit)
    result = await db.execute(query)
    return result.scalars().all()
