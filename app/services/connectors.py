"""M0 — Conversation normalization: raw formats → canonical internal representation."""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class NormalizedMessage:
    """Canonical message representation."""
    external_id: str | None = None
    role: str = "user"
    content: str = ""
    timestamp: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedConversation:
    """Canonical conversation representation (M0 output)."""
    source_type: str = "text"
    external_id: str | None = None
    title: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    messages: list[NormalizedMessage] = field(default_factory=list)


def _detect_format(raw: str) -> str:
    """Auto-detect conversation format from raw text."""
    raw = raw.strip()
    if raw.startswith("["):
        try:
            data = json.loads(raw)
            if isinstance(data, list) and data and "role" in data[0]:
                return "json"
        except json.JSONDecodeError:
            pass
    if '"role"' in raw[:200] and '"content"' in raw[:200]:
        return "json"
    if raw.startswith("{"):
        try:
            data = json.loads(raw)
            if "messages" in data:
                return "json"
            if "choices" in data:
                return "openai_api"
        except json.JSONDecodeError:
            pass
    return "text"


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _external_id(idx: int, content: str) -> str:
    return f"msg-{idx}-{_content_hash(content)}"


def normalize_chatgpt_export(raw: str | dict) -> NormalizedConversation:
    """Normalize ChatGPT conversation export."""
    if isinstance(raw, str):
        data = json.loads(raw)
    else:
        data = raw

    title = data.get("title") or data.get("name")
    created_at = data.get("create_time")
    if isinstance(created_at, (int, float)):
        created_at = datetime.fromtimestamp(created_at, tz=timezone.utc)
    else:
        created_at = None

    messages: list[NormalizedMessage] = []
    for i, msg in enumerate(data.get("mapping", {}).values()):
        if not isinstance(msg, dict):
            continue
        msg_content = msg.get("message", {})
        if not msg_content:
            continue
        role = msg_content.get("author", {}).get("role", "user")
        content = msg_content.get("content", {}).get("parts", [""])[0]
        if not content or not isinstance(content, str):
            continue
        ts = msg_content.get("create_time")
        if isinstance(ts, (int, float)):
            ts = datetime.fromtimestamp(ts, tz=timezone.utc)
        messages.append(NormalizedMessage(
            external_id=_external_id(i, content),
            role=role,
            content=content,
            timestamp=ts,
            metadata={"original_id": msg_content.get("id")},
        ))

    return NormalizedConversation(
        source_type="chatgpt",
        external_id=data.get("id"),
        title=title,
        created_at=created_at,
        messages=messages,
    )


def normalize_json(raw: str | dict) -> NormalizedConversation:
    """Normalize JSON array of messages."""
    if isinstance(raw, str):
        data = json.loads(raw)
    else:
        data = raw

    if isinstance(data, dict) and "messages" in data:
        data = data["messages"]

    if not isinstance(data, list):
        raise ValueError("JSON format expects a list of messages or dict with 'messages' key")

    messages: list[NormalizedMessage] = []
    for i, msg in enumerate(data):
        if not isinstance(msg, dict):
            continue
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if not content or not isinstance(content, str):
            continue
        # Preserve user-provided external_id if present
        external_id = msg.get("external_id") or _external_id(i, content)
        ts = msg.get("timestamp") or msg.get("created_at")
        if isinstance(ts, (int, float)):
            ts = datetime.fromtimestamp(ts, tz=timezone.utc)
        elif isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                ts = None
        else:
            ts = None
        messages.append(NormalizedMessage(
            external_id=external_id,
            role=role,
            content=content,
            timestamp=ts,
            metadata={k: v for k, v in msg.items() if k not in ("role", "content", "timestamp", "created_at")},
        ))

    return NormalizedConversation(source_type="json", messages=messages)


def normalize_text(raw: str) -> NormalizedConversation:
    """Normalize plain text into pseudo-messages (one per paragraph)."""
    paragraphs = [p.strip() for p in raw.split("\n\n") if p.strip()]
    messages: list[NormalizedMessage] = []
    for i, para in enumerate(paragraphs):
        role = "user" if i % 2 == 0 else "assistant"
        messages.append(NormalizedMessage(
            external_id=_external_id(i, para),
            role=role,
            content=para,
            timestamp=None,
        ))

    return NormalizedConversation(source_type="text", messages=messages)


def normalize_jsonl(raw: str) -> NormalizedConversation:
    """Normalize JSONL (one JSON object per line)."""
    lines = raw.strip().split("\n")
    messages: list[NormalizedMessage] = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if not content or not isinstance(content, str):
            continue
        ts = msg.get("timestamp") or msg.get("created_at")
        if isinstance(ts, (int, float)):
            ts = datetime.fromtimestamp(ts, tz=timezone.utc)
        elif isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                ts = None
        else:
            ts = None
        messages.append(NormalizedMessage(
            external_id=_external_id(i, content),
            role=role,
            content=content,
            timestamp=ts,
        ))
    return NormalizedConversation(source_type="jsonl", messages=messages)


def normalize(raw: str | dict, source_type: str | None = None) -> NormalizedConversation:
    """Normalize raw conversation data into canonical form.

    Args:
        raw: Raw conversation data (string or dict)
        source_type: Explicit format override (chatgpt, json, jsonl, text)

    Returns:
        NormalizedConversation with canonical message list
    """
    if source_type is None:
        if isinstance(raw, dict) and "messages" in raw:
            source_type = "json"
        elif isinstance(raw, dict) and "mapping" in raw:
            source_type = "chatgpt"
        elif isinstance(raw, str):
            source_type = _detect_format(raw)
        else:
            source_type = "text"

    normalizers = {
        "chatgpt": normalize_chatgpt_export,
        "json": normalize_json,
        "jsonl": normalize_jsonl,
        "text": normalize_text,
    }

    normalizer = normalizers.get(source_type)
    if normalizer is None:
        raise ValueError(f"Unsupported source_type: {source_type}. Supported: {list(normalizers.keys())}")

    return normalizer(raw)
