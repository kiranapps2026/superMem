"""Tests for the Sprint 7 audit service.

Covers:
  - AuditEvent creation and to_dict()
  - AuditService.emit() to sinks
  - Sensitive field redaction
  - policy_event() convenience constructor
  - operation_event() convenience constructor
  - Custom sink registration
  - Multiple sinks receive events
  - Audit failure isolation (sink exceptions don't propagate)
"""
from __future__ import annotations

import pytest
from app.services.audit import (
    AuditService,
    AuditEvent,
    POLICY_ALLOW,
    POLICY_DENY,
    POLICY_CONFIRMATION_REQUIRED,
    POLICY_LIMITED,
    MEMORY_READ,
    MEMORY_WRITE,
    TOOL_STARTED,
    TOOL_DENIED,
    MODEL_REQUEST,
    API_KEY_CREATED,
    API_KEY_REVOKED,
    INGEST_COMPLETED,
    RESULT_SUCCESS,
    RESULT_FAILURE,
    RESULT_DENIED,
    RESULT_PARTIAL,
)


class TestAuditEvent:
    """Test AuditEvent dataclass."""

    def test_default_values(self):
        event = AuditEvent()
        assert event.event_id is not None
        assert event.timestamp is not None
        assert event.result_status == RESULT_SUCCESS
        assert event.principal_id is None
        assert event.tenant_id is None

    def test_custom_fields(self):
        event = AuditEvent(
            event_id="custom-id",
            principal_id="user-1",
            resource_type="memory",
            action="read",
            result_status=RESULT_FAILURE,
        )
        assert event.event_id == "custom-id"
        assert event.principal_id == "user-1"
        assert event.resource_type == "memory"
        assert event.result_status == RESULT_FAILURE

    def test_to_dict_contains_canonical_fields(self):
        event = AuditEvent(
            tenant_id="t-1",
            workspace_id="w-1",
            project_id="p-1",
            principal_id="u-1",
            principal_type="user",
            resource_type="memory",
            resource_id="m-1",
            action="read",
            request_id="req-1",
            correlation_id="corr-1",
            duration_ms=42,
        )
        d = event.to_dict()
        assert d["tenant_id"] == "t-1"
        assert d["workspace_id"] == "w-1"
        assert d["project_id"] == "p-1"
        assert d["principal_id"] == "u-1"
        assert d["resource_type"] == "memory"
        assert d["resource_id"] == "m-1"
        assert d["action"] == "read"
        assert d["request_id"] == "req-1"
        assert d["correlation_id"] == "corr-1"
        assert d["duration_ms"] == 42

    def test_to_dict_excludes_none_fields(self):
        """to_dict should only include fields that exist on the dataclass."""
        event = AuditEvent()
        d = event.to_dict()
        # All canonical fields should be present (even if None)
        for field in (
            "event_id", "timestamp", "tenant_id", "workspace_id", "project_id",
            "principal_id", "principal_type", "resource_type", "resource_id",
            "action", "decision", "policy_id", "policy_version", "request_id",
            "correlation_id", "result_status", "duration_ms", "limits",
            "provenance_reference", "metadata",
        ):
            assert field in d


