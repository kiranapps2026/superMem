# SwarmVault Enterprise Architecture Prompt — v1 → v2 Crosswalk

This document explains every change made to the original enterprise architecture
forensic prompt (v1) to produce the improved version (v2).

File: `docs/ENTERPRISE_ARCHITECTURE_PROMPT_CROSSWALK.md`

---

## Summary of Changes

| Dimension | v1 | v2 |
|-----------|----|----|
| Specialist agents | 7 + 1 synthesis | 9 + 1 synthesis |
| Final documents | 8 | 8 (restructured) |
| Memory stages | M0–M5 | M0–M6 |
| Lineage requirement | General guidance | Per-transition IO contracts |
| Evidence requirement | Implied | Explicit EVIDENCE TABLE mandate |
| Frontend ↔ Backend | Part of final doc | Separate final document |
| Infrastructure | Not covered | New Agent 8 |
| Test architecture | Not covered | New Agent 9 |
| Memory safety gates | Not explicitly required | Required matrix output |
| Fact/Inference labeling | Not required | Required for every claim |

---

## Change 1: Added Two New Specialist Agents

### Agent 8 — Infrastructure & Deployment Architecture

**Why:** The v1 prompt had no agent analyzing deployment, containerization,
environment configuration, or operational concerns. This is a critical gap for
an enterprise architecture document.

**What it covers:**
- Dockerfile(s) and multi-stage builds
- docker-compose.yml services, volumes, networks
- Environment variable mapping (.env.example → settings)
- PostgreSQL configuration and connection management
- Object storage configuration (filesystem vs S3)
- Process management (uvicorn/gunicorn, workers, timeouts)
- Network architecture (ports, reverse proxy, TLS)
- Scaling considerations
- Monitoring and observability (logging, metrics, health checks)
- Backup and restore strategy

**Output:** `docs/SWARMVAULT_INFRASTRUCTURE_DEPLOYMENT.md`

### Agent 9 — Test Architecture

**Why:** The v1 prompt had no agent analyzing test coverage, test gaps, or
test patterns. Test coverage is essential for understanding what is actually
verified vs assumed to work.

**What it covers:**
- Test inventory (directories, files, runners)
- Test coverage by domain (auth, tenancy, pipeline, etc.)
- Test patterns (fixtures, mocking, DB setup)
- E2E tests (Playwright scenarios)
- Test gaps analysis (what is NOT tested and why it matters)

**Output:** `docs/SWARMVAULT_TEST_ARCHITECTURE.md`

---

## Change 2: Added Memory Stage M6

**Why:** The v1 prompt documented M0–M5 but stopped at retrieval. Modern memory
systems require a stage for memory intelligence operations — the layer where
memory becomes actionable (reasoning, contradiction detection, consolidation,
lifecycle management).

**What M6 covers:**
- Memory intelligence operations
- Contradiction detection and resolution
- Memory consolidation
- Memory lifecycle management
- Intelligence-layer readiness assessment
- Safety gate enforcement before persistence

**Impact on all agents:** Every specialist must now document how data flows
through M6, not just M0–M5.

---

## Change 3: Explicit IO Contracts at Every Data Transition

**Why:** The v1 prompt asked for data tracing but did not specify the exact
contract format. The v2 prompt mandates a structured contract for every
transition:

```
TRANSITION: [name]
Source: [file:function] → Destination: [file:function]
├─────────────────────────────────────────────────────────────────┤
│ INPUT:    schema, fields, types, source system
│ OUTPUT:   schema, fields, types, destination system
│ TRANSFORM: function, logic summary, line number
│ VALIDATE: checks performed, failure handling
│ GUARDRAIL: security/safety control, bypassability
│ FAILURE:  error type, code, user effect
│ PERSIST:  table/collection, write semantics
│ PROVENANCE: trace data generated
│ MEMORY QUALITY: effect on downstream reliability
└─────────────────────────────────────────────────────────────────┘
```

**Impact:** This forces every specialist to be explicit about what each stage
consumes, produces, and how failures propagate.

---

## Change 4: Explicit EVIDENCE TABLE Requirement

**Why:** The v1 prompt asked for citations but did not mandate a structured
evidence table. The v2 prompt requires an EVIDENCE TABLE in every specialist
document:

```
| Claim | File | Line | Function/Route | Confidence |
|-------|------|------|----------------|------------|
```

**Impact:** Forces verifiable claims. Prevents architectural fiction.

---

## Change 5: Added Fact/Inference/Unknown Labeling

**Why:** The v1 prompt did not require distinguishing between verified facts
and inferences. The v2 prompt mandates labeling every claim:

- **[FACT]** — directly verified in source code
- **[INFERRED]** — reasonable conclusion from source, not explicitly stated
- **[UNKNOWN]** — could not determine from available source

**Impact:** The synthesis agent can now identify contradictions between
specialist claims and resolve them by re-reading source.

---

## Change 6: Frontend ↔ Backend Contract Matrix as Separate Final Document

