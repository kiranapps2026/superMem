"""Retrieval evaluation harness for M5 retrieval system (Phase 2).

Evaluates retrieval quality using labeled fixtures with per-category metrics:
- precision@5, recall@k, recall@20, MRR, nDCG@k
- zero-result rate
- tenant-isolation accuracy
"""
from __future__ import annotations

import json
import logging
import math
import os
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ── Metrics ──────────────────────────────────────────────────────────────


def precision_at_k(relevant: set[str], retrieved: list[str], k: int) -> float:
    """Precision@k: fraction of top-k retrieved items that are relevant."""
    if k == 0:
        return 0.0
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for r in top_k if r in relevant)
    return hits / k


def recall_at_k(relevant: set[str], retrieved: list[str], k: int) -> float:
    """Recall@k: fraction of relevant items found in top-k."""
    if not relevant:
        return 1.0
    top_k = set(retrieved[:k])
    return len(top_k & relevant) / len(relevant)


def mrr(relevant: set[str], retrieved: list[str]) -> float:
    """Mean Reciprocal Rank: 1/rank of first relevant item."""
    for i, r in enumerate(retrieved):
        if r in relevant:
            return 1.0 / (i + 1)
    return 0.0


def ndcg_at_k(relevant: set[str], retrieved: list[str], k: int) -> float:
    """Normalized Discounted Cumulative Gain at k."""
    top_k = retrieved[:k]
    dcg = sum(1.0 / math.log2(i + 2) for i, r in enumerate(top_k) if r in relevant)
    ideal = len(relevant)
    if ideal == 0:
        return 0.0
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(ideal, k)))
    return dcg / idcg if idcg > 0 else 0.0


def tenant_isolation_score(retrieved: list[dict], query_workspace_id: str) -> float:
    """Fraction of retrieved items from the correct workspace."""
    if not retrieved:
        return 1.0
    correct = sum(1 for r in retrieved if r.get("workspace_id") == query_workspace_id)
    return correct / len(retrieved)


# ── Fixture loading ───────────────────────────────────────────────────────


def load_eval_fixtures(version: str = "v1") -> dict[str, Any]:
    """Load retrieval evaluation fixtures from disk."""
    # __file__ is app/services/retrieval_eval/__init__.py
    # Go up 4 levels: retrieval_eval/ -> services/ -> app/ -> project_root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    fixture_path = os.path.join(project_root, "tests", "eval", f"retrieval_eval_{version}.json")
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Evaluator ─────────────────────────────────────────────────────────────


@dataclass
class CategoryMetrics:
    """Metrics for a single evaluation category."""
    category: str
    query_count: int = 0
    precision_at_5_sum: float = 0.0
    recall_at_20_sum: float = 0.0
    mrr_sum: float = 0.0
    ndcg_at_5_sum: float = 0.0
    zero_result_count: int = 0
    tenant_isolation_sum: float = 0.0

    @property
    def avg_precision_at_5(self) -> float:
        return self.precision_at_5_sum / self.query_count if self.query_count > 0 else 0.0

    @property
    def avg_recall_at_20(self) -> float:
        return self.recall_at_20_sum / self.query_count if self.query_count > 0 else 0.0

    @property
    def avg_mrr(self) -> float:
        return self.mrr_sum / self.query_count if self.query_count > 0 else 0.0

    @property
    def avg_ndcg_at_5(self) -> float:
        return self.ndcg_at_5_sum / self.query_count if self.query_count > 0 else 0.0

    @property
    def zero_result_rate(self) -> float:
        return self.zero_result_count / self.query_count if self.query_count > 0 else 0.0

    @property
    def avg_tenant_isolation(self) -> float:
        return self.tenant_isolation_sum / self.query_count if self.query_count > 0 else 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "query_count": self.query_count,
            "precision_at_5": round(self.avg_precision_at_5, 4),
            "recall_at_20": round(self.avg_recall_at_20, 4),
            "mrr": round(self.avg_mrr, 4),
            "ndcg_at_5": round(self.avg_ndcg_at_5, 4),
            "zero_result_rate": round(self.zero_result_rate, 4),
            "tenant_isolation": round(self.avg_tenant_isolation, 4),
        }


