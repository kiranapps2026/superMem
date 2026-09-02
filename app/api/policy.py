"""Sprint 7 — Policy management API.

Endpoints for managing policies and policy versions.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.middleware.tenancy import TenantContext, get_tenant_context
from app.middleware.rbac import require_min_role
from app.models import Policy, PolicyVersion
from app.services.policy.engine import PolicyEngine, PolicyDecision, AuthorizationRequest
from app.services.policy.evaluator import evaluate_rbac, build_auth_request
from app.services.policy.repository import PolicyRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policy", tags=["policy"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class RuleCreate(BaseModel):
    resource: str = Field(..., description="Resource pattern, e.g. 'memory', 'tool.fs.*'")
    action: str = Field(..., description="Action: read, search, write, update, execute, delete, export, share, *")
    effect: str = Field(
        ...,
        pattern="^(allow|deny|require_confirmation|allow_with_limits|allow_redacted)$",
        description="Effect: allow, deny, require_confirmation, allow_with_limits, allow_redacted",
    )
    conditions: dict | None = Field(None, description="Optional conditions dict")
    limits: dict | None = Field(None, description="Optional limits for allow_with_limits")
    risk: str = Field("low", pattern="^(low|medium|high|critical)$")


class PolicyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=5000)
    rules: list[RuleCreate] = Field(..., min_length=1)


class PolicyUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=5000)
    status: str | None = Field(None, pattern="^(active|inactive|draft)$")


class PolicyVersionOut(BaseModel):
    version: int
    rules: list[dict]
    status: str
    created_at: str

    class Config:
        from_attributes = True


class PolicyOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str | None
    status: str
    current_version: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PolicyDetail(PolicyOut):
    versions: list[PolicyVersionOut] = []


class AuthorizationTestRequest(BaseModel):
    resource_type: str
    resource_id: str | None = None
    action: str
    principal_id: str | None = None
    principal_type: str = "user"
    context: dict = Field(default_factory=dict)
    requested_limits: dict = Field(default_factory=dict)


class AuthorizationTestResponse(BaseModel):
    decision: str
    reason: str
    policy_id: str | None
    policy_version: int | None
    risk: str
    request_id: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/", response_model=list[PolicyOut])
async def list_policies(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """List all policies for the current tenant."""
    stmt = select(Policy).where(Policy.tenant_id == tc.tenant_id)
    if status_filter:
        stmt = stmt.where(Policy.status == status_filter)
    stmt = stmt.order_by(Policy.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=PolicyOut, status_code=status.HTTP_201_CREATED)
async def create_policy(
    data: PolicyCreate,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_min_role("admin")),
):
    """Create a new policy with initial version."""
    policy = Policy(
        tenant_id=tc.tenant_id,
        name=data.name,
        description=data.description,
        status="active",
        current_version=1,
        created_by=tc.user_id,
    )
    db.add(policy)
    await db.flush()

    version = PolicyVersion(
        policy_id=str(policy.id),
        version=1,
        rules=[r.model_dump() for r in data.rules],
        status="active",
        created_by=tc.user_id,
    )
    db.add(version)
    await db.commit()
    await db.refresh(policy)
    return policy


@router.get("/{policy_id}", response_model=PolicyDetail)
async def get_policy(
    policy_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Get a policy with all its versions."""
    result = await db.execute(
        select(Policy).where(
            Policy.id == policy_id,
            Policy.tenant_id == tc.tenant_id,
        )
    )
    policy = result.scalar_one_or_none()
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")

    versions_result = await db.execute(
        select(PolicyVersion).where(PolicyVersion.policy_id == policy_id)
    )
    versions = versions_result.scalars().all()

    return PolicyDetail(
        id=str(policy.id),
        tenant_id=str(policy.tenant_id),
        name=policy.name,
        description=policy.description,
        status=policy.status,
        current_version=policy.current_version,
        created_at=str(policy.created_at),
        updated_at=str(policy.updated_at),
        versions=[
            PolicyVersionOut(
                version=v.version,
                rules=v.rules or [],
                status=v.status,
                created_at=str(v.created_at),
            )
            for v in versions
        ],
    )


@router.patch("/{policy_id}", response_model=PolicyOut)
async def update_policy(
    policy_id: str,
    data: PolicyUpdate,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Update a policy's metadata."""
    result = await db.execute(
        select(Policy).where(
            Policy.id == policy_id,
            Policy.tenant_id == tc.tenant_id,
        )
    )
    policy = result.scalar_one_or_none()
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")

    if data.name is not None:
        policy.name = data.name
    if data.description is not None:
        policy.description = data.description
    if data.status is not None:
        policy.status = data.status

    await db.commit()
    await db.refresh(policy)
    return policy


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a policy."""
    result = await db.execute(
        select(Policy).where(
            Policy.id == policy_id,
            Policy.tenant_id == tc.tenant_id,
        )
    )
    policy = result.scalar_one_or_none()
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    policy.status = "inactive"
    await db.commit()


@router.post("/{policy_id}/versions", response_model=PolicyVersionOut, status_code=status.HTTP_201_CREATED)
async def create_policy_version(
    policy_id: str,
    data: PolicyCreate,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Create a new version of an existing policy."""
    result = await db.execute(
        select(Policy).where(
            Policy.id == policy_id,
            Policy.tenant_id == tc.tenant_id,
        )
    )
    policy = result.scalar_one_or_none()
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")

    new_version = policy.current_version + 1
    version = PolicyVersion(
        policy_id=policy_id,
        version=new_version,
        rules=[r.model_dump() for r in data.rules],
        status="active",
        created_by=tc.user_id,
    )
    db.add(version)
    policy.current_version = new_version
    await db.commit()
    await db.refresh(version)

    return PolicyVersionOut(
        version=version.version,
        rules=version.rules or [],
        status=version.status,
        created_at=str(version.created_at),
    )


@router.post("/test-authorization", response_model=AuthorizationTestResponse)
async def test_authorization(
    data: AuthorizationTestRequest,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Test authorization for a request against current tenant policies.

    Read-only — does not mutate anything. Useful for debugging and UI preview.
    """
    repo = PolicyRepository(db=db)
    policies = await repo.load_active_policies(tenant_id=tc.tenant_id)

    # Add default policies if no tenant-specific ones exist
    if not policies:
        engine = PolicyEngine()
        policies = engine.default_tenant_policies(tc.tenant_id)

    request = AuthorizationRequest(
        principal_id=data.principal_id or tc.user_id,
        principal_type=data.principal_type,
        resource_type=data.resource_type,
        resource_id=data.resource_id,
        action=data.action,
        tenant_id=tc.tenant_id,
        workspace_id=tc.workspace_id,
        context=data.context,
        requested_limits=data.requested_limits,
    )

    engine = PolicyEngine()
    decision = engine.evaluate(request, policies=policies)

    return AuthorizationTestResponse(
        decision=decision.decision,
        reason=decision.reason,
        policy_id=decision.policy_id,
        policy_version=decision.policy_version,
        risk=decision.risk,
        request_id=decision.request_id,
    )


__all__ = ["router"]
