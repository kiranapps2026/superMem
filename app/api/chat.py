from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.middleware.tenancy import TenantContext, get_tenant_context
from app.models import Session, Message
from app.schemas import ChatRequest, ChatResponse, MessageOut
from datetime import datetime, timezone

router = APIRouter(prefix="/chat", tags=["chat"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/", response_model=ChatResponse)
async def send_chat_message(
    data: ChatRequest,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    session_id = data.session_id
    if session_id is None:
        session = Session(
            workspace_id=tc.workspace_id,
            user_id=tc.user_id,
            title=None,
        )
        db.add(session)
        await db.flush()
        session_id = session.id
    else:
        result = await db.execute(
            select(Session).where(
                Session.id == session_id,
                Session.workspace_id == tc.workspace_id,
                Session.user_id == tc.user_id,
                Session.deleted_at.is_(None),
            )
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

    user_msg = Message(
        session_id=session_id,
        role="user",
        content=data.message,
    )
    db.add(user_msg)

    ai_response_text = (
        f"[Mock AI] I received your message: \"{data.message}\". "
        "This is a placeholder response — replace with your LLM provider "
        "integration in a future sprint."
    )
    ai_msg = Message(
        session_id=session_id,
        role="assistant",
        content=ai_response_text,
    )
    db.add(ai_msg)
    await db.commit()
    await db.refresh(ai_msg)

    return ChatResponse(
        message_id=ai_msg.id,
        session_id=session_id,
        response=ai_response_text,
        model="mock",
        usage={"prompt_tokens": 0, "completion_tokens": 0},
    )
