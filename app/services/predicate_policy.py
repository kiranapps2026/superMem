"""Predicate conflict policy — configuration for contradiction detection.

This module defines the rules for which predicate pairs can be compared
for contradictions. It is the foundation of the deterministic contradiction
detection layer (Phase 5).

The policy answers the question: "Are these two fact values actually
conflicting, or just representing different points in time?"

Key distinction:
  - `customer.status = active` vs. `inactive` → genuine conflict (mutually exclusive)
  - `customer.address = Hyderabad` vs. `Mumbai` → legitimate history (temporal, not exclusive)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class Cardinality(str, Enum):
    """How many values a predicate can hold simultaneously."""
    ONE = "ONE"          # Single value at any point in time
    MANY = "MANY"        # Multiple values can coexist


class TemporalStatus(str, Enum):
    """Whether a predicate's value can change over time legitimately."""
    YES = "YES"          # Value can change (e.g., address, status)
    NO = "NO"            # Value should be stable (e.g., date of birth)


class MutualExclusivity(str, Enum):
    """Whether two different values for the same predicate are mutually exclusive."""
    YES = "YES"          # Cannot have both values simultaneously
    NO = "NO"            # Different values can coexist (different times/contexts)


class ResolutionStrategy(str, Enum):
    """How to handle detected contradictions."""
    LATEST_WINS = "LATEST_WINS"        # Most recent fact takes precedence
    MANUAL_REVIEW = "MANUAL_REVIEW"    # Flag for human review
    BOTH_VALID = "BOTH_VALID"          # Both facts are valid (different contexts)
    SOURCE_PRIORITY = "SOURCE_PRIORITY" # Higher authority source wins


@dataclass
class PredicatePolicy:
    """Policy for a single predicate in contradiction detection.

    Attributes:
        predicate: The predicate name (e.g., "status", "address", "role")
        cardinality: ONE or MANY values at a point in time
        temporal: Whether values can change over time
        mutually_exclusive: Whether different values conflict
        inverse_predicates: List of predicates that are inverses
        resolution_strategy: Default strategy when conflict is detected
        description: Human-readable explanation
    """
    predicate: str
    cardinality: Cardinality = Cardinality.ONE
    temporal: TemporalStatus = TemporalStatus.NO
    mutually_exclusive: MutualExclusivity = MutualExclusivity.YES
    inverse_predicates: list[str] = field(default_factory=list)
    resolution_strategy: ResolutionStrategy = ResolutionStrategy.MANUAL_REVIEW
    description: str = ""


# ── Default Policy Registry ────────────────────────────────────────────────
# This is the out-of-the-box policy set. It can be extended via configuration
# without code changes in production.

