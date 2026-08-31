"""LLM provider abstraction with backward-compatible top-level API.

Providers implement the same interface so the chat router and orchestrator
are provider-agnostic.  The default is Anthropic; OpenAI is also supported.
A mock provider is used when no API key is configured.

The legacy ``chat_completion`` and ``_mock_response`` names are preserved
for existing callers and tests.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, AsyncIterator

from app.core.config import settings


# ── Provider classes ────────────────────────────────────────────────────────


class LLMProvider:
    """Protocol-style base — all providers share these methods."""

    name: str = "base"

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> dict[str, Any] | AsyncIterator[str]:
        ...

    async def aclose(self) -> None:
        ...


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str) -> None:
        from anthropic import AsyncAnthropic
        self._client = AsyncAnthropic(api_key=api_key)

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> dict[str, Any] | AsyncIterator[str]:
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if temperature is not None:
            kwargs["temperature"] = temperature

        if stream:
            return self._stream(messages, model, max_tokens, temperature)

        response = await self._client.messages.create(**kwargs)
        return _anthropic_to_dict(response)

    async def _stream(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float | None,
    ) -> AsyncIterator[str]:
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if temperature is not None:
            kwargs["temperature"] = temperature

        async with self._client.messages.stream(**kwargs) as s:
            async for text in s.text_stream:
                yield text

    async def aclose(self) -> None:
        await self._client.close()


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str) -> None:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=api_key)

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> dict[str, Any] | AsyncIterator[str]:
        if stream:
            return self._stream(messages, model, max_tokens, temperature)

        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return _openai_to_dict(response)

    async def _stream(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield delta

    async def aclose(self) -> None:
        await self._client.close()


class MockProvider(LLMProvider):
    name = "mock"

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> dict[str, Any] | AsyncIterator[str]:
        user_msg = ""
        memory_context = ""
        # Scan for memory context in system messages
        for msg in reversed(messages):
            if msg.get("role") == "system":
                content = msg.get("content", "")
                if "Relevant memories:" in content:
                    parts = content.split("Relevant memories:")
                    if len(parts) > 1:
                        memory_context = parts[1].strip()
                        break
        # Find the last user message
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_msg = msg.get("content", "")
                break

        if memory_context:
            # Include memory context directly in response for test verification
            # Format is "[FACT] ..." or "[DECISION] ..." — extract content
            text = f'[Mock AI] Answer based on ingested memory: {memory_context}'
        else:
            text = (
                f'[Mock AI] I received your message: "{user_msg}". '
                "Set a real LLM_API_KEY in .env to enable live responses."
            )

        if stream:
            async def _gen() -> AsyncIterator[str]:
                for word in text.split(" "):
                    yield word + " "
            return _gen()

        return {
            "content": text,
            "model": model,
            "provider": "mock",
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
            "stop_reason": "mock_end_turn",
        }

    async def aclose(self) -> None:
        pass


# ── Serialisation helpers ────────────────────────────────────────────────────

def _anthropic_to_dict(resp) -> dict[str, Any]:
    return {
        "content": resp.content[0].text,
        "model": resp.model,
        "provider": "anthropic",
        "usage": {
            "prompt_tokens": resp.usage.input_tokens,
            "completion_tokens": resp.usage.output_tokens,
            "total_tokens": resp.usage.input_tokens + resp.usage.output_tokens,
        },
        "stop_reason": resp.stop_reason,
    }


def _openai_to_dict(resp) -> dict[str, Any]:
    return {
        "content": resp.choices[0].message.content or "",
        "model": resp.model,
        "provider": "openai",
        "usage": {
            "prompt_tokens": resp.usage.prompt_tokens,
            "completion_tokens": resp.usage.completion_tokens,
            "total_tokens": resp.usage.total_tokens,
        },
        "stop_reason": resp.choices[0].finish_reason,
    }


# ── Factory ──────────────────────────────────────────────────────────────────

def get_llm_provider() -> LLMProvider:
    """Return the configured provider."""
    provider_name = settings.llm_provider.lower()

    if provider_name == "anthropic" and settings.anthropic_api_key:
        return AnthropicProvider(settings.anthropic_api_key)
    if provider_name == "openai" and settings.openai_api_key:
        return OpenAIProvider(settings.openai_api_key)

    return MockProvider()


# ── Backward-compat API (used by tests and chat_orchestrator) ─────────────────

async def chat_completion(
    messages: list[dict[str, str]],
    model: str | None = None,
    max_tokens: int = 1024,
    system: str | None = None,
) -> dict[str, Any]:
    """Non-streaming completion — backward-compatible wrapper."""
    provider = get_llm_provider()
    resolved_model = model or settings.llm_model

    # Merge system prompt into messages if provided
    if system and messages and messages[0].get("role") != "system":
        messages = [{"role": "system", "content": system}] + messages

    try:
        result = await provider.chat_completion(
            messages=messages,
            model=resolved_model,
            max_tokens=max_tokens,
            temperature=settings.llm_temperature,
            stream=False,
        )
        if isinstance(result, dict):
            return result
        # Should not happen for non-stream, but handle gracefully
        return {
            "content": "".join([c async for c in result]),
            "model": resolved_model,
            "provider": provider.name,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "stop_reason": "end_turn",
        }
    finally:
        await provider.aclose()


def _mock_response(message: str) -> dict[str, Any]:
    """Deterministic mock for environments without an API key."""
    return {
        "content": (
            f'[Mock AI] I received your message: "{message}". '
            "Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env to enable real LLM responses."
        ),
        "model": "mock",
        "provider": "mock",
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
        "stop_reason": "mock_end_turn",
    }
