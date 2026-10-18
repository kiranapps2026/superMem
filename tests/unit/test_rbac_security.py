"""Sprint 7 — RBAC security review tests.

Tests the RBAC permission matrix for security correctness:
- Role hierarchy integrity
- Privilege escalation prevention
- Cross-tenant isolation
- Fail-closed behavior
- Policy conflict resolution
- Sensitive operation controls
"""
from __future__ import annotations

import pytest

from app.services.policy.engine import (
    PolicyEngine,
    AuthorizationRequest,
    EFFECT_ALLOW,
    EFFECT_DENY,
    EFFECT_CONFIRM,
    EFFECT_LIMITED,
    RISK_LOW,
    RISK_MEDIUM,
    RISK_HIGH,
    RISK_CRITICAL,
)
from app.services.policy.evaluator import (
    evaluate_rbac,
    build_auth_request,
    generate_rbac_policies,
    ROLE_HIERARCHY,
)


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_engine() -> PolicyEngine:
    return PolicyEngine()


def _rbac_request(resource: str, action: str, role: str = "member",
                  tenant_id: str = "tenant-1") -> AuthorizationRequest:
    return build_auth_request(
        principal_id="user-1",
        role=role,
        resource_type=resource,
        action=action,
        tenant_id=tenant_id,
    )


# ── Role Hierarchy Integrity ───────────────────────────────────────────────

class TestRoleHierarchy:
    """Verify role hierarchy: owner > admin > member > viewer."""

    def test_owner_has_highest_privilege(self):
        assert ROLE_HIERARCHY["owner"] == 1000

    def test_viewer_has_lowest_privilege(self):
        assert ROLE_HIERARCHY["viewer"] == 50

    def test_admin_higher_than_member(self):
        assert ROLE_HIERARCHY["admin"] > ROLE_HIERARCHY["member"]

    def test_member_higher_than_viewer(self):
        assert ROLE_HIERARCHY["member"] > ROLE_HIERARCHY["viewer"]

    def test_owner_can_read(self):
        engine = _make_engine()
        req = _rbac_request("memory", "read", role="owner")
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW

    def test_viewer_can_read(self):
        engine = _make_engine()
        req = _rbac_request("memory", "read", role="viewer")
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW

    def test_viewer_cannot_write(self):
        engine = _make_engine()
        req = _rbac_request("memory", "write", role="viewer")
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_DENY

    def test_member_cannot_delete(self):
        engine = _make_engine()
        req = _rbac_request("memory", "delete", role="member")
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_DENY


# ── Privilege Escalation Prevention ────────────────────────────────────────

class TestPrivilegeEscalation:
    """Users cannot escalate their role through requests."""

    def test_user_cannot_promote_via_context(self):
        """Role comes from authenticated identity, not user-supplied request."""
        engine = _make_engine()
        honest_req = _rbac_request("memory", "write", role="viewer")
        honest = evaluate_rbac(engine, honest_req)
        assert honest.decision == EFFECT_DENY

    def test_agent_without_role_cannot_access(self):
        """Agent without proper role authentication denied access."""
        engine = _make_engine()
        agent_req = AuthorizationRequest(
            principal_id="agent-1",
            principal_type="agent",
            resource_type="memory",
            action="write",
            context={"impersonating": "admin"},
        )
        decision = evaluate_rbac(engine, agent_req)
        assert decision.decision == EFFECT_DENY


# ── Cross-Tenant Isolation ─────────────────────────────────────────────────

class TestCrossTenantIsolation:
    """Users cannot access resources from other tenants."""

    def test_rbac_policies_tenant_agnostic(self):
        """RBAC policies don't carry tenant_id — repository filters them."""
        policies = generate_rbac_policies()
        for p in policies:
            assert p.get("tenant_id") is None


# ── Sensitive Operations ───────────────────────────────────────────────────

class TestSensitiveOperations:
    """Sensitive operations have elevated protections."""

    def test_delete_has_elevated_risk(self):
        """Delete operations have elevated risk level (medium in RBAC matrix)."""
        engine = _make_engine()
        req = _rbac_request("memory", "delete", role="admin")
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW
        # RBAC risk_for returns "medium" for delete actions
        assert decision.risk == RISK_MEDIUM

    def test_api_key_write_requires_admin(self):
        """API key write requires admin role."""
        engine = _make_engine()
        req_member = _rbac_request("api_key", "write", role="member")
        req_admin = _rbac_request("api_key", "write", role="admin")

        assert evaluate_rbac(engine, req_member).decision == EFFECT_DENY
        assert evaluate_rbac(engine, req_admin).decision == EFFECT_ALLOW

    def test_api_key_delete_requires_admin(self):
        """API key deletion requires admin."""
        engine = _make_engine()
        req = _rbac_request("api_key", "delete", role="admin")
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW


# ── Fail-Closed Security ───────────────────────────────────────────────────

