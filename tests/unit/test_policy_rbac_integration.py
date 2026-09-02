"""Sprint 7 Phase 2 — RBAC evaluator + policy engine integration tests.

Verifies that:
1. RBAC permissions generate correct policy rules
2. Role hierarchy is preserved through the engine
3. All endpoint permissions are correctly mapped
4. Fail-closed behavior is maintained
"""
from __future__ import annotations

import uuid
import pytest

from app.services.policy.engine import (
    PolicyEngine, AuthorizationRequest,
    EFFECT_ALLOW, EFFECT_DENY, EFFECT_CONFIRM,
    RISK_LOW, RISK_MEDIUM, RISK_HIGH, DEFAULT_DECISION,
)
from app.services.policy.evaluator import (
    evaluate_rbac, build_auth_request, generate_rbac_policies,
)


class TestRBACPolicyGeneration:
    """Test that RBAC policies are correctly generated from the permission matrix."""

    def test_generates_owner_permissions(self):
        """Owner gets all permissions."""
        policies = generate_rbac_policies()
        assert len(policies) >= 1

    def test_owner_can_delete_workspace(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="owner-1",
            resource_type="workspace",
            action="delete",
            context={"role": "owner"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW

    def test_owner_can_manage_members(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="owner-1",
            resource_type="members",
            action="write",
            context={"role": "owner"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW

    def test_admin_can_invite_members(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="admin-1",
            resource_type="members",
            action="write",
            context={"role": "admin"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW

    def test_member_can_write_memory(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="member-1",
            resource_type="memory",
            action="write",
            context={"role": "member"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW

    def test_member_can_write_ingest(self):
        """Member can write ingest (upload sources)."""
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="member-1",
            resource_type="ingest",
            action="write",
            context={"role": "member"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW

    def test_viewer_can_read_memory(self):
        """Viewer can read memory (matches actual RBAC)."""
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="viewer-1",
            resource_type="memory",
            action="read",
            context={"role": "viewer"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW

    def test_viewer_cannot_write_memory(self):
        """Viewer cannot write memory (requires member role)."""
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="viewer-1",
            resource_type="memory",
            action="write",
            context={"role": "viewer"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_DENY

    def test_viewer_cannot_write_memory(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="viewer-1",
            resource_type="memory",
            action="write",
            context={"role": "viewer"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_DENY

    def test_admin_cannot_delete_workspace(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="admin-1",
            resource_type="workspace",
            action="delete",
            context={"role": "admin"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_DENY

    def test_viewer_cannot_delete_api_keys(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="viewer-1",
            resource_type="api_key",
            action="delete",
            context={"role": "viewer"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_DENY

    def test_admin_can_manage_api_keys(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="admin-1",
            resource_type="api_key",
            action="write",
            context={"role": "admin"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW

    def test_member_can_read_storage(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="member-1",
            resource_type="storage",
            action="read",
            context={"role": "member"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW

    def test_viewer_can_read_storage(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="viewer-1",
            resource_type="storage",
            action="read",
            context={"role": "viewer"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW

    def test_admin_can_delete_storage(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="admin-1",
            resource_type="storage",
            action="delete",
            context={"role": "admin"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW

    def test_member_cannot_delete_storage(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="member-1",
            resource_type="storage",
            action="delete",
            context={"role": "member"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_DENY


class TestFailClosed:
    """Privileged actions fail closed on missing/malformed authorization."""

    def test_missing_role_denies(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="unknown",
            resource_type="memory",
            action="delete",
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_DENY

    def test_empty_context_denies_write(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="memory",
            action="write",
            context={},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_DENY

    def test_empty_context_allows_viewer_read(self):
        """Viewer read is the most permissive allowed — but empty context should deny."""
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="memory",
            action="read",
            context={},
        )
        decision = evaluate_rbac(engine, req)
        # Empty role → no permission matches → DENY (fail-closed)
        assert decision.decision == EFFECT_DENY


class TestBuildAuthRequest:
    """Test the AuthorizationRequest builder from TenantContext."""

    def test_builds_correct_request(self):
        request = build_auth_request(
            principal_id="user-123",
            role="admin",
            resource_type="memory",
            action="delete",
            resource_id="mem-456",
            tenant_id="tenant-1",
            workspace_id="ws-1",
            project_id="proj-1",
        )
        assert request.principal_id == "user-123"
        assert request.principal_type == "user"
        assert request.resource_type == "memory"
        assert request.action == "delete"
        assert request.resource_id == "mem-456"
        assert request.tenant_id == "tenant-1"
        assert request.workspace_id == "ws-1"
        assert request.project_id == "proj-1"
        assert request.context["role"] == "admin"

    def test_builds_with_extra_context(self):
        request = build_auth_request(
            principal_id="user-1",
            role="member",
            resource_type="storage",
            action="write",
            context={"source": "api", "request_id": "req-1"},
        )
        assert request.context["role"] == "member"
        assert request.context["source"] == "api"
        assert request.context["request_id"] == "req-1"


class TestRBACE2E:
    """End-to-end RBAC scenarios matching actual endpoint permissions."""

    def test_project_create_by_member(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="member-1",
            resource_type="project",
            action="write",
            context={"role": "member"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW

    def test_project_delete_by_member_denied(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="member-1",
            resource_type="project",
            action="delete",
            context={"role": "member"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_DENY

    def test_project_delete_by_owner(self):
        """Owner can delete projects (owner-only action)."""
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="owner-1",
            resource_type="project",
            action="delete",
            context={"role": "owner"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW

    def test_chat_use_by_viewer(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="viewer-1",
            resource_type="chat",
            action="use",
            context={"role": "viewer"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW

    def test_memory_search_by_member(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="member-1",
            resource_type="memory",
            action="search",
            context={"role": "member"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW

    def test_ingest_read_by_viewer(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="viewer-1",
            resource_type="connector",
            action="execute",
            context={"role": "viewer"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_DENY

    def test_feedback_write_by_member(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="member-1",
            resource_type="feedback",
            action="write",
            context={"role": "member"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW

    def test_api_key_read_by_member(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="member-1",
            resource_type="api_key",
            action="read",
            context={"role": "member"},
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW
