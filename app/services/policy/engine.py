"""Policy Engine — core authorization subsystem.

Evaluates structured policy rules against authorization requests.
Fails closed: unknown or missing policy = DENY.
Explicit deny always wins over allow.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EFFECT_ALLOW = "allow"
EFFECT_DENY = "deny"
EFFECT_CONFIRM = "require_confirmation"
EFFECT_LIMITED = "allow_with_limits"
EFFECT_REDACTED = "allow_redacted"

VALID_EFFECTS = {EFFECT_ALLOW, EFFECT_DENY, EFFECT_CONFIRM, EFFECT_LIMITED, EFFECT_REDACTED}

RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"
RISK_CRITICAL = "critical"

VALID_RISKS = {RISK_LOW, RISK_MEDIUM, RISK_HIGH, RISK_CRITICAL}

# Default deny — never change without explicit override
DEFAULT_DECISION = EFFECT_DENY

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class AuthorizationRequest:
    """Canonical authorization request."""
    principal_id: str
    principal_type: Literal["user", "agent", "service", "admin"] = "user"
    resource_type: Literal[
        "memory", "tool", "model", "file", "database",
        "connector", "source", "project", "workspace", "session",
        "provenance", "feedback", "api_key",
    ] = "memory"
    resource_id: str | None = None
    action: Literal[
        "read", "search", "write", "update", "execute",
        "delete", "export", "share",
    ] = "read"
    tenant_id: str | None = None
    workspace_id: str | None = None
    project_id: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    requested_limits: dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid4()))
    """Unique request ID for correlation."""


@dataclass
class PolicyDecision:
    """Result of policy evaluation."""
    decision: str = DEFAULT_DECISION
    reason: str = "no matching policy"
    policy_id: str | None = None
    policy_version: int | None = None
    rules_matched: list[dict[str, Any]] = field(default_factory=list)
    limits: dict[str, Any] | None = None
    redactions: list[str] | None = None
    risk: str = RISK_MEDIUM
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    request_id: str = field(default_factory=lambda: str(uuid4()))


# ---------------------------------------------------------------------------
# Rule matching helpers
# ---------------------------------------------------------------------------


def _match_resource(rule_resource: str, req_resource_type: str, req_resource_id: str | None) -> bool:
    """Match a rule resource pattern against the request.

    Patterns:
      "*"            matches any resource
      "memory"       matches any memory
      "tool.*"       matches any tool
      "tool.fs.*"    matches any filesystem tool
      "memory:abc"   matches specific resource_id
    """
    if rule_resource == "*":
        return True
    if "." not in rule_resource and ":" not in rule_resource:
        # Simple type match
        return rule_resource == req_resource_type
    if rule_resource.startswith(f"{req_resource_type}:"):
        # Specific resource_id match
        rule_id = rule_resource.split(":", 1)[1]
        if rule_id == "*":
            return True
        return req_resource_id is not None and rule_id == req_resource_id
    if rule_resource == req_resource_type:
        # Exact match (covers dotted types like "crm.customer" == "crm.customer")
        return True
    if rule_resource.startswith(req_resource_type + "."):
        # Hierarchical: "memory" matches "memory.foo.bar"
        return True
    # Wildcard rules: "tool.*" matches "tool.utility", "tool.fs", etc.
    if rule_resource.endswith(".*") and req_resource_type.startswith(rule_resource[:-1]):
        return True
    # Colon-separated: "memory:project_A" matches request with resource_type="memory" and resource_id="project_A"
    if ":" in rule_resource:
        rule_type, rule_id = rule_resource.split(":", 1)
        if rule_type == req_resource_type:
            if rule_id == "*" or req_resource_id == rule_id:
                return True
    return False


def _match_action(rule_action: str, req_action: str) -> bool:
    """Match rule action against request action.

    "read" matches only "read"
    "write" matches "write", "update", "delete" (write-family)
    "execute" matches only "execute"
    "*" matches everything
    """
    if rule_action == "*":
        return True
    if rule_action == req_action:
        return True
    # Write-family grouping
    if rule_action == "write" and req_action in ("write", "update", "delete"):
        return True
    # Read-family grouping
    if rule_action == "read" and req_action in ("read", "search"):
        return True
    return False


def _match_conditions(conditions: dict | None, request: AuthorizationRequest) -> bool:
    """Evaluate rule conditions against request context and attributes.

    Conditions are AND-ed. Supported operators:
      eq: exact match
      in: value in list
      has: key exists in context
      role: principal has one of listed roles

    First checks request attributes (tenant_id, workspace_id, project_id),
    then falls back to context dict.
    """
    if not conditions:
        return True
    # Map request attributes that conditions may reference
    _attr_map = {
        "tenant_id": request.tenant_id,
        "workspace_id": request.workspace_id,
        "project_id": request.project_id,
        "principal_id": request.principal_id,
        "principal_type": request.principal_type,
        "resource_type": request.resource_type,
        "resource_id": request.resource_id,
    }
    for key, spec in conditions.items():
        if isinstance(spec, dict):
            op = spec.get("op", "eq")
            val = spec.get("value")
            # Try request attribute first, then context
            req_val = _attr_map.get(key, request.context.get(key))
            if op == "eq":
                if req_val != val:
                    return False
            elif op == "in":
                if req_val not in val:
                    return False
            elif op == "has":
                if req_val is None:
                    return False
            elif op == "role":
                if request.context.get("role") not in val:
                    return False
        else:
            # Simple equality
            req_val = _attr_map.get(key, request.context.get(key))
            if req_val != spec:
                return False
    return True


# ---------------------------------------------------------------------------
# Policy Engine
# ---------------------------------------------------------------------------

ROLE_HIERARCHY: dict[str, int] = {
    "owner": 1000,
    "admin": 500,
    "member": 100,
    "viewer": 50,
}


def _generate_role_policies(min_role: str) -> list[dict[str, Any]]:
    """Generate policies that enforce a minimum role threshold.

    Creates an allow/deny pair for every role level against a synthetic
    ``authorize.role:check`` resource.  Roles at or above the threshold
    get allow; roles below get deny.  DENY rules appear first so they
    short-circuit evaluation.
    """
    required_level = ROLE_HIERARCHY.get(min_role, 0)
    rules = []
    for role, level in ROLE_HIERARCHY.items():
        effect = EFFECT_ALLOW if level >= required_level else EFFECT_DENY
        rules.append({
            "resource": "authorize.role",
            "action": "check",
            "effect": effect,
            "risk": RISK_LOW if effect == EFFECT_ALLOW else RISK_MEDIUM,
            "conditions": {"role": {"op": "in", "value": [role]}},
        })
    return [
        {
            "policy_id": "rbac-role-check",
            "name": f"Role minimum: {min_role}",
            "policy_version": 1,
            "rules": rules,
        },
    ]


class PolicyEngine:
    """Central authorization engine.

    Independent of agent logic, independently testable, deterministic,
    fail-closed for privileged operations.
    """

    def __init__(self, repository: "PolicyRepository | None" = None):
        self._repo = repository
        # Built-in system-level defaults (always active, lowest priority)
        self._system_rules: list[dict] = []

    # ------------------------------------------------------------------
    # Rule evaluation
    # ------------------------------------------------------------------

    def evaluate(
        self,
        request: AuthorizationRequest,
        policies: list[dict] | None = None,
    ) -> PolicyDecision:
        """Evaluate an authorization request against loaded policies.

        Rules are evaluated in order. First explicit DENY wins.
        If no rule matches, returns DEFAULT_DECISION (deny).

        Args:
            request: The authorization request.
            policies: Pre-loaded policy list (if None, uses self._system_rules).

        Returns:
            PolicyDecision with decision, reason, and matched rules.
        """
        rules = policies if policies is not None else self._system_rules
        if not rules:
            return PolicyDecision(
                decision=DEFAULT_DECISION,
                reason="no policies configured",
                risk=RISK_HIGH,
            )

        decision = EFFECT_ALLOW  # baseline — only reached if rules allow
        reason = "default allow"
        matched: list[dict[str, Any]] = []
        limits: dict[str, Any] = {}
        risk = RISK_LOW
        policy_id = None
        policy_version = None

        for policy in rules:
            pid = policy.get("policy_id", "")
            pver = policy.get("policy_version")
            for rule in policy.get("rules", []):
                if not self._rule_matches(rule, request):
                    continue

                effect = rule.get("effect", EFFECT_DENY)
                if effect not in VALID_EFFECTS:
                    logger.warning("unknown effect %r in policy %s", effect, pid)
                    continue

                matched.append({
                    "policy_id": pid,
                    "policy_version": pver,
                    "rule": rule,
                })
                policy_id = pid
                policy_version = pver

                if effect == EFFECT_DENY:
                    return PolicyDecision(
                        decision=EFFECT_DENY,
                        reason=f"denied by rule in policy {pid}",
                        policy_id=pid,
                        policy_version=pver,
                        rules_matched=matched,
                        risk=rule.get("risk", RISK_HIGH),
                        request_id=request.request_id,
                    )

                if effect == EFFECT_CONFIRM:
                    return PolicyDecision(
                        decision=EFFECT_CONFIRM,
                        reason=f"confirmation required by policy {pid}",
                        policy_id=pid,
                        policy_version=pver,
                        rules_matched=matched,
                        risk=rule.get("risk", RISK_MEDIUM),
                        request_id=request.request_id,
                    )

                if effect == EFFECT_REDACTED:
                    return PolicyDecision(
                        decision=EFFECT_REDACTED,
                        reason=f"redacted access per policy {pid}",
                        policy_id=pid,
                        policy_version=pver,
                        rules_matched=matched,
                        limits=rule.get("limits"),
                        redactions=rule.get("redactions"),
                        risk=rule.get("risk", RISK_MEDIUM),
                        request_id=request.request_id,
                    )

                # allow or limited — keep going to see if a deny follows
                if effect == EFFECT_LIMITED:
                    limits.update(rule.get("limits", {}))

                decision = effect
                reason = f"allowed by policy {pid}"
                risk = rule.get("risk", RISK_LOW)

        if not matched:
            return PolicyDecision(
                decision=DEFAULT_DECISION,
                reason="no matching policy rule found",
                risk=RISK_MEDIUM,
                request_id=request.request_id,
            )

        if limits:
            decision = EFFECT_LIMITED

        return PolicyDecision(
            decision=decision,
            reason=reason,
            policy_id=policy_id,
            policy_version=policy_version,
            rules_matched=matched,
            limits=limits or None,
            risk=risk,
            request_id=request.request_id,
        )

    def _rule_matches(self, rule: dict, request: AuthorizationRequest) -> bool:
        """Check if a single rule matches the request."""
        # Resource match
        rule_resource = rule.get("resource", "*")
        if not _match_resource(rule_resource, request.resource_type, request.resource_id):
            return False

        # Action match
        rule_action = rule.get("action", "*")
        if not _match_action(rule_action, request.action):
            return False

        # Conditions
        conditions = rule.get("conditions")
        if not _match_conditions(conditions, request):
            return False

        return True

    # ------------------------------------------------------------------
    # Role-level authorization (for require_min_role)
    # ------------------------------------------------------------------

    def check_role_minimum(
        self,
        principal_id: str,
        role: str,
        min_role: str,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
        request_id: str | None = None,
    ) -> PolicyDecision:
        """Check whether a principal's role meets a minimum threshold.

        This is the canonical path for role-hierarchy checks.  It generates
        RBAC policies that map every role level to explicit allow/deny rules
        for a synthetic ``authorize.role`` resource, then evaluates through
        the standard PolicyEngine pipeline.

        Args:
            principal_id: Authenticated user identifier.
            role: The user's current role (owner/admin/member/viewer).
            min_role: Minimum role required (owner/admin/member/viewer).
            tenant_id: Tenant scope.
            workspace_id: Workspace scope.
            request_id: Optional correlation ID.

        Returns:
            PolicyDecision — ALLOW if role meets minimum, DENY otherwise.
        """
        policies = _generate_role_policies(min_role)
        request = AuthorizationRequest(
            principal_id=principal_id,
            principal_type="user",
            resource_type="authorize.role",
            action="check",
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            context={"role": role, "min_role": min_role},
            request_id=request_id or str(uuid4()),
        )
        return self.evaluate(request, policies=policies)

    # ------------------------------------------------------------------
    # Default policy generation
    # ------------------------------------------------------------------

    def default_tenant_policies(self, tenant_id: str) -> list[dict]:
        """Return the default policy set for a new tenant.

        These are JSON-serializable policy dicts, each with:
          - policy_id
          - name
          - rules[]
        """
        return [
            {
                "policy_id": "default-memory-read",
                "name": "Tenant members can read their workspace memories",
                "policy_version": 1,
                "rules": [
                    {
                        "resource": "memory",
                        "action": "read",
                        "effect": EFFECT_ALLOW,
                        "risk": RISK_LOW,
                    },
                    {
                        "resource": "memory",
                        "action": "search",
                        "effect": EFFECT_ALLOW,
                        "risk": RISK_LOW,
                    },
                    {
                        "resource": "memory",
                        "action": "write",
                        "effect": EFFECT_ALLOW,
                        "risk": RISK_LOW,
                    },
                    {
                        "resource": "memory",
                        "action": "update",
                        "effect": EFFECT_ALLOW,
                        "risk": RISK_LOW,
                    },
                    {
                        "resource": "memory",
                        "action": "delete",
                        "effect": EFFECT_ALLOW,
                        "risk": RISK_MEDIUM,
                    },
                ],
            },
            {
                "policy_id": "default-project-access",
                "name": "Tenant members can access workspace projects",
                "policy_version": 1,
                "rules": [
                    {
                        "resource": "project",
                        "action": "read",
                        "effect": EFFECT_ALLOW,
                        "risk": RISK_LOW,
                    },
                    {
                        "resource": "project",
                        "action": "write",
                        "effect": EFFECT_ALLOW,
                        "risk": RISK_LOW,
                    },
                ],
            },
            {
                "policy_id": "default-chat",
                "name": "Tenant members can use chat",
                "policy_version": 1,
                "rules": [
                    {
                        "resource": "model",
                        "action": "read",
                        "effect": EFFECT_ALLOW,
                        "risk": RISK_LOW,
                    },
                    {
                        "resource": "source",
                        "action": "read",
                        "effect": EFFECT_ALLOW,
                        "risk": RISK_LOW,
                    },
                    {
                        "resource": "provenance",
                        "action": "read",
                        "effect": EFFECT_ALLOW,
                        "risk": RISK_LOW,
                    },
                    {
                        "resource": "feedback",
                        "action": "write",
                        "effect": EFFECT_ALLOW,
                        "risk": RISK_LOW,
                    },
                ],
            },
            {
                "policy_id": "default-ingest",
                "name": "Tenant members can ingest content",
                "policy_version": 1,
                "rules": [
                    {
                        "resource": "connector",
                        "action": "execute",
                        "effect": EFFECT_ALLOW,
                        "risk": RISK_MEDIUM,
                    },
                    {
                        "resource": "source",
                        "action": "write",
                        "effect": EFFECT_ALLOW,
                        "risk": RISK_LOW,
                    },
                    {
                        "resource": "source",
                        "action": "delete",
                        "effect": EFFECT_ALLOW,
                        "risk": RISK_MEDIUM,
                    },
                ],
            },
            {
                "policy_id": "default-tool-read",
                "name": "Tenant members can read tools; execution requires confirmation",
                "policy_version": 1,
                "rules": [
                    {
                        "resource": "tool",
                        "action": "read",
                        "effect": EFFECT_ALLOW,
                        "risk": RISK_LOW,
                    },
                    {
                        "resource": "tool.*",
                        "action": "execute",
                        "effect": EFFECT_CONFIRM,
                        "risk": RISK_MEDIUM,
                    },
                ],
            },
            {
                "policy_id": "default-api-key",
                "name": "Tenant members can manage API keys",
                "policy_version": 1,
                "rules": [
                    {
                        "resource": "api_key",
                        "action": "write",
                        "effect": EFFECT_ALLOW,
                        "risk": RISK_MEDIUM,
                    },
                    {
                        "resource": "api_key",
                        "action": "delete",
                        "effect": EFFECT_ALLOW,
                        "risk": RISK_MEDIUM,
                    },
                ],
            },
            {
                "policy_id": "default-deny-admin",
                "name": "Non-admins cannot access admin functions",
                "policy_version": 1,
                "rules": [
                    {
                        "resource": "workspace",
                        "action": "write",
                        "effect": EFFECT_DENY,
                        "conditions": {"role": {"op": "not_in", "value": ["owner", "admin"]}},
                        "risk": RISK_CRITICAL,
                    },
                ],
            },
            {
                "policy_id": "default-deny-export",
                "name": "Bulk export requires confirmation",
                "policy_version": 1,
                "rules": [
                    {
                        "resource": "*",
                        "action": "export",
                        "effect": EFFECT_CONFIRM,
                        "risk": RISK_HIGH,
                    },
                ],
            },
            {
                "policy_id": "default-deny-credential",
                "name": "Credential access is restricted",
                "policy_version": 1,
                "rules": [
                    {
                        "resource": "credential",
                        "action": "*",
                        "effect": EFFECT_DENY,
                        "risk": RISK_CRITICAL,
                    },
                    {
                        "resource": "secret",
                        "action": "*",
                        "effect": EFFECT_DENY,
                        "risk": RISK_CRITICAL,
                    },
                ],
            },
            {
                "policy_id": "default-deny-export",
                "name": "Bulk export requires confirmation",
                "policy_version": 1,
                "rules": [
                    {
                        "resource": "*",
                        "action": "export",
                        "effect": EFFECT_CONFIRM,
                        "risk": RISK_HIGH,
                    },
                ],
            },
        ]


__all__ = [
    "AuthorizationRequest",
    "PolicyDecision",
    "PolicyEngine",
    "EFFECT_ALLOW",
    "EFFECT_DENY",
    "EFFECT_CONFIRM",
    "EFFECT_LIMITED",
    "EFFECT_REDACTED",
    "VALID_EFFECTS",
    "RISK_LOW",
    "RISK_MEDIUM",
    "RISK_HIGH",
    "RISK_CRITICAL",
    "DEFAULT_DECISION",
]
