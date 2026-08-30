from dataclasses import dataclass
from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from app.models import Tenant, User, Workspace, WorkspaceMember
from app.db import get_db
from app.core.config import settings


@dataclass
class TenantContext:
    tenant_id: str
    tenant_name: str | None = None
    tenant_plan: str | None = None
    workspace_id: str | None = None
    workspace_name: str | None = None
    role: str = "viewer"
    user_id: str | None = None


def _selectinload_workspace():
    from sqlalchemy.orm import selectinload
    return selectinload(WorkspaceMember.workspace)


async def get_tenant_context(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TenantContext:
    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth_header[7:].strip()
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user_result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    workspace_header = request.headers.get("X-Workspace-Id")

    if workspace_header:
        membership_result = await db.execute(
            select(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_header,
                WorkspaceMember.user_id == user.id,
            )
            .options(_selectinload_workspace())
        )
        membership = membership_result.scalar_one_or_none()
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this workspace",
            )
        workspace = membership.workspace
    else:
        membership_result = await db.execute(
            select(WorkspaceMember)
            .where(WorkspaceMember.user_id == user.id)
            .options(_selectinload_workspace())
        )
        rows = membership_result.all()
        membership = rows[0][0] if rows else None
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No workspace membership found",
            )
        workspace = membership.workspace

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == workspace.tenant_id)
    )
    tenant = tenant_result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    return TenantContext(
        tenant_id=tenant.id,
        tenant_name=tenant.name,
        tenant_plan=tenant.plan,
        workspace_id=workspace.id,
        workspace_name=workspace.name,
        role=membership.role,
        user_id=user.id,
    )


async def _get_user(
    user_id: str,
    db: AsyncSession,
) -> User:
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user
