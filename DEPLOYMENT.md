# SwarmVault WebApp — Deployment Runbook
**Version:** 1.0.0
**Date:** 2026-09-01

---

## 1. Prerequisites

| Item | Requirement |
|------|-------------|
| Docker | 24.0+ |
| Docker Compose | 2.20+ |
| PostgreSQL | 16+ (if external) |
| Python | 3.12+ (if bare metal) |
| Disk | 10 GB minimum (app + data) |
| Memory | 2 GB minimum |

---

## 2. First Deployment (Docker)

```bash
# 1. Clone the repository
git clone <repo-url> && cd SwarmVaultwebapp

# 2. Create .env from template
cp .env.example .env

# 3. Generate a secret key (one-time)
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Paste the output into SWARMMAULT_SECRET_KEY in .env

# 4. Set the database password
# Edit .env: set SWARMMAULT_DB_PASSWORD to a strong random value

# 5. Set CORS origins
# Edit .env: set SWARMMAULT_CORS_ORIGINS to your frontend URL(s)
# Example: SWARMMAULT_CORS_ORIGINS=https://app.example.com

# 6. Start services
docker compose up -d

# 7. Verify
curl http://localhost:8000/health/ready
# Expected: {"status": "ready", "database": "connected"}

# 8. Create first admin user
# Use the registration API endpoint or admin CLI
```

---

## 3. First Deployment (Bare Metal)

```bash
# 1. Clone the repository
git clone <repo-url> && cd SwarmVaultwebapp

# 2. Create virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env from template
cp .env.example .env
# Edit .env with real values (see step 3 above)

# 5. Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE swarmvault;"
psql -U postgres -c "CREATE USER swarmvault WITH PASSWORD '<strong-password>';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE swarmvault TO swarmvault;"

# 6. Run migrations
alembic upgrade head

# 7. Start application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2

# 8. Verify
curl http://localhost:8000/health/ready
```

---

## 4. Environment Variables

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `SECRET_KEY` | **Yes** | — | 32+ char random; JWT signing |
| `DATABASE_URL` | **Yes** | — | PostgreSQL connection string |
| `ENVIRONMENT` | No | development | Set to `production` in prod |
| `CORS_ORIGINS` | Yes (prod) | — | Comma-separated; never `*` |
| `ANTHROPIC_API_KEY` | No | — | Required for LLM features |
| `OPENAI_API_KEY` | No | — | Alternative LLM provider |
| `LOG_LEVEL` | No | INFO | DEBUG, INFO, WARNING, ERROR |

---

## 5. Health Checks

```bash
# Liveness (always returns 200 if process is running)
GET /health/live

# Readiness (checks database connectivity)
GET /health/ready
# 200 = ready
# 503 = database unavailable
```

---

## 6. Upgrade Deployment

```bash
# Docker
git pull
docker compose build
docker compose up -d
# Verify: curl http://localhost:8000/health/ready

# Bare metal
git pull
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
# Restart uvicorn process
```

---

## 7. Failed Migration Recovery

```bash
# Check current head
alembic current

# If migration failed mid-way, stamp to last known good revision
alembic stamp head

# Re-run migrations
alembic upgrade head
```

---

## 8. Rollback

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

---

## 9. Backup

```bash
# PostgreSQL backup
pg_dump -U swarmvault -d swarmvault -F c -f backup.dump

# Storage backup (if using filesystem)
tar czf storage-backup.tar.gz storage/
```

---

## 10. Restore

```bash
# Restore database
pg_restore -U swarmvault -d swarmvault backup.dump

# Restore storage
tar xzf storage-backup.tar.gz

# Verify
curl http://localhost:8000/health/ready
```

---

## 11. Shutdown

```bash
# Docker
docker compose down

# Bare metal
# Send SIGTERM to uvicorn (graceful shutdown)
kill -TERM <pid>
```

---

## 12. Troubleshooting

| Symptom | Check | Action |
|---------|-------|--------|
| 503 on /health/ready | Database connectivity | Check PostgreSQL is running; verify `database_url` |
| 500 on startup | Missing env vars | Check `SECRET_KEY`, `DATABASE_URL` |
| Migration errors | Schema drift | `alembic current` → `alembic stamp head` → retry |
| CORS errors | `CORS_ORIGINS` not set | Set in `.env` with frontend URL |
| Slow queries | Missing indexes | Check `ix_memories_workspace`, `ix_facts_workspace` |

---

## 13. Security Checklist (Pre-Production)

- [ ] `SWARMMAULT_SECRET_KEY` set to 32+ char random value
- [ ] `SWARMMAULT_ENVIRONMENT=production`
- [ ] `SWARMMAULT_CORS_ORIGINS` set (not `*`)
- [ ] `SWARMMAULT_DB_PASSWORD` changed from default
- [ ] PostgreSQL not exposed to public internet
- [ ] TLS terminated at reverse proxy (nginx/caddy)
- [ ] `storage/` directory not world-writable
- [ ] `.env` not in version control