**Why:** In v1, the frontend/backend contract was part of the master
architecture document. In v2, it is a separate, detailed document
(Final Document 5) because the matrix is large and needs standalone
maintainability.

**What it adds:**
- Per-screen breakdown: SCREEN → COMPONENT → STATE → API → BACKEND → DATABASE
- Token lifecycle detail
- Error handling patterns
- Loading/empty/error state documentation
- Frontend/backend mismatch identification
- Sequence diagrams for auth flow

---

## Change 7: Memory Safety Gate Matrix

**Why:** The v1 prompt did not explicitly require documenting which conditions
must be satisfied before information becomes persistent memory. The v2 prompt
requires a Memory Safety Gate Matrix as part of Agent 7's output:

```
┌──────────────────────────────────────────────────────────────────┐
│ GATE: [condition that must be satisfied]
│ CHECK: [where it is enforced]
│ ON FAIL: [what happens — block / warn / allow]
│ BYPASSABLE: YES / NO
│ TESTED: YES / NO
│ STAGE: [which M stage]
└──────────────────────────────────────────────────────────────────┘
```

**Impact:** This directly answers "what must be true before this becomes
memory?" — a critical question for the Next Memory Intelligence Layer.

---

## Change 8: Lineage Diagrams in Every Specialist Document

**Why:** The v1 prompt had a cross-agent lineage requirement but did not
require each specialist to produce its own lineage diagram. The v2 prompt
mandates a LINEAGE DIAGRAM in every specialist document using the canonical
pipeline structure.

**Impact:** Each specialist's document is self-contained with visual data flow.

---

## Change 9: Temporal Interpretation Requirements

**Why:** The v1 prompt asked about temporal processing but did not require
temporal interpretation at every stage. The v2 prompt explicitly requires
documenting how temporal information is interpreted, transformed, and used
at each pipeline stage.

**Impact:** Ensures temporal semantics are traced from raw input through
persistence to retrieval.

---

## Change 10: Security Boundary Requirements

**Why:** The v1 prompt did not explicitly require security boundary
documentation at each integration point. The v2 prompt requires every
integration point to document:

- What security boundary is crossed
- How the boundary is enforced
- What happens if enforcement fails
- Whether the boundary can be bypassed

**Impact:** Creates a security boundary map as a first-class artifact.

---

## Change 11: Restructured Final Documents

The 8 final documents in v2 are restructured for clarity:

| v1 | v2 | Change |
|----|----|--------|
| Master Architecture | Master Architecture | Expanded from 16 to 31 sections |
| End-to-End Flows | End-to-End Flows | Added M6, Provenance, Supersession flows |
| Guardrail Matrix | Guardrail Master Matrix | Added Memory Safety Gate sub-matrix |
| Data & Memory Readiness | Persistent Memory Readiness | Added explicit M6 analysis |
| Frontend ↔ Backend | Frontend ↔ Backend Architecture | Expanded to standalone doc |
| Traceability | Architectural Traceability | Added M6 and Infrastructure |
| Gaps & Next Layer | Architectural Gaps & Next Layer | Added P3 classification |
| Architecture Index | Architecture Index | Added glossary requirement |

---

## Change 12: Output Contract Clarification

The v2 prompt ends with a clear OUTPUT CONTRACT section listing all 18
documents with exact paths. This eliminates ambiguity about what the
analysis produces.

---

## Change 13: Quality Standards Section

The v2 prompt adds a QUALITY STANDARDS section requiring:

- **Completeness:** Every file/route/model must be analyzed
- **Accuracy:** Every claim backed by evidence
- **Traceability:** Every capability has an evidence trail
- **Classification:** Every feature/gap has a status classification
- **Lineage:** Every flow has a diagram
- **Actionability:** Every gap has a path to resolution

---

## What Was Removed from v1

1. The v1 prompt's "ABSOLUTE RULES" were preserved but enhanced
2. The v1 prompt's phase structure was preserved with enhancements
3. No significant content was removed — only restructured and enhanced

---

## Migration Notes

If an analysis was started with v1:

1. Complete the 7 specialist agents already in progress
2. Add Agent 8 (Infrastructure) and Agent 9 (Test) analysis
3. Update Agent 7 to include M6 analysis
4. Update all specialists to include IO contracts and evidence tables
5. Re-run synthesis with the new final document structure

---

## Rationale for Each Change

| Change | Rationale |
|--------|-----------|
| Agent 8 | Enterprise architecture must address deployment/operations |
| Agent 9 | Test coverage is the only objective measure of reliability |
| M6 stage | Memory systems need an intelligence operations layer |
| IO contracts | Prevents vague "data flows through pipeline" descriptions |
| Evidence tables | Enables verification, prevents architectural fiction |
| Fact/Inference | Enables contradiction resolution in synthesis |
| Separate F↔B doc | Frontend/backend contract is large enough for its own doc |
| Memory safety gates | Critical for persistent memory trust boundary |
| Lineage diagrams | Makes data flow visible without reading prose |
| Temporal requirements | Temporal semantics are core to memory quality |
| Security boundaries | Security is a cross-cutting concern, not an afterthought |
