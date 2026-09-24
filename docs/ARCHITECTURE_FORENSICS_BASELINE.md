# Architecture Forensics Baseline

**Phase**: M-ARCH — Memory Architecture Freeze Gate
**Purpose**: Immutable record of the source control state before any forensic analysis.
**Created**: 2026-09-10

---

## 1. Repository Identity

| Field | Value |
|-------|-------|
| **Repository Root** | `C:\Users\Administrator\Documents\SwarmVaultwebapp` |
| **Git Branch** | (to be confirmed — run `git branch --show-current`) |
| **HEAD SHA** | `e6f4b1c157afaed052584963b942ea04f9661610` |
| **Analysis Timestamp** | 2026-09-10 |
| **Forensic Status** | Source-first — all claims traceable to executable implementation |

---

## 2. Working Tree State

| Status | Count | Details |
|--------|-------|---------|
| **Modified files** | (pending `git status`) | |
| **Untracked files** | (pending `git status`) | |
| **Staged files** | (pending `git status`) | |

> Run `git status` before analysis to confirm clean working tree.

---

## 3. Repository Structure

```
C:\Users\Administrator\Documents\SwarmVaultwebapp/
├── app/                          # BACKEND — FastAPI application
│   ├── main.py                   # Application entry point
│   ├── core/
│   │   ├── config.py             # Configuration (Pydantic Settings)
│   │   └── security.py           # Password hashing, JWT utilities
│   ├── db.py                     # Database engine + session factory
│   ├── models.py                 # SQLAlchemy ORM models
│   ├── schemas.py                # Pydantic request/response schemas
│   ├── middleware/
│   │   ├── tenancy.py            # TenantContext, JWT decode, workspace membership
│   │   ├── rbac.py               # Role hierarchy, permission matrix
│   │   ├── rate_limit.py         # Sliding window rate limiter
│   │   └── cors.py               # CORS configuration
│   ├── api/
│   │   ├── auth.py               # Authentication endpoints
│   │   ├── workspace.py          # Workspace CRUD
│   │   ├── projects.py           # Project CRUD
│   │   ├── sessions.py           # Session management
│   │   ├── chat.py               # Chat (streaming + non-streaming)
│   │   ├── memory.py             # Memory CRUD
│   │   ├── ingest.py             # Conversation ingestion
│   │   ├── provenance.py         # Provenance queries
│   │   ├── api_keys.py           # API key management
│   │   ├── policy.py             # Policy management
│   │   ├── audit.py              # Audit log queries
│   │   ├── storage.py            # Object storage (S3/MinIO)
│   │   ├── dashboard.py          # Dashboard statistics
│   │   └── feedback.py           # Message feedback
│   ├── services/
│   │   ├── pipeline.py           # M0–M5 ingestion orchestrator
│   │   ├── connectors.py         # M0 normalization (7 connectors)
│   │   ├── m1_session.py         # M1 session understanding
│   │   ├── m2_facts.py           # M2 fact/decision extraction
│   │   ├── m3_temporal.py        # M3 temporal supersession
│   │   ├── m4_graph.py           # M4 graph construction
│   │   ├── m5_retrieval.py       # M5 multi-factor retrieval
│   │   ├── retrieval.py          # Hybrid vector+keyword retrieval
│   │   ├── memory.py             # MemoryService, MemoryRecord
│   │   ├── chat_orchestrator.py  # Chat with provenance
│   │   ├── llm.py                # LLM provider abstraction
│   │   ├── object_storage.py     # Object storage abstraction
│   │   ├── object_storage_s3.py  # S3 backend
│   │   ├── object_storage_minio.py # MinIO backend
│   │   └── audit/
│   │       ├── service.py        # AuditService
│   │       ├── repository.py     # AuditRepository
│   │       └── constants.py      # Event taxonomy
│   └── services/policy/
│       ├── engine.py             # Policy Engine
│       ├── evaluator.py          # RBAC policy generation
│       ├── dependencies.py       # FastAPI policy dependency
│       └── repository.py         # Policy persistence
├── frontend/                     # FRONTEND — Next.js application
│   ├── package.json
│   ├── next.config.js
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── src/app/
│   │   ├── globals.css           # Design system foundation
│   │   ├── layout.tsx            # Root layout
│   │   ├── page.tsx              # Home
│   │   ├── dashboard/            # Dashboard
│   │   ├── projects/             # Projects
│   │   ├── chat/                 # Chat
│   │   ├── sessions/             # Sessions
│   │   ├── memory/               # Memory
│   │   ├── facts/                # Facts
│   │   ├── decisions/            # Decisions
│   │   ├── timeline/             # Timeline
│   │   ├── search/               # Search
│   │   ├── graph/                # Graph visualization
│   │   ├── provenance/           # Provenance
│   │   ├── ingestion/            # Ingestion
│   │   └── settings/             # Settings
│   └── src/components/           # Shared components
│   └── src/lib/                  # Utilities, API client
├── docs/                         # Architecture documentation
│   ├── MEMORY_ARCHITECTURE_DECISION_RECORD.md
│   ├── MEMORY_INTELLIGENCE_READINESS_CERTIFICATION.md
│   ├── CANONICAL_MEMORY_CONTRACT.md
│   ├── CANONICAL_RETRIEVAL_CONTRACT.md
│   ├── TEMPORAL_KNOWLEDGE_STATE_CONTRACT.md
│   ├── PROVENANCE_EVIDENCE_CONTRACT.md
│   ├── MEMORY_WRITE_AUTHORITY_MATRIX.md
│   ├── DERIVED_STATE_CONTRACT.md
│   ├── MEMORY_FAILURE_RECOVERY_CONTRACT.md
│   ├── UNIVERSAL_AGENT_EVENT_CONTRACT.md
│   ├── MEMORY_IDENTITY_CONTRACT.md
│   └── SWARMVAULT_MASTER_GAP_SYNTHESIS.md
├── alembic/                      # Database migrations
├── tests/                        # Test suite
├── .env.example                  # Environment template
├── Dockerfile                    # Container definition
├── docker-compose.yml            # Local development stack
└── pyproject.toml                # Python project config
```

