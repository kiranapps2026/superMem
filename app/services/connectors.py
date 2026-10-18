"""M0 — Conversation normalization: raw formats → canonical internal representation.

Connector registry with validation, detection, and security hardening.
Connectors normalize only — M0–M5 handle memory, facts, decisions, retrieval.
"""

from __future__ import annotations

import json
import hashlib
import re
import itertools
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable
from pathlib import Path


# ── Canonical types ────────────────────────────────────────────────────


@dataclass
class NormalizedMessage:
    """Canonical message representation (M0 output)."""
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


# ── Connector interface ────────────────────────────────────────────────


class ConnectorError(Exception):
    """Raised when a connector cannot parse or validate input."""
    def __init__(self, message: str, connector: str = "unknown"):
        self.connector = connector
        super().__init__(f"[{connector}] {message}")


class BaseConnector:
    """All connectors must implement detect, validate, and parse."""

    name: str = "base"

    def detect(self, raw: str, filename: str = "") -> float:
        """Return confidence score 0.0–1.0 that this connector handles the input."""
        raise NotImplementedError

    def validate(self, raw: str | dict) -> None:
        """Raise ConnectorError if input is malformed or unsafe."""
        raise NotImplementedError

    def parse(self, raw: str | dict) -> NormalizedConversation:
        """Normalize input into canonical representation."""
        raise NotImplementedError


# ── Security utilities ─────────────────────────────────────────────────


_MAX_CONTENT_LENGTH = 10_000_000  # 10 MB
_MAX_MESSAGE_LENGTH = 100_000     # 100 KB per message
_MAX_MESSAGES = 10_000


def _check_size(raw: str | dict) -> None:
    """Reject oversized inputs."""
    if isinstance(raw, str) and len(raw) > _MAX_CONTENT_LENGTH:
        raise ConnectorError(f"Input exceeds {_MAX_CONTENT_LENGTH} bytes", "security")


def _safe_text(text: str, max_len: int = _MAX_MESSAGE_LENGTH) -> str:
    """Truncate safely. Never execute content."""
    text = text[:max_len]
    return text


# ── Helpers ────────────────────────────────────────────────────────────


