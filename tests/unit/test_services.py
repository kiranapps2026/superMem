"""Unit tests for Sprint 2 services: retrieval, LLM, chat orchestrator."""

from __future__ import annotations

import pytest
from fastapi import status

from app.services.retrieval import _cosine_similarity, _keyword_score, _hybrid_score
from app.services.llm import _mock_response, chat_completion


# ── Retrieval unit tests ──────────────────────────────────────────────────


class TestCosineSimilarity:
    def test_identical_vectors(self):
        v = [1.0, 0.0, 0.0]
        assert _cosine_similarity(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        assert _cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        assert _cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)

    def test_empty_vectors(self):
        assert _cosine_similarity([], [1.0, 2.0]) == 0.0
        assert _cosine_similarity([1.0, 2.0], []) == 0.0

    def test_zero_vector(self):
        assert _cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0


class TestKeywordScore:
    def test_perfect_match(self):
        assert _keyword_score("Python is great", "Python") == pytest.approx(1.0)

    def test_partial_match(self):
        score = _keyword_score("I love Python programming", "Python programming")
        assert 0.0 < score <= 1.0

    def test_no_match(self):
        assert _keyword_score("Hello world", "Python Java") == pytest.approx(0.0)

    def test_empty_query(self):
        assert _keyword_score("anything", "") == pytest.approx(0.0)

    def test_case_insensitive(self):
        assert _keyword_score("PYTHON is great", "python") == pytest.approx(1.0)


class TestHybridScore:
    def test_vector_and_keyword(self):
        score = _hybrid_score(
            content="Python programming tips",
            query="Python",
            embedding=[0.9, 0.1],
            query_embedding=[1.0, 0.0],
            vector_weight=0.5,
            keyword_weight=0.5,
        )
        assert 0.0 < score <= 1.0

    def test_keyword_only_when_no_embeddings(self):
        score = _hybrid_score(
            content="Python is great",
            query="Python",
            embedding=None,
            query_embedding=None,
        )
        assert score == pytest.approx(1.0)

    def test_low_score_for_unrelated(self):
        score = _hybrid_score(
            content="The weather is sunny today",
            query="Python programming",
            embedding=None,
            query_embedding=None,
        )
        assert score == pytest.approx(0.0)


# ── LLM unit tests ───────────────────────────────────────────────────────


class TestMockResponse:
    def test_returns_content(self):
        result = _mock_response("Hello")
        assert "Hello" in result["content"]

    def test_returns_mock_model(self):
        result = _mock_response("test")
        assert result["model"] == "mock"

    def test_zero_usage(self):
        result = _mock_response("test")
        assert result["usage"]["prompt_tokens"] == 0
        assert result["usage"]["completion_tokens"] == 0
        assert result["usage"]["total_tokens"] == 0

    def test_stop_reason(self):
        result = _mock_response("test")
        assert result["stop_reason"] == "mock_end_turn"


class TestChatCompletion:
    @pytest.mark.asyncio
    async def test_returns_mock_without_api_key(self):
        result = await chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
        )
        assert "content" in result
        assert "mock" in result["provider"].lower()

    @pytest.mark.asyncio
    async def test_uses_last_user_message(self):
        result = await chat_completion(
            messages=[
                {"role": "user", "content": "First"},
                {"role": "assistant", "content": "Reply"},
                {"role": "user", "content": "Second"},
            ],
        )
        assert "Second" in result["content"]

    @pytest.mark.asyncio
    async def test_system_prompt_injected(self):
        messages = [{"role": "user", "content": "Hello"}]
        result = await chat_completion(
            messages=messages,
            system="You are a test bot.",
        )
        assert "content" in result


# ── Retrieval integration test (in-process) ─────────────────────────────


@pytest.mark.asyncio
async def test_retrieve_memories_empty_db(client, seeded_workspace):
    """Retrieval returns empty list when no memories exist."""
    from app.services.retrieval import retrieve_memories
    from app.db import get_db

    # Use the client's db override via direct call
    # The client fixture already has db overrides; we use the client to
    # verify retrieval indirectly through the API
    resp = await client.post(
        "/api/v1/memory/search",
        json={"query": "nothingmatches", "limit": 10},
        headers=seeded_workspace["headers"],
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == []
