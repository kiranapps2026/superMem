"""Sprint 7 — RBAC enforcement dependency.

Provides a role-based authorization dependency for FastAPI endpoints.
Uses the role hierarchy from workspace.py.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.middleware.tenancy import TenantContext, get_tenant_context


class Role(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


# Hierarchical: higher number = more permissions
ROLE_HIERARCHY: dict[str, int] = {
    Role.OWNER: 1000,
    Role.ADMIN: 500,
    Role.MEMBER: 100,
    Role.VIEWER: 50,
}


# Permission definitions — each endpoint declares the minimum role needed
_PERMISSIONS: dict[str, dict[Role, set[str]]] = {
    Role.OWNER: {
        "workspace.read", "workspace.manage",
        "members.read", "members.manage",
        "project.read", "project.write", "project.delete",
        "memory.read", "memory.write", "memory.delete",
        "chat.use",
        "ingest.create", "ingest.read",
        "storage.read", "storage.write",
        "api_key.manage",
    },
    Role.ADMIN: {
        "workspace.read",
        "members.read", "members.manage",
        "project.read", "project.write",
        "memory.read", "memory.write",
        "chat.use",
        "ingest.create", "ingest.read",
        "storage.read", "storage.write",
        "api_key.manage",
    },
    Role.MEMBER: {
        "workspace.read",
        "project.read",
        "memory.read", "memory.write",
        "chat.use",
        "ingest.create", "ingest.read",
        "storage.read",
    },
    Role.VIEWER: {
        "workspace.read",
        "project.read",
        "memory.read",
        "chat.use",
        "ingest.read",
    },
}


def _get_permissions(role: str) -> set[str]:
    """Return all permissions granted to a role and below."""
    role_enum = Role(role) if role in [r.value for r in Role] else Role.VIEWER
    perms: set[str] = set()
    for r in Role:
        if ROLE_HIERARCHY[r.value] <= ROLE_HIERARCHY[role_enum.value]:
            perms.update(_PERMISSIONS.get(r, set()))
    return perms


def require_permission(*permissions: str):
    """Dependency factory: require the user's role to grant ALL specified permissions.

    Usage:
        @router.delete("/{id}")
        async def delete_thing(
            tc: Annotated[TenantContext, Depends(get_tenant_context)],
            _: None = Depends(require_permission("memory.delete")),
        ):
            ...
    """
    def _check(tc: Annotated[TenantContext, Depends(get_tenant_context)]) -> None:
        user_perms = _get_permissions(tc.role)
        missing = [p for p in permissions if p not in user_perms]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing)}",
            )
    return _check


def require_min_role(min_role: str):
    """Dependency factory: require at least the specified role level.

    Routes through the Policy Engine's role-check path, so that all
    authorization decisions flow through a single boundary:

        require_min_role("admin")
            → AuthorizationRequest (authorize.role:check)
            → PolicyEngine.check_role_minimum()
            → RBAC role policies
            → PolicyDecision

    Usage:
        @router.delete("/{id}")
        async def delete_thing(
            tc: Annotated[TenantContext, Depends(get_tenant_context)],
            _: None = Depends(require_min_role("admin")),
        ):
            ...
    """
    def _check(tc: Annotated[TenantContext, Depends(get_tenant_context)]) -> None:
        from app.services.policy.engine import PolicyEngine, EFFECT_ALLOW
        engine = PolicyEngine()
        decision = engine.check_role_minimum(
            principal_id=tc.user_id or "unknown",
            role=tc.role,
            min_role=min_role,
            tenant_id=tc.tenant_id,
            workspace_id=tc.workspace_id,
        )
        if decision.decision != EFFECT_ALLOW:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{min_role.capitalize()} role required",
            )
    return _check