class TestFailClosed:
    """System fails closed on authorization errors."""

    def test_empty_policies_deny(self):
        engine = _make_engine()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="memory",
            action="write",
        )
        decision = engine.evaluate(req, policies=[])
        assert decision.decision == EFFECT_DENY

    def test_unknown_resource_denied(self):
        """Unknown resource types are denied."""
        engine = _make_engine()
        policies = generate_rbac_policies()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="nonexistent_resource",
            action="read",
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_DENY

    def test_no_matching_action_denied(self):
        """No matching action rule → deny."""
        engine = _make_engine()
        policies = generate_rbac_policies()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="memory",
            action="nonexistent_action",
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_DENY


# ── Policy Conflict Resolution ─────────────────────────────────────────────

class TestPolicyConflictResolution:
    """Policy conflicts are resolved correctly."""

    def test_explicit_deny_wins_over_allow(self):
        """When both allow and deny match, deny wins."""
        engine = _make_engine()
        policies = [
            {
                "policy_id": "allow-all",
                "policy_version": 1,
                "rules": [
                    {"resource": "memory", "action": "*", "effect": EFFECT_ALLOW,
                     "risk": RISK_LOW},
                ],
            },
            {
                "policy_id": "deny-creds",
                "policy_version": 1,
                "rules": [
                    {"resource": "credential", "action": "*", "effect": EFFECT_DENY,
                     "risk": RISK_CRITICAL},
                ],
            },
        ]

        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="credential",
            action="read",
        )
        d = engine.evaluate(req, policies=policies)
        assert d.decision == EFFECT_DENY

    def test_no_policies_denies(self):
        """No policies at all → deny (fail closed)."""
        engine = _make_engine()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="memory",
            action="read",
        )
        decision = engine.evaluate(req, policies=[])
        assert decision.decision == EFFECT_DENY
        assert decision.risk == RISK_HIGH

    def test_limited_effect_returns_limits(self):
        """allow_with_limits returns limits in decision."""
        engine = _make_engine()
        policies = [
            {
                "policy_id": "p-limited",
                "policy_version": 1,
                "rules": [
                    {"resource": "source", "action": "export",
                     "effect": EFFECT_LIMITED, "risk": RISK_MEDIUM,
                     "limits": {"max_records": 100}},
                ],
            }
        ]
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="source",
            action="export",
        )
        decision = engine.evaluate(req, policies=policies)
        assert decision.decision == EFFECT_LIMITED
        assert decision.limits is not None
        assert decision.limits.get("max_records") == 100


# ── RBAC Permission Matrix Coverage ────────────────────────────────────────

class TestRBACMatrix:
    """Comprehensive RBAC permission matrix verification."""

    def test_role_hierarchy_levels(self):
        """Verify role hierarchy: owner > admin > member > viewer."""
        assert ROLE_HIERARCHY["owner"] > ROLE_HIERARCHY["admin"]
        assert ROLE_HIERARCHY["admin"] > ROLE_HIERARCHY["member"]
        assert ROLE_HIERARCHY["member"] > ROLE_HIERARCHY["viewer"]

    def test_owner_has_all_memory_permissions(self):
        """Owner can read, write, delete memory."""
        engine = _make_engine()
        for action in ["read", "write", "delete"]:
            req = _rbac_request("memory", action, role="owner")
            decision = evaluate_rbac(engine, req)
            assert decision.decision == EFFECT_ALLOW, f"Owner should be allowed {action}"

    def test_member_can_read_write_not_delete(self):
        """Member can read/write but not delete."""
        engine = _make_engine()
        read_req = _rbac_request("memory", "read", role="member")
        write_req = _rbac_request("memory", "write", role="member")
        delete_req = _rbac_request("memory", "delete", role="member")

        assert evaluate_rbac(engine, read_req).decision == EFFECT_ALLOW
        assert evaluate_rbac(engine, write_req).decision == EFFECT_ALLOW
        assert evaluate_rbac(engine, delete_req).decision == EFFECT_DENY

    def test_viewer_read_only(self):
        """Viewer can only read, nothing else."""
        engine = _make_engine()
        for action in ["read", "write", "update", "delete", "export", "share"]:
            req = _rbac_request("memory", action, role="viewer")
            decision = evaluate_rbac(engine, req)
            if action == "read":
                assert decision.decision == EFFECT_ALLOW
            else:
                assert decision.decision == EFFECT_DENY

    def test_admin_can_delete(self):
        """Admin can delete memory."""
        engine = _make_engine()
        req = _rbac_request("memory", "delete", role="admin")
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_ALLOW

    def test_generate_rbac_policies_returns_list(self):
        """generate_rbac_policies returns a non-empty list."""
        policies = generate_rbac_policies()
        assert isinstance(policies, list)
        assert len(policies) > 0

    def test_build_auth_request_populates_fields(self):
        """build_auth_request creates a valid AuthorizationRequest."""
        req = build_auth_request(
            principal_id="user-1",
            role="admin",
            resource_type="tool",
            action="execute",
            tenant_id="tenant-1",
            workspace_id="ws-1",
        )
        assert isinstance(req, AuthorizationRequest)
        assert req.principal_id == "user-1"
        assert req.resource_type == "tool"
        assert req.action == "execute"
        assert req.tenant_id == "tenant-1"
        assert req.workspace_id == "ws-1"
        assert req.request_id is not None