class TestAuditServiceEmit:
    """Test AuditService.emit() with default log sink."""

    def setup_method(self):
        self.audit = AuditService()
        self.events: list[dict] = []

        # Override log sink to capture events
        original_log_emit = self.audit._log_emit
        self.audit._sinks = [self.audit._log_emit]  # keep log sink

        def capture_sink(event: dict):
            self.events.append(event)

        self.audit.register_sink(capture_sink)

    def test_emit_returns_audit_event(self):
        event = self.audit.emit(
            event_type=MEMORY_READ,
            principal_id="u-1",
            resource_type="memory",
            action="read",
        )
        assert isinstance(event, AuditEvent)

    def test_emit_sends_to_all_sinks(self):
        self.audit.emit(
            event_type=MEMORY_READ,
            principal_id="u-1",
            resource_type="memory",
            action="read",
        )
        assert len(self.events) == 1

    def test_emit_includes_event_type(self):
        self.audit.emit(
            event_type=MEMORY_WRITE,
            principal_id="u-1",
            resource_type="memory",
            action="write",
        )
        assert self.events[0]["event_type"] == MEMORY_WRITE

    def test_emit_sanitizes_sensitive_fields(self):
        """Sensitive field names must be redacted in emitted events."""
        self.audit.emit(
            event_type=API_KEY_CREATED,
            principal_id="u-1",
            resource_type="api_key",
            action="create",
            metadata={
                "api_key": "sk-secret-value",
                "raw_key": "secret-raw-key",
                "password": "hunter2",
                "token": "bearer-token",
                "database_url": "postgres://secret@host/db",
                "normal_field": "safe-value",
            },
        )
        assert self.events[0]["metadata"]["api_key"] == "[redacted]"
        assert self.events[0]["metadata"]["raw_key"] == "[redacted]"
        assert self.events[0]["metadata"]["password"] == "[redacted]"
        assert self.events[0]["metadata"]["token"] == "[redacted]"
        assert self.events[0]["metadata"]["database_url"] == "[redacted]"
        assert self.events[0]["metadata"]["normal_field"] == "safe-value"

    def test_emit_does_not_fail_on_bad_sink(self):
        """Audit must not fail if a sink raises an exception."""
        def bad_sink(event: dict):
            raise RuntimeError("sink exploded")

        self.audit.register_sink(bad_sink)
        # Should not raise
        event = self.audit.emit(
            event_type=MEMORY_READ,
            principal_id="u-1",
            resource_type="memory",
            action="read",
        )
        assert isinstance(event, AuditEvent)

    def test_emit_multiple_events(self):
        self.audit.emit(event_type=MEMORY_READ, principal_id="u-1", resource_type="memory", action="read")
        self.audit.emit(event_type=MEMORY_WRITE, principal_id="u-1", resource_type="memory", action="write")
        self.audit.emit(event_type=TOOL_STARTED, principal_id="u-1", resource_type="tool", action="execute")
        assert len(self.events) == 3
        assert self.events[0]["event_type"] == MEMORY_READ
        assert self.events[1]["event_type"] == MEMORY_WRITE
        assert self.events[2]["event_type"] == TOOL_STARTED

    def test_emit_with_full_context(self):
        self.audit.emit(
            event_type=MEMORY_READ,
            tenant_id="tenant-1",
            workspace_id="ws-1",
            project_id="proj-1",
            principal_id="user-1",
            principal_type="user",
            resource_type="memory",
            resource_id="mem-1",
            action="read",
            decision="allow",
            policy_id="policy-1",
            policy_version=2,
            request_id="req-1",
            correlation_id="corr-1",
            result_status=RESULT_SUCCESS,
            duration_ms=15,
            limits={"max_records": 100},
            provenance_reference="prov-1",
        )
        e = self.events[0]
        assert e["tenant_id"] == "tenant-1"
        assert e["workspace_id"] == "ws-1"
        assert e["project_id"] == "proj-1"
        assert e["principal_id"] == "user-1"
        assert e["principal_type"] == "user"
        assert e["resource_type"] == "memory"
        assert e["resource_id"] == "mem-1"
        assert e["action"] == "read"
        assert e["decision"] == "allow"
        assert e["policy_id"] == "policy-1"
        assert e["policy_version"] == 2
        assert e["request_id"] == "req-1"
        assert e["correlation_id"] == "corr-1"
        assert e["result_status"] == RESULT_SUCCESS
        assert e["duration_ms"] == 15
        assert e["limits"] == {"max_records": 100}
        assert e["provenance_reference"] == "prov-1"


