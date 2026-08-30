"""Authentication endpoints."""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import settings
from app.db import get_db
from app.middleware.tenancy import TenantContext, get_tenant_context
from app.models import RefreshToken, Tenant, User, Workspace, WorkspaceMember
from app.schemas import (
    ChangePasswordRequest,
    RefreshRequest,
    TokenResponse,
    UserLogin,
    UserOut,
    UserRegister,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _now() -> datetime:
    return datetime.utcnow()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(User).where(User.email == data.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    slug = data.workspace_name.lower().replace(" ", "-")[:50]
    tenant = Tenant(name=data.workspace_name, slug=slug)
    db.add(tenant)
    await db.flush()

    workspace = Workspace(
        tenant_id=tenant.id,
        name=data.workspace_name,
        slug=slug,
    )
    db.add(workspace)
    await db.flush()

    user = User(
        email=data.email,
        name=data.name,
        hashed_password=security.hash_password(data.password),
    )
    db.add(user)
    await db.flush()

    membership = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user.id,
        role="owner",
    )
    db.add(membership)
    await db.commit()
    await db.refresh(user)

    now = _now()
    access_token = security.make_access_token(
        data={"sub": user.id, "email": user.email}
    )
    refresh_token_str = security.make_access_token(
        data={
            "sub": user.id,
            "type": "refresh",
            "jti": f"{user.id}-{now.timestamp()}",
        },
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )
    rt = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=now + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(rt)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(
            User.email == data.email,
            User.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()
    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not security.verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    now = _now()
    access_token = security.make_access_token(
        data={"sub": user.id, "email": user.email}
    )
    refresh_token_str = security.make_access_token(
        data={
            "sub": user.id,
            "type": "refresh",
            "jti": f"{user.id}-{now.timestamp()}",
        },
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )
    rt = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=now + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(rt)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    payload = security.decode_access_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == data.refresh_token,
            RefreshToken.revoked == False,  # noqa: E712
            RefreshToken.expires_at > datetime.utcnow(),
        )
    )
    rt = result.scalar_one_or_none()
    if rt is None:
        raise HTTPException(
            status_code=401, detail="Refresh token not found or expired"
        )

    rt.revoked = True
    user_id = rt.user_id

    user_result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    now = _now()
    access_token = security.make_access_token(
        data={"sub": user.id, "email": user.email}
    )
    new_refresh = security.make_access_token(
        data={
            "sub": user.id,
            "type": "refresh",
            "jti": f"{user.id}-{now.timestamp()}",
        },
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )
    new_rt = RefreshToken(
        user_id=user.id,
        token=new_refresh,
        expires_at=now + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(new_rt)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout", response_model=None)
async def logout(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    tc: TenantContext = Depends(get_tenant_context),
):
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == data.refresh_token,
            RefreshToken.user_id == tc.user_id,
        )
    )
    rt = result.scalar_one_or_none()
    if rt:
        rt.revoked = True
        await db.commit()
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserOut)
async def get_me(
    tc: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.id == tc.user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/change-password")
async def change_password(
    data: "ChangePasswordRequest",
    tc: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    from app.core import security

    result = await db.execute(
        select(User).where(User.id == tc.user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user or not user.hashed_password:
        raise HTTPException(status_code=400, detail="No password set")

    if not security.verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    user.hashed_password = security.hash_password(data.new_password)
    await db.commit()
    return {"detail": "Password updated"}
