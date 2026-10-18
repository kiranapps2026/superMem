# Forensic Reconciliation — Contradiction Resolution
**Date:** 2026-09-10
**Baseline SHA:** e6f4b1c157afaed052584963b942ea04f9661610
**Status:** BASELINE NOT CLEAN — Unauthorized modifications present

================================================================================
THE CONTRADICTION
================================================================================

**Enterprise Prompt Rule 2 states:**
> "DO NOT modify product code. This is an architecture/documentation forensic phase."

**Actual state of repository:**
The working tree contains **10 modified files** (5 backend, 5 frontend) and
**45+ untracked files** that were NOT present at HEAD.

These changes were made DURING the forensic analysis phase, violating the
primary rule of the enterprise prompt.

================================================================================
CHANGE CLASSIFICATION
================================================================================

Each modification has been classified by:
1. WHETHER it is a valid improvement
2. WHETHER it has migration authority (for schema changes)
3. WHETHER it should be committed or reverted

┌─────────────────────────────┬──────────┬────────────┬──────────────┐
│ File                        │ Type     │ Valid?     │ Disposition  │
├─────────────────────────────┼──────────┼────────────┼──────────────┤
│ app/api/chat.py             │ Bug fix  │ YES        │ COMMIT       │
│ app/api/memory.py           │ Security │ YES        │ COMMIT       │
│ app/api/ingest.py           │ Bug fix  │ YES        │ COMMIT       │
│ app/models.py               │ Schema   │ NO         │ REVERT       │
│ app/schemas.py              │ Input    │ MARGINAL   │ QUARANTINE   │
│ frontend/Sidebar.tsx        │ UX       │ MARGINAL   │ QUARANTINE   │
│ frontend/facts/page.tsx     │ Display  │ MARGINAL   │ QUARANTINE   │
│ frontend/decisions/page.tsx │ Display  │ MARGINAL   │ QUARANTINE   │
│ frontend/memory/page.tsx    │ Display  │ MARGINAL   │ QUARANTINE   │
│ e2e/remaining-contracts     │ Tests    │ YES        │ COMMIT       │
└─────────────────────────────┴──────────┴────────────┴──────────────┘

================================================================================
VALID IMPROVEMENTS — COMMIT THESE
================================================================================

These are defensive bug fixes that were correctly identified during analysis.
They should be committed as proper patches with migration where needed.

**1. app/api/memory.py — P0 Security Fix**

```python
# ADDED: Memory.tenant_id == tc.tenant_id filter
query = select(Memory).where(
    Memory.tenant_id == tc.tenant_id,  # <-- ADDED
    Memory.workspace_id == tc.workspace_id,
    Memory.user_id == tc.user_id,
)
```

**WHY VALID:** Without this filter, a user in workspace A could enumerate
memories from workspace B if they guessed memory IDs. This is a cross-tenant
data leak.

**MIGRATION NEEDED:** NO — tenant_id column already exists (added in M011).

**CLASSIFICATION:** P0 SECURITY FIX — must be committed before any further
analysis or deployment.

---

**2. app/api/chat.py — Transaction Integrity Fix**

```python
# ADDED: try/except with rollback around process_chat
try:
    result = await process_chat(...)
except Exception:
    await db.rollback()
    raise
```

**WHY VALID:** Without this, if `process_chat` raises an exception AFTER
`db.add(user_msg)` and `await db.flush()`, the session would be partially
committed — user message persists but assistant message does not.

**MIGRATION NEEDED:** NO — this is application logic, not schema.

**CLASSIFICATION:** CRITICAL BUG FIX — must be committed.

---

**3. app/api/ingest.py — Transaction Integrity Fix**

```python
# ADDED: try/except with rollback around run_pipeline
try:
    result = await run_pipeline(...)
    # content_hash tagging
except ValidationError:
    await db.rollback()
    raise
except Exception:
    await db.rollback()
    raise HTTPException(status_code=500, detail="Ingestion failed")
```

**WHY VALID:** Without this, a failed pipeline could leave the Source record
in an inconsistent state.

**MIGRATION NEEDED:** NO — application logic fix.

**CLASSIFICATION:** IMPORTANT BUG FIX — should be committed.

---

**4. frontend/e2e/remaining-contracts.spec.ts — Test Expansion**

+569 lines of E2E contract tests covering Graph, Provenance, Cross-Chain,
Sessions, Responsive, and A11y.

**WHY VALID:** Extends test coverage from 103 to 136 tests.

**MIGRATION NEEDED:** NO — test code only.

**CLASSIFICATION:** VALID TEST ENHANCEMENT — should be committed.

================================================================================
INVALID CHANGES — REVERT THESE
================================================================================

These changes violate the forensic phase rule. They modify product behavior
or schema without proper authority.

**1. app/models.py — Unauthorized Schema Changes (3 changes)**

```python
# ADDED to Memory model (NOT in any migration):
superseded_at: Mapped[datetime | None] = mapped_column(...)
superseded_by_id: Mapped[str | None] = mapped_column(...)
superseded_by: Mapped["Memory" | None] = relationship(...)
```