DEFAULT_PREDICATE_POLICIES: dict[str, PredicatePolicy] = {
    # ── Entity attributes ──────────────────────────────────────────────────
    "name": PredicatePolicy(
        predicate="name",
        cardinality=Cardinality.ONE,
        temporal=TemporalStatus.NO,
        mutually_exclusive=MutualExclusivity.YES,
        resolution_strategy=ResolutionStrategy.LATEST_WINS,
        description="Entity name — changes are rare but possible (e.g., marriage)",
    ),
    "status": PredicatePolicy(
        predicate="status",
        cardinality=Cardinality.ONE,
        temporal=TemporalStatus.YES,
        mutually_exclusive=MutualExclusivity.YES,
        resolution_strategy=ResolutionStrategy.MANUAL_REVIEW,
        description="Status field — values change over time (active/inactive/pending)",
    ),
    "role": PredicatePolicy(
        predicate="role",
        cardinality=Cardinality.ONE,
        temporal=TemporalStatus.YES,
        mutually_exclusive=MutualExclusivity.YES,
        resolution_strategy=ResolutionStrategy.MANUAL_REVIEW,
        description="User/team role — changes with promotions/reassignments",
    ),
    "email": PredicatePolicy(
        predicate="email",
        cardinality=Cardinality.ONE,
        temporal=TemporalStatus.NO,
        mutually_exclusive=MutualExclusivity.YES,
        resolution_strategy=ResolutionStrategy.LATEST_WINS,
        description="Email address — stable but can be changed",
    ),

    # ── Temporal / location fields ─────────────────────────────────────────
    "address": PredicatePolicy(
        predicate="address",
        cardinality=Cardinality.ONE,
        temporal=TemporalStatus.YES,
        mutually_exclusive=MutualExclusivity.NO,
        resolution_strategy=ResolutionStrategy.BOTH_VALID,
        description="Physical address — changes over time, old values are not conflicts",
    ),
    "location": PredicatePolicy(
        predicate="location",
        cardinality=Cardinality.ONE,
        temporal=TemporalStatus.YES,
        mutually_exclusive=MutualExclusivity.NO,
        resolution_strategy=ResolutionStrategy.BOTH_VALID,
        description="Geographic location — changes over time, not a conflict",
    ),
    "phone": PredicatePolicy(
        predicate="phone",
        cardinality=Cardinality.ONE,
        temporal=TemporalStatus.YES,
        mutually_exclusive=MutualExclusivity.NO,
        resolution_strategy=ResolutionStrategy.BOTH_VALID,
        description="Phone number — changes over time",
    ),

    # ── Relationship fields ────────────────────────────────────────────────
    "reports_to": PredicatePolicy(
        predicate="reports_to",
        cardinality=Cardinality.ONE,
        temporal=TemporalStatus.YES,
        mutually_exclusive=MutualExclusivity.YES,
        resolution_strategy=ResolutionStrategy.MANUAL_REVIEW,
        description="Manager/reporting relationship — changes with org restructuring",
        inverse_predicates=["manages"],
    ),
    "manages": PredicatePolicy(
        predicate="manages",
        cardinality=Cardinality.MANY,
        temporal=TemporalStatus.YES,
        mutually_exclusive=MutualExclusivity.NO,
        resolution_strategy=ResolutionStrategy.BOTH_VALID,
        description="Direct reports — can manage multiple people",
        inverse_predicates=["reports_to"],
    ),
    "member_of": PredicatePolicy(
        predicate="member_of",
        cardinality=Cardinality.MANY,
        temporal=TemporalStatus.YES,
        mutually_exclusive=MutualExclusivity.NO,
        resolution_strategy=ResolutionStrategy.BOTH_VALID,
        description="Team/project membership — can belong to multiple groups",
    ),

    # ── Technical / config fields ──────────────────────────────────────────
    "version": PredicatePolicy(
        predicate="version",
        cardinality=Cardinality.ONE,
        temporal=TemporalStatus.YES,
        mutually_exclusive=MutualExclusivity.YES,
        resolution_strategy=ResolutionStrategy.LATEST_WINS,
        description="Software version — only one version at a time",
    ),
    "config": PredicatePolicy(
        predicate="config",
        cardinality=Cardinality.ONE,
        temporal=TemporalStatus.YES,
        mutually_exclusive=MutualExclusivity.NO,
        resolution_strategy=ResolutionStrategy.LATEST_WINS,
        description="Configuration value — changes over time, not a conflict",
    ),

    # ── Date / time fields ─────────────────────────────────────────────────
    "started_at": PredicatePolicy(
        predicate="started_at",
        cardinality=Cardinality.ONE,
        temporal=TemporalStatus.NO,
        mutually_exclusive=MutualExclusivity.NO,
        resolution_strategy=ResolutionStrategy.LATEST_WINS,
        description="Start date — stable, conflicts indicate data quality issue",
    ),
    "completed_at": PredicatePolicy(
        predicate="completed_at",
        cardinality=Cardinality.ONE,
        temporal=TemporalStatus.NO,
        mutually_exclusive=MutualExclusivity.NO,
        resolution_strategy=ResolutionStrategy.LATEST_WINS,
        description="Completion date — stable, conflicts indicate data quality issue",
    ),
}


