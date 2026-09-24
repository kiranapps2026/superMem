# PHASE 0 — Reconciliation Record

**Date**: 2026-09-10
**Baseline SHA**: `e6f4b1c157afaed052584963b942ea04f9661610`
**Reconciliation**: Disposition of unauthorized implementation deviations found during forensic validation.

---

## UNAUTHORIZED CHANGE: Memory Supersession Fields

**File**: `app/models.py` (Memory class, lines 232-272)
**Change introduced**: Added 3 unauthorized fields:
1. `superseded_at` (DateTime, nullable, indexed)
2. `superseded_by_id` (String(36), nullable, indexed)
3. `superseded_by` (relationship)

**Classification**: `M-ARCH CONTRACT / PLANNED IMPLEMENTATION` — NOT current implementation.

**Disposition**:
- The supersession fields were introduced during an unauthorized implementation attempt before forensic validation was complete.
- They are therefore excluded from the current implementation baseline and classified as M-ARCH planned architecture.
- No migration is created as part of forensic reconciliation.
- No migration exists in the repository for these fields.
- No runtime verification of supersession on Memory model was performed or deemed necessary; the ORM model is now verified to match HEAD baseline.

**Evidence**:
- `git diff` before revert: showed 3 added fields on Memory class
- `git show HEAD:app/models.py | sed -n '232,270p'`: confirmed fields absent in baseline
- `diff` after revert: Memory model matches HEAD exactly
- `grep -r "superseded" app/models.py`: only Fact/Decision `superseded_by_id` remain (authorized baseline)

**Rationale**: Forensic analysis must reconstruct reality, not implement the target architecture. Supersession is part of the planned Memory Intelligence Layer (M-ARCH) but is not implemented in the current codebase. Implementing it during forensics would corrupt the baseline and introduce unverified schema changes.

---

## AUTHORIZED FIXES (Preserved)

### 1. Tenant Isolation Predicate
**File**: `app/api/memory.py`
**Change**: Added `Memory.tenant_id == tc.tenant_id` filter to `list_memories`
**Classification**: `AUTHORIZED FIX` — independently validated P0 security fix
**Basis**: Fixes confirmed cross-tenant data leakage; validated against API contract

### 2. Transaction Rollback Handling
**Files**: `app/api/chat.py`, `app/api/ingest.py`
**Change**: Added try/except with `db.rollback()` on processing failure
**Classification**: `AUTHORIZED FIX` — independently validated bug fix
**Basis**: Fixes orphaned messages and corrupted sessions on failure paths

---

## MARGINAL CHANGES (Preserved — Display Only)

| File | Change | Classification |
|------|--------|----------------|
| `frontend/src/app/projects/[id]/memory/page.tsx` | Authority badge format | Marginal — display only |
| `frontend/src/app/projects/[id]/facts/page.tsx` | Confidence/authority display | Marginal — display only |
| `frontend/src/app/projects/[id]/decisions/page.tsx` | Display formatting | Marginal — display only |
| `frontend/src/components/Sidebar.tsx` | Display formatting | Marginal — display only |

---

## CURRENT BASELINE STATE

**HEAD SHA**: `e6f4b1c157afaed052584963b942ea04f9661610`
**Working tree**: 4 modified backend files, 5 modified frontend files, 58 untracked docs files
**Tests**: 3/3 memory unit tests pass
**ORM verification**: Memory model columns match HEAD baseline exactly

**Allowed modifications remaining in working tree**:
- `app/api/chat.py` — authorized transaction rollback
- `app/api/ingest.py` — authorized transaction rollback
- `app/api/memory.py` — authorized tenant isolation
- `app/schemas.py` — derived from above authorized fixes
- `frontend/src/app/projects/[id]/decisions/page.tsx` — marginal
- `frontend/src/app/projects/[id]/facts/page.tsx` — marginal
- `frontend/src/app/projects/[id]/memory/page.tsx` — marginal
- `frontend/src/components/Sidebar.tsx` — marginal
- `frontend/e2e/remaining-contracts.spec.ts` — marginal

---

## DECISION RECORD

The supersession fields were introduced during an unauthorized implementation attempt before forensic validation was complete. They are therefore excluded from the current implementation baseline and classified as M-ARCH planned architecture. No migration is created as part of forensic reconciliation.
