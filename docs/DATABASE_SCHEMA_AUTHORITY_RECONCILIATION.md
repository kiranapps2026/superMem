# Database Schema Authority Reconciliation
**Date:** 2026-09-10
**Baseline SHA:** e6f4b1c157afaed052584963b942ea04f9661610
**Purpose:** Prove the exact authority chain for the production database schema

================================================================================
1. ALEMBIC STRUCTURE — ACTUAL STATE
================================================================================

**Production Alembic location:** `alembic/` (repository root)
**NOT:** `app/alembic/` (untracked, created during unauthorized repair)

**Migrations present at HEAD (12 migrations, 001-012):**

| Revision | File | Description |
|----------|------|-------------|
| 001 | 001_initial.py | Initial schema (users, workspaces, projects, sessions, messages, sources, normalized_messages) |
| 002 | 002_provenance.py | Provenance tables |
| 003 | 003_sprint3_pipeline.py | Facts, decisions, memory_pipeline_snapshots; adds `error_message` to sources |
| 004 | 004_add_memory_sprint4_columns.py | Memory columns (temporal_status, confidence, authority, embedding) |
| 005 | 005_add_message_feedback.py | Feedback table |
| 006 | 006_add_temporal_to_graph_nodes.py | Temporal fields on graph nodes |
| 007 | 007_add_api_keys.py | API keys table |
| 008 | 008_add_source_content_hash.py | Content hash index on sources |
| 009 | 009_add_policy_engine.py | Policy engine tables |
| 010 | 010_add_audit_events.py | Audit events table |
| 011 | 011_add_tenant_to_memory.py | tenant_id on memories (P0 security fix) |
| 012 | 012_add_invitations.py | Invitations table |

**Migration chain integrity:** All 12 migrations have valid `down_revision` references forming a linear chain from 001 to 012.

**HEAD commit message:** "docs: update E2E test inventory to 136 tests"
**Migration dates:** 2026-08-30 through 2026-09-02

================================================================================
2. AUTHORIZED vs UNAUTHORIZED ALEMBIC CHANGES
================================================================================

**Authorized (committed in legitimate migrations):**
- `alembic/versions/001-012.py` — all committed, part of baseline

**Unauthorized (untracked, created during repair attempt):**
- `app/alembic.ini` — untracked copy of root `alembic.ini`
- `app/alembic/env.py` — untracked copy of root `alembic/env.py`
- `app/alembic/versions/` — empty untracked directory

**Disposition:** REVERT — these files should be removed. The correct Alembic
location is `alembic/` at the repository root.

================================================================================
3. MODEL-TO-MIGRATION ALIGNMENT
================================================================================

**Verified aligned (model changes have migrations):**

| Model Field | Added In | Migration |
|-------------|----------|-----------|
| Memory.tenant_id | M011 | 011_add_tenant_to_memory |
| Memory.temporal_status | M004 | 004_add_memory_sprint4_columns |
| Memory.confidence | M004 | 004_add_memory_sprint4_columns |
| Memory.authority | M004 | 004_add_memory_sprint4_columns |
| Memory.embedding | M004 | 004_add_memory_sprint4_columns |
| Memory.deleted_at | M004 | 004_add_memory_sprint4_columns |
| Source.error_message | M001/M003 | 001_initial.py, 003_sprint3_pipeline |
| Source.content_hash | M008 | 008_add_source_content_hash |
| Fact.superseded_by_id | M003 | 003_sprint3_pipeline |
| Decision.superseded_by_id | M003 | 003_sprint3_pipeline |
| Invitations table | M012 | 012_add_invitations |

**Unauthorized model changes (NO migration):**

| Field | Model | Added In | Migration? |
|-------|-------|----------|------------|
| Memory.superseded_at | Memory | Working tree (unauthorized) | NO |
| Memory.superseded_by_id | Memory | Working tree (unauthorized) | NO |
| Memory.superseded_by | Memory | Working tree (relationship, unauthorized) | NO |
| Source.deleted_at index | Source | Working tree (modified) | NO |

