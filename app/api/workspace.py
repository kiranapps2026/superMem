from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from app.db import get_db
from app.middleware.tenancy import TenantContext, get_tenant_context
from app.middleware.auth import require_auth
from app.models import User, Workspace, WorkspaceMember, Invitation
from app.schemas import (
    WorkspaceOut, WorkspaceMemberInvite, WorkspaceMemberOut,
    WorkspaceMemberUpdate, InvitationOut, InvitationUpdate,
)

router = APIRouter(prefix="/workspace", tags=["workspace"])

ROLE_HIERARCHY = {"owner": 1000, "admin": 500, "member": 100, "viewer": 50}


def _require_min_role(tc: TenantContext, min_role: str):
    if ROLE_HIERARCHY.get(tc.role, 0) < ROLE_HIERARCHY.get(min_role, 0):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{min_role.capitalize()} role required",
        )


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Workspace CRUD ──────────────────────────────────────────────────────────


@router.get("/", response_model=WorkspaceOut)
async def get_workspace(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == tc.workspace_id,
            Workspace.deleted_at.is_(None),
        )
    )
    workspace = result.scalar_one_or_none()
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.patch("/", response_model=WorkspaceOut)
async def update_workspace(
    data: dict,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    _require_min_role(tc, "admin")

    result = await db.execute(
        select(Workspace).where(
            Workspace.id == tc.workspace_id,
            Workspace.deleted_at.is_(None),
        )
    )
    workspace = result.scalar_one_or_none()
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    allowed = {"name", "description", "slug", "perm_join", "perm_member_manage"}
    for field, value in data.items():
        if field in allowed and hasattr(workspace, field):
            setattr(workspace, field, value)

    workspace.updated_at = _now()
    await db.commit()
    await db.refresh(workspace)
    return workspace


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    _require_min_role(tc, "owner")

    result = await db.execute(
        select(Workspace).where(
            Workspace.id == tc.workspace_id,
            Workspace.deleted_at.is_(None),
        )
    )
    workspace = result.scalar_one_or_none()
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    workspace.deleted_at = _now()
    await db.commit()


# ── Members ────────────────────────────────────────────────────────────────


@router.get("/members", response_model=list[WorkspaceMemberOut])
async def list_members(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WorkspaceMember).where(WorkspaceMember.workspace_id == tc.workspace_id)
    )
    memberships = result.scalars().all()

    user_ids = [m.user_id for m in memberships]
    users_result = await db.execute(
        select(User).where(User.id.in_(user_ids))
    )
    users_by_id = {u.id: u for u in users_result.scalars().all()}

    out = []
    for m in memberships:
        u = users_by_id.get(m.user_id)
        out.append(WorkspaceMemberOut(
            id=m.id,
            workspace_id=m.workspace_id,
            user_id=m.user_id,
            user_name=u.name if u else "",
            user_email=u.email if u else "",
            role=m.role,
            joined_at=m.joined_at,
            invited_at=m.invited_at,
            expires=m.expires_at,
        ))
    return out


