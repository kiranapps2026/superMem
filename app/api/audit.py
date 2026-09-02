"""Audit API endpoints (Sprint 7 — Phase 4).

Provides read-only endpoints for querying audit events.
Audit events are immutable from the API perspective.

Endpoints:
  GET /api/v1/audit/events          — list events (filtered, paginated)
  GET /api/v1/audit/events/{id}     — single event by ID
  GET /api/v1/audit/trace/{req_id}  — full correlation trace by request_id
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.middleware.tenancy import TenantContext, get_tenant_context
from app.middleware.auth import require_auth
from app.middleware.rbac import require_min_role
from app.models import AuditEvent as AuditEventModel
from app.services.audit.constants import (
    AUDIT_FIELDS,
    RESULT_SUCCESS,
    RESULT_FAILURE,
    RESULT_DENIED,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


def _event_to_dict(event: AuditEventModel) -> dict[str, Any]:
    """Convert an AuditEvent ORM model to a plain dict."""
    import json
    metadata = {}
    if event.event_metadata:
        try:
            metadata = json.loads(event.event_metadata)
        except (json.JSONDecodeError, TypeError):
            metadata = {}

    return {
        "id": str(event.id),
        "event_id": str(event.id),
        "event_type": event.event_type,
        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
        "tenant_id": str(event.tenant_id) if event.tenant_id else None,
        "workspace_id": str(event.workspace_id) if event.workspace_id else None,
        "project_id": str(event.project_id) if event.project_id else None,
        "principal_id": str(event.principal_id) if event.principal_id else None,
        "principal_type": event.principal_type,
        "resource_type": event.resource_type,
        "resource_id": str(event.resource_id) if event.resource_id else None,
        "action": event.action,
        "decision": event.decision,
        "policy_id": str(event.policy_id) if event.policy_id else None,
        "policy_version": event.policy_version,
        "request_id": str(event.request_id) if event.request_id else None,
        "correlation_id": str(event.correlation_id) if event.correlation_id else None,
        "result_status": event.result_status,
        "duration_ms": event.duration_ms,
        "limits": event.limits,
        "provenance_reference": event.provenance_reference,
        "metadata": metadata,
    }


@router.get("/events")
async def list_audit_events(
    tc: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_min_role("member")),
    principal_id: str | None = Query(None, description="Filter by principal"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    action: str | None = Query(None, description="Filter by action"),
    event_type: str | None = Query(None, description="Filter by event type"),
    decision: str | None = Query(None, description="Filter by policy decision"),
    result_status: str | None = Query(None, description="Filter by result status"),
    from_time: str | None = Query(None, description="ISO timestamp lower bound"),
    to_time: str | None = Query(None, description="ISO timestamp upper bound"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Query audit events for this workspace with optional filters.

    Tenant isolation is enforced server-side via TenantContext.
    """
    stmt = select(AuditEventModel).where(
        AuditEventModel.tenant_id == tc.tenant_id
    )

    if tc.workspace_id is not None:
        stmt = stmt.where(AuditEventModel.workspace_id == tc.workspace_id)
    if principal_id is not None:
        stmt = stmt.where(AuditEventModel.principal_id == principal_id)
    if resource_type is not None:
        stmt = stmt.where(AuditEventModel.resource_type == resource_type)
    if action is not None:
        stmt = stmt.where(AuditEventModel.action == action)
    if event_type is not None:
        stmt = stmt.where(AuditEventModel.event_type == event_type)
    if decision is not None:
        stmt = stmt.where(AuditEventModel.decision == decision)
    if result_status is not None:
        stmt = stmt.where(AuditEventModel.result_status == result_status)
    if from_time is not None:
        stmt = stmt.where(AuditEventModel.timestamp >= from_time)
    if to_time is not None:
        stmt = stmt.where(AuditEventModel.timestamp <= to_time)

    stmt = stmt.order_by(desc(AuditEventModel.timestamp))
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    events = result.scalars().all()

    return {
        "items": [_event_to_dict(e) for e in events],
        "total": len(events),
        "limit": limit,
        "offset": offset,
    }


@router.get("/events/{event_id}")
async def get_audit_event(
    event_id: str,
    tc: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_min_role("member")),
):
    """Retrieve a single audit event by ID.

    Tenant isolation is enforced — users can only access events
    within their own tenant.
    """
    try:
        event_uuid = UUID(event_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid event_id format")

    stmt = select(AuditEventModel).where(AuditEventModel.id == event_uuid)
    result = await db.execute(stmt)
    event = result.scalars().first()

    if event is None:
        raise HTTPException(status_code=404, detail="audit event not found")

    # Enforce tenant isolation
    if event.tenant_id and str(event.tenant_id) != tc.tenant_id:
        raise HTTPException(status_code=403, detail="access denied")

    return _event_to_dict(event)


@router.get("/trace/{request_id}")
async def correlation_trace(
    request_id: str,
    tc: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_min_role("member")),
):
    """Retrieve the full audit trace for a request ID.

    Returns all audit events linked to the given request_id,
    ordered chronologically, providing a complete audit trail
    from policy decision through operation completion.
    """
    stmt = (
        select(AuditEventModel)
        .where(AuditEventModel.request_id == request_id)
        .where(AuditEventModel.tenant_id == tc.tenant_id)
        .order_by(AuditEventModel.timestamp)
    )

    result = await db.execute(stmt)
    events = result.scalars().all()

    if not events:
        raise HTTPException(status_code=404, detail="no events found for request_id")

    return {
        "request_id": request_id,
        "event_count": len(events),
        "events": [_event_to_dict(e) for e in events],
    }