**Source.deleted_at index addition** is a minor schema optimization that
should have its own migration if desired, but does not affect data integrity
since the column already exists.

================================================================================
4. PRODUCTION DATABASE AUTHORITY
================================================================================

**Question:** Is Alembic the production schema authority?
**Answer:** YES — but with a caveat.

The `alembic/` directory at the repository root contains the authoritative
migration chain. The application does NOT use `create_all()` in production
code (verified by grep).

**Question:** Does the current database match migration state?
**Answer:** CANNOT VERIFY — no database connection available in forensic phase.

If a production database exists, it should be at migration HEAD (012). If
the unauthorized model changes were applied via `create_all()` or manual
DDL, the database schema would diverge from the migration chain.

**Question:** Can a fresh database reproduce the production schema solely
from migrations?
**Answer:** YES — all 12 migrations are present and form a complete chain
from 001 to 012. A fresh `alembic upgrade head` should produce a schema
matching the pre-unauthorized-repair state.

================================================================================
5. BASELINE CORRECTION
================================================================================

**Incorrect claim in forensic documents:**
> "Empty Alembic versions/ — 5 model changes without migrations"

**Correct statement:**
> "Root `alembic/versions/` contains 12 migrations (001-012) forming a
> complete chain. The `app/alembic/versions/` directory is empty but is
> an UNTRACKED artifact created during an unauthorized repair attempt and
> should be removed. Additionally, 3 unauthorized model changes exist in
> the working tree (Memory.superseded_at, Memory.superseded_by_id,
> Memory.superseded_by relationship) that have no corresponding migration
> and must be reverted before the repository can be considered clean."

**Impact on other documents:**
- `SWARMVAULT_DATA_MEMORY_ARCHITECTURE.md` — references "empty Alembic" must be corrected
- `SWARMVAULT_SECURITY_OPERATIONAL_ARCHITECTURE.md` — references "empty Alembic" must be corrected
- `SWARMVAULT_WEBAPP_MASTER_ARCHITECTURE.md` — references "empty Alembic" must be corrected
- `SWARMVAULT_ARCHITECTURAL_GAPS_AND_MEMORY_NEXT_LAYER.md` — references "empty Alembic" must be corrected

================================================================================
6. UNAUTHORIZED CHANGE INVENTORY (MODELS)
================================================================================

All changes are in `app/models.py`, unstaged, uncommitted:

**Change 1:** Added `superseded_at` column to Memory model
- Type: NEW COLUMN
- Lines: +4
- Has migration: NO
- Disposition: REVERT

**Change 2:** Added `superseded_by_id` column to Memory model
- Type: NEW COLUMN (FK to memories.id)
- Lines: +4
- Has migration: NO
- Disposition: REVERT

**Change 3:** Added `superseded_by` relationship to Memory model
- Type: NEW RELATIONSHIP
- Lines: +4
- Has migration: NO
- Disposition: REVERT

**Change 4:** Added `index=True` to Source.deleted_at column
- Type: SCHEMA MODIFICATION (index addition)
- Lines: +1
- Has migration: NO
- Disposition: QUARANTINE (minor optimization, needs migration if desired)

================================================================================
7. CONCLUSION
================================================================================

The "empty Alembic" finding was a DOCUMENTATION ERROR caused by checking
`app/alembic/versions/` instead of the correct `alembic/versions/` at the
repository root.

The actual finding is:
1. 12 legitimate migrations exist at `alembic/versions/` (001-012)
2. 3 unauthorized model changes exist in the working tree on Memory model
3. 1 unauthorized index addition on Source.deleted_at
4. An untracked `app/alembic/` directory was created during repair attempt

The repository CAN be restored to a clean forensic baseline by:
1. Reverting `app/models.py` to HEAD
2. Removing untracked `app/alembic/` directory
3. Removing untracked `app/alembic.ini` file
4. Creating a proper migration for any desired schema changes

================================================================================
END OF DATABASE_SCHEMA_AUTHORITY_RECONCILIATION.md
================================================================================
