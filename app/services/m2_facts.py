"""M2 — Fact extraction and decision extraction from conversations.

Deterministic extraction using pattern matching.
Facts:   subject-predicate-object triples
Decisions: statements of choice/commitment
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Fact:
    """Extracted factual statement (subject-predicate-object)."""
    subject: str = ""
    predicate: str = ""
    object: str = ""
    content: str = ""
    confidence: float = 1.0
    authority: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Decision:
    """Extracted decision record."""
    content: str = ""
    context: str = ""
    confidence: float = 1.0
    authority: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


# Patterns for fact extraction
FACT_PATTERNS = [
    # "X uses Y", "X runs on Y", "X is built with Y"
    (re.compile(
        r'(?P<subject>(?:[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*))\s+'
        r'(?P<predicate>(?:uses?|runs?\s+on|built\s+with|powered\s+by|deployed?\s+on|runs?\s+in|runs?\s+on))\s+'
        r'(?P<object>(?:[A-Z][A-Za-z0-9.]+(?:\s+[A-Za-z0-9.]+)*))',
        re.IGNORECASE
    ), "uses"),
    # "X is Y", "X are Y"
    (re.compile(
        r'(?P<subject>(?:[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*))\s+'
        r'(?:is|are)\s+'
        r'(?P<object>(?:a|an|the\s+)?(?:[A-Z][A-Za-z0-9.]+(?:\s+[A-Za-z0-9.]+)*))',
        re.IGNORECASE
    ), "is"),
    # "X supports Y"
    (re.compile(
        r'(?P<subject>(?:[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)*))\s+'
        r'(?:supports?|handles?|manages?)\s+'
        r'(?P<object>(?:[A-Z][A-Za-z0-9.]+(?:\s+[A-Za-z0-9.]+)*))',
        re.IGNORECASE
    ), "supports"),
]

# Patterns for decision extraction
DECISION_PATTERNS = [
    re.compile(
        r'(?:we|the team|i)\s+(?:decided?|chose?|decided?\s+to|are\s+going\s+to|selected?|will|picked?)\s+'
        r'(?:to\s+)?(?:use|adopt|go\s+with|pick|implement|build|deploy)\s+'
        r'(?P<choice>.{3,100}(?:\.|$|\s+(?:for|because|since|as|since)))',
        re.IGNORECASE,
    ),
    re.compile(
        r'(?:decision|chose|picked):\s*(?P<choice>.{3,100}(?:\.|$))',
        re.IGNORECASE,
    ),
    re.compile(
        r'(?:we|the team|i)\s+(?:are\s+using|use|switched?\s+to|migrated?\s+to)\s+'
        r'(?P<choice>.{3,100}(?:\.|$))',
        re.IGNORECASE,
    ),
    re.compile(
        r'(?:we|the team|i)\s+(?:chose|chose\s+to|selected?)\s+'
        r'(?P<choice>.{3,100}(?:\.|$))',
        re.IGNORECASE,
    ),
]


def extract_facts(text: str) -> list[Fact]:
    """Extract factual statements from text.

    Args:
        text: Input text to analyze

    Returns:
        List of extracted Fact objects
    """
    facts: list[Fact] = []

    for pattern, predicate in FACT_PATTERNS:
        for match in pattern.finditer(text):
            subject = match.group("subject").strip()
            obj = match.group("object").strip()
            if len(subject) > 2 and len(obj) > 1:
                content = f"{subject} {predicate} {obj}"
                facts.append(Fact(
                    subject=subject,
                    predicate=predicate,
                    object=obj,
                    content=content,
                    confidence=0.8,
                ))

    return _deduplicate_facts(facts)


def extract_decisions(text: str) -> list[Decision]:
    """Extract decision statements from text.

    Args:
        text: Input text to analyze

    Returns:
        List of extracted Decision objects
    """
    decisions: list[Decision] = []

    for pattern in DECISION_PATTERNS:
        for match in pattern.finditer(text):
            choice = match.group("choice").strip().rstrip(".")
            if len(choice) > 3:
                decisions.append(Decision(
                    content=choice,
                    context=text[:500],
                    confidence=0.75,
                ))

    return _deduplicate_decisions(decisions)


def _deduplicate_facts(facts: list[Fact]) -> list[Fact]:
    """Remove duplicate facts based on normalized subject-predicate-object."""
    seen: set[str] = set()
    result: list[Fact] = []
    for f in facts:
        key = f"{f.subject.lower()}|{f.predicate.lower()}|{f.object.lower()}"
        if key not in seen:
            seen.add(key)
            result.append(f)
    return result


def _deduplicate_decisions(decisions: list[Decision]) -> list[Decision]:
    """Remove duplicate decisions based on content similarity."""
    seen: set[str] = set()
    result: list[Decision] = []
    for d in decisions:
        key = d.content.lower().strip()
        if key not in seen:
            seen.add(key)
            result.append(d)
    return result


def run_m2(messages: list[Any]) -> tuple[list[Fact], list[Decision]]:
    """Run M2 fact/decision extraction on a message list.

    Args:
        messages: List of objects with .content attribute

    Returns:
        Tuple of (facts, decisions)
    """
    all_text = "\n".join(getattr(m, "content", "") for m in messages if getattr(m, "content", ""))

    facts = extract_facts(all_text)
    decisions = extract_decisions(all_text)

    return facts, decisions
