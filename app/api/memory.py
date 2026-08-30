from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.middleware.tenancy import TenantContext, get_tenant_context
from app.models import Memory
from app.schemas import MemoryCreate, MemoryOut, MemorySearchRequest
from datetime import datetime, timezone

router = APIRouter(prefix="/memory", tags=["memory"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/", response_model=MemoryOut, status_code=status.HTTP_201_CREATED)
async def add_memory(
    data: MemoryCreate,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    memory = Memory(
        workspace_id=tc.workspace_id,
        user_id=tc.user_id,
        agent_id=data.agent_id,
        run_id=data.run_id,
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
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    query = select(Memory).where(
        Memory.workspace_id == tc.workspace_id,
        Memory.user_id == tc.user_id,
    )
    if memory_type:
        query = query.where(Memory.memory_type == memory_type)
    query = query.order_by(Memory.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/search", response_model=list[MemoryOut])
async def search_memories(
    data: MemorySearchRequest,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    query = select(Memory).where(
        Memory.workspace_id == tc.workspace_id,
        Memory.user_id == tc.user_id,
        Memory.content.ilike(f"%{data.query}%"),
    )
    if data.memory_type:
        query = query.where(Memory.memory_type == data.memory_type)
    query = query.order_by(Memory.created_at.desc()).limit(data.limit)
    result = await db.execute(query)
    return result.scalars().all()
