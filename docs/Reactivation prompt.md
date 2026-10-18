# Reactivation prompt

Revision 2, scoped to execution. Phases R0 and R4 are complete — their findings are supplied below as inputs rather than re-derived. Paste this whole block into Claude Code opened at `C:\Users\Administrator\Documents\SwarmVaultwebapp`.

```markdown
# SWARMVAULT WEBAPP — EXECUTION & STABILITY PROOF (Recovery Program, Rev 2)

ROLE: Senior release engineer. A prior read-only pass established that the
restored source is complete. Your job is to PROVE THE SYSTEM RUNS. This pass
executes commands. A file you read is not a test you ran.

REPOSITORY: C:\Users\Administrator\Documents\SwarmVaultwebapp

## WHAT IS ALREADY ESTABLISHED (inputs — do not re-derive)

- HEAD = e6f4b1c, .git/ intact, migration chain linear 001..012 at alembic/
- 10 files modified and UNCOMMITTED: app/api/chat.py (±75), app/api/ingest.py
  (±44), app/api/memory.py, app/models.py, app/schemas.py, plus 5 frontend files
- app/alembic/ exists = unauthorized artifact, to be deleted
- Of 9 recorded frontend defects, 8 are fixed/never-wrong. ONE is active:
  frontend/src/features/graph/useGraph.ts:17 calls /api/v1/graph (404);
  correct path is /api/v1/ingest/graph
- New open items: app/db.py:43 deprecated get_event_loop(); app/main.py:269
  undefined logger in /health/ready error path; Sidebar.tsx ProjectNav
  (lines 43-63) omits the Provenance link
- 5 backend APIs have no UI: Policies, Audit, Members, Invitations, System Health

## PRIME DIRECTIVES

1. EXECUTE, DO NOT INSPECT. Every status in your output must be backed by the
   command you ran and its actual output, pasted. Reading a file and concluding
   "already fixed" is NOT verification in this pass. If you did not run it,
   the status is NOT VERIFIED — never "verified".
2. NO CONTRADICTORY VERDICTS. If evidence points two ways, report both and pick
   neither. Do not write a row that says both "broken" and "no fix needed".
3. REPORT THE NUMBER THE TOOL PRINTED. Never a number from a document.
4. STOP ON GATE FAILURE. Report and wait. Do not route around a failure.
5. NO SCOPE CREEP. No refactors, no formatting, no drive-by fixes, no new
   features. The repair list in Phase R5 is closed.

---

## PHASE G — PROTECT THE UNCOMMITTED WORK (do this first, before anything)

The 10 modified files exist in exactly one place on earth. They were never
compiled or tested — the machine was lost first.

1. git rev-parse HEAD (confirm e6f4b1c)
2. git checkout -b recovery/restore-2026-09-24
3. git add -A && git commit -m "chore(recovery): snapshot restored working tree
   (5 backend + 5 frontend uncommitted changes, untested)"
4. git log --oneline -3 to confirm the commit exists
5. Print git diff e6f4b1c..HEAD --stat

GATE G: PASS only when the snapshot commit exists. Everything after this is
now reversible. Do not proceed otherwise.

---

## PHASE R1 — ENVIRONMENT (execute)

1. Print actual: python --version, node --version, npm --version, psql --version.
   Compare to expected 3.12.7 / v24.19.0 / 11.6.0 / PostgreSQL 16. Flag drift;
   a major-version gap is a finding, not something to work around.
2. python -m venv .venv; activate; pip install -r requirements.txt.
   Paste any resolution failure verbatim.
3. cd frontend && npm ci. If package-lock.json is absent, record that as a
   reproducibility finding and use npm install.
4. Confirm PostgreSQL reachable. Create databases swarmvault and
   swarmvault_test, role swarmvault/swarmvault, if absent. Show \l output.
5. Search the backup drive for *.sql / *.dump / *.backup before creating an
   empty database. Report what you found. If a dump exists, STOP and ask
   before restoring — restoring over a fresh schema is not reversible.
6. Write .env from .env.example: SECRET_KEY 32+ chars, DATABASE_URL =
   postgresql+asyncpg://swarmvault:swarmvault@localhost:5432/swarmvault
   Write frontend/.env.local: NEXT_PUBLIC_API_URL=http://localhost:8000
   List every value you had to invent.

GATE R1: both installs complete, psql connects. Paste the proof.

---

## PHASE R2 — BACKEND STABILITY PROOF (the real gate)

1. Delete app/alembic/ (the unauthorized artifact). Confirm alembic.ini at the
   root points at alembic/.
2. Fix app/main.py:269 FIRST — the undefined logger. Rationale: it sits in the
   /health/ready error path, so a database failure raises NameError instead of
   reporting its own cause. One line. Commit separately.
3. alembic upgrade head from the repository root. Then alembic current.
   Expected: revision 012. Paste both outputs.
4. Run: pytest -q. Paste the full summary line.
   - 671 passing: the restored backend behaves as certified.
   - Any other number: list EVERY failing test by name with its assertion, and
     classify each as ENVIRONMENTAL (missing service, version drift) or
     RESTORE-DEFECT (missing/corrupt source) or UNCOMMITTED-WORK (caused by the
     ~125 changed lines in the 5 modified backend files). This three-way
     classification is the single most valuable output of the program.
   - If UNCOMMITTED-WORK failures appear, do NOT fix them yet. Report them.
     git stash-style isolation: re-run pytest against e6f4b1c to prove whether
     the failure is the restored work or the baseline, then report both numbers.
5. Start: uvicorn app.main:app --host 127.0.0.1 --port 8000 (no --reload).
6. curl /health/live, /health/ready, /docs. /health/ready must return 200 with a
   real database check. Paste responses.
7. Enumerate the live route table from the running app; print path and method
   counts. Compare to the documented 81 endpoints and state the delta.
8. Real flow via curl: register -> login -> create project -> GET
   /api/v1/projects/. Confirm tenant + workspace created on register.
9. Leave the backend running.

WRITE: docs/RECOVERY_R2_BACKEND_STABILITY.md ending in an explicit verdict —
BACKEND STABLE / STABLE WITH FINDINGS / NOT STABLE.
GATE R2: migrations at 012, /health/ready 200, pytest result classified.
RESTORE-DEFECT failures = FAIL. Report and stop.

---

## PHASE R3 — FRONTEND EXECUTION

1. cd frontend. npx tsc --noEmit. Paste every error.
2. npm run lint. Errors and warnings separately.
3. npm run build. Paste success or the full failure.
4. npm run dev; confirm http://localhost:3000 serves the login page.
5. With the backend running, exercise the ONE active defect before fixing it:
   curl the graph endpoint both ways to prove 404 vs 200. This converts the
   inspection finding into an executed one.
6. npx playwright test --workers=1. NEVER parallel — the suite shares one
   database. Per-spec counts. Expected: auth 7, dashboard 3, frontend-journey 4,
   golden-journey 14.
7. Enumerate every route under frontend/src/app/ and state renders /
   renders-with-errors / fails. Compare to the documented 23.

GATE R3: production build succeeds and E2E per-spec counts match.

---

## PHASE R5 — CLOSED REPAIR LIST (only after R2 and R3 pass)

Exactly these. One at a time: make the edit, re-run the narrowest proof,
commit separately naming the item. If a fix breaks anything, revert and report.

  R5-1  useGraph.ts:17 -> /api/v1/ingest/graph. Proof: graph page loads data.
  R5-2  Sidebar.tsx ProjectNav -> add the Provenance link. Proof: link renders
        and routes.
  R5-3  app/db.py:43 -> asyncio.get_running_loop(). Proof: pytest still green,
        no DeprecationWarning at startup.
  R5-4  AuditService buffer bound (app/services/audit/service.py) — propose the
        approach and WAIT for approval before editing.

Then: full pytest, full build, full playwright at workers=1. All three green,
or the batch is reverted.

DO NOT in this pass: build the 5 missing pages, rework error handling, touch
the 10 deferred capabilities, or alter the Memory supersession model fields.

---

## PHASE R6 — CONSOLIDATED CERTIFICATION

WRITE: docs/RECOVERY_CERTIFICATION.md

  1. Executive verdict in one paragraph: restore complete? backend stable?
     what remains on the frontend?
  2. Environment: component | expected | actual | drift.
  3. Backend proof: migration revision, pytest summary line as printed, endpoint
     count, health responses, live flow result. Explicit verdict.
  4. Uncommitted-work assessment: did the 10 restored files pass or fail, and
     what is the disposition of each.
  5. Frontend proof: tsc, lint, build, per-route status, per-spec E2E counts.
  6. Repair log: item, commit SHA, proof command, result.
  7. Data loss: what was in PostgreSQL and storage/ that is unrecoverable; what
     must be re-ingested.
  8. Documentation corrections: every docs/ claim proved wrong, with the correct
     statement. Include the Phase 1R inventory line claiming next.config /
     tailwind.config / postcss.config are missing — they are present.
  9. Next sprint, ordered, with a definition of done per item.
 10. NOT VERIFIED list: everything unproven and why.

## OUTPUT DISCIPLINE

- Label every material claim VERIFIED FROM EXECUTION / VERIFIED FROM SOURCE /
  INFERRED / NOT VERIFIED. Only the first counts as proof in this pass.
- Include the command with every number.
- Where a restored file contradicts a docs/ claim, the file wins and the
  contradiction is a finding — never silently correct the doc.
- Report at each gate and wait for go-ahead.
```