---

## 4. Technology Stack

### Backend

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | FastAPI | ^15.0.0 |
| Language | Python | 3.11+ |
| ORM | SQLAlchemy 2.0 (async) | — |
| Database | PostgreSQL (asyncpg) | — |
| LLM | Anthropic Claude (primary) | — |
| Auth | JWT (python-jose) + bcrypt/argon2 | — |
| Validation | Pydantic v2 | — |
| Object Storage | S3 / MinIO | — |

### Frontend

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Next.js | ^15.0.0 |
| Language | TypeScript | 5.x |
| UI | React | 18.3 |
| Styling | Tailwind CSS | 3.4 |
| Icons | lucide-react | ^0.468 |
| Font | Inter (sans), JetBrains Mono (mono) | — |

---

## 5. Key Architectural Decisions (Pre-existing)

| Decision | Status | Location |
|----------|--------|----------|
| Memory model uses separate tables (Fact, Decision, Memory) | BINDING | `MEMORY_ARCHITECTURE_DECISION_RECORD.md:001` |
| Memory model excluded from M5 retrieval | BINDING | `MEMORY_ARCHITECTURE_DECISION_RECORD.md:003` |
| No background ingestion worker | BINDING | `MEMORY_ARCHITECTURE_DECISION_RECORD.md:006` |
| No semantic/embedding retrieval | BINDING | `MEMORY_ARCHITECTURE_DECISION_RECORD.md:005` |
| Two divergent retrieval services | BINDING | `MEMORY_ARCHITECTURE_DECISION_RECORD.md:003` |

---

## 6. Analysis Scope

This forensic analysis covers:

- **Backend**: All files under `app/`
- **Frontend**: All files under `frontend/src/`
- **Tests**: All files under `tests/`
- **Migrations**: All files under `alembic/`
- **Deployment**: Dockerfile, docker-compose.yml
- **Configuration**: .env.example, pyproject.toml
- **Documentation**: All files under `docs/`

**Excluded from scope**: node_modules, __pycache__, .git, alembic/versions (migration bodies reviewed for schema only).

---

## 7. Forensic Principles

1. **Source-first**: Every claim traces to an executable file path:line
2. **No invention**: Only IMPLEMENTED/PARTIAL/MISSING/DOCUMENTED/UNKNOWN classifications
3. **No modification**: This phase documents only — no code changes
4. **Discrepancy flagging**: Documentation that contradicts code is flagged, not silently corrected
5. **Evidence tables**: Every significant claim has a file:line citation

---

*Baseline locked. Analysis proceeds from this state.*
