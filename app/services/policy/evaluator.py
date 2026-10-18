"""RBAC policy evaluator — bridges role hierarchy into PolicyEngine.

Generates RBAC policy rules from the canonical permission matrix,
then evaluates them through the standard PolicyEngine pipeline.

This ensures RBAC is ONE policy mechanism inside the engine, not
a separate authorization path.
"""
from __future__ import annotations

import logging
from typing import Any

from app.services.policy.engine import (
    AuthorizationRequest, PolicyDecision, PolicyEngine, EFFECT_ALLOW, EFFECT_DENY,
    RISK_LOW, RISK_MEDIUM, RISK_HIGH,
)

logger = logging.getLogger(__name__)

# Mirror of rbac.py permission matrix — single source of truth
# Maps resource:action → minimum role level
_RESOURCE_ACTIONS: dict[str, dict[str, str]] = {
    # workspace
    "workspace:read": "viewer",
    "workspace:write": "owner",
    "workspace:delete": "owner",
    # members
    "members:read": "member",
    "members:write": "admin",
    "members:delete": "owner",
    # project
    "project:read": "viewer",
    "project:write": "member",
    "project:delete": "owner",
    # memory
    "memory:read": "viewer",
    "memory:write": "member",   # covers write + update (same permission tier)
    "memory:search": "viewer",
    "memory:delete": "admin",
    # session
    "session:read": "member",
    "session:write": "member",
    "session:delete": "member",
    # chat
    "chat:use": "viewer",
    # ingest
    "ingest:read": "viewer",
    "ingest:write": "member",
    # storage
    "storage:read": "viewer",
    "storage:write": "member",
    "storage:delete": "admin",
    # provenance
    "provenance:read": "member",
    # feedback
    "feedback:write": "member",
    # api_key
    "api_key:read": "member",
    "api_key:write": "admin",
    "api_key:delete": "admin",
}

ROLE_HIERARCHY: dict[str, int] = {
    "owner": 1000,
    "admin": 500,
    "member": 100,
    "viewer": 50,
}


def _role_level(role: str) -> int:
    return ROLE_HIERARCHY.get(role, 0)


def generate_rbac_policies() -> list[dict[str, Any]]:
    """Generate policy rules from the RBAC permission matrix.

    Returns a list of policy dicts ready for PolicyEngine.evaluate().
    One policy per resource type, each containing allow/deny rules.
    Rules are generated for EVERY role level so that role hierarchy is
    correctly enforced by the engine.
    """
    allow_rules = []

    # Sorted ascending by role level so more permissive roles come last
    # (matching engine's "last match wins" for allows)
    sorted_roles = sorted(ROLE_HIERARCHY.items(), key=lambda x: x[1])

    for resource_action, min_role in _RESOURCE_ACTIONS.items():
        resource, action = resource_action.split(":", 1)
        required_level = _role_level(min_role)

        # All roles at or ABOVE the minimum level get a matching allow rule.
        # Conditions in each rule restrict to the specific role.
        for role, level in sorted_roles:
            if level >= required_level:
                allow_rules.append({
                    "resource": resource,
                    "action": action,
                    "effect": "allow",
                    "risk": _risk_for(resource, action),
                    "conditions": {"role": {"op": "in", "value": [role]}},
                })

    policies = [
        {
            "policy_id": "rbac-permissions",
            "name": "Role-Based Access Control",
            "policy_version": 1,
            "rules": allow_rules,
        },
    ]
    return policies


def _risk_for(resource: str, action: str) -> str:
    """Determine risk level for a resource:action combination."""
    if action == "delete":
        return "medium"
    if action == "write" and resource in ("api_key", "storage", "ingest"):
        return "medium"
    if resource == "api_key":
        return "high"
    return "low"


def evaluate_rbac(
    engine: PolicyEngine,
    request: AuthorizationRequest,
) -> PolicyDecision:
    """Evaluate an authorization request against RBAC policies.

    Loads the RBAC policy rules and evaluates through the engine.
    Uses exact action matching — each action in the RBAC permission matrix
    is a separate permission. No family grouping.
    Returns a PolicyDecision — caller checks .require_allowed().
    """
    policies = generate_rbac_policies()

    # Exact action matching: each RBAC action is a separate permission
    exact_policies = []
    for policy in policies:
        exact_rules = [
            rule for rule in policy.get("rules", [])
            if rule.get("action", "*") == "*" or rule.get("action") == request.action
        ]
        if exact_rules:
            exact_policies.append({**policy, "rules": exact_rules})

    return engine.evaluate(request, policies=exact_policies if exact_policies else policies)


def build_auth_request(
    principal_id: str,
    role: str,
    resource_type: str,
    action: str,
    resource_id: str | None = None,
    tenant_id: str | None = None,
    workspace_id: str | None = None,
    project_id: str | None = None,
    context: dict[str, Any] | None = None,
) -> AuthorizationRequest:
    """Build a canonical AuthorizationRequest from auth context.

    This is the single place where TenantContext → AuthorizationRequest
    translation happens.
    """
    return AuthorizationRequest(
        principal_id=principal_id,
        principal_type="user",
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        project_id=project_id,
        context={"role": role, **(context or {})},
    )
