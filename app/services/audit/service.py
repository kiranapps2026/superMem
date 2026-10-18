"""Audit event emission service (Sprint 7).

Emits structured audit events to a structured log stream.
All audit events flow through this service so that:
  - producers do not duplicate formatting logic
  - sensitive fields are consistently redacted
  - events can be routed to multiple sinks (log, DB, external SIEM)

Persistence model:
  - emit() is synchronous — writes to log sinks and accumulates events
  - persist(session) is async — flushes accumulated events to the DB
  - the application calls persist() at the end of request handling
  - DB sink failures never prevent emit() from completing
"""
from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

from app.services.audit.constants import (
    AUDIT_FIELDS,
    SENSITIVE_FIELDS,
    RESULT_SUCCESS,
    RESULT_FAILURE,
    RESULT_DENIED,
    RESULT_PARTIAL,
    POLICY_ALLOW,
    POLICY_DENY,
    POLICY_CONFIRMATION_REQUIRED,
    POLICY_LIMITED,
    POLICY_REQUEST,
)

logger = logging.getLogger("app.audit")

# Type alias for event sink callbacks
EventSink = Callable[[dict[str, Any]], None]


def _sanitize(event: dict[str, Any]) -> dict[str, Any]:
    """Remove sensitive values from an event before emission.

    Recursively redacts any key whose name matches SENSITIVE_FIELDS,
    replacing the value with "[redacted]".
    """
    if not isinstance(event, dict):
        return event
    sanitized = {}
    for key, value in event.items():
        if key.lower() in SENSITIVE_FIELDS or any(s in key.lower() for s in SENSITIVE_FIELDS):
            sanitized[key] = "[redacted]"
        elif isinstance(value, dict):
            sanitized[key] = _sanitize(value)
        elif isinstance(value, list):
            sanitized[key] = [_sanitize(v) if isinstance(v, dict) else v for v in value]
        else:
            sanitized[key] = value
    return sanitized


class AuditEvent:
    """Structured audit event with all canonical fields."""

    __slots__ = (
        "event_id", "timestamp", "event_type",
        "tenant_id", "workspace_id", "project_id",
        "principal_id", "principal_type", "resource_type", "resource_id",
        "action", "decision", "policy_id", "policy_version", "request_id",
        "correlation_id", "result_status", "duration_ms", "limits",
        "provenance_reference", "metadata",
    )

    def __init__(self, **kwargs: Any):
        self.event_id: str = kwargs.get("event_id", str(uuid.uuid4()))
        self.timestamp: str = kwargs.get("timestamp", _iso_now())
        self.event_type: str = kwargs.get("event_type", "")
        self.tenant_id: str | None = kwargs.get("tenant_id")
        self.workspace_id: str | None = kwargs.get("workspace_id")
        self.project_id: str | None = kwargs.get("project_id")
        self.principal_id: str | None = kwargs.get("principal_id")
        self.principal_type: str | None = kwargs.get("principal_type")
        self.resource_type: str | None = kwargs.get("resource_type")
        self.resource_id: str | None = kwargs.get("resource_id")
        self.action: str | None = kwargs.get("action")
        self.decision: str | None = kwargs.get("decision")
        self.policy_id: str | None = kwargs.get("policy_id")
        self.policy_version: int | None = kwargs.get("policy_version")
        self.request_id: str | None = kwargs.get("request_id")
        self.correlation_id: str | None = kwargs.get("correlation_id")
        self.result_status: str = kwargs.get("result_status", RESULT_SUCCESS)
        self.duration_ms: int | None = kwargs.get("duration_ms")
        self.limits: dict[str, Any] | None = kwargs.get("limits")
        self.provenance_reference: str | None = kwargs.get("provenance_reference")
        self.metadata: dict[str, Any] | None = kwargs.get("metadata")

    def to_dict(self) -> dict[str, Any]:
        return {f: getattr(self, f) for f in AUDIT_FIELDS if hasattr(self, f)}

    def __repr__(self) -> str:
        return f"AuditEvent(event_id={self.event_id}, action={self.action}, decision={self.decision})"


