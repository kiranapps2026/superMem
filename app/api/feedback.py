"""Feedback API — thumbs up/down on chat responses."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.middleware.tenancy import TenantContext, get_tenant_context
from app.models import MessageFeedback
from app.schemas import FeedbackCreate, FeedbackOut, FeedbackListResponse


router = APIRouter(prefix="/feedback", tags=["feedback"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/", response_model=FeedbackOut, status_code=201)
async def create_feedback(
    data: FeedbackCreate,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback on a chat response."""
    feedback = MessageFeedback(
        workspace_id=tc.workspace_id,
        user_id=tc.user_id,
        provenance_id=data.provenance_id,
        session_id=data.session_id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return feedback


@router.get("/", response_model=FeedbackListResponse)
async def list_feedback(
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
    session_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List feedback for the workspace, optionally filtered by session."""
    stmt = select(MessageFeedback).where(
        MessageFeedback.workspace_id == tc.workspace_id,
        MessageFeedback.deleted_at.is_(None),
    )
    if session_id:
        stmt = stmt.where(MessageFeedback.session_id == session_id)

    count_stmt = select(func.count(MessageFeedback.id)).where(
        MessageFeedback.workspace_id == tc.workspace_id,
        MessageFeedback.deleted_at.is_(None),
    )
    if session_id:
        count_stmt = count_stmt.where(MessageFeedback.session_id == session_id)
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(MessageFeedback.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return FeedbackListResponse(
        items=[FeedbackOut.model_validate(f) for f in items],
        total=total,
    )


@router.get("/{feedback_id}", response_model=FeedbackOut)
async def get_feedback(
    feedback_id: str,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Get a single feedback entry."""
    result = await db.execute(
        select(MessageFeedback).where(
            MessageFeedback.id == feedback_id,
            MessageFeedback.workspace_id == tc.workspace_id,
            MessageFeedback.deleted_at.is_(None),
        )
    )
    feedback = result.scalar_one_or_none()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback
