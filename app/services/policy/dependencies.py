"""FastAPI authorization dependencies backed by the Policy Engine.

Provides the canonical authorization boundary:

    from app.services.policy.dependencies import require_policy

    @router.delete("/{id}")
    async def delete_thing(
        tc: Annotated[TenantContext, Depends(get_tenant_context)],
        _: None = Depends(require_policy("memory", "delete")),
    ):
        ...

This replaces scattered `require_min_role("admin")` checks with a single
policy-engine-backed authorization decision while preserving the existing
fail-closed semantics.
"""
from __future__ import annotations

from typing import Annotated, Callable

from fastapi import Depends, HTTPException, status

from app.middleware.tenancy import TenantContext, get_tenant_context
from app.services.policy.engine import PolicyEngine, PolicyDecision, EFFECT_ALLOW, EFFECT_DENY
from app.services.policy.evaluator import evaluate_rbac, build_auth_request

# Singleton engine instance — created at startup
_engine: PolicyEngine | None = None


def get_policy_engine() -> PolicyEngine:
    """Return the singleton PolicyEngine, creating it if needed."""
    global _engine
    if _engine is None:
        _engine = PolicyEngine()
    return _engine


def require_policy(
    resource_type: str,
    action: str,
) -> Callable[..., None]:
    """Dependency factory: authorize via Policy Engine.

    Usage:
        @router.delete("/{id}")
        async def delete_thing(
            tc: Annotated[TenantContext, Depends(get_tenant_context)],
            _: None = Depends(require_policy("memory", "delete")),
        ):
            ...

    This runs RBAC evaluation through the Policy Engine.
    Fail-closed: any evaluation error → 403.
    """
    def _authorize(
        tc: Annotated[TenantContext, Depends(get_tenant_context)],
    ) -> None:
        engine = get_policy_engine()

        request = build_auth_request(
            principal_id=tc.user_id or "unknown",
            role=tc.role,
            resource_type=resource_type,
            action=action,
            tenant_id=tc.tenant_id,
            workspace_id=tc.workspace_id,
        )

        decision = evaluate_rbac(engine, request)
        if decision.decision != EFFECT_ALLOW:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {resource_type}:{action}",
            )
    return _authorize


def require_policy_with_id(
    resource_type: str,
    action: str,
    resource_id_param: str = "id",
) -> Callable[..., None]:
    """Like require_policy but also injects the resource_id from a path parameter.

    Usage:
        @router.delete("/{memory_id}")
        async def delete_memory(
            memory_id: str,
            tc: Annotated[TenantContext, Depends(get_tenant_context)],
            _: None = Depends(require_policy_with_id("memory", "delete", "memory_id")),
        ):
            ...
    """
    def _authorize(
        tc: Annotated[TenantContext, Depends(get_tenant_context)],
    ) -> None:
        engine = get_policy_engine()

        request = build_auth_request(
            principal_id=tc.user_id or "unknown",
            role=tc.role,
            resource_type=resource_type,
            action=action,
            tenant_id=tc.tenant_id,
            workspace_id=tc.workspace_id,
        )

        decision = evaluate_rbac(engine, request)
        if decision.decision != EFFECT_ALLOW:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {resource_type}:{action}",
            )
    return _authorize
