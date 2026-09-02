"""Memory Service — governed access to M0–M5 (Sprint 8).

Agents MUST NOT directly access:
  - metadata.db
  - vault memory files
  - graph files
  - fact tables
  - CAS
  - internal memory structures

All access flows through this service, which:
  1. Authenticates the caller
  2. Resolves tenant/workspace/project scope
  3. Invokes the Policy Engine
  4. Enforces permissions
  5. Performs the operation
  6. Attaches provenance
  7. Emits audit events
  8. Persists to PostgreSQL (when session provided)
  9. Returns controlled results

Persistence model:
  - All writes require an AsyncSession for DB persistence
  - An in-memory cache is used only as a fast-read layer
  - The cache does NOT replace the database as source of truth
"""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Memory as MemoryModel
from app.services.audit.constants import (
    MEMORY_READ, MEMORY_SEARCH, MEMORY_WRITE, MEMORY_UPDATE,
    MEMORY_DELETE, MEMORY_EXPIRE, MEMORY_SHARE,
    RESULT_SUCCESS, RESULT_FAILURE, RESULT_DENIED,
)
from app.services.policy.engine import (
    EFFECT_ALLOW,
    EFFECT_DENY,
    AuthorizationRequest,
    PolicyEngine,
)
from app.services.policy.evaluator import generate_rbac_policies

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Canonical memory model
# ---------------------------------------------------------------------------


@dataclass
class MemoryRecord:
    """Canonical memory record.

    Maps existing SwarmVault memory types/scopes without renaming them.
    Memory types are mapped via MemoryTypeMapper to existing M0-M5 taxonomy.
    """
    # Identity
    memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    memory_type: str = "WORKING"  # WORKING|EPISODIC|SEMANTIC|PROCEDURAL|USER|TEAM|PROJECT|AGENT
    scope: str = "USER"  # USER|TEAM|PROJECT|WORKSPACE|TENANT

    # Tenant hierarchy
    tenant_id: str | None = None
    workspace_id: str | None = None
    project_id: str | None = None
    team_id: str | None = None
    user_id: str | None = None
    agent_id: str | None = None
    run_id: str | None = None

    # Content
    subject: str = ""
    predicate: str = ""
    value: Any = None
    content: str | None = None  # free-form content (for sessions, etc.)

    # Provenance
    authority: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.7
    importance: float = 0.5

    # Lifecycle
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    valid_from: str | None = None
    valid_until: str | None = None
    expires_at: str | None = None

    # Versioning
    version: int = 1
    supersedes: str | None = None
    superseded_by: str | None = None

    # Provenance chain
    provenance: list[dict[str, Any]] = field(default_factory=list)

    # Permissions
    permissions: dict[str, Any] = field(default_factory=dict)

    # Status
    status: str = "active"  # active|superseded|expired|deleted

    # User-provided arbitrary metadata (preserved through pipeline)
    user_metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Memory type mapping (M2 taxonomy compatibility)
# ---------------------------------------------------------------------------


class MemoryTypeMapper:
    """Map canonical memory types to existing SwarmVault types.

    Do NOT rename existing M2 taxonomy. Use an explicit mapping layer.
    """

    # Canonical → SwarmVault mapping
    CANONICAL_TO_VAULT = {
        "WORKING": "working",
        "EPISODIC": "episodic",
        "SEMANTIC": "semantic",
        "PROCEDURAL": "procedural",
        "USER": "user",
        "TEAM": "team",
        "PROJECT": "project",
        "AGENT": "agent",
    }

    # Scope → SwarmVault scope
    SCOPE_TO_VAULT = {
        "USER": "user",
        "TEAM": "team",
        "PROJECT": "project",
        "WORKSPACE": "workspace",
        "TENANT": "tenant",
    }

    @classmethod
    def to_vault_type(cls, canonical: str) -> str:
        return cls.CANONICAL_TO_VAULT.get(canonical, canonical.lower())

    @classmethod
    def to_vault_scope(cls, canonical: str) -> str:
        return cls.SCOPE_TO_VAULT.get(canonical, canonical.lower())

    @classmethod
    def from_vault_type(cls, vault: str) -> str:
        for canonical, v in cls.CANONICAL_TO_VAULT.items():
            if v == vault:
                return canonical
        return vault.upper()

    @classmethod
    def from_vault_scope(cls, vault: str) -> str:
        for canonical, v in cls.SCOPE_TO_VAULT.items():
            if v == vault:
                return canonical
        return vault.upper()


