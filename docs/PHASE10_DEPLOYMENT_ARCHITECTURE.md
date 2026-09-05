# PHASE10_DEPLOYMENT_ARCHITECTURE.md

## Phase 10 — Deployment Architecture

**Date:** 2026-09-05
**Baseline SHA:** `39ce4b4`

---

## Deployment Configuration

### Services (docker-compose.yml)

| Service | Image | Port | Restart | Health Check |
|---------|-------|------|---------|--------------|
| postgres | postgres:16-alpine | 127.0.0.1:5432 | unless-stopped | pg_isready |
| app | Built from Dockerfile | 127.0.0.1:8000 | unless-stopped | /health/ready |

### Volumes

| Volume | Mount Point | Purpose |
|--------|-------------|---------|
| postgres_data | /var/lib/postgresql/data | Database persistence |
| app_storage | /app/storage | File uploads |
| app_logs | /app/logs | Application logs |

### Networks

| Network | Driver | Purpose |
|---------|--------|---------|
| swarmvault | bridge | Service isolation |

### Environment Variables (Backend)

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| SECRET_KEY | Yes | (empty) | JWT signing secret |
| DATABASE_URL | Yes | (empty) | PostgreSQL connection |
| ENVIRONMENT | No | development | Runtime mode |
| CORS_ORIGINS | No | (empty) | Allowed origins |
| ANTHROPIC_API_KEY | No | (empty) | LLM provider |
| OPENAI_API_KEY | No | (empty) | LLM provider |

### Environment Variables (Frontend)

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| NEXT_PUBLIC_API_URL | Yes | http://localhost:8000 | Backend URL |
| NEXT_PUBLIC_APP_NAME | No | SwarmVault | App display name |

### Startup Order

1. PostgreSQL (depends_on: condition=service_healthy)
2. Backend (depends_on: postgres service_healthy)
   - Runs `alembic upgrade head` then starts uvicorn
3. Frontend (Next.js dev server on port 3000)

### Backend Dockerfile

- Multi-stage build: python:3.12-slim
- Non-root user (swarmvault)
- Alembic migrations run on container start
- Uvicorn with 2 workers
- Health check: /health/live every 30s

### Docker Build Status

**BLOCKED** — Docker is not available on this Windows Server environment.
Docker build, image tagging, and container replacement cannot be verified.
This is an environmental limitation, not a product issue.

### Deployment Modes

| Mode | Method | Status |
|------|--------|--------|
| Docker Compose | docker-compose up | BLOCKED (no Docker) |
| Direct uvicorn | uvicorn app.main:app | ✅ Available |
| Direct Next.js | npm run dev | ✅ Available |
| PostgreSQL service | Docker or local | ✅ Available (local) |

### Frontend Deployment

No Dockerfile for frontend. Deployed via:
- `npm run dev` (development)
- `npm run build && npm start` (production)
- Single env var required: `NEXT_PUBLIC_API_URL`

### Database Migration

- Alembic configured with `alembic.ini`
- 12 migration files (001_initial through 012_add_invitations)
- Migration chain verified linear
- Runs automatically on container startup

---

## Production Readiness Assessment

| Component | Status | Notes |
|-----------|--------|-------|
| Docker images | BLOCKED | Docker unavailable |
| Docker Compose | BLOCKED | Docker unavailable |
| Container health checks | Reviewed | Config present, untested |
| Non-root user | ✅ | swarmvault user in Dockerfile |
| Volume persistence | Reviewed | postgres_data, app_storage, app_logs |
| Network isolation | Reviewed | swarmvault bridge network |
| Secret management | Reviewed | Env vars, no hardcoded secrets |
| Startup order | Reviewed | PostgreSQL → Backend → Frontend |
| Auto-migration | ✅ | alembic upgrade head on startup |
| Restart policy | ✅ | unless-stopped |
