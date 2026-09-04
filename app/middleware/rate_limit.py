"""Rate limiting for Sprint 6.

In-memory sliding window rate limiter.
Production should replace with Redis-backed implementation.
"""

from __future__ import annotations

import time
import threading
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings


@dataclass
class RateLimitRule:
    """Rate limit configuration for a path pattern."""
    path_pattern: str
    max_requests: int
    window_seconds: int
    key_func: str = "ip"  # "ip", "user", "workspace"


_RULES: list[RateLimitRule] = [
    RateLimitRule("/api/v1/auth/login", settings.rate_limit_login, 60, "ip"),
    RateLimitRule("/api/v1/auth/register", settings.rate_limit_login, 60, "ip"),
    RateLimitRule("/api/v1/chat/", settings.rate_limit_chat, 60, "user"),
    RateLimitRule("/api/v1/ingest/upload", settings.rate_limit_ingest, 3600, "user"),
    RateLimitRule("/api/v1/ingest/search", settings.rate_limit_search, 60, "user"),
]


class _RateLimiter:
    """Thread-safe in-memory sliding window rate limiter."""

    _disabled_for_testing: bool = False

    def __init__(self) -> None:
        self._windows: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        """Check if request is allowed. Returns (allowed, remaining)."""
        if self._disabled_for_testing:
            return True, max_requests
        now = time.monotonic()
        cutoff = now - window_seconds

        with self._lock:
            timestamps = self._windows[key]
            # Remove expired entries
            self._windows[key] = [t for t in timestamps if t > cutoff]
            current = len(self._windows[key])

            if current >= max_requests:
                return False, 0

            self._windows[key].append(now)
            return True, max_requests - current - 1


_rate_limiter = _RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply rate limiting based on configured rules."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        # Always pass in test environments (flag from pytest conftest)
        if getattr(request.app.state, "testing", False):
            return await call_next(request)

        # In non-production environments, allow test header bypass for
        # external e2e test suites that cannot set app.state.testing.
        # NEVER active when environment=production.
        if settings.environment != "production":
            if request.headers.get("X-E2E") == "true":
                return await call_next(request)

        path = request.url.path

        for rule in _RULES:
            if path == rule.path_pattern or path.startswith(rule.path_pattern + "/"):
                if rule.key_func == "ip":
                    key = f"ip:{request.client.host if request.client else 'unknown'}:{rule.path_pattern}"
                elif rule.key_func == "user":
                    # Extract from auth header
                    auth = request.headers.get("Authorization", "")
                    key = f"user:{auth}:{rule.path_pattern}"
                    if not auth:
                        key = f"ip:{request.client.host if request.client else 'unknown'}:{rule.path_pattern}"
                elif rule.key_func == "workspace":
                    auth = request.headers.get("Authorization", "")
                    key = f"workspace:{auth}:{rule.path_pattern}"
                    if not auth:
                        key = f"ip:{request.client.host if request.client else 'unknown'}:{rule.path_pattern}"
                else:
                    key = f"default:{path}"

                allowed, remaining = _rate_limiter.is_allowed(key, rule.max_requests, rule.window_seconds)
                if not allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded. Try again in {rule.window_seconds}s.",
                        headers={"Retry-After": str(rule.window_seconds)},
                    )

                response = await call_next(request)
                response.headers["X-RateLimit-Limit"] = str(rule.max_requests)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                return response

        return await call_next(request)
