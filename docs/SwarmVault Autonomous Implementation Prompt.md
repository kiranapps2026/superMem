# SwarmVault Memory Intelligence + Execution Integrity Layer — Autonomous Implementation Prompt

Sep 25, 2026 · @Kiran

This is the phase-gated execution prompt for the autonomous agent implementing SwarmVault's Memory Intelligence + Execution Integrity layer, building on the backend certified stable on 2026-09-25 (670/671 pytest, 222/225 Playwright). Each phase must reach its own PASS certification before the next begins.

## Operating rules

These apply to every phase below, without exception.

1. **Source code is authority.** Every claim in a phase's certification report cites `file:line — description`, matching the convention already used in `RECOVERY_CERTIFICATION.md` and `SWARMVAULT_BACKEND_ARCHITECTURE.md`.
2. **Phase gate rule.** Phase *N+1* does not start until Phase *N* produces a certification report with a PASS verdict on every gate. A FAIL halts execution and reports the failing gate — it does not proceed on a partial pass.
3. **Non-destructive principle.** No operation may `UPDATE` or `DELETE` an existing `Memory`, `Fact`, `Decision`, or `GraphNode` row's content, outside the established `deleted_at` soft-delete pattern. New states are represented as new rows plus linking (lineage relationships, `superseded_by_id`, contradiction records) — never in-place mutation of `content`.
4. **Flag-first rollout.** Every new subsystem ships behind a config flag (`FEATURE_RERANKING_ENABLED`, `FEATURE_CONTRADICTION_DETECTION_ENABLED`, `FEATURE_SEMANTIC_CONTRADICTION_ENABLED`), defaulting to `false` until its own phase certification passes.
5. **Test-first.** No phase is complete without pytest coverage of new service logic and, where user-facing, Playwright coverage of new routes or pages.
6. **Migration discipline.** Every schema change is a sequentially numbered Alembic migration starting at `013`, with a real `downgrade()` (not `pass`), and a backfill script for existing rows where applicable.
7. **Idempotency and concurrency discipline.** Every asynchronous job (embedding generation, contradiction detection, consolidation) carries a job id, is safe to retry without duplicating work, and takes a row-level or advisory lock on the record it's processing so two workers can never produce two conflicting results for the same record. Each such job's phase includes a crash-recovery test: kill the worker mid-batch, restart it, and verify it resumes cleanly rather than duplicating or corrupting state.
8. **Severity system.** Gaps found mid-phase are logged with the existing P0–P3 system (P0 critical/data-loss/security, P1 functional impairment, P2 maintainability, P3 nice-to-have). A P0 or P1 found during a phase blocks that phase's certification — it is not deferred to Phase 7.
9. **Scope discipline.** An agent implementing Phase *N* touches only the files listed in that phase's Implementation Scope. Anything else noticed along the way is logged as a gap, not fixed inline.
10. **Halt condition.** If a gate fails twice after a fix attempt, stop and produce a `PHASE_N_BLOCKED.md` report instead of retrying indefinitely.

## Phase 0 — Baseline safety snapshot

**Preconditions:** none — this phase runs first.

**Objective:** capture a verifiable, reproducible baseline so every later phase's certification diffs against a known-good state, and so no phase silently regresses the 2026-09-25 certification (670/671 pytest, 222/225 Playwright).

**Tasks**

1. Tag the current commit: `git tag pre-memory-intelligence-baseline`.
2. Run and archive: `pytest -q > baseline/pytest.txt`, `npx playwright test --workers=1 --reporter=line > baseline/playwright.txt`, `npx tsc --noEmit`, `npm run lint`, `npm run build`.
3. Snapshot `alembic current` — expect `012_add_invitations (head)`.
4. Record row counts for `memories`, `facts`, `decisions`, `graph_nodes`, `graph_edges` into `baseline/row_counts.json`. These counts must never decrease in any later phase except via legitimate soft-delete.
5. Confirm `.env`/`.env.example` values for `RATE_LIMIT_INGEST`, `CORS_ORIGINS`, `STORAGE_BACKEND` match what `SWARMVAULT_SECURITY_OPERATIONAL_ARCHITECTURE.md` documents, as the reference point for later phases.

**Certification gate — Gate 0**