def _ts(value: int | float | str | None) -> datetime | None:
    """Convert timestamp to datetime."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    return None


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _external_id(idx: int, content: str) -> str:
    return f"msg-{idx}-{_content_hash(content)}"


# ── Connectors ─────────────────────────────────────────────────────────


class ChatGPTConnector(BaseConnector):
    name = "chatgpt"

    def detect(self, raw: str, filename: str = "") -> float:
        raw = raw.strip() if isinstance(raw, str) else ""
        if raw.startswith("{"):
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    if "mapping" in data:
                        return 0.95
                    if "title" in data and "messages" not in data:
                        return 0.7
            except json.JSONDecodeError:
                pass
        if filename.lower().endswith(".json") and "chat" in filename.lower():
            return 0.4
        return 0.0

    def validate(self, raw: str | dict) -> None:
        _check_size(raw)
        if isinstance(raw, str):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as e:
                raise ConnectorError(f"Invalid JSON: {e}", self.name)
        else:
            data = raw
        if not isinstance(data, dict):
            raise ConnectorError("Expected JSON object", self.name)
        if "mapping" not in data and "messages" not in data:
            raise ConnectorError("Missing 'mapping' or 'messages' field", self.name)

    def parse(self, raw: str | dict) -> NormalizedConversation:
        self.validate(raw)
        if isinstance(raw, str):
            data = json.loads(raw)
        else:
            data = raw

        title = data.get("title") or data.get("name")
        created_at = _ts(data.get("create_time"))

        messages: list[NormalizedMessage] = []
        mapping = data.get("mapping", {})
        if not mapping and "messages" in data:
            # Generic JSON format
            return GenericJSONConnector().parse(raw)

        for i, entry in enumerate(itertools.islice(mapping.values(), _MAX_MESSAGES)):
            if not isinstance(entry, dict):
                continue
            msg_content = entry.get("message", {})
            if not msg_content:
                continue
            author = msg_content.get("author", {})
            role = author.get("role", "user")
            parts = msg_content.get("content", {}).get("parts", [""])
            content = parts[0] if parts else ""
            if not content or not isinstance(content, str):
                continue
            ts = _ts(msg_content.get("create_time"))
            messages.append(NormalizedMessage(
                external_id=f"chatgpt-{msg_content.get('id', _external_id(i, content))}",
                role=role,
                content=_safe_text(content),
                timestamp=ts,
                metadata={"original_id": msg_content.get("id"), "connector": self.name},
            ))

        return NormalizedConversation(
            source_type=self.name,
            external_id=data.get("id"),
            title=title,
            created_at=created_at,
            messages=messages,
        )


class ClaudeConnector(BaseConnector):
    name = "claude"

    def detect(self, raw: str, filename: str = "") -> float:
        raw = raw.strip() if isinstance(raw, str) else ""
        if raw.startswith("{"):
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    if "chat_messages" in data or "conversations" in data:
                        return 0.95
            except json.JSONDecodeError:
                pass
        if "claude" in filename.lower() and filename.endswith(".json"):
            return 0.6
        return 0.0

    def validate(self, raw: str | dict) -> None:
        _check_size(raw)
        if isinstance(raw, str):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as e:
                raise ConnectorError(f"Invalid JSON: {e}", self.name)
        else:
            data = raw
        if not isinstance(data, dict):
            raise ConnectorError("Expected JSON object", self.name)
        if "chat_messages" not in data and "conversations" not in data:
            raise ConnectorError("Missing 'chat_messages' or 'conversations' field", self.name)

    def parse(self, raw: str | dict) -> NormalizedConversation:
        self.validate(raw)
        if isinstance(raw, str):
            data = json.loads(raw)
        else:
            data = raw

        messages_list = data.get("chat_messages", [])
        conversations = data.get("conversations", [])
        title = data.get("title")

        if conversations:
            # Multi-conversation export
            all_messages: list[NormalizedMessage] = []
            created_at = None
            for conv in conversations:
                conv_title = conv.get("title", "")
                if not title and conv_title:
                    title = conv_title
                for msg in conv.get("messages", []):
                    role = msg.get("sender", "user")
                    content = msg.get("text", msg.get("content", ""))
                    if not content:
                        continue
                    ts = _ts(msg.get("created_at") or msg.get("timestamp"))
                    if created_at is None and ts:
                        created_at = ts
                    all_messages.append(NormalizedMessage(
                        external_id=f"claude-{msg.get('uuid', _external_id(len(all_messages), content))}",
                        role=role,
                        content=_safe_text(content),
                        timestamp=ts,
                        metadata={"connector": self.name},
                    ))
            return NormalizedConversation(
                source_type=self.name,
                title=title,
                created_at=created_at,
                messages=all_messages[:_MAX_MESSAGES],
            )

        # Single conversation with chat_messages
        messages: list[NormalizedMessage] = []
        for i, msg in enumerate(messages_list):
            role = msg.get("sender", "user")
            content = msg.get("text", msg.get("content", ""))
            if not content:
                continue
            ts = _ts(msg.get("created_at") or msg.get("timestamp"))
            messages.append(NormalizedMessage(
                external_id=f"claude-{msg.get('uuid', _external_id(i, content))}",
                role=role,
                content=_safe_text(content),
                timestamp=ts,
                metadata={"connector": self.name},
            ))

        return NormalizedConversation(
            source_type=self.name,
            external_id=data.get("uuid"),
            title=title,
            created_at=_ts(data.get("created_at")),
            messages=messages,
        )


class ClaudeCodeConnector(BaseConnector):
    """Claude Code session format: JSONL with user/assistant/tool/system events."""

    name = "claude-code"

    def detect(self, raw: str, filename: str = "") -> float:
        if not isinstance(raw, str):
            return 0.0
        if filename.endswith(".jsonl"):
            return 0.7
        lines = raw.strip().split("\n")
        if len(lines) >= 2:
            try:
                first = json.loads(lines[0])
                if isinstance(first, dict) and first.get("type") in ("user", "assistant", "system", "summary"):
                    return 0.9
            except (json.JSONDecodeError, AttributeError):
                pass
        return 0.0

    def validate(self, raw: str | dict) -> None:
        _check_size(raw)
        if isinstance(raw, dict):
            raise ConnectorError("Claude Code requires JSONL string input", self.name)

    def parse(self, raw: str | dict) -> NormalizedConversation:
        self.validate(raw)
        lines = raw.strip().split("\n") if isinstance(raw, str) else []

        messages: list[NormalizedMessage] = []
        for i, line in enumerate(lines[: _MAX_MESSAGES]):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue

            event_type = event.get("type", "")
            content = ""
            role = "user"

            if event_type == "user":
                # Extract text content - try message.content first, then top-level text
                msg_data = event.get("message", {})
                content = msg_data.get("content", "")
                if isinstance(content, list):
                    parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            parts.append(block.get("text", ""))
                    content = "\n".join(parts)
                elif not content:
                    content = event.get("text", "")
                role = "user"

            elif event_type == "assistant":
                role = "assistant"
                # Try multiple content sources
                msg_data = event.get("message", {})
                content = msg_data.get("content", "")
                if isinstance(content, list):
                    parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            parts.append(block.get("text", ""))
                        elif isinstance(block, dict) and block.get("type") == "tool_use":
                            parts.append(f"[tool:{block.get('name', 'unknown')}]")
                    content = "\n".join(parts)
                elif not content:
                    content = event.get("text", "")

            elif event_type == "system":
                role = "system"
                content = event.get("text", "")

            elif event_type == "summary":
                role = "system"
                content = event.get("text", event.get("summary", ""))

            if content and isinstance(content, str) and content.strip():
                messages.append(NormalizedMessage(
                    external_id=f"cc-{i}-{_content_hash(content)}",
                    role=role,
                    content=_safe_text(content),
                    timestamp=_ts(event.get("timestamp") or event.get("ts")),
                    metadata={
                        "connector": self.name,
                        "event_type": event_type,
                        "raw_keys": sorted([k for k in event.keys() if k not in ("message", "text", "content")]),
                    },
                ))

        if not messages:
            raise ConnectorError("No valid messages found in JSONL", self.name)

        return NormalizedConversation(
            source_type=self.name,
            title=f"Claude Code session ({len(messages)} events)",
            messages=messages,
        )


class GenericJSONConnector(BaseConnector):
    """Generic JSON: array of {role, content} objects or {messages: [...]}."""

    name = "json"

    def detect(self, raw: str, filename: str = "") -> float:
        raw = raw.strip() if isinstance(raw, str) else ""
        if not raw.startswith("{") and not raw.startswith("["):
            return 0.0
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return 0.0
        if isinstance(data, list) and data and "role" in data[0] and "content" in data[0]:
            return 0.9
        if isinstance(data, dict) and "messages" in data:
            msgs = data["messages"]
            if isinstance(msgs, list) and msgs and "role" in msgs[0]:
                return 0.85
        return 0.0

    def validate(self, raw: str | dict) -> None:
        _check_size(raw)
        if isinstance(raw, str):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as e:
                raise ConnectorError(f"Invalid JSON: {e}", self.name)
        else:
            data = raw
        if isinstance(data, dict):
            data = data.get("messages", [])
        if not isinstance(data, list) or not data:
            raise ConnectorError("Expected array of messages", self.name)

    def parse(self, raw: str | dict) -> NormalizedConversation:
        self.validate(raw)
        if isinstance(raw, str):
            data = json.loads(raw)
        else:
            data = raw
        if isinstance(data, dict) and "messages" in data:
            data = data["messages"]

        title = None
        if isinstance(raw, dict):
            title = raw.get("title")
        elif isinstance(raw, str):
            try:
                top = json.loads(raw)
                title = top.get("title") if isinstance(top, dict) else None
            except Exception:
                pass

        messages: list[NormalizedMessage] = []
        for i, msg in enumerate(data[:_MAX_MESSAGES]):
            if not isinstance(msg, dict):
                continue
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if not content or not isinstance(content, str):
                continue
            ts = _ts(msg.get("timestamp") or msg.get("created_at"))
            messages.append(NormalizedMessage(
                external_id=msg.get("external_id") or _external_id(i, content),
                role=role,
                content=_safe_text(content),
                timestamp=ts,
                metadata={k: v for k, v in msg.items() if k not in ("role", "content", "timestamp", "created_at", "external_id")},
            ))

        return NormalizedConversation(
            source_type="json",
            title=title,
            messages=messages,
        )


class JSONLConnector(BaseConnector):
    name = "jsonl"

    def detect(self, raw: str, filename: str = "") -> float:
        if not filename.endswith(".jsonl"):
            return 0.0
        lines = raw.strip().split("\n")
        if not lines:
            return 0.0
        try:
            json.loads(lines[0])
            return 0.9
        except json.JSONDecodeError:
            return 0.0

    def validate(self, raw: str | dict) -> None:
        _check_size(raw)
        if isinstance(raw, dict):
            raise ConnectorError("JSONL requires string input", self.name)

    def parse(self, raw: str | dict) -> NormalizedConversation:
        self.validate(raw)
        lines = raw.strip().split("\n") if isinstance(raw, str) else []
        messages: list[NormalizedMessage] = []

        for i, line in enumerate(lines[:_MAX_MESSAGES]):
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(msg, dict):
                continue
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if not content or not isinstance(content, str):
                continue
            ts = _ts(msg.get("timestamp") or msg.get("created_at"))
            messages.append(NormalizedMessage(
                external_id=msg.get("external_id") or _external_id(i, content),
                role=role,
                content=_safe_text(content),
                timestamp=ts,
                metadata={k: v for k, v in msg.items() if k not in ("role", "content", "timestamp", "created_at", "external_id")},
            ))

        if not messages:
            raise ConnectorError("No valid messages found", self.name)

        return NormalizedConversation(source_type="jsonl", messages=messages)


class MarkdownConnector(BaseConnector):
    name = "markdown"

    def detect(self, raw: str, filename: str = "") -> float:
        if filename.endswith(".md") or filename.endswith(".markdown"):
            return 0.8
        if raw.strip().startswith("#"):
            return 0.5
        return 0.0

    def validate(self, raw: str | dict) -> None:
        _check_size(raw)
        if isinstance(raw, dict):
            raise ConnectorError("Markdown requires string input", self.name)

    def parse(self, raw: str | dict) -> NormalizedConversation:
        self.validate(raw)
        text = raw if isinstance(raw, str) else ""

        # Extract title from first H1
        title = None
        h1_match = re.match(r'^#\s+(.+)$', text.strip(), re.MULTILINE)
        if h1_match:
            title = h1_match.group(1).strip()

        # Split by user/assistant markers or by ## headers
        lines = text.split("\n")
        messages: list[NormalizedMessage] = []
        current_role = "user"
        current_content: list[str] = []

        for line in lines:
            if line.startswith("## User") or line.startswith("**User**"):
                if current_content:
                    messages.append(NormalizedMessage(
                        external_id=_external_id(len(messages), "".join(current_content)),
                        role=current_role,
                        content="\n".join(current_content).strip(),
                    ))
                    current_content = []
                current_role = "user"
            elif line.startswith("## Assistant") or line.startswith("**Assistant**"):
                if current_content:
                    messages.append(NormalizedMessage(
                        external_id=_external_id(len(messages), "".join(current_content)),
                        role=current_role,
                        content="\n".join(current_content).strip(),
                    ))
                    current_content = []
                current_role = "assistant"
            else:
                current_content.append(line)

        if current_content:
            messages.append(NormalizedMessage(
                external_id=_external_id(len(messages), "".join(current_content)),
                role=current_role,
                content="\n".join(current_content).strip(),
            ))

        if not messages:
            # Fallback: treat entire text as single message
            messages.append(NormalizedMessage(
                external_id="md-0",
                role="user",
                content=_safe_text(text.strip()),
            ))

        return NormalizedConversation(
            source_type="markdown",
            title=title,
            messages=messages[:_MAX_MESSAGES],
        )


class TextConnector(BaseConnector):
    name = "text"

    def detect(self, raw: str, filename: str = "") -> float:
        # Lowest priority fallback
        return 0.1

    def validate(self, raw: str | dict) -> None:
        _check_size(raw)
        if not isinstance(raw, str):
            raise ConnectorError("Text requires string input", self.name)
        stripped = raw.strip()
        if not stripped:
            raise ConnectorError("Empty input", self.name)

    def parse(self, raw: str | dict) -> NormalizedConversation:
        self.validate(raw)
        text = raw if isinstance(raw, str) else ""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        messages: list[NormalizedMessage] = []
        for i, para in enumerate(paragraphs[:_MAX_MESSAGES]):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append(NormalizedMessage(
                external_id=_external_id(i, para),
                role=role,
                content=_safe_text(para),
            ))

        return NormalizedConversation(source_type="text", messages=messages)


# ── Registry ───────────────────────────────────────────────────────────


class ConnectorRegistry:
    """Pluggable connector registry. Adding a connector does not touch M0–M5."""

    def __init__(self) -> None:
        self._connectors: list[BaseConnector] = [
            ChatGPTConnector(),
            ClaudeConnector(),
            ClaudeCodeConnector(),
            GenericJSONConnector(),
            JSONLConnector(),
            MarkdownConnector(),
            TextConnector(),
        ]

    def detect(self, raw: str, filename: str = "", explicit_type: str | None = None) -> BaseConnector:
        """Find best connector for the input."""
        if explicit_type:
            for c in self._connectors:
                if c.name == explicit_type:
                    return c
            raise ConnectorError(f"Unknown connector type: {explicit_type}", "registry")

        best: BaseConnector | None = None
        best_score = 0.0
        for c in self._connectors:
            score = c.detect(raw, filename)
            if score > best_score:
                best_score = score
                best = c

        if best is None or best_score < 0.1:
            raise ConnectorError("Could not detect conversation format", "registry")
        return best

    def list_connectors(self) -> list[dict[str, Any]]:
        """Return connector metadata for API responses."""
        return [
            {
                "name": c.name,
                "formats": self._formats_for(c),
                "description": self._description_for(c),
            }
            for c in self._connectors
        ]

    def _formats_for(self, connector: BaseConnector) -> list[str]:
        return {
            "chatgpt": [".json"],
            "claude": [".json"],
            "claude-code": [".jsonl"],
            "json": [".json"],
            "jsonl": [".jsonl"],
            "markdown": [".md", ".markdown"],
            "text": [".txt", ".text"],
        }.get(connector.name, [".txt"])

    def _description_for(self, connector: BaseConnector) -> str:
        return {
            "chatgpt": "ChatGPT conversation export (JSON)",
            "claude": "Claude conversation export (JSON)",
            "claude-code": "Claude Code session JSONL",
            "json": "Generic JSON messages array",
            "jsonl": "JSONL (one message per line)",
            "markdown": "Markdown conversation transcript",
            "text": "Plain text (paragraph alternation)",
        }.get(connector.name, "")


# ── Public API ─────────────────────────────────────────────────────────

registry = ConnectorRegistry()


def detect_format(raw: str, filename: str = "") -> str:
    """Detect and return connector name for raw input."""
    return registry.detect(raw, filename).name


def _detect_from_input(raw: str | dict, filename: str, explicit_type: str | None) -> str:
    """Detect source type from raw input, handling both str and dict."""
    if explicit_type:
        return explicit_type
    if isinstance(raw, dict):
        if "mapping" in raw:
            return "chatgpt"
        if "chat_messages" in raw or "conversations" in raw:
            return "claude"
        if "messages" in raw:
            return "json"
        raise ConnectorError("Cannot detect format from dict input — specify source_type", "registry")
    connector = registry.detect(raw, filename)
    return connector.name


def normalize(raw: str | dict, source_type: str | None = None, filename: str = "") -> NormalizedConversation:
    """Normalize raw conversation data into canonical form.

    Args:
        raw: Raw conversation data (string or dict)
        source_type: Explicit format override (chatgpt, claude, claude-code, json, jsonl, markdown, text)
        filename: Filename hint for auto-detection

    Returns:
        NormalizedConversation with canonical message list

    Raises:
        ConnectorError: If input cannot be parsed or validated
    """
    source_type = _detect_from_input(raw, filename, source_type)
    connector = registry.detect(raw, filename, source_type)
    return connector.parse(raw)


def parse_file(path: str | Path, source_type: str | None = None) -> NormalizedConversation:
    """Read a file and normalize its contents."""
    path = Path(path)
    raw = path.read_text(encoding="utf-8")
    return normalize(raw, source_type=source_type, filename=path.name)
