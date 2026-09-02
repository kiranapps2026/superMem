"""Policy repository — database-backed policy storage.

Reads policies from PostgreSQL (policies + policy_versions tables).
Returns empty list when DB is unavailable (fail-closed: no policies = no access).
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class PolicyRepository:
    """Load active policy rules from PostgreSQL.

    Returns a list of policy dicts, each containing:
      - policy_id
      - name
      - tenant_id
      - policy_version
      - rules: list of rule dicts
    """

    def __init__(self, db: AsyncSession | None = None):
        self._db = db
        self._cache: dict[str, list[dict[str, Any]]] = {}
        self._cache_ts: float = 0.0

    async def load_active_policies(self, tenant_id: str | None = None) -> list[dict[str, Any]]:
        """Load all active policies, optionally filtered by tenant.

        Returns an empty list (deny-all) if the DB is unavailable.
        Fail-closed: no policies = no access.
        """
        if self._db is None:
            return []

        try:
            from app.models import Policy, PolicyVersion
            stmt = (
                select(Policy, PolicyVersion)
                .join(PolicyVersion, Policy.current_version == PolicyVersion.version)
                .where(Policy.status == "active", PolicyVersion.status == "active")
            )
            if tenant_id:
                stmt = stmt.where(Policy.tenant_id == tenant_id)
            stmt = stmt.order_by(Policy.created_at)

            result = await self._db.execute(stmt)
            rows = result.all()

            policies: list[dict[str, Any]] = []
            for policy, version in rows:
                policies.append({
                    "policy_id": str(policy.id),
                    "name": policy.name,
                    "tenant_id": str(policy.tenant_id),
                    "policy_version": version.version,
                    "rules": version.rules if isinstance(version.rules, list) else [],
                })
            return policies

        except Exception as exc:
            logger.error("[policy] FAIL-CLOSED: DB unavailable, returning empty policies: %s", exc)
            return []

    async def load_policy(self, policy_id: str) -> dict | None:
        """Load a single policy by ID. Returns None if unavailable (fail-closed)."""
        if self._db is None:
            return None

        try:
            from app.models import Policy, PolicyVersion
            stmt = (
                select(Policy, PolicyVersion)
                .join(PolicyVersion, Policy.current_version == PolicyVersion.version)
                .where(Policy.id == policy_id, Policy.status == "active")
            )
            result = await self._db.execute(stmt)
            row = result.first()
            if row is None:
                return None
            policy, version = row
            return {
                "policy_id": str(policy.id),
                "name": policy.name,
                "tenant_id": str(policy.tenant_id),
                "policy_version": version.version,
                "rules": version.rules if isinstance(version.rules, list) else [],
            }
        except Exception as exc:
            logger.error("[policy] FAIL-CLOSED: DB unavailable for policy %s: %s", policy_id, exc)
            return None

    async def save_policy(self, policy: dict[str, Any]) -> bool:
        """Persist a new policy + first version. Returns True on success."""
        if self._db is None:
            return False

        try:
            from app.models import Policy, PolicyVersion
            p = Policy(
                id=policy["policy_id"],
                tenant_id=policy["tenant_id"],
                name=policy["name"],
                description=policy.get("description"),
                status="active",
                current_version=1,
                created_by=policy.get("created_by"),
            )
            v = PolicyVersion(
                policy_id=p.id,
                version=1,
                rules=policy.get("rules", []),
                status="active",
                created_by=policy.get("created_by"),
            )
            self._db.add(p)
            self._db.add(v)
            await self._db.flush()
            return True
        except Exception as exc:
            logger.warning("[policy] failed to save policy: %s", exc)
            return False


__all__ = ["PolicyRepository"]