def _iso_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class AuditService:
    """Central audit event emitter.

    Usage:
        audit = AuditService()
        audit.emit(
            event_type=POLICY_DENY,
            tenant_id="...",
            principal_id="...",
            resource_type="tool",
            action="execute",
        )

    Events are emitted to all registered sinks.  By default a structured
    log sink is registered.  Additional sinks (DB, webhook, SIEM) can be
    added via register_sink().

    For DB persistence, call `await audit.persist(session)` at the end of
    each request.  Events accumulate in memory between persists.
    """

    def __init__(self) -> None:
        self._sinks: list[EventSink] = []
        self._log_sink = logger
        self._buffer: list[AuditEvent] = []
        self._max_buffer_size = 1000
        self._db_repo: Any = None  # AuditRepository, set by register_db_sink
        self._register_default_sinks()

    def _register_default_sinks(self) -> None:
        self._sinks.append(self._log_emit)

    def register_sink(self, sink: EventSink) -> None:
        """Register an additional synchronous event sink."""
        self._sinks.append(sink)

    def register_db_sink(self) -> None:
        """Enable DB persistence.

        Call this once at startup.  Events are then persisted when
        `await audit.persist(session)` is called.
        """
        try:
            from app.services.audit.repository import AuditRepository
            self._db_repo = AuditRepository()
        except ImportError:
            logger.warning("AuditRepository not available; DB persistence disabled")

    def emit(self, event_type: str, **kwargs: Any) -> AuditEvent:
        """Create and emit an audit event to all sinks.

        Sensitive fields are automatically redacted before emission.
        Each sink receives an independent dict copy.
        The event is also buffered for later DB persistence.
        """
        event = AuditEvent(event_type=event_type, **kwargs)
        base = _sanitize(event.to_dict())

        for sink in self._sinks:
            try:
                sink(dict(base))
            except Exception:
                # Audit must not fail the calling operation
                pass

        # Buffer for DB persistence — drop oldest when bound is reached
        if len(self._buffer) >= self._max_buffer_size:
            self._buffer.pop(0)
        self._buffer.append(event)

        return event

    async def persist(self, session: Any) -> int:
        """Persist all buffered events to the database.

        Call this at the end of each request.  Clears the buffer on success.

        Returns the number of events persisted.
        Never raises — failures are logged and the buffer is still cleared
        to prevent unbounded memory growth.
        """
        if not self._buffer or self._db_repo is None:
            self._buffer.clear()
            return 0

        events_to_save = self._buffer
        self._buffer = []

        persisted = 0
        for event in events_to_save:
            try:
                await self._db_repo.save(session, event)
                persisted += 1
            except Exception:
                logger.warning("failed to persist audit event %s", event.event_id, exc_info=True)

        return persisted

    @property
    def pending_count(self) -> int:
        """Number of events buffered for persistence."""
        return len(self._buffer)

    def clear_buffer(self) -> None:
        """Discard all pending events.  Use with caution."""
        self._buffer.clear()

    def _log_emit(self, event: dict[str, Any]) -> None:
        """Default sink: structured log entry."""
        self._log_sink.info(
            "audit_event",
            extra={"audit_event": event},
        )


# ── Convenience constructors for common event patterns ──────────────────────


def policy_event(
    audit: AuditService,
    decision: str,
    request_id: str,
    *,
    principal_id: str,
    principal_type: str = "user",
    resource_type: str,
    action: str,
    resource_id: str | None = None,
    tenant_id: str | None = None,
    workspace_id: str | None = None,
    policy_id: str | None = None,
    policy_version: int | None = None,
    limits: dict[str, Any] | None = None,
    correlation_id: str | None = None,
    duration_ms: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    """Emit a policy decision audit event with the appropriate event type."""
    event_type_map = {
        "allow": POLICY_ALLOW,
        "deny": POLICY_DENY,
        "require_confirmation": POLICY_CONFIRMATION_REQUIRED,
        "allow_with_limits": POLICY_LIMITED,
        "allow_redacted": POLICY_LIMITED,
    }
    event_type = event_type_map.get(decision, POLICY_REQUEST)
    return audit.emit(
        event_type=event_type,
        decision=decision,
        request_id=request_id,
        principal_id=principal_id,
        principal_type=principal_type,
        resource_type=resource_type,
        action=action,
        resource_id=resource_id,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        policy_id=policy_id,
        policy_version=policy_version,
        limits=limits,
        correlation_id=correlation_id,
        duration_ms=duration_ms,
        metadata=metadata,
    )


def operation_event(
    audit: AuditService,
    event_type: str,
    *,
    principal_id: str,
    principal_type: str = "user",
    resource_type: str,
    action: str,
    result_status: str = RESULT_SUCCESS,
    resource_id: str | None = None,
    tenant_id: str | None = None,
    workspace_id: str | None = None,
    project_id: str | None = None,
    request_id: str | None = None,
    duration_ms: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    """Emit a general operation audit event."""
    return audit.emit(
        event_type=event_type,
        result_status=result_status,
        principal_id=principal_id,
        principal_type=principal_type,
        resource_type=resource_type,
        action=action,
        resource_id=resource_id,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        project_id=project_id,
        request_id=request_id,
        duration_ms=duration_ms,
        metadata=metadata,
    )


__all__ = [
    "AuditService",
    "AuditEvent",
    "EventSink",
    "policy_event",
    "operation_event",
]