# ── Policy Engine ──────────────────────────────────────────────────────────


class PredicatePolicyEngine:
    """Engine for looking up and evaluating predicate policies.

    Provides methods to:
    - Look up policy for a predicate
    - Check if two values for the same predicate conflict
    - Get the resolution strategy for a conflict

    The engine can be extended with custom policies at runtime.
    """

    def __init__(self, extra_policies: dict[str, PredicatePolicy] | None = None) -> None:
        self._policies: dict[str, PredicatePolicy] = dict(DEFAULT_PREDICATE_POLICIES)
        if extra_policies:
            self._policies.update(extra_policies)

    def get_policy(self, predicate: str) -> PredicatePolicy | None:
        """Get the policy for a predicate, or None if not defined.

        Unregistered predicates default to conservative behavior:
        - temporal=NO, mutually_exclusive=YES, resolution=MANUAL_REVIEW
        """
        return self._policies.get(predicate)

    def get_or_default(self, predicate: str) -> PredicatePolicy:
        """Get policy for a predicate, falling back to conservative defaults."""
        policy = self._policies.get(predicate)
        if policy is None:
            logger.debug("No policy for predicate '%s' — using conservative defaults", predicate)
            return PredicatePolicy(
                predicate=predicate,
                resolution_strategy=ResolutionStrategy.MANUAL_REVIEW,
            )
        return policy

    def is_temporal(self, predicate: str) -> bool:
        """Check if a predicate's value can change over time."""
        policy = self.get_or_default(predicate)
        return policy.temporal == TemporalStatus.YES

    def is_mutually_exclusive(self, predicate: str) -> bool:
        """Check if two different values for the same predicate are mutually exclusive."""
        policy = self.get_or_default(predicate)
        return policy.mutually_exclusive == MutualExclusivity.YES

    def would_conflict(
        self,
        predicate: str,
        temporal_status_a: str = "current",
        temporal_status_b: str = "current",
    ) -> bool:
        """Determine if two facts with the same predicate would be considered conflicting.

        Two facts conflict if:
        1. The predicate is mutually exclusive, AND
        2. Either fact is temporal=False, OR both are current/active

        If both facts are temporal (different points in time), they are NOT
        conflicting — they represent a value change, not a contradiction.
        """
        if not self.is_mutually_exclusive(predicate):
            return False

        # If both facts are temporal (historical), they're not conflicting
        if temporal_status_a != "current" and temporal_status_b != "current":
            return False

        # At least one is current, and predicate is mutually exclusive → conflict
        return True

    def get_resolution_strategy(self, predicate: str) -> ResolutionStrategy:
        """Get the resolution strategy for a predicate."""
        policy = self.get_or_default(predicate)
        return policy.resolution_strategy

    def get_inverse_predicates(self, predicate: str) -> list[str]:
        """Get predicates that are inverses of this one."""
        policy = self.get_or_default(predicate)
        return policy.inverse_predicates

    def register_policy(self, policy: PredicatePolicy) -> None:
        """Register or override a predicate policy at runtime."""
        self._policies[policy.predicate] = policy
        logger.debug("Registered policy for predicate '%s'", policy.predicate)

    @property
    def registered_predicates(self) -> list[str]:
        """List all registered predicate names."""
        return list(self._policies.keys())


# ── Singleton ──────────────────────────────────────────────────────────────


_policy_engine: PredicatePolicyEngine | None = None


def get_predicate_policy_engine(
    extra_policies: dict[str, PredicatePolicy] | None = None,
) -> PredicatePolicyEngine:
    """Get or create the global predicate policy engine singleton."""
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PredicatePolicyEngine(extra_policies=extra_policies)
    return _policy_engine


def reset_predicate_policy_engine() -> None:
    """Reset the singleton — for testing only."""
    global _policy_engine
    _policy_engine = None