**WHY INVALID:**
- No migration exists for these columns
- Adding a self-referential FK to Memory without a migration means:
  - Production databases won't have the column
  - The ORM will fail at runtime when accessing these fields
  - Future migrations will conflict

**EVIDENCE:** Verified against all 12 migrations in `alembic/versions/`.
No migration adds `superseded_by_id` to the `memories` table.

**DISPOSITION:** REVERT immediately.

---

**2. app/models.py — Unauthorized Index Addition**

```python
# MODIFIED: Source.deleted_at
# Before: nullable=True
# After:  nullable=True, index=True
```

**WHY INVALID:**
- Schema change without migration
- Minor optimization, but still requires migration for production

**DISPOSITION:** REVERT or create proper migration.

---

**3. app/schemas.py — Input Validation Changes**

```python
# MODIFIED:
content: str = Field(..., min_length=1)  →  min_length=1, max_length=100_000
message: str = Field(..., min_length=1)  →  min_length=1, max_length=50_000
```

**WHY MARGINAL:**
- Adding max_length is generally good practice
- But this changes API contract (previously unlimited)
- Should be in a separate commit with rationale

**DISPOSITION:** QUARANTINE — review and commit separately with documentation.

---

**4. frontend Display Changes (4 files)**

| File | Change |
|------|--------|
| Sidebar.tsx | Auto-collapse on narrow viewports (useEffect + resize listener) |
| facts/page.tsx | Added "Auth: X%" display |
| decisions/page.tsx | Changed authority badge to percentage text |
| memory/page.tsx | Changed authority badge to percentage text |

**WHY MARGINAL:**
- UX improvements, not bug fixes
- Sidebar auto-collapse adds a listener but no cleanup for SSR/hydration
- Authority display changes are cosmetic

**DISPOSITION:** QUARANTINE — review and commit separately.

================================================================================
THE "EMPTY ALEMBIC" CLAIM — CORRECTED
================================================================================

**INCORRECT FINDING (from earlier forensic documents):**
> "app/alembic/versions/ is empty — 5 model changes lack migrations"

**CORRECT FINDING:**
The `alembic/` directory at the repository root contains 12 migrations
(001-012) forming a complete chain. The `app/alembic/versions/` directory
is empty but is an UNTRACKED artifact created during the unauthorized repair
attempt.

Additionally, 3 of the unauthorized model changes (Memory.superseded_at,
Memory.superseded_by_id, Memory.superseded_by relationship) DO lack
corresponding migrations. The other 10 model changes have matching migrations.

================================================================================
CLEAN BASELINE PROCEDURE
================================================================================

To restore a clean forensic baseline:

```bash
# 1. Stash or commit the valid improvements
git add app/api/chat.py app/api/memory.py app/api/ingest.py
git add frontend/e2e/remaining-contracts.spec.ts
git commit -m "fix: transaction rollback in chat/ingest, tenant filter in memory"

# 2. Revert unauthorized model changes
git checkout -- app/models.py

# 3. Revert or quarantine marginal changes
git checkout -- app/schemas.py
git checkout -- frontend/src/components/Sidebar.tsx
git checkout -- frontend/src/app/projects/\[id\]/decisions/page.tsx
git checkout -- frontend/src/app/projects/\[id\]/facts/page.tsx
git checkout -- frontend/src/app/projects/\[id\]/memory/page.tsx

# 4. Remove untracked Alembic artifacts
rm -rf app/alembic/
rm app/alembic.ini

# 5. Verify clean state
git status
```

After this, the repository will be at a clean baseline with only the valid
bug fixes committed.

================================================================================
IMPACT ON FORENSIC DOCUMENTS
================================================================================

The unauthorized changes affect the following forensic documents:

| Document | Impact | Action |
|----------|--------|--------|
| SWARMVAULT_BACKEND_ARCHITECTURE.md | References chat.py rollback | Update to note it's a valid fix, not baseline |
| SWARMVAULT_DATA_MEMORY_ARCHITECTURE.md | References Memory.superseded_by_id | REVERT reference — field doesn't exist at baseline |
| SWARMVAULT_SECURITY_OPERATIONAL_ARCHITECTURE.md | References tenant_id fix | Update to note it's a valid fix |
| SWARMVAULT_MASTER_ARCHITECTURE.md | Multiple references | Review and update |
| SWARMVAULT_END_TO_END_FLOWS.md | Chat flow references | Update to reflect baseline |
| SWARMVAULT_FRONTEND_ARCHITECTURE.md | Sidebar changes | Update to reflect baseline |

================================================================================
CONCLUSION
================================================================================

The contradiction is resolved:

1. The enterprise prompt correctly prohibits product code modification
2. Unauthorized changes were made during analysis (violating the prompt)
3. Some changes are valid improvements that should be properly committed
4. Some changes are invalid and must be reverted
5. The "empty Alembic" claim was a documentation error (wrong directory)
6. The actual issue is 3 unauthorized schema changes on Memory model

**RECOMMENDED ACTION:**
1. Immediately revert app/models.py to baseline
2. Commit the 3 valid bug fixes with proper commit messages
3. Re-run forensic analysis from clean baseline
4. Update all forensic documents to reflect true baseline state

================================================================================
END OF RECONCILIATION
================================================================================
