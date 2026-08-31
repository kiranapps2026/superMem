"""Sprint 3 API routes: sources, facts, decisions, graph, timeline, search."""

from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.middleware.tenancy import TenantContext, get_tenant_context
from app.models import (
    Source, NormalizedMessage, Fact, Decision,
    GraphNode, GraphEdge, Memory, Project,
)
from app.schemas import (
    IngestUploadRequest, IngestUploadResponse, IngestQueued, IngestJobOut,
    SourceOut, SourceDetail, SourceListResponse, NormalizedMessageOut,
    FactOut, FactListResponse,
    DecisionOut, DecisionListResponse,
    GraphNodeOut, GraphEdgeOut, GraphResponse,
    TimelineItem, TimelineResponse,
    SearchResultItem, SearchResponse,
)
from app.services.m5_retrieval import retrieve_hybrid, RetrievalResult

router = APIRouter(prefix="/ingest", tags=["ingest"])


# ── Upload / Pipeline ──────────────────────────────────────────────────


@router.post("/upload", response_model=IngestUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_and_ingest(
    data: IngestUploadRequest,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Upload a conversation and run the full M0→M1→M2→M3→M4 pipeline.

    Deduplication: if content with the same hash was already ingested for this
    workspace, the existing source is returned without reprocessing.
    """
    # Verify project exists in this workspace
    proj_result = await db.execute(
        select(Project).where(
            Project.id == data.project_id,
            Project.workspace_id == tc.workspace_id,
            Project.deleted_at.is_(None),
        )
    )
    if proj_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Project not found")

    # Content-hash dedup: skip re-processing identical content
    import hashlib
    content_hash = hashlib.sha256(data.content.encode("utf-8")).hexdigest()
    existing = await db.execute(
        select(Source).where(
            Source.workspace_id == tc.workspace_id,
            Source.content_hash == content_hash,
        )
    )
    dup = existing.scalar_one_or_none()
    if dup:
        # Return existing source data without re-running pipeline
        return IngestUploadResponse(
            source_id=dup.id,
            status=dup.status,
            stage=dup.stage,
            message=f"Duplicate content (hash {dup.content_hash[:12]}...), reusing existing source",
        )

    # Validate content size (already bounded by schema max_length)
    from app.services.pipeline import run_pipeline
    result = await run_pipeline(
        db=db,
        workspace_id=tc.workspace_id,
        tenant_id=tc.tenant_id,
        project_id=data.project_id,
        user_id=tc.user_id,
        source_type=data.source_type,
        raw_content=data.content,
        title=data.title,
        config=data.config,
    )
    # Tag the source with the content hash for future dedup
    source_id = result.get("source_id")
    if source_id:
        src = await db.get(Source, source_id)
        if src:
            src.content_hash = content_hash
            await db.commit()
    return IngestUploadResponse(**result)


@router.post("/", response_model=IngestJobOut, status_code=status.HTTP_201_CREATED)
async def legacy_start_ingest(
    data: IngestQueued,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Legacy ingest endpoint: creates a queued job (backward compat)."""
    from app.models import IngestJob

    proj_result = await db.execute(
        select(Project).where(
            Project.id == data.project_id,
            Project.workspace_id == tc.workspace_id,
            Project.deleted_at.is_(None),
        )
    )
    if proj_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Project not found")

    job = IngestJob(
        project_id=data.project_id,
        workspace_id=tc.workspace_id,
        source_type=data.source_type,
        config=data.config,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


# ── Sources ────────────────────────────────────────────────────────────


@router.get("/sources", response_model=SourceListResponse)
async def list_sources(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    project_id: str | None = None,
    status: str | None = Query(None, description="Filter by ingestion status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List ingestion sources for the workspace, optionally filtered by status."""
    stmt = select(Source).where(
        Source.workspace_id == tc.workspace_id,
        Source.deleted_at.is_(None),
    )
    if project_id:
        stmt = stmt.where(Source.project_id == project_id)
    if status:
        stmt = stmt.where(Source.status == status)
    stmt = stmt.order_by(Source.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    items = result.scalars().all()

    count_stmt = select(func.count(Source.id)).where(
        Source.workspace_id == tc.workspace_id,
        Source.deleted_at.is_(None),
    )
    if project_id:
        count_stmt = count_stmt.where(Source.project_id == project_id)
    if status:
        count_stmt = count_stmt.where(Source.status == status)
    total = (await db.execute(count_stmt)).scalar() or 0

    return SourceListResponse(
        items=[SourceOut.model_validate(s) for s in items],
        total=total,
    )


@router.get("/sources/{source_id}", response_model=SourceDetail)
async def get_source(
    source_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Get source detail with normalized messages."""
    result = await db.execute(
        select(Source).where(
            Source.id == source_id,
            Source.workspace_id == tc.workspace_id,
            Source.deleted_at.is_(None),
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    msgs_result = await db.execute(
        select(NormalizedMessage).where(
            NormalizedMessage.source_id == source_id,
        ).order_by(NormalizedMessage.message_index)
    )
    messages = msgs_result.scalars().all()

    return SourceDetail(
        **SourceOut.model_validate(source).model_dump(),
        normalized_messages=[NormalizedMessageOut.model_validate(m) for m in messages],
    )


@router.get("/sources/{source_id}/messages")
async def get_source_messages(
    source_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Get normalized messages for a source."""
    # Verify source ownership
    src_result = await db.execute(
        select(Source).where(
            Source.id == source_id,
            Source.workspace_id == tc.workspace_id,
        )
    )
    if src_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Source not found")

    msgs_result = await db.execute(
        select(NormalizedMessage).where(
            NormalizedMessage.source_id == source_id,
        ).order_by(NormalizedMessage.message_index)
    )
    messages = msgs_result.scalars().all()

    return {
        "items": [NormalizedMessageOut.model_validate(m).model_dump() for m in messages],
        "total": len(messages),
    }


# ── Facts ──────────────────────────────────────────────────────────────


@router.get("/facts", response_model=FactListResponse)
async def list_facts(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    project_id: str | None = None,
    subject: str | None = None,
    temporal_status: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List facts for the workspace."""
    stmt = select(Fact).where(
        Fact.workspace_id == tc.workspace_id,
        Fact.deleted_at.is_(None),
    )
    if project_id:
        stmt = stmt.where(Fact.project_id == project_id)
    if subject:
        stmt = stmt.where(Fact.subject.ilike(f"%{subject}%"))
    if temporal_status:
        stmt = stmt.where(Fact.temporal_status == temporal_status)

    total_stmt = select(func.count(Fact.id)).where(
        Fact.workspace_id == tc.workspace_id,
        Fact.deleted_at.is_(None),
    )
    if project_id:
        total_stmt = total_stmt.where(Fact.project_id == project_id)
    if subject:
        total_stmt = total_stmt.where(Fact.subject.ilike(f"%{subject}%"))
    if temporal_status:
        total_stmt = total_stmt.where(Fact.temporal_status == temporal_status)

    total = (await db.execute(total_stmt)).scalar() or 0

    stmt = stmt.order_by(Fact.created_at.desc()).limit(limit).offset(offset)
    items = (await db.execute(stmt)).scalars().all()

    return FactListResponse(
        items=[FactOut.model_validate(f) for f in items],
        total=total,
    )


@router.get("/facts/{fact_id}")
async def get_fact(
    fact_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Fact).where(
            Fact.id == fact_id,
            Fact.workspace_id == tc.workspace_id,
            Fact.deleted_at.is_(None),
        )
    )
    fact = result.scalar_one_or_none()
    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found")
    return FactOut.model_validate(fact)


# ── Decisions ──────────────────────────────────────────────────────────


@router.get("/decisions", response_model=DecisionListResponse)
async def list_decisions(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    project_id: str | None = None,
    temporal_status: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List decisions for the workspace."""
    stmt = select(Decision).where(
        Decision.workspace_id == tc.workspace_id,
        Decision.deleted_at.is_(None),
    )
    if project_id:
        stmt = stmt.where(Decision.project_id == project_id)
    if temporal_status:
        stmt = stmt.where(Decision.temporal_status == temporal_status)

    total_stmt = select(func.count(Decision.id)).where(
        Decision.workspace_id == tc.workspace_id,
        Decision.deleted_at.is_(None),
    )
    if project_id:
        total_stmt = total_stmt.where(Decision.project_id == project_id)
    if temporal_status:
        total_stmt = total_stmt.where(Decision.temporal_status == temporal_status)

    total = (await db.execute(total_stmt)).scalar() or 0
    stmt = stmt.order_by(Decision.created_at.desc()).limit(limit).offset(offset)
    items = (await db.execute(stmt)).scalars().all()

    return DecisionListResponse(
        items=[DecisionOut.model_validate(d) for d in items],
        total=total,
    )


@router.get("/decisions/{decision_id}")
async def get_decision(
    decision_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Decision).where(
            Decision.id == decision_id,
            Decision.workspace_id == tc.workspace_id,
            Decision.deleted_at.is_(None),
        )
    )
    dec = result.scalar_one_or_none()
    if not dec:
        raise HTTPException(status_code=404, detail="Decision not found")
    return DecisionOut.model_validate(dec)


# ── Graph ──────────────────────────────────────────────────────────────


@router.get("/graph", response_model=GraphResponse)
async def get_graph(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    project_id: str | None = None,
    include_historical: bool = Query(False, description="Include historical/superseded nodes"),
):
    """Get the knowledge graph for the workspace.

    By default, only current (non-historical) nodes are returned.
    Set include_historical=true to see all temporal states.
    """
    node_stmt = select(GraphNode).where(
        GraphNode.workspace_id == tc.workspace_id,
        GraphNode.deleted_at.is_(None),
    )
    if project_id:
        node_stmt = node_stmt.where(GraphNode.project_id == project_id)
    if not include_historical:
        node_stmt = node_stmt.where(GraphNode.temporal_status == "current")
    nodes = (await db.execute(node_stmt)).scalars().all()

    node_ids = [str(n.id) for n in nodes]

    edge_stmt = select(GraphEdge).where(
        GraphEdge.workspace_id == tc.workspace_id,
        GraphEdge.deleted_at.is_(None),
    )
    if not include_historical:
        edge_stmt = edge_stmt.where(GraphEdge.temporal_status == "current")
    if node_ids:
        edge_stmt = edge_stmt.where(
            GraphEdge.source_node_id.in_(node_ids),
            GraphEdge.target_node_id.in_(node_ids),
        )
    edges = (await db.execute(edge_stmt)).scalars().all()

    return GraphResponse(
        nodes=[GraphNodeOut.model_validate(n) for n in nodes],
        edges=[GraphEdgeOut.model_validate(e) for e in edges],
    )


# ── Timeline ───────────────────────────────────────────────────────────


@router.get("/timeline", response_model=TimelineResponse)
async def get_timeline(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    project_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    """Get chronological timeline of all events in the workspace."""
    items: list[TimelineItem] = []

    # Facts
    fact_stmt = select(Fact).where(
        Fact.workspace_id == tc.workspace_id,
        Fact.deleted_at.is_(None),
    )
    if project_id:
        fact_stmt = fact_stmt.where(Fact.project_id == project_id)
    for f in (await db.execute(fact_stmt.limit(limit))).scalars().all():
        items.append(TimelineItem(
            item_type="fact",
            id=str(f.id),
            title=f"{f.subject} {f.predicate} {f.object}",
            timestamp=f.created_at,
            temporal_status=f.temporal_status,
            content=f.content,
        ))

    # Decisions
    dec_stmt = select(Decision).where(
        Decision.workspace_id == tc.workspace_id,
        Decision.deleted_at.is_(None),
    )
    if project_id:
        dec_stmt = dec_stmt.where(Decision.project_id == project_id)
    for d in (await db.execute(dec_stmt.limit(limit))).scalars().all():
        items.append(TimelineItem(
            item_type="decision",
            id=str(d.id),
            title=d.content[:100],
            timestamp=d.created_at,
            temporal_status=d.temporal_status,
            content=d.content,
        ))

    # Memories
    mem_stmt = select(Memory).where(
        Memory.workspace_id == tc.workspace_id,
        Memory.user_id == tc.user_id,
        Memory.deleted_at.is_(None),
    )
    if project_id:
        mem_stmt = mem_stmt.where(Memory.project_id == project_id)
    for m in (await db.execute(mem_stmt.limit(limit))).scalars().all():
        items.append(TimelineItem(
            item_type="memory",
            id=str(m.id),
            title=m.content[:100],
            timestamp=m.created_at,
            temporal_status=getattr(m, "temporal_status", None),
            content=m.content,
        ))

    # Sort by timestamp descending
    items.sort(key=lambda x: x.timestamp or datetime.min, reverse=True)
    return TimelineResponse(items=items[:limit], total=len(items))


# ── Search (M5 retrieval) ────────────────��─────────────────────────────


@router.post("/search", response_model=SearchResponse)
async def search(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    query: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Search the workspace using M5 multi-factor retrieval."""
    results = await retrieve_hybrid(
        db, tc.workspace_id, query, limit=limit,
    )

    items = []
    for r in results:
        item_type = r.item_type
        item_id = str(r.item.id)
        content = ""
        if item_type == "memory":
            content = r.item.content
        elif item_type == "fact":
            content = r.item.content
        elif item_type == "decision":
            content = r.item.content

        items.append(SearchResultItem(
            item_type=item_type,
            id=item_id,
            score=round(r.score, 4),
            content=content[:500],
            temporal_status=getattr(r.item, "temporal_status", None),
            created_at=r.item.created_at,
        ))

    return SearchResponse(
        items=items,
        total=len(items),
        query=query,
    )


# ── Jobs ───────────────────────────────────────────────────────────────


@router.get("/jobs")
async def list_jobs(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List ingestion jobs for the workspace."""
    from app.models import IngestJob
    stmt = select(IngestJob).where(
        IngestJob.workspace_id == tc.workspace_id,
    ).order_by(IngestJob.created_at.desc()).limit(limit).offset(offset)
    jobs = (await db.execute(stmt)).scalars().all()

    count_result = await db.execute(
        select(func.count(IngestJob.id)).where(
            IngestJob.workspace_id == tc.workspace_id,
        )
    )
    total = count_result.scalar() or 0

    return {
        "items": [
            {
                "id": str(j.id),
                "project_id": j.project_id,
                "workspace_id": j.workspace_id,
                "source_type": j.source_type,
                "status": j.status,
                "stage": j.stage,
                "progress": j.progress,
                "error_message": j.error_message,
                "config": j.config,
                "created_at": j.created_at,
            }
            for j in jobs
        ],
        "total": total,
    }


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    from app.models import IngestJob
    result = await db.execute(
        select(IngestJob).where(
            IngestJob.id == job_id,
            IngestJob.workspace_id == tc.workspace_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Ingest job not found")
    return {
        "id": str(job.id),
        "project_id": job.project_id,
        "workspace_id": job.workspace_id,
        "source_type": job.source_type,
        "status": job.status,
        "stage": job.stage,
        "progress": job.progress,
        "error_message": job.error_message,
        "config": job.config,
        "created_at": job.created_at,
    }