| Check | Expected |
| --- | --- |
| Git tag | `pre-memory-intelligence-baseline` present |
| pytest | 670/671 (1 known ENVIRONMENTAL failure) |
| Playwright | 222/225 (1 known test defect, 2 skips) |
| tsc | 0 errors |
| Row counts recorded | `baseline/row_counts.json` present |

**Output:** `PHASE_0_BASELINE.md`.

## Phase 1 — Embedding backfill & minimal execution context

**Preconditions:** Phase 0 = PASS.

**Objective:** populate `Memory.embedding` on an explicitly chosen, versioned embedding backend — closing the gap where the model/dimension/storage decision could otherwise be made implicitly by whatever the migration happens to do — and lay the minimal identity trace (`trace_id`, `correlation_id`) that every later phase will need, without pulling the full Agent/Run migration (Phase 4) forward.

**Implementation scope:** `app/services/embeddings/` (new), `app/models.py` (`Memory.embedding` + versioning columns, `TenantContext` trace fields), `alembic/versions/013_*`, `app/services/memory.py` (write path), `scripts/backfill_embeddings.py`.

**Tasks**

1. Add `trace_id` and `correlation_id` to the existing `TenantContext` (the minimal `ExecutionContext` — `tenant_id`/`workspace_id`/`user_id` already flow through it). This is the only identity work in this phase; `Agent`/`AgentVersion`/`Run`/`RunStep` tables and the validation gate stay in Phase 4, where the migration and backfill risk is contained on its own.
2. **Embedding backend gate — signed off before migration 013 is written:** document the provider/model, dimension, storage type (pgvector vs. a plain array/JSON column vs. an external vector store — confirm explicitly rather than assuming, given pgvector availability has previously been inconsistent in this environment), distance metric, index type, and production availability. A migration that runs cleanly but locks in the wrong storage choice is the failure mode this gate exists to prevent.
3. Add embedding versioning columns alongside `embedding`: `embedding_model`, `embedding_dimension`, `embedding_version`, `embedded_at` — required so a future model change can identify exactly which rows need re-embedding, instead of guessing.
4. Migration `013_embedding_dimension` — the column(s) and versioning fields from tasks 2–3, with a real `upgrade()`/`downgrade()`.
5. Add embedding generation to `MemoryService.write()` (`app/services/memory.py`) — every new `Memory` gets an embedding plus its version stamp; document whether this is synchronous or queued.
6. Write `scripts/backfill_embeddings.py` — batches existing `Memory` rows lacking an embedding, rate-limited, and idempotent: keyed on `content_hash + embedding_version`, so a rerun (or a second worker) never generates a duplicate embedding for the same content/version pair. Logs failures without halting the batch.
7. Extend `/health/ready` (or add `/health/embeddings`) to report backfill progress as a percentage.

**Tests**

- Unit (`tests/unit/test_embeddings_service.py`): generation, dimension validation, failure handling — provider timeout retries then dead-letters, never silently drops.
- Backfill script: run against seeded rows with null embeddings, assert 100% populated after; assert a second run is a no-op (idempotency); kill the script mid-batch and restart it — assert it resumes without re-embedding already-completed rows (crash recovery).

**Certification gate — Gate 1**

| Check | Expected |
| --- | --- |
| Embedding backend gate | Signed off in writing before migration 013 existed |
| Migration applied | `alembic current` = `013_*` |
| Trace fields | `trace_id`/`correlation_id` present on `TenantContext` and populated on every new write |
| New writes | 100% of `Memory` rows created after this phase have a non-null `embedding` and version stamp |
| Backfill coverage | ≥ 99%, and every remaining row carries an explicit classification (e.g. empty content, invalid encoding) — a bare P2 log line without a reason is not sufficient |
| Idempotency & crash recovery | Rerun is a no-op; mid-batch restart resumes without duplication, verified by test |
| pytest | baseline count + new tests, all passing |
| No regression | Phase 0 row counts for facts/decisions/graph unchanged |

**Output:** `PHASE_1_CERTIFICATION.md`.

## Phase 2 — Retrieval evaluation harness

**Preconditions:** Phase 1 = PASS.

**Objective:** build a small labeled query → relevant-memory dataset, scored on more than a blended average, so Phase 3's reranking weights are tuned against numbers that actually reflect the cases that matter — a reranker that raises the overall average while getting worse on temporal or tenant-isolation queries would otherwise pass unnoticed.

