"""Sprint 7 — Policy Engine unit tests.

Tests the core authorization engine, rule matching, and decision logic.
"""
from __future__ import annotations

import pytest

from app.services.policy.engine import (
    PolicyEngine,
    AuthorizationRequest,
    PolicyDecision,
    EFFECT_ALLOW,
    EFFECT_DENY,
    EFFECT_CONFIRM,
    EFFECT_LIMITED,
    EFFECT_REDACTED,
    RISK_LOW,
    RISK_MEDIUM,
    RISK_HIGH,
    RISK_CRITICAL,
    DEFAULT_DECISION,
    VALID_EFFECTS,
)


# ── Rule matching helpers ──────────────────────────────────────────────────


class TestRuleMatching:
    def test_allow_matching_resource_and_action(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="memory",
            action="read",
        )
        policies = [{
            "policy_id": "p1",
            "policy_version": 1,
            "rules": [
                {"resource": "memory", "action": "read", "effect": EFFECT_ALLOW, "risk": RISK_LOW},
            ],
        }]
        decision = engine.evaluate(req, policies=policies)
        assert decision.decision == EFFECT_ALLOW
        assert decision.policy_id == "p1"

    def test_deny_explicit(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="memory",
            action="delete",
        )
        policies = [{
            "policy_id": "p1",
            "policy_version": 1,
            "rules": [
                {"resource": "memory", "action": "delete", "effect": EFFECT_DENY, "risk": RISK_HIGH},
            ],
        }]
        decision = engine.evaluate(req, policies=policies)
        assert decision.decision == EFFECT_DENY

    def test_wildcard_resource(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="tool",
            action="execute",
        )
        policies = [{
            "policy_id": "p1",
            "policy_version": 1,
            "rules": [
                {"resource": "*", "action": "execute", "effect": EFFECT_DENY, "risk": RISK_HIGH},
            ],
        }]
        decision = engine.evaluate(req, policies=policies)
        assert decision.decision == EFFECT_DENY

    def test_no_match_returns_default_deny(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="memory",
            action="export",
        )
        policies = [{
            "policy_id": "p1",
            "policy_version": 1,
            "rules": [
                {"resource": "memory", "action": "read", "effect": EFFECT_ALLOW, "risk": RISK_LOW},
            ],
        }]
        decision = engine.evaluate(req, policies=policies)
        assert decision.decision == DEFAULT_DECISION
        assert decision.reason == "no matching policy rule found"

    def test_empty_policies_returns_default_deny(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="memory",
            action="read",
        )
        decision = engine.evaluate(req, policies=[])
        assert decision.decision == DEFAULT_DECISION
        assert decision.reason == "no policies configured"

    def test_deny_overrides_allow(self):
        """Explicit deny always wins — first deny match short-circuits."""
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="memory",
            action="read",
        )
        policies = [{
            "policy_id": "p1",
            "policy_version": 1,
            "rules": [
                {"resource": "memory", "action": "read", "effect": EFFECT_ALLOW, "risk": RISK_LOW},
                {"resource": "memory", "action": "read", "effect": EFFECT_DENY, "risk": RISK_HIGH},
            ],
        }]
        decision = engine.evaluate(req, policies=policies)
        assert decision.decision == EFFECT_DENY

    def test_require_confirmation(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="memory",
            action="delete",
        )
        policies = [{
            "policy_id": "p1",
            "policy_version": 1,
            "rules": [
                {"resource": "memory", "action": "delete", "effect": EFFECT_CONFIRM, "risk": RISK_MEDIUM},
            ],
        }]
        decision = engine.evaluate(req, policies=policies)
        assert decision.decision == EFFECT_CONFIRM

    def test_allow_with_limits(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="memory",
            action="export",
        )
        policies = [{
            "policy_id": "p1",
            "policy_version": 1,
            "rules": [
                {"resource": "memory", "action": "export", "effect": EFFECT_LIMITED,
                 "limits": {"max_records": 500, "allowed_fields": ["id", "status"]}, "risk": RISK_MEDIUM},
            ],
        }]
        decision = engine.evaluate(req, policies=policies)
        assert decision.decision == EFFECT_LIMITED
        assert decision.limits["max_records"] == 500

    def test_allow_redacted(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="memory",
            action="export",
        )
        policies = [{
            "policy_id": "p1",
            "policy_version": 1,
            "rules": [
                {"resource": "memory", "action": "export", "effect": EFFECT_REDACTED,
                 "limits": {"redact_fields": ["email", "phone"]}, "risk": RISK_MEDIUM},
            ],
        }]
        decision = engine.evaluate(req, policies=policies)
        assert decision.decision == EFFECT_REDACTED
        assert decision.limits["redact_fields"] == ["email", "phone"]


# ── Condition matching ─────────────────────────────────────────────────────


