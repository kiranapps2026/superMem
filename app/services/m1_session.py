"""M1 — Session understanding: conversation-level comprehension.

Takes a NormalizedConversation and enriches it with:
- Summary
- Topic detection
- Intent classification
- Entity mention extraction (lightweight)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionUnderstanding:
    """Enriched session understanding (M1 output)."""
    summary: str = ""
    topics: list[str] = field(default_factory=list)
    intents: list[str] = field(default_factory=list)
    entities_mentioned: list[str] = field(default_factory=list)
    message_count: int = 0
    participants: list[str] = field(default_factory=list)
    language: str = "en"
    confidence: float = 1.0


def _extract_entities(content: str) -> list[str]:
    """Lightweight entity extraction: proper nouns, technologies, product names."""
    entities: set[str] = set()

    # Tech stacks: PostgreSQL, MongoDB, Redis, Python, TypeScript, etc.
    tech_patterns = [
        r'\b(PostgreSQL|Postgres|MongoDB|Mongo|MySQL|Redis|Docker|Kubernetes|'
        r'Python|JavaScript|TypeScript|Java|Go|Rust|React|Vue|Next\.js|Node\.js|'
        r'AWS|GCP|Azure|Terraform|GraphQL|REST|gRPC|Kafka|RabbitMQ|'
        r'FastAPI|Django|Flask|Express|Spring|Rails|Laravel)\b',
    ]
    for pattern in tech_patterns:
        entities.update(re.findall(pattern, content, re.IGNORECASE))

    # Project names: multi-word capitalized sequences after project/initiative markers
    project_pattern = r'(?:project|initiative|system|app)\s+((?:[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*))'
    matches = re.findall(project_pattern, content, re.IGNORECASE)
    for m in matches:
        cleaned = m.strip().rstrip('.,;:')
        if len(cleaned) > 1:
            entities.add(cleaned)

    # Decision keywords: "we decided", "we chose", "we will use"
    decision_patterns = [
        r'(?:we|the team|i)\s+(?:decided?|chose?|will|are going to|selected?|picked?)\s+(?:to\s+)?(?:use|adopt|go with|pick)\s+([A-Z][A-Za-z0-9.]+)',
    ]
    for pattern in decision_patterns:
        entities.update(re.findall(pattern, content, re.IGNORECASE))

    return sorted(entities)


def _detect_topics(messages: list[Any]) -> list[str]:
    """Detect topics from message content."""
    all_content = " ".join(getattr(m, "content", "") for m in messages)
    topics: set[str] = set()

    topic_keywords = {
        "database": [r"\b(database|db|sql|nosql|postgres|mongo|mysql|redis)\b", re.I],
        "architecture": [r"\b(architecture|design|pattern|microservice|monolith)\b", re.I],
        "deployment": [r"\b(deploy|ci/cd|pipeline|docker|kubernetes|k8s)\b", re.I],
        "api": [r"\b(api|endpoint|rest|graphql|rpc)\b", re.I],
        "auth": [r"\b(auth|login|jwt|oauth|permission|rbac)\b", re.I],
        "testing": [r"\b(test|spec|coverage|e2e|unit test|integration)\b", re.I],
        "frontend": [r"\b(frontend|react|vue|angular|ui|ux|component)\b", re.I],
        "backend": [r"\b(backend|server|api|microservice|handler)\b", re.I],
        "performance": [r"\b(performance|latency|throughput|cache|optimize)\b", re.I],
        "security": [r"\b(security|encrypt|vulnerability|cve|audit)\b", re.I],
    }

    for topic, (pattern, flags) in topic_keywords.items():
        if re.search(pattern, all_content, flags=flags):
            topics.add(topic)

    return sorted(topics)


def understand_session(
    messages: list[Any],
    summary_llm: Any = None,
) -> SessionUnderstanding:
    """Analyze a session's messages to produce enriched understanding.

    Args:
        messages: List of NormalizedMessage objects
        summary_llm: Optional LLM callable(summary_prompt) -> str

    Returns:
        SessionUnderstanding with topics, entities, etc.
    """
    if not messages:
        return SessionUnderstanding(confidence=0.5)

    all_content = "\n".join(m.content for m in messages if m.content)
    participants = sorted(set(m.role for m in messages if m.role))

    # Deterministic analysis
    topics = _detect_topics(messages)
    entities = _extract_entities(all_content)

    # Simple intent detection
    intents: set[str] = set()
    if re.search(r"\b(how do i|how can i|how to)\b", all_content, re.I):
        intents.add("how_to")
    if re.search(r"\b(decid|choos|select|will|going to)\w*\b", all_content, re.I):
        intents.add("decision_making")
    if re.search(r"\b(bug|error|fix|issue|problem|broken)\b", all_content, re.I):
        intents.add("debugging")
    if re.search(r"\b(build|create|implement|add|develop)\b", all_content, re.I):
        intents.add("building")
    if re.search(r"\b(review|look at|check|examine)\b", all_content, re.I):
        intents.add("review")

    # LLM summary if available
    summary = ""
    if summary_llm and callable(summary_llm):
        try:
            summary = summary_llm(all_content[:4000])
        except Exception:
            summary = ""

    return SessionUnderstanding(
        summary=summary,
        topics=topics,
        intents=sorted(intents),
        entities_mentioned=entities,
        message_count=len(messages),
        participants=participants,
        confidence=1.0 if entities else 0.5,
    )