class RetrievalEvaluator:
    """Evaluate M5 retrieval quality against labeled fixtures.

    Usage:
        evaluator = RetrievalEvaluator()
        evaluator.load_fixtures("v1")
        results = await evaluator.evaluate(db_session)
        report = evaluator.scorecard()
    """

    def __init__(self, version: str = "v1") -> None:
        self.version = version
        self._fixtures: dict[str, Any] | None = None
        self._categories: dict[str, CategoryMetrics] = {}
        self._results: list[dict[str, Any]] = []

    def load_fixtures(self, version: str | None = None) -> None:
        """Load evaluation fixtures from disk."""
        if version:
            self.version = version
        self._fixtures = load_eval_fixtures(self.version)
        self._categories = {cat: CategoryMetrics(category=cat) for cat in self._fixtures.get("categories", {})}

    async def evaluate(self, retrieve_func: Any) -> dict[str, Any]:
        """Run evaluation against a retrieval function.

        Args:
            retrieve_func: async callable(db, workspace_id, query, limit) -> list[dict]

        Returns:
            Scorecard dict with per-category and overall metrics.
        """
        self._ensure_fixtures_loaded()
        if self._fixtures is None:
            return {"error": "no fixtures loaded"}

        self._results = []
        self._categories = {cat: CategoryMetrics(category=cat) for cat in self._fixtures.get("categories", {})}

        for cat_name, cat_data in self._fixtures.get("categories", {}).items():
            for query_entry in cat_data.get("queries", []):
                relevant_ids: set[str] = set(query_entry.get("relevant_ids", []))
                workspace_id: str = query_entry.get("workspace_id", "default")
                query: str = query_entry["query"]

                try:
                    retrieved = await retrieve_func(None, workspace_id, query, limit=20)
                except Exception as exc:
                    logger.error("[eval] retrieval failed for '%s': %s", query, exc)
                    retrieved = []

                retrieved_ids = [r.get("id", "") for r in retrieved if r.get("id")]

                m = self._categories[cat_name]
                m.query_count += 1
                m.precision_at_5_sum += precision_at_k(relevant_ids, retrieved_ids, 5)
                m.recall_at_20_sum += recall_at_k(relevant_ids, retrieved_ids, 20)
                m.mrr_sum += mrr(relevant_ids, retrieved_ids)
                m.ndcg_at_5_sum += ndcg_at_k(relevant_ids, retrieved_ids, 5)
                if not retrieved_ids:
                    m.zero_result_count += 1
                m.tenant_isolation_sum += tenant_isolation_score(retrieved, workspace_id)

                self._results.append({
                    "category": cat_name,
                    "query": query,
                    "workspace_id": workspace_id,
                    "relevant_count": len(relevant_ids),
                    "retrieved_count": len(retrieved_ids),
                    "precision_at_5": round(precision_at_k(relevant_ids, retrieved_ids, 5), 4),
                    "recall_at_20": round(recall_at_k(relevant_ids, retrieved_ids, 20), 4),
                    "mrr": round(mrr(relevant_ids, retrieved_ids), 4),
                    "ndcg_at_5": round(ndcg_at_k(relevant_ids, retrieved_ids, 5), 4),
                    "zero_result": len(retrieved_ids) == 0,
                    "tenant_isolation": round(tenant_isolation_score(retrieved, workspace_id), 4),
                })

        return self.scorecard()

    def _ensure_fixtures_loaded(self) -> None:
        if self._fixtures is None:
            self.load_fixtures()

    def scorecard(self) -> dict[str, Any]:
        """Return the evaluation scorecard."""
        self._ensure_fixtures_loaded()
        category_scores = {name: m.to_dict() for name, m in self._categories.items()}

        all_metrics = list(self._categories.values())
        total_queries = sum(m.query_count for m in all_metrics)
        overall = {
            "total_queries": total_queries,
            "precision_at_5": round(sum(m.precision_at_5_sum for m in all_metrics) / total_queries, 4) if total_queries > 0 else 0.0,
            "recall_at_20": round(sum(m.recall_at_20_sum for m in all_metrics) / total_queries, 4) if total_queries > 0 else 0.0,
            "mrr": round(sum(m.mrr_sum for m in all_metrics) / total_queries, 4) if total_queries > 0 else 0.0,
            "ndcg_at_5": round(sum(m.ndcg_at_5_sum for m in all_metrics) / total_queries, 4) if total_queries > 0 else 0.0,
            "zero_result_rate": round(sum(m.zero_result_count for m in all_metrics) / total_queries, 4) if total_queries > 0 else 0.0,
            "tenant_isolation": round(sum(m.tenant_isolation_sum for m in all_metrics) / total_queries, 4) if total_queries > 0 else 1.0,
        }

        return {
            "version": self.version,
            "overall": overall,
            "by_category": category_scores,
            "per_query": self._results,
        }

    def save_scorecard(self, output_path: str) -> None:
        """Save scorecard to JSON file."""
        scorecard = self.scorecard()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(scorecard, f, indent=2)
        logger.info("[eval] Scorecard saved to %s", output_path)