class TestConditionMatching:
    def test_condition_role_match(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="admin-1",
            resource_type="workspace",
            action="write",
            context={"role": "admin"},
        )
        policies = [{
            "policy_id": "p1",
            "policy_version": 1,
            "rules": [
                {"resource": "workspace", "action": "write", "effect": EFFECT_DENY,
                 "conditions": {"role": {"op": "not_in", "value": ["owner", "admin"]}},
                 "risk": RISK_CRITICAL},
            ],
        }]
        decision = engine.evaluate(req, policies=policies)
        # admin IS in the allowed list, so condition fails → rule doesn't match
        assert decision.decision == DEFAULT_DECISION

    def test_condition_role_mismatch_triggers_deny(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="viewer-1",
            resource_type="workspace",
            action="write",
            context={"role": "viewer"},
        )
        policies = [{
            "policy_id": "p1",
            "policy_version": 1,
            "rules": [
                {"resource": "workspace", "action": "write", "effect": EFFECT_DENY,
                 "conditions": {"role": {"op": "not_in", "value": ["owner", "admin"]}},
                 "risk": RISK_CRITICAL},
            ],
        }]
        decision = engine.evaluate(req, policies=policies)
        assert decision.decision == EFFECT_DENY


# ── Default policies ───────────────────────────────────────────────────────


class TestDefaultPolicies:
    def test_default_tenant_policies_exist(self):
        engine = PolicyEngine()
        defaults = engine.default_tenant_policies("tenant-1")
        assert len(defaults) > 0
        ids = [p["policy_id"] for p in defaults]
        assert "default-memory-read" in ids
        assert "default-deny-admin" in ids

    def test_default_memory_allow_read(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="memory",
            action="read",
            context={"role": "member"},
        )
        decision = engine.evaluate(req, policies=engine.default_tenant_policies("tenant-1"))
        assert decision.decision == EFFECT_ALLOW

    def test_default_memory_search_allowed(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="memory",
            action="search",
            context={"role": "member"},
        )
        decision = engine.evaluate(req, policies=engine.default_tenant_policies("tenant-1"))
        assert decision.decision == EFFECT_ALLOW

    def test_default_export_requires_confirmation(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="memory",
            action="export",
            context={"role": "member"},
        )
        decision = engine.evaluate(req, policies=engine.default_tenant_policies("tenant-1"))
        assert decision.decision == EFFECT_CONFIRM

    def test_default_tool_execute_denied(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="tool",
            action="execute",
            context={"role": "viewer"},
        )
        decision = engine.evaluate(req, policies=engine.default_tenant_policies("tenant-1"))
        # Default policies require confirmation for tool execution
        assert decision.decision in (EFFECT_CONFIRM, EFFECT_DENY)
        assert decision.risk in ("medium", "high")


# ── Risk levels ────────────────────────────────────────────────────────────


class TestRiskLevels:
    def test_deny_carries_critical_risk(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="database",
            action="delete",
        )
        policies = [{
            "policy_id": "p1",
            "policy_version": 1,
            "rules": [
                {"resource": "database", "action": "delete", "effect": EFFECT_DENY,
                 "risk": RISK_CRITICAL},
            ],
        }]
        decision = engine.evaluate(req, policies=policies)
        assert decision.risk == RISK_CRITICAL

    def test_low_risk_default(self):
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="user-1",
            resource_type="memory",
            action="read",
        )
        policies = [{
            "policy_id": "p1",
            "policy_version": 1,
            "rules": [
                {"resource": "memory", "action": "read", "effect": EFFECT_ALLOW, "risk": RISK_LOW},
            ],
        }]
        decision = engine.evaluate(req, policies=policies)
        assert decision.risk == RISK_LOW


# ── Integration scenarios ──────────────────────────────────────────────────


