"""Phase 4: Execution context — server-derived identity threaded through write paths.

The ExecutionContext is derived from the authenticated request plus validated
Agent/Run rows. It is NEVER trusted verbatim from client JSON.

Design:
  - TenantContext flows from JWT auth middleware (tenancy.py)
  - Agent/Run are validated server-side from the DB
  - The combined ExecutionContext is passed as a dependency to services
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.tenancy import TenantContext
from app.models import (
    Agent,
    AgentVersion,
    Run,
)
from app.db import get_db

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """Server-derived execution context for write operations.

    Combines tenant/workspace info (from TenantContext) with validated
    agent/run identity. Threaded through API → pipeline → MemoryService.
    """
    tenant_id: str
    workspace_id: str
    project_id: str | None = None
    user_id: str | None = None
    role: str = "viewer"
    agent_id: str | None = None
    agent_version_id: str | None = None
    run_id: str | None = None
    trace_id: str | None = None
    correlation_id: str | None = None

    @classmethod
    def from_tenant_context(
        cls,
        ctx: TenantContext,
        agent_id: str | None = None,
        agent_version_id: str | None = None,
        run_id: str | None = None,
        trace_id: str | None = None,
        correlation_id: str | None = None,
    ) -> ExecutionContext:
        """Build from a TenantContext (request-scoped auth info)."""
        return cls(
            tenant_id=ctx.tenant_id,
            workspace_id=ctx.workspace_id or "",
            project_id=None,
            user_id=ctx.user_id,
            role=ctx.role,
            agent_id=agent_id,
            agent_version_id=agent_version_id,
            run_id=run_id,
            trace_id=trace_id or ctx.trace_id,
            correlation_id=correlation_id or ctx.correlation_id,
        )

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "role": self.role,
            "agent_id": self.agent_id,
            "agent_version_id": self.agent_version_id,
            "run_id": self.run_id,
            "trace_id": self.trace_id,
            "correlation_id": self.correlation_id,
        }


async def validate_agent(
    agent_id: str,
    db: AsyncSession,
    workspace_id: str,
) -> Agent:
    """Validate that an agent exists, belongs to the workspace, and is active.

    Validation chain:
      1. Agent exists and is not soft-deleted
      2. Agent belongs to the requesting workspace
      3. Agent.is_active == True

    Args:
        agent_id: Agent ID to validate
        db: Database session
        workspace_id: Workspace the agent must belong to

    Returns:
        The validated Agent

    Raises:
        HTTPException 404: Agent not found or soft-deleted
        HTTPException 403: Agent exists but doesn't belong to this workspace
        HTTPException 403: Agent exists but is inactive
    """
    result = await db.execute(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.deleted_at.is_(None),
        )
    )
    agent = result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    if agent.workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent does not belong to this workspace",
        )
    if not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent is inactive",
        )
    return agent


async def validate_run(
    run_id: str,
    db: AsyncSession,
    agent_id: str,
    workspace_id: str,
) -> Run:
    """Validate that a run exists, belongs to the agent, and is not cancelled.

    Validation chain:
      1. Run exists
      2. Run belongs to the validated agent
      3. Run belongs to the same workspace
      4. Run.status != "cancelled"

    Args:
        run_id: Run ID to validate
        db: Database session
        agent_id: Agent the run must belong to
        workspace_id: Workspace the run must belong to

    Returns:
        The validated Run

    Raises:
        HTTPException 404: Run not found
        HTTPException 403: Run doesn't belong to agent/workspace or is cancelled
    """
    result = await db.execute(
        select(Run).where(
            Run.id == run_id,
            Run.agent_id == agent_id,
            Run.workspace_id == workspace_id,
        )
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    if run.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Run is cancelled",
        )
    return run


async def get_execution_context(
    request: Request,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ExecutionContext:
    """Build ExecutionContext from request + validated identity.

    Reads agent_id/run_id from X-Agent-Id and X-Run-Id headers
    (server-derived, never from client JSON body). Validates against DB.
    """
    agent_id = request.headers.get("X-Agent-Id")
    run_id = request.headers.get("X-Run-Id")

    validated_agent = None
    validated_run = None

    if agent_id:
        validated_agent = await validate_agent(
            agent_id, db, tenant_ctx.workspace_id or ""
        )
        if run_id:
            validated_run = await validate_run(
                run_id, db, validated_agent.id, tenant_ctx.workspace_id or ""
            )

    return ExecutionContext.from_tenant_context(
        tenant_ctx,
        agent_id=validated_agent.id if validated_agent else agent_id,
        agent_version_id=validated_agent.version if validated_agent else None,
        run_id=validated_run.id if validated_run else run_id,
        trace_id=tenant_ctx.trace_id,
        correlation_id=tenant_ctx.correlation_id,
    )
