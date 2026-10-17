"""M5 — Multi-factor memory retrieval and ranking.

Replaces simple keyword+cosine hybrid scoring with a comprehensive
multi-factor ranking system that considers:

- Keyword relevance (BM25-style term frequency)
- Authority (source reliability)
- Confidence (extraction confidence)
- Recency (temporal decay)
- Temporal status (current > historical)
- Graph context (number of graph connections)
- Provenance quality
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select, func, case, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Fact, Decision, GraphEdge
from app.services.reranking import RerankingService, RerankingResult
from app.core.config import settings


_reranking_service = RerankingService()


@dataclass
class RetrievalResult:
    """A scored retrieval candidate."""
    item: Any
    item_type: str  # "memory", "fact", "decision"
    score: float
    factors: dict[str, float] = field(default_factory=dict)


def _bm25_score(content: str, query: str) -> float:
    """BM25-inspired keyword relevance score.

    Simplified BM25 without IDF (since we query per-workspace):
    - Term frequency normalization
    - Document length normalization
    """
    query_terms = query.lower().split()
    if not query_terms:
        return 0.0

    content_lower = content.lower()
    doc_len = len(content_lower.split())
    if doc_len == 0:
        return 0.0

    avg_dl = 100.0  # assumed average document length
    k1, b = 1.5, 0.75

    score = 0.0
    for term in query_terms:
        tf = content_lower.count(term)
        if tf == 0:
            continue
        # Simplified TF with length normalization
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * doc_len / avg_dl)
        score += numerator / denominator

    return score


def _recency_score(created_at: Any) -> float:
    """Score based on recency — newer items score higher.

    Uses exponential decay with 30-day half-life.
    """
    if created_at is None:
        return 0.5
    age_seconds = time.time() - created_at.timestamp()
    age_days = age_seconds / 86400
    half_life = 30.0
    return math.exp(-0.693 * age_days / half_life)


async def _graph_context_score(db: AsyncSession, item_id: str) -> float:
    """Score based on graph connectivity — more connections = higher authority.

    Properly async — must be awaited.
    """
    result = await db.execute(
        select(func.count(GraphEdge.id)).where(
            (GraphEdge.source_node_id == item_id) | (GraphEdge.target_node_id == item_id),
            GraphEdge.deleted_at.is_(None),
        )
    )
    count = result.scalar()
    if count is None or count == 0:
        return 0.0
    # Logarithmic scaling: 1 connection = 0.3, 10 = 0.6, 100 = 0.9
    return min(1.0, math.log(max(1, count)) * 0.3)


async def rank_facts(
    db: AsyncSession,
    workspace_id: str,
    query: str,
    *,
    project_id: str | None = None,
    limit: int = 20,
) -> list[RetrievalResult]:
    """Retrieve and rank facts using M5 multi-factor scoring.

    Prioritizes current facts over historical ones.
    """
    stmt = select(Fact).where(
        Fact.workspace_id == workspace_id,
        Fact.deleted_at.is_(None),
    )
    if project_id:
        stmt = stmt.where(Fact.project_id == project_id)

    stmt = stmt.limit(limit * 3)
    result = await db.execute(stmt)
    candidates = list(result.scalars().all())

    scored: list[RetrievalResult] = []
    for fact in candidates:
        # Temporal status bonus
        temporal_bonus = 1.0 if fact.temporal_status == "current" else 0.3

        factors = {
            "keyword": min(1.0, _bm25_score(fact.content, query) * 0.5),
            "recency": _recency_score(fact.created_at),
            "authority": fact.authority,
            "confidence": fact.confidence,
            "temporal": temporal_bonus,
            "graph": await _graph_context_score(db, str(fact.id)),
        }

        score = (
            0.25 * factors["keyword"]
            + 0.15 * factors["recency"]
            + 0.15 * factors["authority"]
            + 0.15 * factors["confidence"]
            + 0.20 * factors["temporal"]
            + 0.10 * factors["graph"]
        )
        factors["final"] = score
        scored.append(RetrievalResult(
            item=fact,
            item_type="fact",
            score=score,
            factors=factors,
        ))

    scored.sort(key=lambda r: r.score, reverse=True)
    return scored[:limit]


async def rank_decisions(
    db: AsyncSession,
    workspace_id: str,
    query: str,
    *,
    project_id: str | None = None,
    limit: int = 20,
) -> list[RetrievalResult]:
    """Retrieve and rank decisions using M5 multi-factor scoring.

    Prioritizes current decisions over historical ones.
    """
    stmt = select(Decision).where(
        Decision.workspace_id == workspace_id,
        Decision.deleted_at.is_(None),
    )
    if project_id:
        stmt = stmt.where(Decision.project_id == project_id)

    stmt = stmt.limit(limit * 3)
    result = await db.execute(stmt)
    candidates = list(result.scalars().all())

    scored: list[RetrievalResult] = []
    for dec in candidates:
        temporal_bonus = 1.0 if dec.temporal_status == "current" else 0.3

        factors = {
            "keyword": min(1.0, _bm25_score(dec.content, query) * 0.5),
            "recency": _recency_score(dec.created_at),
            "authority": dec.authority,
            "confidence": dec.confidence,
            "temporal": temporal_bonus,
        }

        score = (
            0.25 * factors["keyword"]
            + 0.15 * factors["recency"]
            + 0.15 * factors["authority"]
            + 0.15 * factors["confidence"]
            + 0.30 * factors["temporal"]
        )
        factors["final"] = score
        scored.append(RetrievalResult(
            item=dec,
            item_type="decision",
            score=score,
            factors=factors,
        ))

    scored.sort(key=lambda r: r.score, reverse=True)
    return scored[:limit]


async def retrieve_hybrid(
    db: AsyncSession,
    workspace_id: str,
    query: str,
    *,
    project_id: str | None = None,
    limit: int = 20,
) -> list[RetrievalResult]:
    """M5 hybrid retrieval: combine facts and decisions.

    This is the main retrieval function used by chat.
    It runs fact and decision retrievers and merges by final score.

    Note: Memory model has no deleted_at column, so memory ranking
    is deferred until that model is updated.

    Args:
        db: Database session
        workspace_id: Workspace scope
        query: Query string
        project_id: Optional project filter
        limit: Max total results

    Returns:
        Merged, ranked list of RetrievalResult items
    """
    fact_results = await rank_facts(db, workspace_id, query, project_id=project_id, limit=limit)
    dec_results = await rank_decisions(db, workspace_id, query, project_id=project_id, limit=limit)

    combined = fact_results + dec_results
    combined.sort(key=lambda r: r.score, reverse=True)
    return combined[:limit]


async def retrieve_for_chat(
    db: AsyncSession,
    workspace_id: str,
    query: str,
    *,
    project_id: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Retrieve context for chat grounding.

    Runs M5 hybrid retrieval, then optionally applies Phase 3 reranking
    when FEATURE_RERANKING_ENABLED=true. In shadow mode (default), reranking
    scores are computed and logged but do not affect served context.

    Returns formatted context string + provenance chain.
    """
    results = await retrieve_hybrid(db, workspace_id, query, project_id=project_id, limit=limit)

    # Phase 3: Optional reranking
    reranking_applied = False
    if settings.feature_reranking_enabled:
        candidates = [
            {
                "item": r.item,
                "item_type": r.item_type,
                "content": getattr(r.item, "content", ""),
                "score": r.score,
                "confidence": getattr(r.item, "confidence", 1.0),
                "authority": getattr(r.item, "authority", 1.0),
                "temporal_status": getattr(r.item, "temporal_status", "current"),
            }
            for r in results
        ]
        reranked = await _reranking_service.rerank(query, candidates, top_k=limit)
        reranking_applied = True

        # Replace results with reranked ones, keeping provenance mapping
        new_results = []
        for rr in reranked:
            # Find the original RetrievalResult for provenance
            orig = next((r for r in results if r.item == rr.item), None)
            if orig:
                new_result = RetrievalResult(
                    item=orig.item,
                    item_type=orig.item_type,
                    score=rr.final_score,
                    factors={**orig.factors, **rr.factors},
                )
                # Attach reranking metadata for explainability
                new_result.retrieval_score = rr.retrieval_score
                new_result.reranker_score = rr.reranker_score
                new_result.abstained = rr.abstained
                new_result.abstention_reason = rr.abstention_reason
                new_results.append(new_result)
        results = new_results

    context_parts = []
    provenance = []

    for r in results:
        item = r.item
        if r.item_type == "fact":
            context_parts.append(f"[FACT] {item.content}")
            provenance.append({
                "type": "fact",
                "id": str(item.id),
                "source_id": item.source_id,
                "session_id": item.session_id,
                "temporal_status": item.temporal_status,
                "confidence": item.confidence,
                "score": r.score,
            })
        elif r.item_type == "decision":
            context_parts.append(f"[DECISION] {item.content}")
            provenance.append({
                "type": "decision",
                "id": str(item.id),
                "source_id": item.source_id,
                "session_id": item.session_id,
                "temporal_status": item.temporal_status,
                "confidence": item.confidence,
                "score": r.score,
            })

    context = "\n".join(context_parts) if context_parts else "No relevant memory found."

    return {
        "context": context,
        "results": results,
        "provenance": provenance,
        "query": query,
    }
