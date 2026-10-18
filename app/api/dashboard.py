"""Dashboard API — workspace and project-level knowledge summaries."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.middleware.tenancy import TenantContext, get_tenant_context
from app.models import Memory, Source, Session, Fact, Decision, GraphNode, GraphEdge, MessageFeedback, Project
from app.schemas import DashboardOverview, ProjectDashboard


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _seven_days_ago() -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=7)


@router.get("/", response_model=DashboardOverview)
async def workspace_overview(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Aggregated workspace knowledge overview."""
    cutoff = _seven_days_ago()

    # Total counts
    total_memories = (await db.execute(
        select(func.count(Memory.id)).where(
            Memory.workspace_id == tc.workspace_id,
            Memory.deleted_at.is_(None),
        )
    )).scalar() or 0

    total_sources = (await db.execute(
        select(func.count(Source.id)).where(
            Source.workspace_id == tc.workspace_id,
            Source.deleted_at.is_(None),
        )
    )).scalar() or 0

    total_sessions = (await db.execute(
        select(func.count(Session.id)).where(
            Session.workspace_id == tc.workspace_id,
            Session.deleted_at.is_(None),
        )
    )).scalar() or 0

    total_facts = (await db.execute(
        select(func.count(Fact.id)).where(
            Fact.workspace_id == tc.workspace_id,
            Fact.deleted_at.is_(None),
        )
    )).scalar() or 0

    total_decisions = (await db.execute(
        select(func.count(Decision.id)).where(
            Decision.workspace_id == tc.workspace_id,
            Decision.deleted_at.is_(None),
        )
    )).scalar() or 0

    total_graph_nodes = (await db.execute(
        select(func.count(GraphNode.id)).where(
            GraphNode.workspace_id == tc.workspace_id,
            GraphNode.deleted_at.is_(None),
        )
    )).scalar() or 0

    total_graph_edges = (await db.execute(
        select(func.count(GraphEdge.id)).where(
            GraphEdge.workspace_id == tc.workspace_id,
            GraphEdge.deleted_at.is_(None),
        )
    )).scalar() or 0

    # Recent activity (last 7 days)
    recent_memories = (await db.execute(
        select(func.count(Memory.id)).where(
            Memory.workspace_id == tc.workspace_id,
            Memory.created_at >= cutoff,
        )
    )).scalar() or 0

    recent_sessions = (await db.execute(
        select(func.count(Session.id)).where(
            Session.workspace_id == tc.workspace_id,
            Session.created_at >= cutoff,
        )
    )).scalar() or 0

    # Memory type breakdown
    type_rows = (await db.execute(
        select(Memory.memory_type, func.count(Memory.id)).where(
            Memory.workspace_id == tc.workspace_id,
            Memory.deleted_at.is_(None),
        ).group_by(Memory.memory_type)
    )).fetchall()
    memory_types = {row[0]: row[1] for row in type_rows}

    return DashboardOverview(
        workspace_id=tc.workspace_id,
        total_memories=total_memories,
        total_sources=total_sources,
        total_sessions=total_sessions,
        total_facts=total_facts,
        total_decisions=total_decisions,
        total_graph_nodes=total_graph_nodes,
        total_graph_edges=total_graph_edges,
        recent_memories=recent_memories,
        recent_sessions=recent_sessions,
        memory_types=memory_types,
    )


@router.get("/projects/{project_id}", response_model=ProjectDashboard)
async def project_dashboard(
    project_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Project-level knowledge dashboard."""
    # Verify project exists in workspace
    proj_result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.workspace_id == tc.workspace_id,
            Project.deleted_at.is_(None),
        )
    )
    project = proj_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    total_memories = (await db.execute(
        select(func.count(Memory.id)).where(
            Memory.workspace_id == tc.workspace_id,
            Memory.project_id == project_id,
            Memory.deleted_at.is_(None),
        )
    )).scalar() or 0

    total_sources = (await db.execute(
        select(func.count(Source.id)).where(
            Source.workspace_id == tc.workspace_id,
            Source.project_id == project_id,
            Source.deleted_at.is_(None),
        )
    )).scalar() or 0

    total_facts = (await db.execute(
        select(func.count(Fact.id)).where(
            Fact.workspace_id == tc.workspace_id,
            Fact.project_id == project_id,
            Fact.deleted_at.is_(None),
        )
    )).scalar() or 0

    total_decisions = (await db.execute(
        select(func.count(Decision.id)).where(
            Decision.workspace_id == tc.workspace_id,
            Decision.project_id == project_id,
            Decision.deleted_at.is_(None),
        )
    )).scalar() or 0

    total_graph_nodes = (await db.execute(
        select(func.count(GraphNode.id)).where(
            GraphNode.workspace_id == tc.workspace_id,
            GraphNode.project_id == project_id,
            GraphNode.deleted_at.is_(None),
        )
    )).scalar() or 0

    total_feedback = (await db.execute(
        select(func.count(MessageFeedback.id)).where(
            MessageFeedback.workspace_id == tc.workspace_id,
            MessageFeedback.deleted_at.is_(None),
        )
    )).scalar() or 0

    # Memory type breakdown
    type_rows = (await db.execute(
        select(Memory.memory_type, func.count(Memory.id)).where(
            Memory.workspace_id == tc.workspace_id,
            Memory.project_id == project_id,
            Memory.deleted_at.is_(None),
        ).group_by(Memory.memory_type)
    )).fetchall()
    memory_types = {row[0]: row[1] for row in type_rows}

    return ProjectDashboard(
        project_id=project_id,
        project_name=project.name,
        total_memories=total_memories,
        total_sources=total_sources,
        total_facts=total_facts,
        total_decisions=total_decisions,
        total_graph_nodes=total_graph_nodes,
        total_feedback=total_feedback,
        memory_types=memory_types,
    )