**Implementation scope:** `app/services/retrieval_eval/` (new), `tests/eval/` (new), `scripts/build_eval_set.py`.

**Tasks**

1. Sample 50–150 representative queries per workspace segment; label the genuinely relevant `Memory`/`Fact` rows for each, by a human reviewer or a documented heuristic.
2. Split the fixture set into categories, each labeled and scored separately rather than pooled into one number: semantic similarity, exact factual retrieval, temporal queries, contradictory queries (stub now, populate once Phase 5 exists), multi-hop queries, low-confidence memories, tenant-isolation queries.
3. Store as versioned fixtures (`tests/eval/retrieval_eval_v1.json`) — never as production DB rows, so the set stays reproducible and reviewable.
4. Build `RetrievalEvaluator` — runs `retrieve_hybrid()` (`app/services/m5_retrieval.py`) against the fixtures, computing precision@5, recall@k, recall@20, MRR, nDCG@k, zero-result rate, and tenant-isolation accuracy (a query never returns another workspace's rows) — each reported per category, not only as an overall blend.
5. Wire into CI as a non-blocking report for now: `make eval-retrieval` outputs a per-category scorecard without failing the build. This scorecard becomes the pass/fail baseline Phase 3 must beat — per category, not just on average.

**Tests**

- Unit: the evaluator's own scoring math — each metric computed correctly on a synthetic fixture with a known answer, including nDCG and tenant-isolation checks.

**Certification gate — Gate 2**

| Check | Expected |
| --- | --- |
| Fixture set | ≥ 50 labeled queries, versioned, split across all seven categories |
| Evaluator | Runs end-to-end against current M5 retrieval, reports per-category metrics |
| Baseline scorecard | `PHASE_2_BASELINE_SCORES.json` recorded, broken out by category — this is what Phase 3 must beat |

**Output:** `PHASE_2_CERTIFICATION.md`.

## Phase 3 — Reranking (shadow → live)

**Preconditions:** Phase 2 = PASS.

**Objective:** add a second-stage reranker on top of M5 hybrid retrieval — additive, not a replacement — with the cross-encoder as the primary ranking signal, an explicit abstention path for low-relevance results, and proof against the Phase 2 per-category baseline before it ever affects a served response.

**Implementation scope:** `app/services/reranking/` (`cross_encoder.py`, `scorer.py`, `policy.py`), `app/services/m5_retrieval.py` (call site), `app/core/config.py` (`FEATURE_RERANKING_ENABLED`, `MIN_RELEVANCE`, weight config), `app/api/chat.py` (score plumbing near the existing retrieval threshold).

**Tasks**

1. Implement `RerankingService.rerank(query, candidates, top_k)`. Candidate generation is unchanged (M5); the reranker computes `reranker_score` as the primary signal.
2. Score model: `reranker_score` is the primary ranking signal. `confidence`, `authority`, `temporal status`, and source quality apply only as small, bounded adjustments (e.g. a multiplier clamped to roughly ±15%) — never as flat weighted terms competing equally with relevance. This follows directly from the architecture's own note that `confidence`/`authority` are uncalibrated defaults (0.7/1.0), not learned probabilities, and shouldn't be trusted to dominate ranking.
3. Add an abstention gate: `reranker_score < MIN_RELEVANCE` (configurable) → abstain, don't inject that candidate into context. The caller receives an explicit "no sufficiently relevant memory found" signal instead of the top-ranked-but-irrelevant result being forced through — the single biggest lever here for reducing false grounding.
4. Preserve `retrieval_score`, `reranker_score`, and `final_score` as separate fields on the response — explainability is a requirement, not an option.
5. Ship behind `FEATURE_RERANKING_ENABLED=false` by default. In shadow mode, compute reranked (and abstention) results and log them without changing what is served to the LLM.
6. Run the Phase 2 evaluator against shadow-mode output — over at least a week of real traffic, or a full fixture re-run if traffic isn't available. Reranked precision/recall/nDCG/MRR must meet or beat the Phase 2 baseline **per category**, not just on average, before the flag flips.
7. Flip to live only after that comparison passes. Keep the flag in place so reranking can be reverted instantly without a redeploy.

**Tests**

- Unit (`tests/unit/test_reranking_service.py`): scoring model (bounded adjustments, not flat weights), abstention threshold, top-k truncation, explainability fields present on every result.
- Integration: shadow mode produces zero change to what `chat.py` serves; live mode does; a query with no sufficiently relevant memories abstains rather than returning a weak top-1.

**Certification gate — Gate 3**

| Check | Expected |
| --- | --- |
| Shadow-mode eval | Reranked metrics ≥ Phase 2 baseline, per category — no category regresses even if the average improves |
| Abstention | Verified by test: a no-relevant-memory query abstains, doesn't force a weak result |
| Explainability | Every response carries `retrieval_score`, `reranker_score`, `final_score` per memory |
| Flag reversible | Toggling `FEATURE_RERANKING_ENABLED` needs config only, no schema change |
| pytest / Playwright | No regressions vs. Phase 0 baseline |

**Output:** `PHASE_3_CERTIFICATION.md`.

## Phase 4 — Execution identity foundation

**Preconditions:** Phase 3 = PASS.

**Objective:** replace client-supplied, unvalidated `agent_id`/`run_id` with real entities and a server-derived `ExecutionContext` threaded through every write path — the change with the widest blast radius, so it runs after the lower-risk retrieval work, not before it.

**Implementation scope:** `app/models.py` (new `Agent`, `AgentVersion`, `Run`, `RunStep`, `ToolExecution` tables), `alembic/versions/014_*`, `app/core/context.py` (new `ExecutionContext`), every router currently accepting client-supplied `agent_id`/`run_id`, `app/services/memory.py`.

**Tasks**

1. Define the five new tables — `Tenant → Workspace → Project → Agent → AgentVersion → Run → RunStep → ToolExecution` — scoped by `tenant_id`/`workspace_id` following the existing tenancy pattern (`tenancy.py`).
2. Migration `014_execution_identity` — additive only. Existing `Memory.agent_id`/`run_id` become foreign keys, with a backfill pass that links legacy rows to a synthesized `legacy` Agent/Run or leaves them null with a logged, reviewable count — never a silent drop.
3. Build `ExecutionContext` (frozen dataclass: `tenant_id, workspace_id, project_id, user_id, agent_id, run_id, trace_id, correlation_id`) derived server-side from the authenticated session plus validated Agent/Run rows — never trusted verbatim from client JSON.
4. Add the validation gate: agent exists → belongs to workspace → active → run exists → belongs to agent → belongs to workspace → active → authorized actor → allow. Reject with 403 plus an audit event otherwise, extending `AuditPersistenceMiddleware`/`AuditService`.
5. Thread `ExecutionContext` through API → pipeline (`app/services/pipeline.py`) → `MemoryService` → M5 retrieval → reranker (Phase 3) → chat orchestrator → tool execution → audit.

**Tests**

- Unit: every branch of the validation-gate state machine; `ExecutionContext` construction from a mocked authenticated request.
- Integration: a forged or invalid `agent_id`/`run_id` is rejected end-to-end; a valid one flows through and appears correctly on the resulting `Memory`/`AuditEvent` rows.

**Certification gate — Gate 4**

| Check | Expected |
| --- | --- |
| No client-trusted identity | Grep confirms no router reads `agent_id`/`run_id` from the request body without passing the validation gate |
| Backfill | 100% of pre-existing `Memory` rows with non-null agent/run resolve to a real Agent/Run row |
| Rejection path tested | Invalid agent/run → 403 + audit event, verified by test |
| pytest / Playwright | No regressions |

**Output:** `PHASE_4_CERTIFICATION.md`.

## Phase 5 — Contradiction detection

**Preconditions:** Phase 4 = PASS.

**Objective:** detect conflicting Facts without ever deleting evidence — governed by an explicit predicate conflict policy so the deterministic layer knows which fields can legitimately hold multiple values over time, run asynchronously so it never blocks ingest.

**Implementation scope:** `app/services/memory_intelligence/contradiction.py`, `app/models.py` (new `MemoryContradiction` table, predicate policy config), `alembic/versions/015_*`, an async job runner (new or existing queue — must not run inline in the M0–M4 pipeline given `RATE_LIMIT_INGEST=5`).

**Tasks**

1. **Predicate conflict policy — a precondition of the deterministic layer, not an afterthought:** for every predicate the detector compares, define `cardinality` (`ONE`|`MANY`), `temporal` (`YES`|`NO`), `mutually_exclusive` (`YES`|`NO`), `inverse_predicates`, and `resolution_strategy`, as configuration reviewable and extendable without a deploy. Without this, `customer.status = active` vs. `inactive` (genuinely conflicting) and `customer.address = Hyderabad` vs. `Mumbai` (legitimate history, not a conflict) are indistinguishable to the detector, and the deterministic layer will drown in false positives on exactly the predicates that change normally.
2. `MemoryContradiction` table: `id, workspace_id, fact_a_id, fact_b_id, contradiction_type, confidence, status, detected_at, resolved_at, resolution, resolved_by`. Statuses: `DETECTED / UNDER_REVIEW / RESOLVED_A / RESOLVED_B / BOTH_VALID / DISMISSED`. Types: `VALUE_CONFLICT / TEMPORAL_CONFLICT / RELATIONSHIP_CONFLICT / SOURCE_CONFLICT / DIRECT_NEGATION`.
3. Deterministic layer (ship first, behind `FEATURE_CONTRADICTION_DETECTION_ENABLED`): same-subject, same-predicate comparison gated by the policy from task 1, run as an async post-ingest job, idempotent via a `contradiction_job_id` and a unique constraint so the same fact pair is never flagged twice by overlapping job runs. Takes an advisory lock keyed on the fact pair (or workspace) during detection so two concurrent workers can't create duplicate contradiction records.
4. Temporal check before flagging: for predicates marked `temporal: YES` in the policy, a value change across dated Facts is evaluated as a possible legitimate update first, cross-referencing the existing `temporal_status`/`superseded_by_id` semantics — not flagged as a contradiction by default.
5. Semantic layer (Layer 2, NLI/LLM-based): separate flag `FEATURE_SEMANTIC_CONTRADICTION_ENABLED`, off by default. Do not enable until the deterministic layer has run in production for a defined soak period with a measured, acceptable false-positive rate.
6. Every detection defaults to `UNDER_REVIEW`, never auto-resolved. Extend the existing Facts/Decisions pages (`frontend/src/app/projects/[id]/facts`, `.../decisions`) with a contradiction indicator and resolve action, gated by a new `require_policy("memory", "review")` scope following the existing policy pattern.

**Tests**

- Unit: deterministic detector on structured fixtures — true positives, true negatives, and policy-driven non-contradictions (e.g. a `temporal: YES`, `mutually_exclusive: NO` predicate like address).
- Unit: the async job does not measurably slow the M0–M4 pipeline; rerunning the job on the same batch is a no-op (idempotency).
- Concurrency: two workers processing the same fact pair concurrently produce exactly one contradiction record, not two.
- Recovery: kill the contradiction worker mid-batch, restart it, verify it resumes without duplicate records.
- Playwright: the review UI surfaces `UNDER_REVIEW` items and records a resolution.

**Certification gate — Gate 5**

| Check | Expected |
| --- | --- |
| Predicate policy | Exists, reviewed, covers every predicate the detector compares |
| Non-blocking | Ingest latency unchanged vs. Phase 4 baseline |
| False-positive rate | Measured on a reviewed sample, documented — not assumed |
| No auto-resolution | 100% of detections start `UNDER_REVIEW` |
| Idempotency & concurrency | Rerun produces no duplicates; concurrent-worker test passes |
| No data loss | Zero rows deleted from `facts`/`decisions` as a result of contradiction handling |
| pytest / Playwright | No regressions |

**Output:** `PHASE_5_CERTIFICATION.md`.

## Phase 6 — Memory consolidation

**Preconditions:** Phase 5 = PASS.

**Objective:** merge duplicate or contradiction-resolved memories into a canonical record with fully preserved, navigable lineage — never forcing a winner when two candidates are genuinely too close to call.

**Implementation scope:** `app/services/memory_intelligence/consolidation.py`, `app/models.py` (new `memory_lineage` relationship table — or, as a design decision to make explicitly before migration 016, new edge types on the existing `GraphNode`/`GraphEdge` tables, which already model entity relationships; don't default to a parallel structure without weighing that option first), `alembic/versions/016_*`.

**Tasks**

1. Define the canonical-memory scoring function explicitly before writing code — e.g. `canonical_score = authority * confidence * recency_decay(temporal_status)`, corroboration count as a tiebreaker. Goes into a short design note reviewed before implementation.
2. Three outcomes, not one automatic winner: `CANONICAL` (clear winner), `CONSOLIDATION_PENDING_REVIEW` (scores too close — e.g. `|score_a - score_b| < 0.05`, routed to human review rather than an arbitrary pick), `CONFLICTING` (the cluster includes an unresolved Phase 5 contradiction — consolidation waits on that resolution).
3. Consolidation pipeline: find similar memories (embedding similarity from Phase 1) → cluster → detect duplicates → cross-reference Phase 5 contradiction resolutions → apply the three-outcome scoring from task 2 → for `CANONICAL` clusters, create the consolidated `Memory` with a lineage record per source.
4. Never physically delete source rows. Record lineage as `memory_lineage` rows: `id, derived_memory_id, source_memory_id, relationship_type, confidence, created_at, run_id, agent_id`, with `relationship_type` one of `DERIVED_FROM / CONSOLIDATED_FROM / SUPERSEDES / SUPPORTED_BY / CONTRADICTS / CORROBORATED_BY` — so provenance can answer "why does the system believe this" as a navigable graph, not a single flat pointer.
5. A consolidated `Memory C` gets its own freshly computed embedding from its own canonical content — never inherited from a source record, since C's text may not match any single source verbatim.
6. Idempotency and concurrency: a `consolidation_job_id` per run; rerunning consolidation on the same cluster produces the same canonical record (no duplicate); a row-level or advisory lock on the cluster during consolidation so two workers can never create two different canonical memories from the same source set.
7. Add `GET /api/v1/memory/{id}/lineage`, following the existing provenance router pattern (`app/api/provenance.py`), returning the full lineage graph by relationship type.

**Tests**

- Unit: the scoring function against fixtures with known expected winners, including a deliberately close tie that must route to `CONSOLIDATION_PENDING_REVIEW`, not an arbitrary pick.
- Unit: consolidation never issues a `DELETE` on `facts`/`memories`/`decisions` — asserted via a DB-call spy, not code review alone.
- Integration: consolidate three near-duplicate memories, verify the lineage endpoint returns all three sources plus the canonical record with correct relationship types.
- Concurrency: two workers consolidating the same cluster concurrently produce exactly one canonical memory.
- Recovery: kill the consolidation job halfway, restart it, verify no duplicate canonical memory is created.

**Certification gate — Gate 6**

| Check | Expected |
| --- | --- |
| Scoring function documented | Design note exists, reviewed before implementation, matches shipped code |
| Three outcomes | `CONSOLIDATION_PENDING_REVIEW` and `CONFLICTING` verified by test, not just `CANONICAL` |
| Zero destructive ops | Verified by test spy |
| Lineage graph | `/lineage` endpoint returns the full relationship-typed derivation chain |
| Fresh embedding | Canonical memories never inherit a source's embedding, verified by test |
| Idempotency & concurrency | Rerun and concurrent-worker tests pass |
| pytest / Playwright | No regressions |

**Output:** `PHASE_6_CERTIFICATION.md`.

## Phase 7 — Unified certification

**Preconditions:** Phases 0–6 = PASS.

**Objective:** certify the complete Memory Intelligence + Execution Integrity layer as a whole, in the same style as `RECOVERY_CERTIFICATION.md` — full regression, full end-to-end trace, full flag audit.

**Tasks**

1. Full pytest run, full Playwright run, `tsc --noEmit`, `npm run lint`, `npm run build` — compared against the Phase 0 baseline, zero net regressions.
2. Flag audit: enumerate every feature flag introduced in Phases 1, 3, and 5, and its current default. Confirm each is an intentional decision for the target environment, not an accidental leftover in shadow mode.
3. End-to-end trace test: one request through the full spine — `ExecutionContext` → M0–M4 → contradiction check → M5 retrieval → reranking → context builder → LLM → tool execution → memory write → consolidation eligibility → audit — verified by a single `trace_id`/`correlation_id` appearing consistently across every log and audit row it touches.
4. Row-count and data-integrity check against the Phase 0 baseline: no unexplained deletions across `memories`, `facts`, `decisions`, `graph_nodes`.
5. Produce `MEMORY_INTELLIGENCE_CERTIFICATION.md` in the exact evidence/gate-table format of `RECOVERY_CERTIFICATION.md` — Executive Verdict, Evidence Summary, Findings, Outstanding Items, Not in Scope.

**Certification gate — Gate 7 (final)**

| Check | Expected |
| --- | --- |
| Full regression | 0 new failures vs. Phase 0 baseline |
| Flag audit | Every flag's state is a documented decision |
| End-to-end trace | A single `trace_id` visible across the full spine |
| Data integrity | No unexplained row loss |

**Output:** `MEMORY_INTELLIGENCE_CERTIFICATION.md` — the terminal artifact of this prompt.

## Phase 8 — Memory quality score

**Preconditions:** Phase 7 = PASS. This phase is an extension of the core layer, not a blocker for it — Phase 7's certification stands on its own.

**Objective:** separate `confidence` (how certain extraction was) from a new `MemoryQualityScore` (how trustworthy and useful the resulting persistent memory actually is) — two different concepts the current model conflates by only having the first.

**Implementation scope:** `app/services/memory_intelligence/quality.py`, `alembic/versions/017_*` (new `MemoryQualityScore` fields), reads the existing `MessageFeedback` model for a retrieval-usefulness signal.

**Tasks**

1. Define `MemoryQualityScore` inputs: source authority, confidence, corroboration count (via `memory_lineage` from Phase 6), recency, contradiction status (via `MemoryContradiction` from Phase 5), provenance completeness, retrieval usefulness.
2. Retrieval usefulness starts as a placeholder, low-weighted term — no feedback loop exists yet. Wire it to the existing `MessageFeedback` model as usage data accumulates, and document the minimum feedback volume before this term is trusted at full weight.
3. Recompute the quality score on every consolidation event and on a scheduled interval (decay over time). Never let this recomputation write to `confidence` — the two fields must stay independent.
4. Surface the quality score on the existing Memory/Facts/Decisions frontend pages as a visible indicator, and make it available to Phase 3's reranker as an optional additional bounded adjustment — not required for Phase 3 to ship; this is a later enhancement to it.

**Tests**

- Unit: scoring function against fixtures with known expected scores.
- Unit (regression guard): recomputing quality never mutates `confidence` on the same row.

**Certification gate — Gate 8**

| Check | Expected |
| --- | --- |
| Distinct from confidence | Verified: quality recomputation never writes to `confidence` |
| Computed post-consolidation | Every canonical memory has a quality score |
| Feedback signal documented | Placeholder weighting and minimum-volume threshold specified in writing |
| pytest / Playwright | No regressions |

**Output:** `PHASE_8_CERTIFICATION.md`.

## Appendix — Certification report template & severity reference

Every `PHASE_N_CERTIFICATION.md` follows this shape, matching `RECOVERY_CERTIFICATION.md`:

| Section | Contents |
| --- | --- |
| Executive verdict | One line: CERTIFIED / BLOCKED, and why |
| Evidence summary | Gate |
| Findings | # · Severity · Description, using the severity table below |
| Outstanding items | Item · Priority · Notes — carried into the next phase or flagged for follow-up |
| Not in scope | What this phase deliberately did not touch |

**Gap severity system** (reused from the existing architecture docs):

| Severity | Meaning |
| --- | --- |
| P0 | Critical — data loss, security breach, or system failure possible. Blocks certification. |
| P1 | High — functional impairment, data inconsistency, or security weakness. Blocks certification. |
| P2 | Medium — missing capability, technical debt, maintainability risk. Logged, does not block. |
| P3 | Low — nice-to-have, documentation gap, minor inconsistency. Logged, does not block. |

**Escalation rule:** a P0 or P1 found during any phase is reported in that phase's own certification document and blocks that phase's PASS verdict — it is never silently deferred to Phase 7's flag audit.

**References this prompt builds on:** `RECOVERY_CERTIFICATION.md`, `SWARMVAULT_ARCHITECTURE_PROMPT.md`, `SWARMVAULT_BACKEND_ARCHITECTURE.md`, `SWARMVAULT_DOMAIN_MANIFEST.md`, `SWARMVAULT_CODEBASE_INDEX.md`, `SWARMVAULT_SECURITY_OPERATIONAL_ARCHITECTURE.md`.

Phases with asynchronous jobs (1, 5, 6, 8) additionally follow Operating Rule 7's idempotency, concurrency, and crash-recovery checklist — each such phase's certification report includes evidence for all three, not just its own gate table. Phase 8 (memory quality) is an optional extension gated on Phase 7, not a precondition for the core layer's certification.
