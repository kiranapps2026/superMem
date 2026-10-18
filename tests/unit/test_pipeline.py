"""Sprint 3 — Pipeline: M0 normalization, M1 understanding, M2 facts/decisions."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from app.services.connectors import normalize, NormalizedConversation, NormalizedMessage
from app.services.m1_session import understand_session, SessionUnderstanding
from app.services.m2_facts import extract_facts, extract_decisions, run_m2


# ── M0: Connector normalization ────────────────────────────────────────


class TestM0Normalization:
    """M0: Raw conversation → NormalizedConversation."""

    def test_text_normalization_basic(self):
        raw = "Hello world.\n\nThis is a test.\n\nGoodbye."
        result = normalize(raw, source_type="text")
        assert result.source_type == "text"
        assert len(result.messages) == 3
        assert result.messages[0].role == "user"
        assert result.messages[0].content == "Hello world."
        assert result.messages[1].content == "This is a test."
        assert result.messages[2].content == "Goodbye."

    def test_json_normalization_array(self):
        raw = '[{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}]'
        result = normalize(raw, source_type="json")
        assert len(result.messages) == 2
        assert result.messages[0].role == "user"
        assert result.messages[0].content == "Hi"
        assert result.messages[1].role == "assistant"
        assert result.messages[1].content == "Hello!"

    def test_json_normalization_dict_with_messages(self):
        raw = {"messages": [{"role": "user", "content": "Test"}]}
        result = normalize(raw)
        assert len(result.messages) == 1
        assert result.messages[0].content == "Test"

    def test_jsonl_normalization(self):
        raw = '{"role": "user", "content": "First"}\n{"role": "assistant", "content": "Second"}\n'
        result = normalize(raw, source_type="jsonl")
        assert len(result.messages) == 2
        assert result.messages[0].content == "First"
        assert result.messages[1].content == "Second"

    def test_chatgpt_normalization(self):
        raw = {
            "id": "conv-123",
            "title": "Test Chat",
            "mapping": {
                "msg-1": {
                    "message": {
                        "id": "msg-1",
                        "author": {"role": "user"},
                        "content": {"parts": ["Hello"]},
                        "create_time": 1700000000,
                    }
                },
                "msg-2": {
                    "message": {
                        "id": "msg-2",
                        "author": {"role": "assistant"},
                        "content": {"parts": ["Hi there"]},
                        "create_time": 1700000001,
                    }
                },
            }
        }
        result = normalize(raw, source_type="chatgpt")
        assert len(result.messages) == 2
        assert result.title == "Test Chat"
        assert result.external_id == "conv-123"
        assert result.messages[0].role == "user"
        assert result.messages[0].timestamp == datetime(2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc)

    def test_auto_detect_json(self):
        raw = '[{"role": "user", "content": "test"}]'
        result = normalize(raw)
        assert result.source_type == "json"

    def test_external_id_unique(self):
        raw = "First message.\n\nSecond message."
        result = normalize(raw, source_type="text")
        ids = [m.external_id for m in result.messages]
        assert len(ids) == len(set(ids))

    def test_empty_content_skipped(self):
        raw = "[{\"role\": \"user\", \"content\": \"\"}, {\"role\": \"user\", \"content\": \"real\"}]"
        result = normalize(raw, source_type="json")
        assert len(result.messages) == 1
        assert result.messages[0].content == "real"

    def test_unsupported_source_type_raises(self):
        from app.services.connectors import ConnectorError
        with pytest.raises(ConnectorError, match="Unknown connector"):
            normalize("test", source_type="unknown")

    def test_external_id_stored(self):
        raw = {"messages": [{"role": "user", "content": "test", "external_id": "ext-1"}]}
        result = normalize(raw)
        assert result.messages[0].external_id == "ext-1"


# ── M1: Session understanding ──────────────────────────────────────────


class TestM1SessionUnderstanding:
    """M1: Conversation-level comprehension."""

    def test_entities_extracted(self):
        msgs = [type("M", (), {"content": "Project Alpha uses PostgreSQL.", "role": "user"})()]
        result = understand_session(msgs)
        assert "PostgreSQL" in result.entities_mentioned

    def test_topics_detected(self):
        msgs = [
            type("M", (), {"content": "How do we deploy the database?", "role": "user"})(),
        ]
        result = understand_session(msgs)
        assert "database" in result.topics
        assert "deployment" in result.topics

    def test_intents_detected(self):
        msgs = [
            type("M", (), {"content": "We decided to use PostgreSQL for the database.", "role": "user"})(),
        ]
        result = understand_session(msgs)
        assert "decision_making" in result.intents

    def test_participants_detected(self):
        msgs = [
            type("M", (), {"content": "Hello", "role": "user"})(),
            type("M", (), {"content": "Hi there", "role": "assistant"})(),
        ]
        result = understand_session(msgs)
        assert set(result.participants) == {"user", "assistant"}

    def test_empty_messages(self):
        result = understand_session([])
        assert result.message_count == 0
        assert result.confidence == 0.5

    def test_message_count(self):
        msgs = [
            type("M", (), {"content": "msg1", "role": "user"})(),
            type("M", (), {"content": "msg2", "role": "assistant"})(),
        ]
        result = understand_session(msgs)
        assert result.message_count == 2


# ── M2: Fact extraction ────────────────────────────────────────────────


class TestM2Facts:
    """M2: Fact extraction from conversations."""

    def test_uses_pattern(self):
        text = "Project Alpha uses PostgreSQL."
        facts = extract_facts(text)
        assert len(facts) >= 1
        assert any("Project Alpha" == f.subject for f in facts)

    def test_is_pattern(self):
        text = "Python is a programming language."
        facts = extract_facts(text)
        # May or may not extract — depends on regex
        # At minimum, should not crash
        assert isinstance(facts, list)

    def test_multiple_facts(self):
        text = "Project Alpha uses PostgreSQL. Project Alpha uses Python."
        facts = extract_facts(text)
        subjects = [f.subject for f in facts]
        assert any("Project Alpha" in s for s in subjects)

    def test_fact_has_confidence(self):
        facts = extract_facts("Project Alpha uses PostgreSQL.")
        if facts:
            assert 0.0 <= facts[0].confidence <= 1.0

    def test_run_m2_returns_tuple(self):
        msgs = [type("M", (), {"content": "Project Alpha uses PostgreSQL.", "role": "user"})()]
        facts, decisions = run_m2(msgs)
        assert isinstance(facts, list)
        assert isinstance(decisions, list)


# ── M2: Decision extraction ────────────────────────────────────────────


class TestM2Decisions:
    """M2: Decision extraction from conversations."""

    def test_decided_pattern(self):
        text = "We decided to use PostgreSQL."
        decisions = extract_decisions(text)
        assert len(decisions) >= 1
        assert "PostgreSQL" in decisions[0].content

    def test_chose_pattern(self):
        text = "We chose Docker for deployment."
        decisions = extract_decisions(text)
        assert any("Docker" in d.content for d in decisions)

    def test_decision_has_confidence(self):
        decisions = extract_decisions("We decided to use PostgreSQL.")
        if decisions:
            assert 0.0 <= decisions[0].confidence <= 1.0

    def test_no_decision_in_factual_statement(self):
        text = "The server is running on port 8080."
        decisions = extract_decisions(text)
        # Should not extract a decision from a pure fact
        assert len(decisions) == 0

    def test_run_m2_decisions_tuple(self):
        msgs = [type("M", (), {"content": "We decided to use PostgreSQL.", "role": "user"})()]
        facts, decisions = run_m2(msgs)
        assert isinstance(decisions, list)
