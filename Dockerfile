# SwarmVault WebApp — Production Dockerfile
# Multi-stage build for minimal attack surface
FROM python:3.12-slim AS builder

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─── Runtime stage ───────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL maintainer="SwarmVault" \
      version="1.0.0" \
      description="SwarmVault WebApp — production image"

# System dependencies (runtime only)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r swarmvault && useradd -r -g swarmvault -d /app swarmvault

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=swarmvault:swarmvault app/ ./app/
COPY --chown=swarmvault:swarmvault alembic/ ./alembic/
COPY --chown=swarmvault:swarmvault alembic.ini ./

# Runtime directories (owned by non-root user)
RUN mkdir -p /app/storage /app/logs \
    && chown -R swarmvault:swarmvault /app/storage /app/logs

# Switch to non-root user
USER swarmvault

# Expose
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -sf http://localhost:8000/health/live || exit 1

# Environment defaults (can be overridden at runtime)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Startup — runs migrations then starts uvicorn
CMD alembic upgrade head && \
    uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 2 \
        --log-level info \
        --access-log \
        --no-use-colors