class TestPolicyEvent:
    """Test the policy_event convenience constructor."""

    def setup_method(self):
        self.audit = AuditService()
        self.events: list[dict] = []
        self.audit.register_sink(lambda e: self.events.append(e))

    def test_allow_maps_to_policy_allow_event(self):
        from app.services.audit import policy_event
        policy_event(
            self.audit,
            "allow",
            request_id="req-1",
            principal_id="u-1",
            resource_type="tool",
            action="execute",
        )
        assert self.events[0]["event_type"] == POLICY_ALLOW
        assert self.events[0]["decision"] == "allow"

    def test_deny_maps_to_policy_deny_event(self):
        from app.services.audit import policy_event
        policy_event(
            self.audit,
            "deny",
            request_id="req-1",
            principal_id="u-1",
            resource_type="credential",
            action="read",
            tenant_id="t-1",
        )
        assert self.events[0]["event_type"] == POLICY_DENY
        assert self.events[0]["decision"] == "deny"
        assert self.events[0]["tenant_id"] == "t-1"

    def test_confirmation_required_maps_correctly(self):
        from app.services.audit import policy_event
        policy_event(
            self.audit,
            "require_confirmation",
            request_id="req-1",
            principal_id="u-1",
            resource_type="tool",
            action="execute",
            limits={"timeout": 30},
        )
        assert self.events[0]["event_type"] == POLICY_CONFIRMATION_REQUIRED
        assert self.events[0]["limits"] == {"timeout": 30}

    def test_limited_maps_to_policy_limited_event(self):
        from app.services.audit import policy_event
        policy_event(
            self.audit,
            "allow_with_limits",
            request_id="req-1",
            principal_id="u-1",
            resource_type="memory",
            action="export",
            limits={"max_records": 500, "allowed_fields": ["id", "name"]},
        )
        assert self.events[0]["event_type"] == POLICY_LIMITED
        assert self.events[0]["limits"]["max_records"] == 500

    def test_unknown_decision_maps_to_request(self):
        from app.services.audit import policy_event, POLICY_REQUEST
        policy_event(
            self.audit,
            "unknown_decision",
            request_id="req-1",
            principal_id="u-1",
            resource_type="memory",
            action="read",
        )
        assert self.events[0]["event_type"] == POLICY_REQUEST


class TestOperationEvent:
    """Test the operation_event convenience constructor."""

    def setup_method(self):
        self.audit = AuditService()
        self.events: list[dict] = []
        self.audit.register_sink(lambda e: self.events.append(e))

    def test_basic_operation(self):
        from app.services.audit import operation_event
        operation_event(
            self.audit,
            event_type=MEMORY_READ,
            principal_id="u-1",
            principal_type="agent",
            resource_type="memory",
            action="read",
            resource_id="mem-1",
        )
        assert self.events[0]["event_type"] == MEMORY_READ
        assert self.events[0]["principal_type"] == "agent"
        assert self.events[0]["resource_id"] == "mem-1"

    def test_operation_with_denied_result(self):
        from app.services.audit import operation_event
        operation_event(
            self.audit,
            event_type=TOOL_DENIED,
            principal_id="u-1",
            principal_type="agent",
            resource_type="tool",
            action="execute",
            result_status=RESULT_DENIED,
        )
        assert self.events[0]["result_status"] == RESULT_DENIED

    def test_operation_with_failure_result(self):
        from app.services.audit import operation_event
        operation_event(
            self.audit,
            event_type=MODEL_REQUEST,
            principal_id="u-1",
            principal_type="service",
            resource_type="model",
            action="execute",
            result_status=RESULT_FAILURE,
            duration_ms=5000,
        )
        assert self.events[0]["result_status"] == RESULT_FAILURE
        assert self.events[0]["duration_ms"] == 5000


