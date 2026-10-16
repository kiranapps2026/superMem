"""Phase 5: Deterministic contradiction detection.

Compares Facts and Decisions within a workspace to find value conflicts
gated by the predicate conflict policy. Runs as an async post-ingest job
— never inline in the M0-M4 pipeline.

Key design:
  - Idempotent via `contradiction_job_id` on MemoryContradiction
  - Unique constraint on (workspace_id, fact_a_id, fact_b_id) prevents duplicates
  - Temporal check before flagging: policy marks whether predicate changes are legitimate
  - All detections default to UNDER_REVIEW (never auto-resolved)
  - Runs behind FEATURE_CONTRADICTION_DETECTION_ENABLED flag
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, and_, func, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Fact, Decision, MemoryContradiction, ContradictionType, ContradictionStatus
from app.core.config import settings
from app.services.predicate_policy import (
    get_predicate_policy_engine,
    PredicatePolicyEngine,
    Cardinality,
    TemporalStatus,
    MutualExclusivity,
)

logger = logging.getLogger(__name__)


# ── Contradiction Detector ────────────────────────────────────────────────


class ContradictionDetector:
    """Detects contradictions between facts and decisions.

    Groups facts by (subject, predicate) and compares pairs within each
    group. Uses the predicate policy engine to determine if a difference
    constitutes a genuine contradiction or a legitimate temporal change.
    """

    def __init__(
        self,
        policy_engine: PredicatePolicyEngine | None = None,
        batch_size: int = 100,
    ) -> None:
        self.policy_engine = policy_engine or get_predicate_policy_engine()
        self.batch_size = batch_size

    async def detect_for_workspace(
        self,
        db: AsyncSession,
        workspace_id: str,
        job_id: str | None = None,
        agent_id: str | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        """Run contradiction detection for all facts/decisions in a workspace.

        Fetches data from the DB, then delegates to detect().
        Short-circuits immediately when the feature flag is disabled.

        Args:
            db: Database session
            workspace_id: Workspace to scan
            job_id: Optional job identifier for idempotency tracking
            agent_id: Agent that triggered this detection (provenance)
            run_id: Run that triggered this detection (provenance)

        Returns:
            Summary dict with counts of detected contradictions
        """
        # Gate 4: Feature flag — skip entirely when disabled
        if not getattr(settings, "feature_contradiction_detection_enabled", False):
            return {
                "job_id": job_id or str(uuid.uuid4()),
                "workspace_id": workspace_id,
                "status": "skipped",
                "reason": "feature_contradiction_detection_enabled is false",
                "facts_scanned": 0,
                "decisions_scanned": 0,
                "contradictions_found": 0,
                "skipped_existing": 0,
                "elapsed_ms": 0,
            }

        # Acquire advisory lock to prevent concurrent detection on the same workspace
        # Uses PostgreSQL advisory lock (non-blocking for other operations)
        lock_acquired = await self._acquire_workspace_lock(db, workspace_id)
        if not lock_acquired:
            return {
                "job_id": job_id or str(uuid.uuid4()),
                "workspace_id": workspace_id,
                "status": "skipped",
                "reason": "workspace already locked by another detection run",
                "facts_scanned": 0,
                "decisions_scanned": 0,
                "contradictions_found": 0,
                "skipped_existing": 0,
                "elapsed_ms": 0,
            }

        try:
            job_id = job_id or f"contradiction-{uuid.uuid4().hex[:8]}"
            facts = await self._fetch_facts(db, workspace_id)
            decisions = await self._fetch_decisions(db, workspace_id)
            result = await self.detect(
                workspace_id, facts, decisions, job_id,
                agent_id=agent_id, run_id=run_id,
                db=db,
            )
            result["status"] = "completed"
            return result
        finally:
            await self._release_workspace_lock(db, workspace_id)

    async def _acquire_workspace_lock(
        self, db: AsyncSession, workspace_id: str
    ) -> bool:
        """Acquire PostgreSQL advisory lock for workspace detection.

        Uses hashed workspace_id as lock key. Returns True if acquired,
        False if another worker holds the lock.
        """
        # Hash the workspace_id to a bigint for pg_advisory_lock
        # Use abs(hash) to ensure positive value for PostgreSQL
        lock_id = abs(hash(workspace_id)) % (2**31)
        try:
            result = await db.execute(
                text("SELECT pg_try_advisory_lock(:lock_id)"),
                {"lock_id": lock_id},
            )
            acquired = result.scalar_one()
            if not acquired:
                logger.info(
                    "Contradiction detection skipped: workspace=%s locked by another worker",
                    workspace_id,
                )
            return acquired
        except Exception as e:
            logger.warning(
                "Could not acquire advisory lock for workspace=%s: %s. "
                "Proceeding without lock (unique constraint still protects).",
                workspace_id, e,
            )
            return True  # Proceed even if lock fails (fallback to unique constraint)

    async def _release_workspace_lock(
        self, db: AsyncSession, workspace_id: str
    ) -> None:
        """Release PostgreSQL advisory lock for workspace."""
        lock_id = abs(hash(workspace_id)) % (2**31)
        try:
            await db.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"),
                {"lock_id": lock_id},
            )
        except Exception as e:
            logger.warning(
                "Could not release advisory lock for workspace=%s: %s",
                workspace_id, e,
            )

    async def detect(
        self,
        workspace_id: str,
        facts: list[Any],
        decisions: list[Any],
        job_id: str | None = None,
        agent_id: str | None = None,
        run_id: str | None = None,
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """Run contradiction detection on pre-fetched fact/decision lists.

        Pure analysis logic — writes to DB only when a session is provided.
        When db is None (test mode), counts contradictions without writing.

        Args:
            workspace_id: Workspace scope
            facts: List of Fact objects
            decisions: List of Decision objects
            job_id: Optional job identifier for idempotency tracking
            agent_id: Agent that triggered this detection (provenance)
            run_id: Run that triggered this detection (provenance)
            db: Optional DB session — when provided, contradictions are persisted

        Returns:
            Summary dict with counts of detected contradictions
        """
        job_id = job_id or str(uuid.uuid4())
        t0 = datetime.now(timezone.utc)

        logger.info(
            "Contradiction detection: workspace=%s, facts=%d, decisions=%d, job_id=%s",
            workspace_id, len(facts), len(decisions), job_id,
        )

        # Group by (subject, predicate) for efficient pair comparison
        fact_groups = self._group_by_subject_predicate(facts)
        decision_groups = self._group_by_subject_predicate(decisions)

        contradictions_found = 0
        skipped_existing = 0

        # Process fact groups
        for (subject, predicate), group_facts in fact_groups.items():
            if len(group_facts) < 2:
                continue
            pairs = self._generate_pairs(group_facts)
            for fact_a, fact_b in pairs:
                if db is not None:
                    if await self._is_contradiction(
                        db, workspace_id, fact_a, fact_b, job_id,
                        agent_id=agent_id, run_id=run_id,
                    ):
                        contradictions_found += 1
                    else:
                        skipped_existing += 1
                else:
                    if self._check_contradiction(fact_a, fact_b):
                        contradictions_found += 1
                    else:
                        skipped_existing += 1

        # Process decision groups
        for (subject, predicate), group_decs in decision_groups.items():
            if len(group_decs) < 2:
                continue
            pairs = self._generate_pairs(group_decs)
            for dec_a, dec_b in pairs:
                if db is not None:
                    if await self._is_contradiction(
                        db, workspace_id, dec_a, dec_b, job_id,
                        agent_id=agent_id, run_id=run_id,
                    ):
                        contradictions_found += 1
                    else:
                        skipped_existing += 1
                else:
                    if self._check_contradiction(dec_a, dec_b):
                        contradictions_found += 1
                    else:
                        skipped_existing += 1

        elapsed_ms = int((datetime.now(timezone.utc) - t0).total_seconds() * 1000)

        logger.info(
            "Contradiction detection complete: workspace=%s, found=%d, skipped=%d, elapsed=%dms",
            workspace_id, contradictions_found, skipped_existing, elapsed_ms,
        )

        return {
            "job_id": job_id,
            "workspace_id": workspace_id,
            "facts_scanned": len(facts),
            "decisions_scanned": len(decisions),
            "contradictions_found": contradictions_found,
            "skipped_existing": skipped_existing,
            "elapsed_ms": elapsed_ms,
        }

    async def _fetch_facts(self, db: AsyncSession, workspace_id: str) -> list[Fact]:
        """Fetch all non-deleted facts for a workspace."""
        stmt = (
            select(Fact)
            .where(
                Fact.workspace_id == workspace_id,
                Fact.deleted_at.is_(None),
                Fact.status == "active",
            )
            .order_by(Fact.subject, Fact.predicate, Fact.created_at)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def _fetch_decisions(self, db: AsyncSession, workspace_id: str) -> list[Decision]:
        """Fetch all non-deleted decisions for a workspace."""
        stmt = (
            select(Decision)
            .where(
                Decision.workspace_id == workspace_id,
                Decision.deleted_at.is_(None),
                Decision.status == "active",
            )
            .order_by(Decision.content, Decision.created_at)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    def _group_by_subject_predicate(
        self, items: list[Any]
    ) -> dict[tuple[str, str], list[Any]]:
        """Group items by (subject, predicate).

        Facts use their actual subject+predicate.
        Decisions (which lack subject/predicate) are all grouped under a
        single key so every decision in the workspace is compared against
        every other decision.
        """
        groups: dict[tuple[str, str], list[Any]] = {}
        for item in items:
            if hasattr(item, "subject") and item.subject:
                key = (item.subject, item.predicate or "unknown")
            else:
                # Decisions: group all together for cross-comparison
                key = ("__all_decisions__", "decision")
            groups.setdefault(key, []).append(item)
        return groups

    def _generate_pairs(self, items: list[Any]) -> list[tuple[Any, Any]]:
        """Generate all unique pairs from a list of items."""
        pairs = []
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                pairs.append((items[i], items[j]))
        return pairs

    async def _is_contradiction(
        self,
        db: AsyncSession,
        workspace_id: str,
        item_a: Any,
        item_b: Any,
        job_id: str,
        agent_id: str | None = None,
        run_id: str | None = None,
    ) -> bool:
        """Check if two items constitute a contradiction and create a DB record.

        Returns True if a contradiction was found and recorded, False otherwise.
        Delegates to _check_contradiction() for the pure logic.
        """
        if not self._check_contradiction(item_a, item_b):
            return False

        # Determine contradiction type and metadata
        predicate = getattr(item_a, "predicate", None) or getattr(item_b, "predicate", "unknown")
        value_a = getattr(item_a, "object", None) or getattr(item_a, "content", "")
        value_b = getattr(item_b, "object", None) or getattr(item_b, "content", "")
        temporal_status_a = getattr(item_a, "temporal_status", "current")
        temporal_status_b = getattr(item_b, "temporal_status", "current")
        policy = self.policy_engine.get_or_default(predicate)
        contradiction_type = self._determine_type(item_a, item_b, policy)

        # Create the contradiction record (idempotent via unique constraint)
        try:
            contradiction = MemoryContradiction(
                workspace_id=workspace_id,
                fact_a_id=getattr(item_a, "id", str(item_a)),
                fact_b_id=getattr(item_b, "id", str(item_b)),
                detected_by_agent_id=agent_id,
                detected_by_run_id=run_id,
                contradiction_type=contradiction_type.value,
                confidence=min(
                    getattr(item_a, "confidence", 1.0),
                    getattr(item_b, "confidence", 1.0),
                ),
                status=ContradictionStatus.UNDER_REVIEW.value,
                metadata={
                    "job_id": job_id,
                    "predicate": predicate,
                    "value_a": value_a[:500],
                    "value_b": value_b[:500],
                    "temporal_status_a": temporal_status_a,
                    "temporal_status_b": temporal_status_b,
                    "resolution_strategy": policy.resolution_strategy.value,
                },
            )
            db.add(contradiction)
            await db.flush()
        except Exception:
            await db.rollback()
            return False

        logger.debug(
            "Contradiction detected: workspace=%s, type=%s, pair=(%s, %s)",
            workspace_id, contradiction_type.value,
            getattr(item_a, "id", "?"), getattr(item_b, "id", "?"),
        )
        return True

    def _check_contradiction(self, item_a: Any, item_b: Any) -> bool:
        """Pure logic: determine if two items would be a contradiction.

        No DB access, no side effects. Used by detect() for pure analysis
        and by _is_contradiction() before writing to DB.
        """
        # Skip if values are identical
        value_a = getattr(item_a, "object", None) or getattr(item_a, "content", "")
        value_b = getattr(item_b, "object", None) or getattr(item_b, "content", "")
        if value_a == value_b:
            return False

        # Determine the predicate to check
        predicate = getattr(item_a, "predicate", None) or getattr(item_b, "predicate", "unknown")

        # Get the policy for this predicate
        policy = self.policy_engine.get_or_default(predicate)
        temporal_status_a = getattr(item_a, "temporal_status", "current")
        temporal_status_b = getattr(item_b, "temporal_status", "current")

        # Check if the predicate policy says these values are mutually exclusive
        if policy.mutually_exclusive != MutualExclusivity.YES:
            return False

        # Check temporal: if both facts are historical (not current), they're
        # value changes over time, not contradictions
        if temporal_status_a != "current" and temporal_status_b != "current":
            return False

        return True

    def _determine_type(
        self,
        item_a: Any,
        item_b: Any,
        policy: Any,
    ) -> ContradictionType:
        """Determine the specific type of contradiction."""
        # Check for direct negation (one value is the opposite of the other)
        val_a = str(getattr(item_a, "object", getattr(item_a, "content", ""))).lower()
        val_b = str(getattr(item_b, "object", getattr(item_b, "content", ""))).lower()

        negations = [
            ("active", "inactive"), ("enabled", "disabled"), ("true", "false"),
            ("yes", "no"), ("on", "off"), ("approved", "rejected"),
        ]
        for pos, neg in negations:
            if (pos in val_a and neg in val_b) or (neg in val_a and pos in val_b):
                return ContradictionType.DIRECT_NEGATION

        # Check for source conflict (different sources, same value — suspicious)
        source_a = getattr(item_a, "source_id", None)
        source_b = getattr(item_b, "source_id", None)
        if source_a and source_b and source_a != source_b:
            return ContradictionType.SOURCE_CONFLICT

        # Check for temporal conflict (same subject/predicate, different values, different times)
        created_a = getattr(item_a, "created_at", None)
        created_b = getattr(item_b, "created_at", None)
        if created_a and created_b and created_a != created_b:
            return ContradictionType.TEMPORAL_CONFLICT

        # Default: value conflict
        return ContradictionType.VALUE_CONFLICT


# ── Async Job Runner ──────────────────────────────────────────────────────


class ContradictionJobRunner:
    """Runs contradiction detection asynchronously, idempotently.

    Designed to be called from a background task or Celery/RQ worker.
    Never runs inline in the M0-M4 pipeline.
    """

    def __init__(self, detector: ContradictionDetector | None = None) -> None:
        self.detector = detector or ContradictionDetector()

    async def run(
        self,
        db: AsyncSession,
        workspace_id: str,
        job_id: str | None = None,
    ) -> dict[str, Any]:
        """Run contradiction detection for a workspace.

        Args:
            db: Database session
            workspace_id: Workspace to scan
            job_id: Optional job ID for tracking

        Returns:
            Summary of the run
        """
        job_id = job_id or f"contradiction-{uuid.uuid4().hex[:8]}"

        logger.info("Contradiction job started: workspace=%s, job_id=%s", workspace_id, job_id)

        result = await self.detector.detect_for_workspace(db, workspace_id, job_id)

        logger.info(
            "Contradiction job complete: workspace=%s, found=%d, job_id=%s",
            workspace_id, result["contradictions_found"], job_id,
        )
        return result

    async def run_batch(
        self,
        db: AsyncSession,
        workspace_ids: list[str],
        base_job_id: str | None = None,
    ) -> dict[str, Any]:
        """Run contradiction detection for multiple workspaces.

        Each workspace gets its own sub-job ID for granular tracking.
        """
        base_job_id = base_job_id or f"contradiction-batch-{uuid.uuid4().hex[:8]}"
        results = []

        for ws_id in workspace_ids:
            job_id = f"{base_job_id}-{ws_id[:8]}"
            try:
                result = await self.run(db, ws_id, job_id)
                results.append(result)
            except Exception as e:
                logger.error(
                    "Contradiction job failed for workspace %s: %s", ws_id, e
                )
                results.append({
                    "job_id": job_id,
                    "workspace_id": ws_id,
                    "error": str(e),
                })

        return {
            "batch_job_id": base_job_id,
            "workspaces_processed": len(workspace_ids),
            "results": results,
            "total_contradictions": sum(r.get("contradictions_found", 0) for r in results),
        }


# ── Singletons ────────────────────────────────────────────────────────────


_detector: ContradictionDetector | None = None
_runner: ContradictionJobRunner | None = None


def get_contradiction_detector() -> ContradictionDetector:
    """Get or create the global contradiction detector."""
    global _detector
    if _detector is None:
        _detector = ContradictionDetector()
    return _detector


def get_contradiction_runner() -> ContradictionJobRunner:
    """Get or create the global contradiction job runner."""
    global _runner
    if _runner is None:
        _runner = ContradictionJobRunner()
    return _runner
