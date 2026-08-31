from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.middleware.tenancy import TenantContext, get_tenant_context
from app.models import MessageProvenance, Memory
from app.schemas import ProvenanceOut, MemoryReferenceOut

router = APIRouter(prefix="/provenance", tags=["provenance"])


@router.get("/", response_model=list[ProvenanceOut])
async def list_provenance(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    session_id: str | None = Query(None),
    project_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List provenance records for this workspace.

    Optionally filter by session_id or project_id.
    """
    stmt = select(MessageProvenance).where(
        MessageProvenance.workspace_id == tc.workspace_id
    )
    if session_id:
        stmt = stmt.where(MessageProvenance.session_id == session_id)
    if project_id:
        stmt = stmt.where(MessageProvenance.project_id == project_id)

    stmt = stmt.order_by(MessageProvenance.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    records = result.scalars().all()

    return [
        ProvenanceOut(
            id=str(r.id),
            workspace_id=str(r.workspace_id),
            project_id=str(r.project_id) if r.project_id else None,
            session_id=str(r.session_id) if r.session_id else None,
            user_message_id=str(r.user_message_id) if r.user_message_id else None,
            assistant_message_id=str(r.assistant_message_id) if r.assistant_message_id else None,
            model=r.model,
            provider=r.provider,
            retrieval_method=r.retrieval_method,
            memory_ids_used=r.memory_ids_used,
            retrieval_sources=r.retrieval_sources,
            user_message_preview=r.user_message_preview,
            prompt_tokens=r.prompt_tokens,
            completion_tokens=r.completion_tokens,
            total_tokens=r.total_tokens,
            latency_ms=r.latency_ms,
            confidence=r.confidence,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.get("/{provenance_id}", response_model=ProvenanceOut)
async def get_provenance(
    provenance_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Get a single provenance record by ID."""
    result = await db.execute(
        select(MessageProvenance).where(
            MessageProvenance.id == provenance_id,
            MessageProvenance.workspace_id == tc.workspace_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Provenance record not found")

    return ProvenanceOut(
        id=str(record.id),
        workspace_id=str(record.workspace_id),
        project_id=str(record.project_id) if record.project_id else None,
        session_id=str(record.session_id) if record.session_id else None,
        user_message_id=str(record.user_message_id) if record.user_message_id else None,
        assistant_message_id=str(record.assistant_message_id) if record.assistant_message_id else None,
        model=record.model,
        provider=record.provider,
        retrieval_method=record.retrieval_method,
        memory_ids_used=record.memory_ids_used,
        retrieval_sources=record.retrieval_sources,
        user_message_preview=record.user_message_preview,
        prompt_tokens=record.prompt_tokens,
        completion_tokens=record.completion_tokens,
        total_tokens=record.total_tokens,
        latency_ms=record.latency_ms,
        confidence=record.confidence,
        created_at=record.created_at,
    )


@router.get("/{provenance_id}/memories", response_model=list[MemoryReferenceOut])
async def get_provenance_memories(
    provenance_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Expand memory_ids_used into readable memory reference objects."""
    result = await db.execute(
        select(MessageProvenance).where(
            MessageProvenance.id == provenance_id,
            MessageProvenance.workspace_id == tc.workspace_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Provenance record not found")

    memory_ids = record.memory_ids_used or []
    if not memory_ids:
        return []

    mem_result = await db.execute(
        select(Memory).where(
            Memory.id.in_(memory_ids),
            Memory.workspace_id == tc.workspace_id,
            Memory.deleted_at.is_(None),
        )
    )
    memories = mem_result.scalars().all()

    return [
        MemoryReferenceOut(
            memory_id=str(m.id),
            content=m.content,
            memory_type=m.memory_type,
            confidence=m.confidence,
            authority=m.authority,
            temporal_status=m.temporal_status,
            created_at=m.created_at,
            project_id=m.project_id,
        )
        for m in memories
    ]
