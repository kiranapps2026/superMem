"""Audit event persistence repository (Sprint 7 — Phase 4).

Provides async database operations for the AuditEvent model.
All audit writes go through this repository; the application
never updates or deletes audit records directly.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditEvent as AuditEventModel
from app.services.audit.constants import (
    AUDIT_FIELDS,
    SENSITIVE_FIELDS,
    POLICY_DENY,
    POLICY_ALLOW,
    POLICY_CONFIRMATION_REQUIRED,
    POLICY_LIMITED,
    RESULT_DENIED,
    RESULT_SUCCESS,
    RESULT_FAILURE,
    RESULT_PARTIAL,
)
from app.services.audit.service import AuditEvent as AuditEventDTO

logger = logging.getLogger(__name__)


class AuditRepository:
    """Async repository for persistent audit events.

    Provides application-append-only semantics:
      - writes are inserts only
      - no update or delete operations
      - queries support tenant isolation and time-range filtering
    """

    async def save(self, session: AsyncSession, event: AuditEventDTO) -> AuditEventModel:
        """Persist an audit event.

        The AuditEventDTO is converted to the ORM model and inserted.
        Sensitive fields are already redacted by the AuditService before
        reaching this point.
        """
        # Convert DTO to ORM — only set canonical fields
        data = event.to_dict()
        model = AuditEventModel(
            id=data.get("event_id"),
            tenant_id=data.get("tenant_id"),
            workspace_id=data.get("workspace_id"),
            project_id=data.get("project_id"),
            principal_id=data.get("principal_id"),
            principal_type=data.get("principal_type"),
            resource_type=data.get("resource_type"),
            resource_id=data.get("resource_id"),
            action=data.get("action"),
            decision=data.get("decision"),
            policy_id=data.get("policy_id"),
            policy_version=data.get("policy_version"),
            request_id=data.get("request_id"),
            correlation_id=data.get("correlation_id"),
            event_type=data.get("event_type", ""),
            result_status=data.get("result_status", RESULT_SUCCESS),
            duration_ms=data.get("duration_ms"),
            limits=data.get("limits"),
            provenance_reference=data.get("provenance_reference"),
            event_metadata=data.get("metadata") or {},
            timestamp=data.get("timestamp"),
        )
        session.add(model)
        await session.flush()
        return model

    async def query(
        self,
        session: AsyncSession,
        *,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
        principal_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        event_type: str | None = None,
        decision: str | None = None,
        result_status: str | None = None,
        from_time: str | None = None,
        to_time: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEventModel]:
        """Query audit events with database-level filtering.

        Tenant isolation is enforced at the query level — never rely
        on client-side filtering for security.
        """
        stmt = select(AuditEventModel)

        if tenant_id is not None:
            stmt = stmt.where(AuditEventModel.tenant_id == tenant_id)
        if workspace_id is not None:
            stmt = stmt.where(AuditEventModel.workspace_id == workspace_id)
        if principal_id is not None:
            stmt = stmt.where(AuditEventModel.principal_id == principal_id)
        if resource_type is not None:
            stmt = stmt.where(AuditEventModel.resource_type == resource_type)
        if resource_id is not None:
            stmt = stmt.where(AuditEventModel.resource_id == resource_id)
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

        # Order by timestamp descending (most recent first)
        stmt = stmt.order_by(desc(AuditEventModel.timestamp))
        stmt = stmt.limit(limit).offset(offset)

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def count(
        self,
        session: AsyncSession,
        *,
        tenant_id: str | None = None,
        from_time: str | None = None,
        to_time: str | None = None,
    ) -> int:
        """Count audit events matching filters."""
        from sqlalchemy import func
        stmt = select(func.count(AuditEventModel.id))
        if tenant_id is not None:
            stmt = stmt.where(AuditEventModel.tenant_id == tenant_id)
        if from_time is not None:
            stmt = stmt.where(AuditEventModel.timestamp >= from_time)
        if to_time is not None:
            stmt = stmt.where(AuditEventModel.timestamp <= to_time)
        result = await session.execute(stmt)
        return result.scalar_one_or_none() or 0

    async def get_by_request_id(
        self, session: AsyncSession, request_id: str
    ) -> AuditEventModel | None:
        """Retrieve an audit event by request ID for correlation."""
        stmt = select(AuditEventModel).where(
            AuditEventModel.request_id == request_id
        ).order_by(desc(AuditEventModel.timestamp))
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_correlation_id(
        self, session: AsyncSession, correlation_id: str
    ) -> list[AuditEventModel]:
        """Retrieve all audit events for a correlation chain."""
        stmt = select(AuditEventModel).where(
            AuditEventModel.correlation_id == correlation_id
        ).order_by(AuditEventModel.timestamp)
        result = await session.execute(stmt)
        return list(result.scalars().all())


__all__ = ["AuditRepository"]