class TestIntegrationScenarios:
    def test_customer_support_agent_scenario(self):
        """customer_support_agent: ALLOW crm.customer.read, DENY credentials.export"""
        engine = PolicyEngine()
        policies = [{
            "policy_id": "crm-policy",
            "policy_version": 1,
            "rules": [
                {"resource": "crm.customer", "action": "read", "effect": EFFECT_ALLOW, "risk": RISK_LOW},
                {"resource": "credentials", "action": "export", "effect": EFFECT_DENY, "risk": RISK_CRITICAL},
            ],
        }]

        # Allowed
        read_req = AuthorizationRequest(
            principal_id="csa-1", principal_type="agent",
            resource_type="crm.customer", action="read",
        )
        assert engine.evaluate(read_req, policies=policies).decision == EFFECT_ALLOW

        # Denied
        export_req = AuthorizationRequest(
            principal_id="csa-1", principal_type="agent",
            resource_type="credentials", action="export",
        )
        assert engine.evaluate(export_req, policies=policies).decision == EFFECT_DENY

    def test_cross_project_isolation(self):
        """Agent A can read project A but not project B."""
        engine = PolicyEngine()
        policies = [{
            "policy_id": "isolation",
            "policy_version": 1,
            "rules": [
                {"resource": "memory:project_A", "action": "read", "effect": EFFECT_ALLOW, "risk": RISK_LOW},
                {"resource": "memory:project_B", "action": "read", "effect": EFFECT_DENY, "risk": RISK_HIGH},
            ],
        }]

        req_a = AuthorizationRequest(
            principal_id="agent-A", principal_type="agent",
            resource_type="memory", resource_id="project_A", action="read",
        )
        assert engine.evaluate(req_a, policies=policies).decision == EFFECT_ALLOW

        req_b = AuthorizationRequest(
            principal_id="agent-A", principal_type="agent",
            resource_type="memory", resource_id="project_B", action="read",
        )
        assert engine.evaluate(req_b, policies=policies).decision == EFFECT_DENY

    def test_deployment_agent_confirmation(self):
        """Deployment agent: shell.execute requires confirmation."""
        engine = PolicyEngine()
        policies = [{
            "policy_id": "deploy",
            "policy_version": 1,
            "rules": [
                {"resource": "tool.shell", "action": "execute", "effect": EFFECT_CONFIRM,
                 "risk": RISK_HIGH},
            ],
        }]
        req = AuthorizationRequest(
            principal_id="deploy-agent", principal_type="agent",
            resource_type="tool", resource_id="shell", action="execute",
        )
        decision = engine.evaluate(req, policies=policies)
        assert decision.decision == EFFECT_CONFIRM
        assert decision.risk == RISK_HIGH

    def test_analytics_agent_limited_export(self):
        """Analytics agent: export with limits on fields and record count."""
        engine = PolicyEngine()
        policies = [{
            "policy_id": "analytics",
            "policy_version": 1,
            "rules": [
                {"resource": "crm.customer", "action": "export", "effect": EFFECT_LIMITED,
                 "limits": {"max_records": 500, "allowed_fields": ["id", "status", "created_at"]},
                 "risk": RISK_MEDIUM},
            ],
        }]
        req = AuthorizationRequest(
            principal_id="analytics-agent", principal_type="agent",
            resource_type="crm.customer", action="export",
        )
        decision = engine.evaluate(req, policies=policies)
        assert decision.decision == EFFECT_LIMITED
        assert decision.limits["max_records"] == 500
        assert decision.limits["allowed_fields"] == ["id", "status", "created_at"]

    def test_unknown_principal_denied(self):
        """Unknown agent/user → no policies match → DENY."""
        engine = PolicyEngine()
        req = AuthorizationRequest(
            principal_id="unknown",
            principal_type="agent",
            resource_type="memory",
            action="read",
        )
        decision = engine.evaluate(req, policies=[])
        assert decision.decision == DEFAULT_DECISION

    def test_tenant_isolation_via_conditions(self):
        """Policy with tenant_id condition isolates tenants."""
        engine = PolicyEngine()
        policies = [{
            "policy_id": "tenant-a-only",
            "policy_version": 1,
            "rules": [
                {"resource": "memory", "action": "read", "effect": EFFECT_ALLOW,
                 "conditions": {"tenant_id": "tenant-a"}, "risk": RISK_LOW},
            ],
        }]
        # Tenant A → allowed
        req_a = AuthorizationRequest(
            principal_id="user-a", resource_type="memory", action="read",
            tenant_id="tenant-a",
        )
        assert engine.evaluate(req_a, policies=policies).decision == EFFECT_ALLOW

        # Tenant B → condition fails → default deny
        req_b = AuthorizationRequest(
            principal_id="user-b", resource_type="memory", action="read",
            tenant_id="tenant-b",
        )
        assert engine.evaluate(req_b, policies=policies).decision == DEFAULT_DECISION


# ── Authoritative modes ─────────────────────────────────────────────────────


class TestAuthoritativeMode:
    def test_authoritative_deny_blocks_even_legacy_allow(self):
        """In authoritative mode, engine deny overrides legacy permissive checks."""
        engine = PolicyEngine()

        # Deny for shell.execute — authoritative
        policies = [{
            "policy_id": "auth-shell",
            "policy_version": 1,
            "rules": [
                {"resource": "tool.shell", "action": "execute", "effect": EFFECT_DENY,
                 "risk": RISK_CRITICAL},
            ],
        }]
        req = AuthorizationRequest(
            principal_id="agent-1", principal_type="agent",
            resource_type="tool", resource_id="shell", action="execute",
        )
        decision = engine.evaluate(req, policies=policies)
        assert decision.decision == EFFECT_DENY
        assert decision.policy_id == "auth-shell"
        assert decision.risk == RISK_CRITICAL


__all__ = [
    "TestRuleMatching",
    "TestConditionMatching",
    "TestDefaultPolicies",
    "TestRiskLevels",
    "TestIntegrationScenarios",
    "TestAuthoritativeMode",
]
