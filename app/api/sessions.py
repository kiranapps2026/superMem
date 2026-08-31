from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.middleware.tenancy import TenantContext, get_tenant_context
from app.models import Session, Message
from app.schemas import SessionCreate, SessionOut, MessageCreate, MessageOut
from datetime import datetime, timezone

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/", response_model=list[SessionOut])
async def list_sessions(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(
            Session.workspace_id == tc.workspace_id,
            Session.user_id == tc.user_id,
            Session.deleted_at.is_(None),
        ).order_by(Session.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreate,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    session = Session(
        workspace_id=tc.workspace_id,
        user_id=tc.user_id,
        title=data.title,
        extra_metadata=data.extra_metadata,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.workspace_id == tc.workspace_id,
            Session.user_id == tc.user_id,
            Session.deleted_at.is_(None),
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/{session_id}/history")
async def get_session_history(
    session_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Get session with all messages included."""
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Session)
        .options(selectinload(Session.messages))
        .where(
            Session.id == session_id,
            Session.workspace_id == tc.workspace_id,
            Session.user_id == tc.user_id,
            Session.deleted_at.is_(None),
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    meta = session.extra_metadata or {}
    return {
        "session_id": str(session.id),
        "title": session.title,
        "source": meta.get("source", "chat"),
        "messages": [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in sorted(session.messages, key=lambda x: x.created_at)
        ],
    }


@router.post("/{session_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def add_message(
    session_id: str,
    data: MessageCreate,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    session_result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.workspace_id == tc.workspace_id,
            Session.user_id == tc.user_id,
            Session.deleted_at.is_(None),
        )
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    message = Message(
        session_id=session_id,
        role=data.role,
        content=data.content,
        metadata=data.metadata,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.workspace_id == tc.workspace_id,
            Session.user_id == tc.user_id,
            Session.deleted_at.is_(None),
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.deleted_at = _now()
    await db.commit()