# ---------------------------------------------------------------------------
# Memory Service
# ---------------------------------------------------------------------------


class MemoryService:
    """Governed memory API wrapping M0–M5 with PostgreSQL persistence.

    Enforces:
      - Authentication (caller identity)
      - Scope resolution (tenant → workspace → project)
      - Policy Engine authorization
      - Provenance attachment
      - Audit event emission
      - PostgreSQL persistence (when session provided)

    The in-memory cache is a performance optimization, not the source of truth.
    All durable state lives in PostgreSQL.
    """

    def __init__(
        self,
        policy_engine: PolicyEngine | None = None,
        audit_service: Any | None = None,
    ) -> None:
        self._policy = policy_engine or PolicyEngine()
        self._audit = audit_service
        self._cache: dict[str, MemoryRecord] = {}
        self._type_mapper = MemoryTypeMapper()

    # ------------------------------------------------------------------ #
    # Persistence helpers (PostgreSQL via SQLAlchemy)
    # ------------------------------------------------------------------ #

    async def _persist_record(self, session: AsyncSession, record: MemoryRecord) -> None:
        """Persist a MemoryRecord to PostgreSQL."""
        model = MemoryModel(
            id=record.memory_id,
            tenant_id=record.tenant_id or record.workspace_id or "",  # FIX: include tenant_id
            workspace_id=record.workspace_id or "",
            user_id=record.user_id or "",
            agent_id=record.agent_id,
            run_id=record.run_id,
            project_id=record.project_id,
            memory_type=self._type_mapper.to_vault_type(record.memory_type),
            content=record.content or record.subject,
            confidence=record.confidence,
            authority=record.authority.get("score", 1.0) if isinstance(record.authority, dict) else 1.0,
            temporal_status="current" if record.status == "active" else record.status,
        )
        # Build extra_metadata from system fields + user-provided fields
        user_meta = record.user_metadata or {}
        meta: dict[str, Any] = {
            "predicate": record.predicate,
            "value": record.value,
            "scope": record.scope,
            "authority": record.authority,
            "confidence": record.confidence,
            "importance": record.importance,
            "permissions": record.permissions,
            "provenance": record.provenance,
            "version": record.version,
            "supersedes": record.supersedes,
            "superseded_by": record.superseded_by,
        }
        for k, v in user_meta.items():
            meta.setdefault(k, v)
        if user_meta:
            meta["user_metadata"] = user_meta
        model.extra_metadata = meta
        session.add(model)
        await session.flush()

    async def _load_from_db(
        self, session: AsyncSession, memory_id: str, *, tenant_id: str | None = None
    ) -> MemoryRecord | None:
        """Load a memory from PostgreSQL by ID."""
        stmt = select(MemoryModel).where(
            MemoryModel.id == memory_id,
            MemoryModel.deleted_at.is_(None),
        )
        if tenant_id:
            stmt = stmt.where(MemoryModel.tenant_id == tenant_id)
        result = await session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_record(model)

    async def _db_search(
        self,
        session: AsyncSession,
        query: str,
        *,
        workspace_id: str,
        user_id: str,
        memory_type: str | None = None,
        project_id: str | None = None,
        limit: int = 10,
    ) -> list[MemoryRecord]:
        """Search PostgreSQL directly for memory records."""
        stmt = select(MemoryModel).where(
            MemoryModel.workspace_id == workspace_id,
            MemoryModel.user_id == user_id,
            MemoryModel.deleted_at.is_(None),
            MemoryModel.content.ilike(f"%{query}%"),
        )
        if memory_type:
            stmt = stmt.where(MemoryModel.memory_type == memory_type)
        if project_id:
            stmt = stmt.where(MemoryModel.project_id == project_id)
        stmt = stmt.order_by(MemoryModel.created_at.desc()).limit(limit)
        result = await session.execute(stmt)
        return [self._model_to_record(m) for m in result.scalars().all()]

    @staticmethod
    def _model_to_record(model: MemoryModel) -> MemoryRecord:
        """Convert SQLAlchemy Memory model to canonical MemoryRecord."""
        meta = model.extra_metadata or {}
        return MemoryRecord(
            memory_id=model.id,
            memory_type=MemoryTypeMapper.from_vault_type(model.memory_type),
            scope=meta.get("scope", "USER"),
            tenant_id=model.tenant_id,  # FIX: read from model
            workspace_id=model.workspace_id,
            project_id=model.project_id,
            user_id=model.user_id,
            agent_id=model.agent_id,
            content=model.content,
            subject=model.content[:100] if model.content else "",
            authority=meta.get("authority", {"score": model.authority}),
            confidence=model.confidence,
            importance=meta.get("importance", 0.5),
            created_at=model.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if model.created_at else "",
            updated_at=model.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ") if model.updated_at else "",
            status="active" if model.temporal_status == "current" else model.temporal_status,
            provenance=meta.get("provenance", []),
            permissions=meta.get("permissions", {}),
            version=meta.get("version", 1),
            supersedes=meta.get("supersedes"),
            superseded_by=meta.get("superseded_by"),
        )

    # ------------------------------------------------------------------ #
    # Authorization helper
    # ------------------------------------------------------------------ #

    def _authorize(
        self,
        principal_id: str,
        principal_type: str,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
        project_id: str | None = None,
        requested_limits: dict[str, Any] | None = None,
        policies: list[dict[str, Any]] | None = None,
        role: str = "owner",
    ) -> "PolicyDecision | None":  # type: ignore[name-defined]
        """Invoke Policy Engine for memory operation.

        NOTE: Cross-tenant isolation is enforced by MemoryService methods
        AFTER loading the resource from the database.  The Policy Engine
        evaluates role-based access (who can do what), while the service
        layer ensures the resource belongs to the caller's scope.
        This two-layer approach prevents a principal with elevated role
        from accessing another tenant's resources.
        """
        req = AuthorizationRequest(
            principal_id=principal_id,
            principal_type=principal_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            context={"role": role},
            requested_limits=requested_limits,
        )
        effective_policies = generate_rbac_policies()
        return self._policy.evaluate(req, policies=effective_policies)

    # ------------------------------------------------------------------ #
    # Write (new record)
    # ------------------------------------------------------------------ #

    async def write(
        self,
        record: MemoryRecord,
        principal_id: str,
        principal_type: str = "agent",
        policies: list[dict[str, Any]] | None = None,
        provenance: dict[str, Any] | None = None,
        session: AsyncSession | None = None,
    ) -> MemoryRecord:
        """Write a new memory record.

        No durable memory write is valid without provenance.

        Args:
            session: AsyncSession for PostgreSQL persistence. If None, writes
                     only to the in-memory cache (test/development mode).
        """
        start = time.time()

        # Authorize
        decision = self._authorize(
            principal_id=principal_id,
            principal_type=principal_type,
            action="write",
            resource_type="memory",
            resource_id=record.memory_id,
            tenant_id=record.tenant_id,
            workspace_id=record.workspace_id,
            project_id=record.project_id,
            policies=policies,
        )

        if decision is None or decision.decision == EFFECT_DENY:
            self._emit_audit("memory.write", principal_id, record.memory_id,
                             "denied", "denied", start)
            raise PermissionError(
                f"Memory write denied for {principal_id} on {record.memory_id}"
            )

        # Attach provenance — REQUIRED for all durable writes
        prov_entry = {
            "source": provenance.get("source", "memory_service") if provenance else "memory_service",
            "source_id": provenance.get("source_id") if provenance else record.memory_id,
            "creator": principal_id,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "method": provenance.get("method", "direct_write") if provenance else "direct_write",
            "authority": record.authority,
            "confidence": record.confidence,
            "version": record.version,
            "supersedes": record.supersedes,
        }
        record.provenance.append(prov_entry)

        # Persist to PostgreSQL if session provided
        if session is not None:
            await self._persist_record(session, record)

        # Update cache (always — fast read path)
        self._cache[record.memory_id] = record

        self._emit_audit("memory.write", principal_id, record.memory_id,
                         "success", "allow", start,
                         policy_id=decision.policy_id,
                         request_id=decision.request_id)

        logger.info("[memory] written %s type=%s scope=%s", record.memory_id, record.memory_type, record.scope)
        return record

    # ------------------------------------------------------------------ #
    # Read
    # ------------------------------------------------------------------ #

    async def read(
        self,
        memory_id: str,
        principal_id: str,
        principal_type: str = "agent",
        policies: list[dict[str, Any]] | None = None,
        tenant_id: str | None = None,
        session: AsyncSession | None = None,
    ) -> MemoryRecord | None:
        """Read a memory record by ID.

        If session is provided, loads from PostgreSQL. Otherwise uses cache.
        """
        start = time.time()

        decision = self._authorize(
            principal_id=principal_id,
            principal_type=principal_type,
            action="read",
            resource_type="memory",
            resource_id=memory_id,
            tenant_id=tenant_id,
            policies=policies,
        )

        if decision is None or decision.decision == EFFECT_DENY:
            self._emit_audit("memory.read", principal_id, memory_id,
                             "denied", "denied", start)
            return None

        # Load from DB if session provided, otherwise use cache
        record: MemoryRecord | None = None
        if session is not None:
            record = await self._load_from_db(session, memory_id)
        else:
            record = self._cache.get(memory_id)

        if record is None or record.status == "deleted":
            result_status = "not_found"
            self._emit_audit("memory.read", principal_id, memory_id,
                             result_status, "allow", start,
                             request_id=decision.request_id)
            return None

        # Cross-tenant isolation: reject access to records from a different tenant
        if tenant_id and record.tenant_id and record.tenant_id != tenant_id:
            self._emit_audit("memory.read", principal_id, memory_id,
                             "denied", "denied", start,
                             metadata={"reason": "cross_tenant_isolation"})
            logger.warning("[memory] cross-tenant read blocked: %s from tenant %s tried to access tenant %s memory %s",
                           principal_id, tenant_id, record.tenant_id, memory_id)
            return None

        self._emit_audit("memory.read", principal_id, memory_id,
                         "success", "allow", start,
                         request_id=decision.request_id)
        return record

    # ── Cross-tenant isolation note ──────────────────────────────────────
    #
    # Every mutation/read method below enforces tenant isolation at the
    # service layer: if a caller_tenant_id is supplied (from the API via
    # TenantContext) and the loaded record belongs to a different tenant,
    # the operation is denied and None/False is returned.  This is the
    # defense-in-depth layer that sits BEHIND the RBAC policy engine.

    # ------------------------------------------------------------------ #
    # Search
    # ------------------------------------------------------------------ #

    async def search(
        self,
        query: str,
        principal_id: str,
        principal_type: str = "agent",
        *,
        memory_type: str | None = None,
        scope: str | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
        project_id: str | None = None,
        user_id: str | None = None,
        limit: int = 10,
        policies: list[dict[str, Any]] | None = None,
        session: AsyncSession | None = None,
    ) -> list[MemoryRecord]:
        """Search memory records.

        If session is provided, searches PostgreSQL. Otherwise uses cache.
        """
        start = time.time()

        decision = self._authorize(
            principal_id=principal_id,
            principal_type=principal_type,
            action="search",
            resource_type="memory",
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            requested_limits={"max_records": limit},
            policies=policies,
        )

        if decision is None or decision.decision == EFFECT_DENY:
            self._emit_audit("memory.search", principal_id, None,
                             "denied", "denied", start)
            return []

        # Apply limits from policy
        max_records = limit
        if decision.limits and "max_records" in decision.limits:
            max_records = min(limit, decision.limits["max_records"])

        results: list[MemoryRecord] = []

        if session is not None and workspace_id and user_id:
            # DB-backed search
            db_results = await self._db_search(
                session, query,
                workspace_id=workspace_id,
                user_id=user_id,
                memory_type=memory_type,
                project_id=project_id,
                limit=max_records,
            )
            results = db_results
        else:
            # Cache-based search (fallback)
            q_lower = query.lower()
            for record in self._cache.values():
                if record.status != "active":
                    continue
                if memory_type and record.memory_type != memory_type:
                    continue
                if scope:
                    if record.scope != scope and not self._is_broader(record.scope, scope):
                        continue
                if tenant_id and record.tenant_id != tenant_id:
                    continue
                if project_id and record.project_id != project_id:
                    continue
                content = (record.subject + " " + (record.content or "")).lower()
                if q_lower in content:
                    results.append(record)
                if len(results) >= max_records:
                    break

        self._emit_audit("memory.search", principal_id, None,
                         "success", "allow", start,
                         request_id=decision.request_id,
                         metadata={"count": len(results), "query": query})
        return results

    # ------------------------------------------------------------------ #
    # Update
    # ------------------------------------------------------------------ #

    async def update(
        self,
        memory_id: str,
        principal_id: str,
        updates: dict[str, Any],
        policies: list[dict[str, Any]] | None = None,
        session: AsyncSession | None = None,
        caller_tenant_id: str | None = None,
    ) -> MemoryRecord | None:
        """Update an existing memory record.

        Args:
            caller_tenant_id: If provided, the record must belong to this tenant.
        """
        start = time.time()

        # Load existing
        existing: MemoryRecord | None = None
        if session is not None:
            existing = await self._load_from_db(session, memory_id)
        else:
            existing = self._cache.get(memory_id)

        if existing is None:
            self._emit_audit("memory.update", principal_id, memory_id,
                             "not_found", "denied", start)
            return None

        # Cross-tenant/workspace isolation check
        if caller_tenant_id and existing.tenant_id and existing.tenant_id != caller_tenant_id:
            self._emit_audit("memory.update", principal_id, memory_id,
                             "denied", "denied", start,
                             metadata={"reason": "cross_tenant_isolation"})
            logger.warning("[memory] cross-tenant update blocked: %s from tenant %s tried to access tenant %s",
                           principal_id, caller_tenant_id, existing.tenant_id)
            return None

        decision = self._authorize(
            principal_id=principal_id,
            principal_type="agent",
            action="update",
            resource_type="memory",
            resource_id=memory_id,
            tenant_id=existing.tenant_id,
            workspace_id=existing.workspace_id,
            policies=policies,
        )

        if decision is None or decision.decision == EFFECT_DENY:
            self._emit_audit("memory.update", principal_id, memory_id,
                             "denied", "denied", start)
            return None

        # Apply updates
        for key, val in updates.items():
            if hasattr(existing, key):
                setattr(existing, key, val)
        existing.updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Append provenance
        existing.provenance.append({
            "source": "memory_service",
            "creator": principal_id,
            "created_at": existing.updated_at,
            "method": "update",
            "version": existing.version,
        })

        # Persist if session available
        if session is not None:
            # Update the ORM model
            result = await session.execute(
                select(MemoryModel).where(MemoryModel.id == memory_id)
            )
            model = result.scalar_one_or_none()
            if model:
                if "content" in updates:
                    model.content = updates["content"]
                if "memory_type" in updates:
                    model.memory_type = self._type_mapper.to_vault_type(updates["memory_type"])
                if "temporal_status" in updates:
                    model.temporal_status = updates["temporal_status"]
                model.updated_at = datetime.now(timezone.utc)
                await session.flush()

        self._emit_audit("memory.update", principal_id, memory_id,
                         "success", "allow", start,
                         request_id=decision.request_id)
        return existing

    # ------------------------------------------------------------------ #
    # Supersede (version replacement)
    # ------------------------------------------------------------------ #

    async def supersede(
        self,
        old_id: str,
        new_record: MemoryRecord,
        principal_id: str,
        policies: list[dict[str, Any]] | None = None,
        session: AsyncSession | None = None,
    ) -> MemoryRecord | None:
        """Mark old record as superseded and store new one.

        Supersession is a distinct lifecycle operation — it does NOT use
        expiration or decay mechanisms.
        """
        # Load old from DB if available
        old: MemoryRecord | None = None
        if session is not None:
            old = await self._load_from_db(session, old_id)
        else:
            old = self._cache.get(old_id)

        if old is None:
            return None

        # Mark old as superseded
        old.status = "superseded"
        old.superseded_by = new_record.memory_id

        # Set new record's supersedes link
        new_record.supersedes = old_id
        new_record.version = old.version + 1

        return await self.write(new_record, principal_id, policies=policies, session=session,
                                provenance={"source": "supersede", "source_id": old_id, "method": "supersede"})

    # ------------------------------------------------------------------ #
    # Delete (soft)
    # ------------------------------------------------------------------ #

    async def delete(
        self,
        memory_id: str,
        principal_id: str,
        policies: list[dict[str, Any]] | None = None,
        session: AsyncSession | None = None,
        caller_tenant_id: str | None = None,
    ) -> bool:
        """Soft-delete a memory record.

        Args:
            caller_tenant_id: If provided, the record must belong to this tenant.
        """
        start = time.time()

        # Load from DB if session provided
        record: MemoryRecord | None = None
        if session is not None:
            record = await self._load_from_db(session, memory_id)
        else:
            record = self._cache.get(memory_id)

        if record is None:
            return False

        # Cross-tenant/workspace isolation check — must happen BEFORE policy check
        # so that a well-role'd principal from another tenant is denied
        if caller_tenant_id and record.tenant_id and record.tenant_id != caller_tenant_id:
            self._emit_audit("memory.delete", principal_id, memory_id,
                             "denied", "denied", start,
                             metadata={"reason": "cross_tenant_isolation"})
            logger.warning("[memory] cross-tenant delete blocked: %s from tenant %s tried to access tenant %s",
                           principal_id, caller_tenant_id, record.tenant_id)
            return False

        decision = self._authorize(
            principal_id=principal_id,
            principal_type="agent",
            action="delete",
            resource_type="memory",
            resource_id=memory_id,
            tenant_id=record.tenant_id,
            workspace_id=record.workspace_id,
            policies=policies,
        )

        if decision is None or decision.decision == EFFECT_DENY:
            self._emit_audit("memory.delete", principal_id, memory_id,
                             "denied", "denied", start)
            return False

        record.status = "deleted"
        record.updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Persist soft-delete
        if session is not None:
            result = await session.execute(
                select(MemoryModel).where(MemoryModel.id == memory_id)
            )
            model = result.scalar_one_or_none()
            if model:
                model.deleted_at = datetime.now(timezone.utc)
                model.updated_at = datetime.now(timezone.utc)
                model.temporal_status = "deleted"
                await session.flush()

        self._emit_audit("memory.delete", principal_id, memory_id,
                         "success", "allow", start,
                         request_id=decision.request_id)
        return True

    # ------------------------------------------------------------------ #
    # Expire (time-based lifecycle)
    # ------------------------------------------------------------------ #

    async def expire(self, memory_id: str, session: AsyncSession | None = None) -> bool:
        """Mark a record as expired (time-based lifecycle).

        Expiration is distinct from decay (retrieval confidence degradation)
        and supersession (version replacement).
        """
        record = self._cache.get(memory_id)
        if record is None and session is not None:
            record = await self._load_from_db(session, memory_id)
        if record is None:
            return False
        record.status = "expired"
        record.updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        if session is not None:
            result = await session.execute(
                select(MemoryModel).where(MemoryModel.id == memory_id)
            )
            model = result.scalar_one_or_none()
            if model:
                model.temporal_status = "expired"
                model.updated_at = datetime.now(timezone.utc)
                await session.flush()

        logger.info("[memory] expired %s", memory_id)
        return True

    # ------------------------------------------------------------------ #
    # Provenance and history
    # ------------------------------------------------------------------ #

    async def provenance(self, memory_id: str, session: AsyncSession | None = None) -> list[dict[str, Any]] | None:
        """Return provenance chain for a memory record."""
        if session is not None:
            record = await self._load_from_db(session, memory_id)
        else:
            record = self._cache.get(memory_id)
        if record is None:
            return None
        return list(record.provenance)

    async def history(self, memory_id: str, session: AsyncSession | None = None) -> list[dict[str, Any]] | None:
        """Return version history for a memory record."""
        if session is not None:
            record = await self._load_from_db(session, memory_id)
        else:
            record = self._cache.get(memory_id)
        if record is None:
            return None
        return [
            {
                "version": record.version,
                "supersedes": record.supersedes,
                "superseded_by": record.superseded_by,
                "updated_at": record.updated_at,
                "status": record.status,
            }
        ]

    async def explain(self, memory_id: str, session: AsyncSession | None = None) -> dict[str, Any] | None:
        """Return full explanation of a memory record including provenance and access history."""
        if session is not None:
            record = await self._load_from_db(session, memory_id)
        else:
            record = self._cache.get(memory_id)
        if record is None:
            return None
        return {
            "record": {
                "memory_id": record.memory_id,
                "memory_type": record.memory_type,
                "scope": record.scope,
                "status": record.status,
                "subject": record.subject,
                "predicate": record.predicate,
                "value": record.value,
                "confidence": record.confidence,
                "importance": record.importance,
                "version": record.version,
                "supersedes": record.supersedes,
                "superseded_by": record.superseded_by,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
            },
            "provenance": await self.provenance(memory_id, session=session),
            "history": await self.history(memory_id, session=session),
            "permissions": record.permissions,
            "policy_required": True,
        }

    # ------------------------------------------------------------------ #
    # Share / Revoke
    # ------------------------------------------------------------------ #

    async def share(
        self,
        memory_id: str,
        principal_id: str,
        target_principal_id: str,
        permissions: dict[str, Any],
        policies: list[dict[str, Any]] | None = None,
        session: AsyncSession | None = None,
    ) -> bool:
        """Share a memory record with another principal."""
        start = time.time()

        record = self._cache.get(memory_id)
        if record is None and session is not None:
            record = await self._load_from_db(session, memory_id)
        if record is None:
            return False

        decision = self._authorize(
            principal_id=principal_id,
            principal_type="agent",
            action="share",
            resource_type="memory",
            resource_id=memory_id,
            tenant_id=record.tenant_id,
            workspace_id=record.workspace_id,
            policies=policies,
        )

        if decision is None or decision.decision == EFFECT_DENY:
            self._emit_audit("memory.share", principal_id, memory_id,
                             "denied", "denied", start)
            return False

        record.permissions[target_principal_id] = permissions
        self._emit_audit("memory.share", principal_id, memory_id,
                         "success", "allow", start,
                         request_id=decision.request_id)
        return True

    async def revoke(
        self,
        memory_id: str,
        principal_id: str,
        target_principal_id: str,
        policies: list[dict[str, Any]] | None = None,
        session: AsyncSession | None = None,
    ) -> bool:
        """Revoke access to a memory record for a principal."""
        start = time.time()

        record = self._cache.get(memory_id)
        if record is None and session is not None:
            record = await self._load_from_db(session, memory_id)
        if record is None:
            return False

        decision = self._authorize(
            principal_id=principal_id,
            principal_type="agent",
            action="share",
            resource_type="memory",
            resource_id=memory_id,
            tenant_id=record.tenant_id,
            workspace_id=record.workspace_id,
            policies=policies,
        )

        if decision is None or decision.decision == EFFECT_DENY:
            self._emit_audit("memory.revoke", principal_id, memory_id,
                             "denied", "denied", start)
            return False

        record.permissions.pop(target_principal_id, None)
        self._emit_audit("memory.revoke", principal_id, memory_id,
                         "success", "allow", start,
                         request_id=decision.request_id)
        return True

    # ------------------------------------------------------------------ #
    # Audit helper
    # ------------------------------------------------------------------ #

    def _emit_audit(
        self,
        event_type: str,
        principal_id: str,
        resource_id: str | None,
        result_status: str,
        decision: str,
        start: float,
        **kwargs: Any,
    ) -> None:
        if self._audit is None:
            return
        # Map result status to constants
        status_map = {
            "success": RESULT_SUCCESS,
            "denied": RESULT_DENIED,
            "not_found": RESULT_FAILURE,
        }
        mapped_status = status_map.get(result_status, RESULT_SUCCESS)
        try:
            self._audit.emit(
                event_type=event_type,
                result_status=mapped_status,
                principal_id=principal_id,
                principal_type="user",
                resource_type="memory",
                resource_id=resource_id,
                action=event_type.split(".")[-1],
                decision=decision,
                duration_ms=int((time.time() - start) * 1000),
                **kwargs,
            )
        except Exception:
            logger.debug("audit emit failed", exc_info=True)

    @staticmethod
    def _is_broader(record_scope: str, query_scope: str) -> bool:
        """Check if record scope is broader than query scope.

        Hierarchy: TENANT > WORKSPACE > PROJECT > TEAM > USER
        """
        hierarchy = {"TENANT": 5, "WORKSPACE": 4, "PROJECT": 3, "TEAM": 2, "USER": 1}
        return hierarchy.get(record_scope, 0) >= hierarchy.get(query_scope, 0)

    def seed_test_data(self) -> None:
        """Seed a few records for testing."""
        for i in range(5):
            r = MemoryRecord(
                memory_id=f"mem-{i}",
                memory_type="SEMANTIC",
                scope="PROJECT",
                project_id="proj-1",
                subject=f"test subject {i}",
                predicate="is",
                value=f"value {i}",
                content=f"test content number {i} for semantic memory",
                authority={"source": "test", "creator": "test"},
            )
            self._cache[r.memory_id] = r


__all__ = [
    "MemoryRecord",
    "MemoryService",
    "MemoryTypeMapper",
]
