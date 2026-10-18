"""Orchestrate chat: retrieval → LLM call → provenance tracking."""

from __future__ import annotations

import time
import re as _re_mod
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Fact, Decision, MessageProvenance
from app.schemas import ProvenanceCreate
from app.core.config import settings
from app.services.llm import get_llm_provider
from app.services.m5_retrieval import retrieve_for_chat


SYSTEM_PROMPT = """You are a helpful assistant in a SwarmVault workspace.
Use the provided memory context to personalize your responses.
If no memory context is available, respond helpfully from your general knowledge.
Keep responses concise and relevant."""


async def process_chat(
    db: AsyncSession,
    *,
    workspace_id: str,
    user_id: str,
    user_message: str,
    session_id: str,
    model: str = "claude-sonnet-4-5-20250929",
    project_id: str | None = None,
    memory_limit: int = 5,
) -> dict[str, Any]:
    """Process a chat message end-to-end.

    1. Retrieve relevant facts/decisions (M5 hybrid search)
    2. Build messages for the LLM with memory context
    3. Call the LLM
    4. Record provenance

    Returns:
        {
            "response": str,
            "session_id": str,
            "message_id": str,
            "model": str,
            "usage": {...},
            "memory_ids_used": [...],
            "retrieval_method": str,
            "latency_ms": int,
            "confidence": float,
        }
    """
    t0 = time.monotonic()

    # Step 1: Retrieve relevant facts/decisions via M5
    retrieval = await retrieve_for_chat(
        db=db,
        workspace_id=workspace_id,
        query=user_message,
        project_id=project_id,
        limit=memory_limit,
    )

    context_block = retrieval["context"] if retrieval["context"] else None
    memory_ids_used: list[str] = []
    retrieval_sources = []

    for r in retrieval["results"]:
        item = r.item
        item_id = str(item.id)
        memory_ids_used.append(item_id)
        content_preview = getattr(item, 'content', '')[:200]
        source = {
            "memory_id": item_id,
            "content": content_preview,
            "item_type": r.item_type,
            "score": round(r.score, 3),
        }
        # Phase 3: include reranking explainability fields when present
        if hasattr(r, "retrieval_score"):
            source["retrieval_score"] = round(r.retrieval_score, 3)
            source["reranker_score"] = round(r.reranker_score, 3)
        retrieval_sources.append(source)

    user_message_preview = user_message[:500] if user_message else None

    # Step 2: Build LLM messages
    messages: list[dict[str, str]] = []
    if context_block:
        messages.append({
            "role": "system",
            "content": f"{SYSTEM_PROMPT}\n\nRelevant memories:\n{context_block}",
        })
    else:
        messages.append({"role": "system", "content": SYSTEM_PROMPT})

    messages.append({"role": "user", "content": user_message})

    # Step 3: Call the LLM via provider abstraction
    provider = get_llm_provider()
    try:
        llm_result = await provider.chat_completion(
            messages=messages,
            model=model,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            stream=False,
        )
        if hasattr(llm_result, "__await__"):
            llm_result = await llm_result
    finally:
        await provider.aclose()

    latency_ms = int((time.monotonic() - t0) * 1000)

    # Step 4: Compute a simple confidence score
    confidence: float | None = None
    if context_block and llm_result["content"]:
        base = 0.7 if memory_ids_used else 0.5
        length_bonus = min(0.3, len(llm_result["content"]) / 1000)
        confidence = min(1.0, base + length_bonus)

    # Step 5: Save provenance record
    provenance = MessageProvenance(
        workspace_id=workspace_id,
        session_id=session_id,
        project_id=project_id,
        model=llm_result["model"],
        provider=llm_result.get("provider", provider.name),
        retrieval_method="hybrid" if memory_ids_used else "none",
        memory_ids_used=memory_ids_used or None,
        retrieval_sources=retrieval_sources or None,
        user_message_preview=user_message_preview,
        prompt_tokens=llm_result["usage"]["prompt_tokens"],
        completion_tokens=llm_result["usage"]["completion_tokens"],
        total_tokens=llm_result["usage"]["total_tokens"],
        latency_ms=latency_ms,
        confidence=confidence,
    )
    db.add(provenance)
    await db.flush()

    return {
        "response": llm_result["content"],
        "session_id": session_id,
        "model": llm_result["model"],
        "usage": llm_result["usage"],
        "memory_ids_used": memory_ids_used,
        "retrieval_method": "hybrid" if memory_ids_used else "none",
        "retrieval_sources": retrieval_sources,
        "latency_ms": latency_ms,
        "confidence": confidence,
        "provider": llm_result.get("provider", provider.name),
    }
