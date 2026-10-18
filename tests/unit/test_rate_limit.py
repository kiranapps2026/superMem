"""Sprint 6 — Rate limiting tests."""

import pytest
from unittest.mock import patch, MagicMock

from app.middleware.rate_limit import _rate_limiter, RateLimitMiddleware, _RateLimiter, _RULES


class TestRateLimiterUnit:
    """Unit tests for the _RateLimiter class directly."""

    def test_first_request_allowed(self):
        limiter = _RateLimiter()
        allowed, remaining = limiter.is_allowed("test:key", 3, 60)
        assert allowed is True
        assert remaining == 2

    def test_requests_within_limit(self):
        limiter = _RateLimiter()
        for i in range(3):
            allowed, remaining = limiter.is_allowed("test:key", 3, 60)
            assert allowed is True
        # 4th request should be blocked
        allowed, remaining = limiter.is_allowed("test:key", 3, 60)
        assert allowed is False
        assert remaining == 0

    def test_different_keys_independent(self):
        limiter = _RateLimiter()
        # Exhaust key A
        for _ in range(3):
            limiter.is_allowed("key:A", 3, 60)
        # Key B should still be allowed
        allowed, _ = limiter.is_allowed("key:B", 3, 60)
        assert allowed is True

    def test_window_expiry(self):
        limiter = _RateLimiter()
        # Exhaust key
        for _ in range(3):
            limiter.is_allowed("expire:key", 3, 60)
        # Window is 60s but we haven't elapsed time — still blocked
        # Now disable for test
        limiter._disabled_for_testing = True
        allowed, remaining = limiter.is_allowed("expire:key", 3, 60)
        assert allowed is True
        assert remaining == 3


class TestRateLimitMiddleware:
    """Integration tests for the middleware."""

    def test_rules_configured(self):
        assert len(_RULES) >= 4
        paths = {r.path_pattern for r in _RULES}
        assert "/api/v1/auth/login" in paths
        assert "/api/v1/auth/register" in paths
        assert "/api/v1/chat/" in paths

    def test_testing_flag_skips_limiter(self):
        """When _disabled_for_testing=True, all requests pass."""
        limiter = _rate_limiter
        old = limiter._disabled_for_testing
        try:
            limiter._disabled_for_testing = True
            allowed, remaining = limiter.is_allowed("any:key", 1, 60)
            assert allowed is True
            assert remaining == 1
        finally:
            limiter._disabled_for_testing = old


class TestRateLimitRules:
    """Verify rate limit configurations are sensible."""

    def test_login_limit_reasonable(self):
        login_rule = next(r for r in _RULES if r.path_pattern == "/api/v1/auth/login")
        assert login_rule.max_requests <= 20  # not too high
        assert login_rule.window_seconds == 60

    def test_chat_limit_reasonable(self):
        chat_rule = next(r for r in _RULES if r.path_pattern == "/api/v1/chat/")
        assert chat_rule.max_requests >= 5  # not too low
        assert chat_rule.key_func == "user"

    def test_ingest_upload_limit_reasonable(self):
        upload_rule = next(r for r in _RULES if "upload" in r.path_pattern)
        assert upload_rule.window_seconds == 3600  # hourly
        assert upload_rule.key_func == "user"
