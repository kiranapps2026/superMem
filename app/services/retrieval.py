"""Hybrid retrieval: keyword + optional vector similarity.

Without pgvector, embeddings stored in Memory.embedding (JSON list of floats)
are compared using numpy cosine similarity in Python after fetching candidates
from the database.

Falls back gracefully to keyword-only when no embeddings are present.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Memory


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not a or not b:
        return 0.0
    arr_a = np.array(a, dtype=np.float64)
    arr_b = np.array(b, dtype=np.float64)
    norm_a = np.linalg.norm(arr_a)
    norm_b = np.linalg.norm(arr_b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(arr_a, arr_b) / (norm_a * norm_b))


def _keyword_score(content: str, query: str) -> float:
    """Score content relevance to query via keyword overlap."""
    query_words = set(query.lower().split())
    content_words = set(content.lower().split())
    if not query_words:
        return 0.0
    overlap = query_words & content_words
    return len(overlap) / len(query_words)


def _hybrid_score(
    content: str,
    query: str,
    embedding: list[float] | None,
    query_embedding: list[float] | None,
    vector_weight: float = 0.6,
    keyword_weight: float = 0.4,
) -> float:
    """Combine vector and keyword relevance into a single score."""
    kw = _keyword_score(content, query)
    if embedding and query_embedding:
        vec = _cosine_similarity(embedding, query_embedding)
        return vector_weight * vec + keyword_weight * kw
    return kw


async def retrieve_memories(
    db: AsyncSession,
    workspace_id: str,
    query: str,
    *,
    user_id: str | None = None,
    memory_type: str | None = None,
    limit: int = 20,
    vector_weight: float = 0.6,
    keyword_weight: float = 0.4,
    query_embedding: list[float] | None = None,
) -> list[tuple[Memory, float]]:
    """Retrieve memories scoped to a workspace, ranked by hybrid relevance.

    Args:
        db: Database session
        workspace_id: Workspace to scope the search
        query: User's query string
        user_id: Optional user filter (None = all users in workspace)
        memory_type: Optional memory type filter
        limit: Max results to return
        vector_weight: Weight for embedding similarity (0-1)
        keyword_weight: Weight for keyword overlap (0-1)
        query_embedding: Optional pre-computed embedding for the query

    Returns:
        List of (Memory, score) tuples, sorted by score descending
    """
    # Build the base query
    stmt = select(Memory).where(Memory.workspace_id == workspace_id)

    if user_id:
        stmt = stmt.where(Memory.user_id == user_id)
    if memory_type:
        stmt = stmt.where(Memory.memory_type == memory_type)

    # Fetch a generous candidate pool for re-ranking
    stmt = stmt.limit(limit * 3)
    result = await db.execute(stmt)
    candidates = result.scalars().all()

    # If no candidates, return early
    if not candidates:
        return []

    # Score each candidate
    scored: list[tuple[Memory, float]] = []
    for mem in candidates:
        score = _hybrid_score(
            content=mem.content,
            query=query,
            embedding=mem.embedding,
            query_embedding=query_embedding,
            vector_weight=vector_weight,
            keyword_weight=keyword_weight,
        )
        scored.append((mem, score))

    # Sort by score descending, take top N
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]
