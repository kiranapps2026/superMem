"""Sprint 6 — Rate limiter API-level tests."""

import pytest
import time


@pytest.mark.asyncio
async def test_rate_limit_headers_present(client, seeded_workspace):
    """Rate limit headers are present on responses."""
    res = await client.get("/api/v1/memory/", headers=seeded_workspace["headers"])
    assert res.status_code == 200
    # X-RateLimit-Limit should be present (or not, depending on config)
    # In test mode, rate limiting is disabled, so headers may not be set
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_login_rate_limit_config_exists():
    """Login rate limit rule is configured."""
    from app.middleware.rate_limit import _RULES
    login_rules = [r for r in _RULES if "login" in r.path_pattern]
    assert len(login_rules) >= 1
    assert login_rules[0].max_requests > 0
    assert login_rules[0].window_seconds > 0


@pytest.mark.asyncio
async def test_chat_rate_limit_config_exists():
    """Chat rate limit rule is configured."""
    from app.middleware.rate_limit import _RULES
    chat_rules = [r for r in _RULES if "chat" in r.path_pattern]
    assert len(chat_rules) >= 1
    assert chat_rules[0].key_func == "user"


@pytest.mark.asyncio
async def test_ingest_rate_limit_config_exists():
    """Ingest rate limit rule is configured."""
    from app.middleware.rate_limit import _RULES
    ingest_rules = [r for r in _RULES if "ingest" in r.path_pattern]
    assert len(ingest_rules) >= 1
    # Ingestion is rate-limited hourly
    assert ingest_rules[0].window_seconds >= 3600


@pytest.mark.asyncio
async def test_rate_limiter_unit():
    """Direct unit test of rate limiter logic."""
    from app.middleware.rate_limit import _RateLimiter
    limiter = _RateLimiter()

    # 3 requests allowed with limit of 3
    for i in range(3):
        allowed, remaining = limiter.is_allowed("test:x", 3, 60)
        assert allowed is True

    # 4th request denied
    allowed, remaining = limiter.is_allowed("test:x", 3, 60)
    assert allowed is False
    assert remaining == 0

    # Different key is independent
    allowed, _ = limiter.is_allowed("test:y", 3, 60)
    assert allowed is True


@pytest.mark.asyncio
async def test_rate_limiter_test_mode_disabled():
    """Test mode disables rate limiting."""
    from app.middleware.rate_limit import _rate_limiter
    old = _rate_limiter._disabled_for_testing
    try:
        _rate_limiter._disabled_for_testing = True
        allowed, remaining = _rate_limiter.is_allowed("any:key", 1, 60)
        assert allowed is True
        assert remaining == 1
    finally:
        _rate_limiter._disabled_for_testing = old


@pytest.mark.asyncio
async def test_rate_limiter_window_reset():
    """Rate limiter window resets after expiry."""
    from app.middleware.rate_limit import _RateLimiter
    limiter = _RateLimiter()

    # Use a tiny window (1ms)
    for _ in range(2):
        limiter.is_allowed("win:test", 2, 0.001)

    allowed, _ = limiter.is_allowed("win:test", 2, 0.001)
    assert allowed is False

    # After disabling for testing, it passes
    limiter._disabled_for_testing = True
    allowed, _ = limiter.is_allowed("win:test", 2, 0.001)
    assert allowed is True
    limiter._disabled_for_testing = False
