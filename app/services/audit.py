"""Audit + Provenance Service.

Provides first-class operational audit stream while preserving existing
provenance semantics. Append-only from the application perspective.

Event types:
  policy.request / policy.allow / policy.deny / policy.confirmation_required
  memory.read / memory.search / memory.write / memory.update / memory.delete
  tool.request / tool.started / tool.completed / tool.failed / tool.denied
  model.request / model.completed / model.failed
"""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


class EventCategory(str, Enum):
    POLICY = "policy"
    MEMORY = "memory"
    TOOL = "tool"
    MODEL = "model"


class EventResult(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"
    PENDING = "pending"


@dataclass
class AuditEvent:
    """Single audit event."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    tenant_id: str | None = None
    workspace_id: str | None = None
    project_id: str | None = None
    principal_id: str | None = None
    principal_type: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    action: str | None = None
    decision: str | None = None
    policy_id: str | None = None
    policy_version: int | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    result_status: str = EventResult.SUCCESS.value
    duration_ms: float | None = None
    limits: dict[str, Any] | None = None
    provenance_reference: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditQuery:
    """Filter for querying audit events."""
    tenant_id: str | None = None
    workspace_id: str | None = None
    project_id: str | None = None
    principal_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    event_type: str | None = None
    decision: str | None = None
    result_status: str | None = None
    from_time: str | None = None
    to_time: str | None = None
    limit: int = 100
    offset: int = 0


# ---------------------------------------------------------------------------
# In-memory event store
# ---------------------------------------------------------------------------


class EventStore:
    """Append-only event store with query support."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        self._events.append(event)

    def query(self, q: AuditQuery) -> list[AuditEvent]:
        results = self._events
        if q.tenant_id:
            results = [e for e in results if e.tenant_id == q.tenant_id]
        if q.principal_id:
            results = [e for e in results if e.principal_id == q.principal_id]
        if q.resource_type:
            results = [e for e in results if e.resource_type == q.resource_type]
        if q.resource_id:
            results = [e for e in results if e.resource_id == q.resource_id]
        if q.event_type:
            results = [e for e in results if e.event_type == q.event_type]
        if q.decision:
            results = [e for e in results if e.decision == q.decision]
        if q.result_status:
            results = [e for e in results if e.result_status == q.result_status]
        if q.from_time:
            results = [e for e in results if e.timestamp >= q.from_time]
        if q.to_time:
            results = [e for e in results if e.timestamp <= q.to_time]
        return results[q.offset : q.offset + q.limit]

    def count(self, q: AuditQuery | None = None) -> int:
        if q is None:
            return len(self._events)
        return len(self.query(q))

    def all(self) -> list[AuditEvent]:
        return list(self._events)

    def clear(self) -> None:
        self._events.clear()


# ---------------------------------------------------------------------------
# Audit Service
# ---------------------------------------------------------------------------


class AuditService:
    """Operational audit service.

    Records policy decisions, memory operations, tool executions, and
    model invocations. Ordinary agents cannot alter audit records —
    the service is the sole writer.
    """

    def __init__(self, store: EventStore | None = None) -> None:
        self._store = store or EventStore()

    @property
    def store(self) -> EventStore:
        return self._store

    def record_event(
        self,
        event_type: str,
        principal_id: str | None = None,
        principal_type: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        action: str | None = None,
        decision: str | None = None,
        policy_id: str | None = None,
        policy_version: int | None = None,
        request_id: str | None = None,
        correlation_id: str | None = None,
        result_status: str = EventResult.SUCCESS.value,
        duration_ms: float | None = None,
        limits: dict[str, Any] | None = None,
        provenance_reference: str | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
        project_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Record an audit event. Returns event_id."""
        event = AuditEvent(
            event_type=event_type,
            principal_id=principal_id,
            principal_type=principal_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            decision=decision,
            policy_id=policy_id,
            policy_version=policy_version,
            request_id=request_id,
            correlation_id=correlation_id,
            result_status=result_status,
            duration_ms=duration_ms,
            limits=limits,
            provenance_reference=provenance_reference,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            metadata=metadata or {},
        )
        self._store.append(event)
        logger.debug("[audit] %s: %s %s on %s/%s → %s",
                     event.event_id, event_type, action, resource_type, resource_id, result_status)
        return event.event_id

    def query(self, q: AuditQuery) -> list[AuditEvent]:
        return self._store.query(q)

    def count(self, q: AuditQuery | None = None) -> int:
        return self._store.count(q)

    # Convenience helpers for common event types

    def record_policy_decision(
        self, decision: "PolicyDecision",  # type: ignore[name-defined]
        *,
        principal_type: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        action: str | None = None,
        correlation_id: str | None = None,
    ) -> str:
        return self.record_event(
            event_type=f"policy.{decision.decision}",
            principal_id=decision.principal_id,
            principal_type=principal_type,
            resource_type=resource_type or getattr(decision, "resource_type", None),
            resource_id=resource_id,
            action=action,
            decision=decision.decision,
            policy_id=decision.policy_id,
            policy_version=decision.policy_version,
            request_id=decision.request_id,
            correlation_id=correlation_id,
            result_status=EventResult.SUCCESS.value
            if decision.decision == "allow"
            else EventResult.DENIED.value,
            limits=decision.limits,
        )

    def record_memory_read(
        self,
        principal_id: str,
        memory_id: str,
        *,
        result_status: str = EventResult.SUCCESS.value,
        duration_ms: float | None = None,
        tenant_id: str | None = None,
        request_id: str | None = None,
    ) -> str:
        return self.record_event(
            event_type="memory.read",
            principal_id=principal_id,
            principal_type="agent",
            resource_type="memory",
            resource_id=memory_id,
            action="read",
            result_status=result_status,
            duration_ms=duration_ms,
            tenant_id=tenant_id,
            request_id=request_id,
        )

    def record_tool_execution(
        self,
        tool_id: str,
        action: str,
        *,
        principal_id: str | None = None,
        result_status: str = EventResult.SUCCESS.value,
        duration_ms: float | None = None,
        error: str | None = None,
        request_id: str | None = None,
        correlation_id: str | None = None,
    ) -> str:
        if result_status == EventResult.FAILURE.value:
            event_type = "tool.failed"
        elif result_status == EventResult.DENIED.value:
            event_type = "tool.denied"
        else:
            event_type = "tool.completed"
        return self.record_event(
            event_type=event_type,
            principal_id=principal_id,
            principal_type="agent",
            resource_type="tool",
            resource_id=tool_id,
            action=action,
            result_status=result_status,
            duration_ms=duration_ms,
            request_id=request_id,
            correlation_id=correlation_id,
            metadata={"error": error} if error else {},
        )


__all__ = [
    "AuditEvent",
    "AuditQuery",
    "AuditService",
    "EventCategory",
    "EventResult",
    "EventStore",
]
