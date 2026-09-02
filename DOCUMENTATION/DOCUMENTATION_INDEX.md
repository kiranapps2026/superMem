# SwarmVault WebApp — Documentation Index
**Version:** 1.0.0
**Date:** 2026-09-01
**Commit:** 902d85e81b3e08c79cecf189ac2b5d55a5769cfa

---

## Documentation Hierarchy

```text
SWARMVAULT WEBAPP DOCUMENTATION
│
├── PHASE 1 — FOUNDATION
│   ├── 01_MASTER_ARCHITECTURE.md
│   │   System identity, product architecture, multi-tenant model,
│   │   backend/frontend/data/memory/security/deployment architecture,
│   │   data lifecycle, architectural boundaries, capability map, glossary
│   │
│   └── 02_PRODUCT_AND_CAPABILITY_CATALOG.md
│       Per-capability reference: purpose, user journey, inputs, outputs,
│       API, UI, permissions, dependencies, security, testing, status
│
├── PHASE 2 — TECHNICAL SYSTEM
│   ├── 03_BACKEND_IMPLEMENTATION_REFERENCE.md
│   │   Repository structure, every module, API-to-service-to-model mapping,
│   │   database, migrations, configuration, dependencies
│   │
│   └── 04_MEMORY_KNOWLEDGE_AND_M0-M5.md
│       Authoritative developer reference for M0–M5 intelligence pipeline,
│       knowledge lifecycle, temporal truth, graph, retrieval, provenance
│
├── PHASE 3 — PRODUCT SURFACE
│   ├── 05_API_CONTRACT_REFERENCE.md
│   │   Complete API reference: every verified endpoint with method, route,
│   │   schemas, auth, errors, pagination, security
│   │
│   └── 06_UI_PRODUCT_AND_EXPERIENCE_GUIDE.md
│       Every verified UI surface: pages, components, user flows,
│       permissions, states, responsive behavior
│
└── PHASE 4 — OPERATIONS
    ├── 07_INTEGRATION_CATALOG.md
    │   Every verified external integration with auth, capabilities,
    │   data mapping, security, and testing
    │
    └── 08_DEPLOYMENT_MIGRATION_TESTING_AND_CERTIFICATION.md
        Deployment, Docker, migration, backup/restore, testing strategy,
        certification evidence, rollback procedures
```

---

## Cross-Reference Matrix

| Document | Read First | Then Read |
|----------|-----------|-----------|
| 01_MASTER_ARCHITECTURE | — | 02, 03, 04, 05, 07, 08 |
| 02_PRODUCT_AND_CAPABILITY_CATALOG | 01 | 04, 05, 06 |
| 03_BACKEND_IMPLEMENTATION_REFERENCE | 01 | 04, 05, 08 |
| 04_MEMORY_KNOWLEDGE_AND_M0-M5 | 01, 03 | 05 |
| 05_API_CONTRACT_REFERENCE | 03 | 06 |
| 06_UI_PRODUCT_AND_EXPERIENCE_GUIDE | 02, 05 | — |
| 07_INTEGRATION_CATALOG | 01, 03 | 08 |
| 08_DEPLOYMENT_MIGRATION_TESTING_AND_CERTIFICATION | 01, 03 | — |

---

## Key Evidence Sources

| Source | Location |
|--------|----------|
| Source code | `C:\Users\Administrator\Documents\SwarmVaultwebapp\app\` |
| Tests | `C:\Users\Administrator\Documents\SwarmVaultwebapp\tests\` |
| Migrations | `C:\Users\Administrator\Documents\SwarmVaultwebapp\alembic\versions\` |
| Frontend | `C:\Users\Administrator\Documents\SwarmVaultwebapp\frontend\` |
| Deployment | `C:\Users\Administrator\Documents\SwarmVaultwebapp\Dockerfile`, `docker-compose.yml` |
| Certification | `C:\Users\Administrator\Documents\SwarmVaultwebapp\CERTIFICATION\` |

---

## Terminology Quick Reference

| Term | Definition |
|------|-----------|
| Tenant | Top-level organization boundary |
| Workspace | Collaborative space within a tenant |
| Project | Knowledge container within a workspace |
| Session | Conversation context within a project |
| Memory | Extracted/persisted knowledge unit |
| Fact | Extracted factual statement (subject-predicate-object) |
| Decision | Extracted decision record |
| Source | Ingested conversation/document |
| Provenance | Evidence chain linking answer to sources |
| M0 | Normalization & deduplication |
| M1 | Session understanding |
| M2 | Fact/decision extraction |
| M3 | Temporal truth processing |
| M4 | Knowledge graph construction |
| M5 | Retrieval & intelligence |
