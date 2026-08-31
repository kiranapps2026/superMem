"""Chat API — streaming and non-streaming."""

from __future__ import annotations

import json
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.core.config import settings
from app.db import get_db
from app.middleware.tenancy import TenantContext, get_tenant_context
from app.models import Message, Session
from app.schemas import ChatRequest, ChatResponse
from app.services.chat_orchestrator import process_chat
from app.services.llm import get_llm_provider
from app.services.retrieval import retrieve_memories

router = APIRouter(prefix="/chat", tags=["chat"])


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
    await db.flush()

    result = await process_chat(
        db=db,
        workspace_id=tc.workspace_id,
        user_id=tc.user_id,
        user_message=data.message,
        session_id=session_id,
        project_id=data.project_id,
    )

    assistant_msg = Message(
        session_id=session_id,
        role="assistant",
        content=result["response"],
        metadata={
            "model": result["model"],
            "usage": result["usage"],
            "memory_ids_used": result.get("memory_ids_used", []),
            "latency_ms": result.get("latency_ms"),
            "confidence": result.get("confidence"),
        },
    )
    db.add(assistant_msg)
    await db.flush()
    await db.commit()

    return ChatResponse(
        message_id=str(assistant_msg.id),
        session_id=result["session_id"],
        response=result["response"],
        model=result["model"],
        usage=result["usage"],
        memory_ids_used=result.get("memory_ids_used"),
    )


async def _sse_stream(data: dict) -> str:
    return f"data: {json.dumps(data, default=str)}\n\n"


@router.post("/stream")
async def stream_chat(
    data: ChatRequest,
    tc: Annotated[TenantContext, Depends(get_tenant_context)],
    db: AsyncSession = Depends(get_db),
):
    """Stream a chat response as SSE.

    Events:
      token   - incremental text chunk
      sources - retrieved memory sources
      done    - final metadata
      error   - fatal error
    """
    async def _gen():
        t0 = time.monotonic()
        try:
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
                    yield await _sse_stream({"type": "error", "detail": "Session not found"})
                    return

            user_msg = Message(
                session_id=session_id,
                role="user",
                content=data.message,
            )
            db.add(user_msg)
            await db.flush()

            # Retrieve memories for sources event
            retrieved = await retrieve_memories(
                db=db,
                workspace_id=tc.workspace_id,
                query=data.message,
                user_id=tc.user_id,
                limit=5,
            )
            memory_ids_used: list[str] = []
            sources = []
            for mem, score in retrieved:
                if score > 0.1:
                    memory_ids_used.append(mem.id)
                    sources.append({
                        "memory_id": str(mem.id),
                        "content": mem.content[:200],
                        "memory_type": mem.memory_type,
                        "score": round(score, 3),
                    })

            # Send sources event first
            yield await _sse_stream({"type": "sources", "sources": sources})

            # Stream LLM response
            provider = get_llm_provider()
            try:
                context_parts = [f"[Memory: {s['content']}]" for s in sources]
                context_block = "\n".join(context_parts) if context_parts else None

                messages: list[dict[str, str]] = []
                system_prompt = (
                    "You are a helpful assistant in a SwarmVault workspace. "
                    "Use the provided memory context to personalize your responses. "
                    "If no memory context is available, respond helpfully from your general knowledge. "
                    "Keep responses concise and relevant."
                )
                if context_block:
                    messages.append({"role": "system", "content": f"{system_prompt}\n\nRelevant memories:\n{context_block}"})
                else:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": data.message})

                stream_result = await provider.chat_completion(
                    messages=messages,
                    model=settings.llm_model,
                    max_tokens=settings.llm_max_tokens,
                    temperature=settings.llm_temperature,
                    stream=True,
                )

                # chat_completion is async, so await it first
                # Result is dict (non-stream) or AsyncIterator (stream)
                if hasattr(stream_result, "__aiter__"):
                    stream = stream_result
                else:
                    # Non-streaming fallback: treat as single token
                    async def _single():
                        yield stream_result.get("content", "")
                    stream = _single()

                full_text = ""
                async for chunk in stream:
                    full_text += chunk
                    yield await _sse_stream({"type": "token", "content": chunk})

                latency_ms = int((time.monotonic() - t0) * 1000)

                assistant_msg = Message(
                    session_id=session_id,
                    role="assistant",
                    content=full_text,
                    metadata={
                        "model": settings.llm_model,
                        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                        "memory_ids_used": memory_ids_used,
                        "latency_ms": latency_ms,
                    },
                )
                db.add(assistant_msg)
                await db.flush()
                await db.commit()

                yield await _sse_stream({
                    "type": "done",
                    "message_id": str(assistant_msg.id),
                    "session_id": session_id,
                    "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    "latency_ms": latency_ms,
                    "memory_grounded": bool(sources),
                })
            finally:
                await provider.aclose()

        except Exception as exc:
            yield await _sse_stream({"type": "error", "detail": str(exc)})

    return StreamingResponse(
        _gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