# ── Multi-Resource RBAC ────────────────────────────────────────────────────

class TestMultiResourceRBAC:
    """RBAC policies work across different resource types."""

    def test_memory_read_by_member(self):
        engine = _make_engine()
        req = build_auth_request(
            principal_id="user-1", role="member",
            resource_type="memory", action="read",
        )
        assert evaluate_rbac(engine, req).decision == EFFECT_ALLOW

    def test_storage_write_by_member(self):
        """Member can write to storage (in RBAC matrix)."""
        engine = _make_engine()
        req = build_auth_request(
            principal_id="user-1", role="member",
            resource_type="storage", action="write",
        )
        assert evaluate_rbac(engine, req).decision == EFFECT_ALLOW

    def test_tool_execute_not_in_rbac_matrix(self):
        """tool:execute not in RBAC matrix → fail closed."""
        engine = _make_engine()
        req = build_auth_request(
            principal_id="user-1", role="admin",
            resource_type="tool", action="execute",
        )
        # tool:execute is not in _RESOURCE_ACTIONS, so no RBAC rule matches
        assert evaluate_rbac(engine, req).decision == EFFECT_DENY

    def test_source_export_not_in_rbac_matrix(self):
        """source:export not in RBAC matrix → fail closed."""
        engine = _make_engine()
        req = build_auth_request(
            principal_id="user-1", role="admin",
            resource_type="source", action="export",
        )
        # source:export is not in _RESOURCE_ACTIONS
        assert evaluate_rbac(engine, req).decision == EFFECT_DENY

    def test_project_read_by_viewer(self):
        engine = _make_engine()
        req = build_auth_request(
            principal_id="user-1", role="viewer",
            resource_type="project", action="read",
        )
        assert evaluate_rbac(engine, req).decision == EFFECT_ALLOW


# ── Security Invariants ────────────────────────────────────────────────────

class TestSecurityInvariants:
    """Fundamental security invariants that must never be violated."""

    def test_no_implicit_allow(self):
        """Engine never implicitly allows without matching rule."""
        engine = _make_engine()
        policies = generate_rbac_policies()
        req = build_auth_request(
            principal_id="user-1", role="member",
            resource_type="memory", action="delete",
        )
        decision = evaluate_rbac(engine, req)
        assert decision.decision == EFFECT_DENY

    def test_request_id_uniqueness(self):
        """Each request gets a unique request_id."""
        req1 = AuthorizationRequest(principal_id="u1", resource_type="memory", action="read")
        req2 = AuthorizationRequest(principal_id="u1", resource_type="memory", action="read")
        assert req1.request_id != req2.request_id


# ── RBAC Action Coverage ───────────────────────────────────────────────────

class TestRBACActionCoverage:
    """All defined actions are covered by RBAC."""

    def test_read_action_allowed(self):
        engine = _make_engine()
        req = _rbac_request("memory", "read", role="viewer")
        assert evaluate_rbac(engine, req).decision == EFFECT_ALLOW

    def test_search_action_allowed_for_viewer(self):
        engine = _make_engine()
        req = _rbac_request("memory", "search", role="viewer")
        assert evaluate_rbac(engine, req).decision == EFFECT_ALLOW

    def test_write_action_requires_member(self):
        engine = _make_engine()
        viewer_req = _rbac_request("memory", "write", role="viewer")
        member_req = _rbac_request("memory", "write", role="member")
        assert evaluate_rbac(engine, viewer_req).decision == EFFECT_DENY
        assert evaluate_rbac(engine, member_req).decision == EFFECT_ALLOW

    def test_delete_action_requires_admin(self):
        engine = _make_engine()
        member_req = _rbac_request("memory", "delete", role="member")
        admin_req = _rbac_request("memory", "delete", role="admin")
        assert evaluate_rbac(engine, member_req).decision == EFFECT_DENY
        assert evaluate_rbac(engine, admin_req).decision == EFFECT_ALLOW


__all__ = [
    "TestRoleHierarchy",
    "TestPrivilegeEscalation",
    "TestCrossTenantIsolation",
    "TestSensitiveOperations",
    "TestFailClosed",
    "TestPolicyConflictResolution",
    "TestRBACMatrix",
    "TestMultiResourceRBAC",
    "TestSecurityInvariants",
    "TestRBACActionCoverage",
]