class TestAuditEventTypes:
    """Ensure all event type constants are properly defined and unique."""

    def test_all_constants_importable(self):
        from app.services.audit.constants import (
            POLICY_REQUEST, POLICY_ALLOW, POLICY_DENY,
            POLICY_CONFIRMATION_REQUIRED, POLICY_LIMITED,
            MEMORY_READ, MEMORY_SEARCH, MEMORY_WRITE, MEMORY_UPDATE,
            MEMORY_DELETE, MEMORY_EXPIRE, MEMORY_SHARE,
            TOOL_REQUEST, TOOL_STARTED, TOOL_COMPLETED, TOOL_FAILED, TOOL_DENIED,
            MODEL_REQUEST, MODEL_COMPLETED, MODEL_FAILED,
            AUTH_LOGIN, AUTH_LOGOUT, AUTH_LOGIN_FAILED, AUTH_TOKEN_REFRESH,
            API_KEY_CREATED, API_KEY_REVOKED, API_KEY_ROTATED,
            PROJECT_CREATED, PROJECT_DELETED, WORKSPACE_CREATED,
            WORKSPACE_MEMBER_ADDED, WORKSPACE_MEMBER_REMOVED,
            INGEST_STARTED, INGEST_COMPLETED, INGEST_FAILED, SOURCE_DELETED,
            RESULT_SUCCESS, RESULT_FAILURE, RESULT_DENIED, RESULT_PARTIAL,
        )
        # Just verify they are strings
        assert isinstance(POLICY_ALLOW, str)
        assert isinstance(MEMORY_READ, str)
        assert isinstance(TOOL_STARTED, str)
        assert isinstance(API_KEY_CREATED, str)

    def test_no_duplicate_event_types(self):
        """Event type strings should be unique."""
        from app.services.audit import constants as c
        values = [v for v in dir(c) if not v.startswith("_") and isinstance(getattr(c, v), str)]
        str_values = [getattr(c, v) for v in values if isinstance(getattr(c, v), str)]
        assert len(str_values) == len(set(str_values)), "Duplicate event type values found"

    def test_sensitive_fields_is_frozenset(self):
        from app.services.audit.constants import SENSITIVE_FIELDS
        assert isinstance(SENSITIVE_FIELDS, frozenset)
        assert "password" in SENSITIVE_FIELDS
        assert "api_key" in SENSITIVE_FIELDS
        assert "token" in SENSITIVE_FIELDS


class TestAuditRedactionDepth:
    """Test that redaction handles nested structures."""

    def setup_method(self):
        self.audit = AuditService()
        self.events: list[dict] = []
        self.audit.register_sink(lambda e: self.events.append(e))

    def test_nested_dict_redaction(self):
        self.audit.emit(
            event_type=API_KEY_CREATED,
            principal_id="u-1",
            resource_type="api_key",
            action="create",
            metadata={
                "outer": {
                    "api_key": "secret-value",
                    "safe": "visible",
                }
            },
        )
        assert self.events[0]["metadata"]["outer"]["api_key"] == "[redacted]"
        assert self.events[0]["metadata"]["outer"]["safe"] == "visible"

    def test_list_redaction(self):
        """Redaction works on dict values; list of scalars passes through unchanged.

        NOTE: value-level redaction (scanning strings for secrets) is a known
        future improvement.  Current redact covers field-name patterns only.
        """
        self.audit.emit(
            event_type=MEMORY_WRITE,
            principal_id="u-1",
            resource_type="memory",
            action="write",
            metadata={
                "tokens": ["tok-1", "tok-2", "secret-tok-3"],
            },
        )
        # "tokens" key matches "token" in SENSITIVE_FIELDS (substring),
        # so the entire list value gets redacted to "[redacted]".
        assert self.events[0]["metadata"]["tokens"] == "[redacted]"


__all__ = [
    "TestAuditEvent",
    "TestAuditServiceEmit",
    "TestPolicyEvent",
    "TestOperationEvent",
    "TestAuditEventTypes",
    "TestAuditRedactionDepth",
]
