"""Reranking service — second-stage scoring on top of M5 retrieval.

Design:
  - reranker_score is the PRIMARY signal (keyword overlap quality)
  - confidence, authority, temporal_status are BOUNDED adjustments (+15%)
  - Abstention: score below MIN_RELEVANCE → don't inject into context

Ships behind FEATURE_RERANKING_ENABLED=false (shadow mode by default).
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────

# Default relevance threshold — results below this are abstained
DEFAULT_MIN_RELEVANCE = 0.3

# Maximum bounded adjustment multiplier (1.0 ± this fraction)
MAX_ADJUSTMENT = 0.15  # ±15%


# ── Data classes ──────────────────────────────────────────────────────────


@dataclass
class RerankingResult:
    """A reranked retrieval candidate with explainability fields."""
    item: Any
    item_type: str  # "memory", "fact", "decision"
    retrieval_score: float  # Original M5 score
    reranker_score: float   # Cross-encoder / relevance score
    final_score: float      # Combined score
    factors: dict[str, float] = field(default_factory=dict)
    abstained: bool = False  # True if score below threshold
    abstention_reason: str | None = None


@dataclass
class RerankingConfig:
    """Configuration for reranking behavior."""
    enabled: bool = False  # Feature flag — shadow mode by default
    min_relevance: float = DEFAULT_MIN_RELEVANCE
    adjustment_cap: float = MAX_ADJUSTMENT


# ── Scoring ───────────────────────────────────────────────────────────────


def compute_reranker_score(
    query: str,
    content: str,
    *,
    item_type: str = "fact",
) -> tuple[float, dict[str, float]]:
    """Compute the reranker score (primary signal) for a candidate.

    The reranker score reflects how well the content matches the query intent.
    Uses three factors:
    1. Query term coverage — what fraction of query terms appear in content
    2. Term proximity — are query terms near each other in content?
    3. Length normalization — penalize very long or very short content

    Returns:
        (score, factors_dict) where score is in [0, 1]
    """
    factors: dict[str, float] = {}
    query_terms = [t.lower() for t in query.split() if len(t) > 2]
    content_lower = content.lower()

    if not query_terms:
        return 0.0, {"coverage": 0.0, "proximity": 0.0, "length_penalty": 0.0}

    # Factor 1: Term coverage — fraction of query terms present
    covered = sum(1 for t in query_terms if t in content_lower)
    coverage = covered / len(query_terms)
    factors["coverage"] = coverage

    # Factor 2: Term proximity — how close are query terms in the content
    if covered > 1:
        positions = []
        content_words = content_lower.split()
        for term in query_terms:
            if term in content_lower:
                idx = content_lower.index(term)
                word_idx = len(content_lower[:idx].split())
                positions.append(word_idx)
        if len(positions) > 1:
            positions.sort()
            spread = (positions[-1] - positions[0]) / max(len(content_words), 1)
            proximity = max(0.0, 1.0 - spread)
        else:
            proximity = 0.5
    elif covered == 1:
        proximity = 0.3
    else:
        proximity = 0.0
    factors["proximity"] = round(proximity, 4)

    # Factor 3: Length normalization — prefer medium-length content
    content_len = len(content.split())
    if content_len < 5:
        length_penalty = 0.5
    elif content_len < 15:
        length_penalty = 0.8
    elif content_len <= 200:
        length_penalty = 1.0
    elif content_len <= 500:
        length_penalty = 0.9
    else:
        length_penalty = 0.7
    factors["length_penalty"] = length_penalty

    # Combine: coverage is primary, proximity and length are modifiers
    raw_score = coverage * 0.6 + proximity * 0.25 + length_penalty * 0.15
    factors["raw"] = round(raw_score, 4)

    return raw_score, factors


def apply_bounded_adjustments(
    base_score: float,
    confidence: float = 1.0,
    authority: float = 1.0,
    temporal_status: str = "current",
    content_quality: float = 1.0,
    cap: float = MAX_ADJUSTMENT,
) -> tuple[float, dict[str, float]]:
    """Apply bounded adjustments to a base score.

    Adjustments are capped multipliers (±15%). This prevents uncalibrated
    defaults from dominating the relevance signal.

    Args:
        base_score: The primary reranker score
        confidence: Extraction confidence (default 1.0, range 0-1)
        authority: Source authority (default 1.0, range 0-1)
        temporal_status: "current" or "historical"
        content_quality: Signal from content analysis (0-1)
        cap: Maximum adjustment fraction (default 0.15 = ±15%)

    Returns:
        (adjusted_score, adjustment_factors)
    """
    factors: dict[str, float] = {}

    # Confidence adjustment: 0.0 → -15%, 1.0 → 0%
    conf_factor = 0.85 + 0.15 * confidence  # maps [0,1] to [0.85, 1.0]
    conf_adj = conf_factor - 1.0  # [-0.15, 0.0]
    conf_adj = max(-cap, min(cap, conf_adj))
    factors["confidence_adj"] = round(conf_adj, 4)

    # Authority adjustment: 0.0 → -15%, 1.0 → 0%
    auth_factor = 0.85 + 0.15 * authority
    auth_adj = auth_factor - 1.0
    auth_adj = max(-cap, min(cap, auth_adj))
    factors["authority_adj"] = round(auth_adj, 4)

    # Temporal adjustment: current → 0%, historical → -15%
    temporal_adj = 0.0 if temporal_status == "current" else -cap
    factors["temporal_adj"] = round(temporal_adj, 4)

    # Content quality adjustment
    qual_adj = (content_quality - 1.0) * cap
    qual_adj = max(-cap, min(cap, qual_adj))
    factors["quality_adj"] = round(qual_adj, 4)

    # Total adjustment (sum of bounded adjustments)
    total_adj = conf_adj + auth_adj + temporal_adj + qual_adj
    total_adj = max(-2 * cap, min(2 * cap, total_adj))
    factors["total_adj"] = round(total_adj, 4)

    # Apply as multiplier on base score
    adjusted = base_score * (1.0 + total_adj)
    factors["final"] = round(max(0.0, min(1.0, adjusted)), 4)

    return max(0.0, min(1.0, adjusted)), factors


# ── Service ───────────────────────────────────────────────────────────────


class RerankingService:
    """Second-stage reranking service for M5 retrieval results.

    Usage:
        service = RerankingService()
        results = service.rerank_sync(query, candidates, top_k=10)
    """

    def __init__(self, config: RerankingConfig | None = None) -> None:
        self.config = config or RerankingConfig(
            enabled=getattr(settings, "feature_reranking_enabled", False),
            min_relevance=getattr(settings, "reranking_min_relevance", DEFAULT_MIN_RELEVANCE),
        )

    def _rerank_impl(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        *,
        top_k: int = 10,
    ) -> list[RerankingResult]:
        """Core reranking implementation (synchronous, pure computation)."""
        if not candidates:
            return []

        reranked: list[RerankingResult] = []

        for cand in candidates:
            content = cand.get("content", "") or ""
            item = cand.get("item")
            item_type = cand.get("item_type", "fact")
            retrieval_score = float(cand.get("score", 0.0))
            confidence = float(cand.get("confidence", 1.0))
            authority = float(cand.get("authority", 1.0))
            temporal_status = cand.get("temporal_status", "current")

            # Step 1: Compute reranker score (primary signal)
            rr_score, rr_factors = compute_reranker_score(query, content, item_type=item_type)

            # Step 2: Apply bounded adjustments
            adjusted_score, adj_factors = apply_bounded_adjustments(
                base_score=rr_score,
                confidence=confidence,
                authority=authority,
                temporal_status=temporal_status,
                cap=self.config.adjustment_cap,
            )

            # Step 3: Check abstention (only in live mode)
            abstained = False
            abstention_reason = None
            if self.config.enabled and adjusted_score < self.config.min_relevance:
                abstained = True
                abstention_reason = (
                    f"reranker_score {adjusted_score:.3f} < min_relevance {self.config.min_relevance}"
                )

            # Step 4: Combine with original retrieval score
            # Final score: 60% reranker, 40% retrieval
            final_score = 0.6 * adjusted_score + 0.4 * min(retrieval_score, 1.0)

            all_factors = {
                **rr_factors,
                **adj_factors,
                "retrieval_score": round(retrieval_score, 4),
                "reranker_score": round(rr_score, 4),
                "final_score": round(final_score, 4),
            }

            result = RerankingResult(
                item=item,
                item_type=item_type,
                retrieval_score=retrieval_score,
                reranker_score=rr_score,
                final_score=final_score,
                factors=all_factors,
                abstained=abstained,
                abstention_reason=abstention_reason,
            )
            reranked.append(result)

        # Sort by final_score descending (abstained items sink to bottom)
        reranked.sort(key=lambda r: r.final_score, reverse=True)

        # top_k truncation only applies in live mode
        if self.config.enabled and top_k:
            return reranked[:top_k]

        return reranked

    def rerank_sync(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        *,
        top_k: int = 10,
    ) -> list[RerankingResult]:
        """Synchronous rerank — for tests and non-async contexts."""
        return self._rerank_impl(query, candidates, top_k=top_k)

    async def rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        *,
        top_k: int = 10,
    ) -> list[RerankingResult]:
        """Async rerank — for use in API handlers.

        Usage:
            results = await service.rerank(query, candidates)
        """
        return self._rerank_impl(query, candidates, top_k=top_k)

    def filter_active(self, results: list[RerankingResult]) -> list[RerankingResult]:
        """Remove abstained results — for use when flag is live."""
        return [r for r in results if not r.abstained]
