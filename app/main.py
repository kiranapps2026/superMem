from contextlib import asynccontextmanager
import time
import uuid
import logging
import json

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi import FastAPI, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db import init_db
from app.services.audit.service import AuditService
from app.services.audit.service import AuditService


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Inject X-Request-ID and measure request latency."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = req_id
        t0 = time.monotonic()

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logging.getLogger("app.main").info(
                "request_complete",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code if "response" in dir() else "error",
                    "latency_ms": latency_ms,
                    "request_id": req_id,
                },
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        else:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https: http:; "
                "font-src 'self' data:; "
                "connect-src 'self' http://localhost:* ws://localhost:*; "
                "frame-ancestors 'none'"
            )
        return response


# ── Structured logging ────────────────────────────────────────────────


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))


# ── Error handlers ────────────────────────────────────────────────────


def _sanitize_detail(detail: str | dict | list) -> str | dict | list:
    """Remove sensitive data from error details."""
    if isinstance(detail, str):
        if any(secret in detail.lower() for secret in ["password", "secret", "token", "api_key", "database_url"]):
            return "Internal server error"
        import re
        detail = re.sub(r'[A-Z]:\\[^\s]+', '[redacted path]', detail)
        detail = re.sub(r'/\w+/[^\s]+', '[redacted path]', detail)
        return detail
    return detail


def _error_response(status: int, error_type: str, message: str, request: Request | None = None) -> JSONResponse:
    content = {
        "error": {
            "type": error_type,
            "message": _sanitize_detail(message),
        }
    }
    if request:
        content["error"]["request_id"] = getattr(request.state, "request_id", None)
    return JSONResponse(status_code=status, content=content)


# ── API routers ───────────────────────────────────────────────────────


from app.api import auth, workspace, projects, sessions, chat, memory, ingest, provenance, dashboard, feedback, api_keys, storage, policy, audit

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth.router)
api_v1.include_router(workspace.router)
api_v1.include_router(projects.router)
api_v1.include_router(sessions.router)
api_v1.include_router(chat.router)
api_v1.include_router(memory.router)
api_v1.include_router(ingest.router)
api_v1.include_router(provenance.router)
api_v1.include_router(dashboard.router)
api_v1.include_router(feedback.router)
api_v1.include_router(api_keys.router)
api_v1.include_router(storage.router)
api_v1.include_router(policy.router)
api_v1.include_router(audit.router)


# ── Audit service ──────────────────────────────────────────────────────

audit = AuditService()

# ── Lifespan ──────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.environment == "development":
        setup_logging()
    await init_db()
    # Wire DB persistence for audit events
    audit.register_db_sink()
    yield


# ── App ───────────────────────────────────────────────────────────────


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# Security headers (outermost)
app.add_middleware(SecurityHeadersMiddleware)

# Request ID + latency
app.add_middleware(RequestIdMiddleware)

# Audit persistence — flush buffered audit events after each request
class AuditPersistenceMiddleware(BaseHTTPMiddleware):
    """Persist buffered audit events to PostgreSQL after each request.

    Uses a short-lived independent session so audit writes are atomic
    with respect to the request's transaction.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        response = await call_next(request)
        # Persist audit events (failures are logged, never block the response)
        try:
            from app.db import async_session_factory
            async with async_session_factory() as session:
                await audit.persist(session)
                await session.commit()
        except Exception:
            logging.getLogger("app.main").warning("audit persist failed", exc_info=True)
        return response


app.add_middleware(AuditPersistenceMiddleware)

# CORS — production-safe
cors_origins = settings.cors_origins_safe
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    max_age=600,
)

# Rate limiting (disabled in tests via _rate_limiter._disabled_for_testing)
from app.middleware.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

# Error handlers
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return _error_response(422, "validation_error", str(exc.errors()), request)


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(request: Request, exc: SQLAlchemyError):
    logging.getLogger("app.main").error("database_error", exc_info=exc)
    return _error_response(500, "database_error", "A database error occurred", request)


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logging.getLogger("app.main").error("unhandled_error", exc_info=exc)
    # Never expose raw exception text to clients, regardless of debug mode
    # Full details are in server logs via exc_info above
    return _error_response(500, "internal_error", "Internal server error", request)

# Register API routes
app.include_router(api_v1)


# ── Health checks ─────────────────────────────────────────────────────


@app.get("/health/live")
async def liveness():
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    try:
        from app.db import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as exc:
        logger.warning("readiness check failed: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "unavailable"},
        )


@app.get("/health")
async def health():
    return {"status": "ok"}