@router.post("/members", response_model=WorkspaceMemberOut)
async def invite_member(
    data: WorkspaceMemberInvite,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    _require_min_role(tc, "admin")

    target_result = await db.execute(
        select(User).where(User.email == data.email)
    )
    target_user = target_result.scalar_one_or_none()
    if target_user is None:
        target_user = User(
            email=data.email,
            name=data.email.split("@")[0],
            is_active=True,
        )
        db.add(target_user)
        await db.flush()

    existing_result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == tc.workspace_id,
            WorkspaceMember.user_id == target_user.id,
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="User is already a member of this workspace",
        )

    membership = WorkspaceMember(
        workspace_id=tc.workspace_id,
        user_id=target_user.id,
        role=data.role,
        joined_at=_now(),
        expires_at=data.invitation_expires,
    )
    db.add(membership)
    await db.flush()

    invitation = Invitation(
        workspace_id=tc.workspace_id,
        email=data.email,
        role=data.role,
        message=data.message,
        expires_at=data.invitation_expires,
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(membership)

    return WorkspaceMemberOut(
        id=membership.id,
        workspace_id=membership.workspace_id,
        user_id=membership.user_id,
        user_name=target_user.name,
        user_email=target_user.email,
        role=membership.role,
        joined_at=membership.joined_at,
        invited_at=membership.invited_at,
        expires=membership.expires_at,
    )


@router.patch("/members/{member_id}", response_model=WorkspaceMemberOut)
async def update_member(
    member_id: str,
    data: WorkspaceMemberUpdate,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    _require_min_role(tc, "admin")

    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.id == member_id,
            WorkspaceMember.workspace_id == tc.workspace_id,
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=404, detail="Member not found")

    # Prevent self-demotion from owner (would orphan the workspace)
    if membership.user_id == tc.user_id and data.role and data.role != "owner":
        raise HTTPException(
            status_code=400,
            detail="Cannot change your own role from owner",
        )

    if data.role is not None:
        membership.role = data.role
    if data.expires is not None:
        membership.expires_at = data.expires

    await db.commit()
    await db.refresh(membership)

    user_result = await db.execute(
        select(User).where(User.id == membership.user_id)
    )
    user = user_result.scalar_one_or_none()

    return WorkspaceMemberOut(
        id=membership.id,
        workspace_id=membership.workspace_id,
        user_id=membership.user_id,
        user_name=user.name if user else "",
        user_email=user.email if user else "",
        role=membership.role,
        joined_at=membership.joined_at,
        invited_at=membership.invited_at,
        expires=membership.expires_at,
    )


@router.delete("/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    user_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    _require_min_role(tc, "admin")

    if user_id == tc.user_id:
        raise HTTPException(
            status_code=400,
            detail="Use the leave endpoint to remove yourself",
        )

    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == tc.workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=404, detail="Member not found")

    # Only owner can remove another owner
    if membership.role == "owner" and tc.role != "owner":
        raise HTTPException(
            status_code=403,
            detail="Only the owner can remove another owner",
        )

    await db.delete(membership)
    await db.commit()


@router.post("/member/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_workspace(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == tc.workspace_id,
            WorkspaceMember.user_id == tc.user_id,
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=404, detail="Not a member")

    if membership.role == "owner":
        raise HTTPException(
            status_code=400,
            detail="Owner cannot leave — transfer ownership first or delete the workspace",
        )

    await db.delete(membership)
    await db.commit()


# ── Invitations ────────────────────────────────────────────────────────────


@router.get("/members/invitations", response_model=list[InvitationOut])
async def list_invitations(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    _require_min_role(tc, "member")

    result = await db.execute(
        select(Invitation).where(
            Invitation.workspace_id == tc.workspace_id,
        ).order_by(Invitation.created_at.desc())
    )
    return result.scalars().all()


@router.get(
    "/members/invitations/{state}",
    response_model=list[InvitationOut],
)
async def list_invitations_by_state(
    state: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    _require_min_role(tc, "member")

    result = await db.execute(
        select(Invitation).where(
            Invitation.workspace_id == tc.workspace_id,
            Invitation.state == state,
        ).order_by(Invitation.created_at.desc())
    )
    return result.scalars().all()


@router.patch("/members/invitation/{invitation_id}", response_model=InvitationOut)
async def update_invitation(
    invitation_id: str,
    data: InvitationUpdate,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    _require_min_role(tc, "admin")

    result = await db.execute(
        select(Invitation).where(
            Invitation.id == invitation_id,
            Invitation.workspace_id == tc.workspace_id,
        )
    )
    invitation = result.scalar_one_or_none()
    if invitation is None:
        raise HTTPException(status_code=404, detail="Invitation not found")

    if data.state is not None:
        invitation.state = data.state
        invitation.responded_at = _now()
    if data.role is not None:
        invitation.role = data.role
    if data.expires is not None:
        invitation.expires_at = data.expires

    await db.commit()
    await db.refresh(invitation)
    return invitation


@router.delete("/members/invitation/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invitation(
    invitation_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    _require_min_role(tc, "admin")

    result = await db.execute(
        select(Invitation).where(
            Invitation.id == invitation_id,
            Invitation.workspace_id == tc.workspace_id,
        )
    )
    invitation = result.scalar_one_or_none()
    if invitation is None:
        raise HTTPException(status_code=404, detail="Invitation not found")

    await db.delete(invitation)
    await db.commit()


# ── Workspace Discovery ────────────────────────────────────────────────────


@router.get("/workspaces/all")
async def list_all_workspaces(
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WorkspaceMember).where(WorkspaceMember.user_id == user.id)
    )
    memberships = result.scalars().all()
    workspace_ids = [m.workspace_id for m in memberships]

    workspaces_result = await db.execute(
        select(Workspace).where(
            Workspace.id.in_(workspace_ids),
            Workspace.deleted_at.is_(None),
        )
    )
    workspaces = workspaces_result.scalars().all()

    return [
        {
            "id": ws.id,
            "name": ws.name,
            "slug": ws.slug,
            "role": next((m.role for m in memberships if m.workspace_id == ws.id), "viewer"),
        }
        for ws in workspaces
    ]


@router.get("/workspaces/available")
async def list_available_workspaces(
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    member_ws_ids = [
        row[0] for row in
        (await db.execute(
            select(WorkspaceMember.workspace_id).where(WorkspaceMember.user_id == user.id)
        )).all()
    ]

    result = await db.execute(
        select(Workspace).where(
            Workspace.deleted_at.is_(None),
            Workspace.id.notin_(member_ws_ids) if member_ws_ids else True,
        )
    )
    return [
        {"id": ws.id, "name": ws.name, "slug": ws.slug}
        for ws in result.scalars().all()
    ]
