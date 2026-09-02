"""Audit event types and canonical schema constants (Sprint 7).

Every audit event in the system uses these constants so that:
  - producers agree on event type names
  - consumers can filter consistently
  - the audit service knows how to log each category
"""
from __future__ import annotations

# ── Event categories ────────────────────────────────────────────────────────

# Policy decisions
POLICY_REQUEST = "policy.request"
POLICY_ALLOW = "policy.allow"
POLICY_DENY = "policy.deny"
POLICY_CONFIRMATION_REQUIRED = "policy.confirmation_required"
POLICY_LIMITED = "policy.limited"

# Memory operations
MEMORY_READ = "memory.read"
MEMORY_SEARCH = "memory.search"
MEMORY_WRITE = "memory.write"
MEMORY_UPDATE = "memory.update"
MEMORY_DELETE = "memory.delete"
MEMORY_EXPIRE = "memory.expire"
MEMORY_SHARE = "memory.share"

# Tool operations
TOOL_REQUEST = "tool.request"
TOOL_STARTED = "tool.started"
TOOL_COMPLETED = "tool.completed"
TOOL_FAILED = "tool.failed"
TOOL_DENIED = "tool.denied"

# Model operations
MODEL_REQUEST = "model.request"
MODEL_COMPLETED = "model.completed"
MODEL_FAILED = "model.failed"

# Authentication
AUTH_LOGIN = "auth.login"
AUTH_LOGOUT = "auth.logout"
AUTH_LOGIN_FAILED = "auth.login_failed"
AUTH_TOKEN_REFRESH = "auth.token_refresh"

# Resource management
API_KEY_CREATED = "api_key.created"
API_KEY_REVOKED = "api_key.revoked"
API_KEY_ROTATED = "api_key.rotated"
PROJECT_CREATED = "project.created"
PROJECT_DELETED = "project.deleted"
WORKSPACE_CREATED = "workspace.created"
WORKSPACE_MEMBER_ADDED = "workspace.member_added"
WORKSPACE_MEMBER_REMOVED = "workspace.member_removed"

# Data lifecycle
INGEST_STARTED = "ingest.started"
INGEST_COMPLETED = "ingest.completed"
INGEST_FAILED = "ingest.failed"
SOURCE_DELETED = "source.deleted"

# ── Audit event schema fields (canonical) ──────────────────────────────────

AUDIT_FIELDS = (
    "event_id",
    "timestamp",
    "event_type",
    "tenant_id",
    "workspace_id",
    "project_id",
    "principal_id",
    "principal_type",
    "resource_type",
    "resource_id",
    "action",
    "decision",
    "policy_id",
    "policy_version",
    "request_id",
    "correlation_id",
    "result_status",
    "duration_ms",
    "limits",
    "provenance_reference",
    "metadata",
)

# ── Sensitive fields that must never appear in audit logs ───────────────────

SENSITIVE_FIELDS = frozenset({
    "password",
    "hashed_password",
    "secret",
    "api_key",
    "raw_key",
    "token",
    "refresh_token",
    "database_url",
    "connection_string",
    "private_key",
    "encryption_key",
})

# ── Audit result statuses ──────────────────────────────────────────────────

RESULT_SUCCESS = "success"
RESULT_FAILURE = "failure"
RESULT_DENIED = "denied"
RESULT_PARTIAL = "partial"

__all__ = [
    "POLICY_REQUEST",
    "POLICY_ALLOW",
    "POLICY_DENY",
    "POLICY_CONFIRMATION_REQUIRED",
    "POLICY_LIMITED",
    "MEMORY_READ",
    "MEMORY_SEARCH",
    "MEMORY_WRITE",
    "MEMORY_UPDATE",
    "MEMORY_DELETE",
    "MEMORY_EXPIRE",
    "MEMORY_SHARE",
    "TOOL_REQUEST",
    "TOOL_STARTED",
    "TOOL_COMPLETED",
    "TOOL_FAILED",
    "TOOL_DENIED",
    "MODEL_REQUEST",
    "MODEL_COMPLETED",
    "MODEL_FAILED",
    "AUTH_LOGIN",
    "AUTH_LOGOUT",
    "AUTH_LOGIN_FAILED",
    "AUTH_TOKEN_REFRESH",
    "API_KEY_CREATED",
    "API_KEY_REVOKED",
    "API_KEY_ROTATED",
    "PROJECT_CREATED",
    "PROJECT_DELETED",
    "WORKSPACE_CREATED",
    "WORKSPACE_MEMBER_ADDED",
    "WORKSPACE_MEMBER_REMOVED",
    "INGEST_STARTED",
    "INGEST_COMPLETED",
    "INGEST_FAILED",
    "SOURCE_DELETED",
    "AUDIT_FIELDS",
    "SENSITIVE_FIELDS",
    "RESULT_SUCCESS",
    "RESULT_FAILURE",
    "RESULT_DENIED",
    "RESULT_PARTIAL",
]
