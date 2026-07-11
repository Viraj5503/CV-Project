"""Pluggable LLM providers for RAG generation.

Provider selection honors the no-Anthropic-key constraint: `PCB_RAG_PROVIDER`
picks the backend explicitly (anthropic | gemini | none); when unset we
auto-detect from available keys — Anthropic first (the in-code default),
then Gemini (the expected free-tier generator). No key at all -> None,
which generate.py treats as extractive mode (retrieved passages verbatim).
"""

from __future__ import annotations

import os
from typing import Protocol

PROVIDER_CHOICES = ("anthropic", "gemini", "none")


class LLMProvider(Protocol):
    model: str

    def complete(self, system: str, user: str) -> str: ...


class AnthropicProvider:
    DEFAULT_MODEL = "claude-opus-4-8"

    def __init__(self, api_key: str, model: str | None = None):
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model or self.DEFAULT_MODEL

    def complete(self, system: str, user: str) -> str:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in response.content if b.type == "text").strip()


class GeminiProvider:
    # Rolling alias on the *lite* line: free-tier daily quotas are per-model,
    # Google retires/requotas pinned models without notice (2.5-flash-lite ->
    # 404, 2.0-flash -> limit 0), and as of 2026-07 every flagship flash
    # (2.5-flash, 3.5-flash) is capped at 20 req/day free — only the lite line
    # has a usable free quota. Pin via PCB_RAG_MODEL if reproducibility matters.
    DEFAULT_MODEL = "gemini-flash-lite-latest"  # free tier (AI Studio), no card

    def __init__(self, api_key: str, model: str | None = None):
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self.model = model or self.DEFAULT_MODEL

    def complete(self, system: str, user: str) -> str:
        from google.genai import types

        response = self._client.models.generate_content(
            model=self.model,
            contents=user,
            config=types.GenerateContentConfig(system_instruction=system),
        )
        return (response.text or "").strip()


def provider_from_env() -> LLMProvider | None:
    """Build a provider from PCB_RAG_PROVIDER (+ key env vars), or None.

    A selected provider whose key is missing degrades to None rather than
    raising — same graceful-degradation philosophy as Phase 1's VLM reports.
    Only a *misspelled* provider name is a hard error.
    """
    choice = os.environ.get("PCB_RAG_PROVIDER", "").strip().lower()
    model = os.environ.get("PCB_RAG_MODEL") or None
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if choice == "none":
        return None
    if choice == "anthropic":
        return AnthropicProvider(anthropic_key, model) if anthropic_key else None
    if choice == "gemini":
        return GeminiProvider(gemini_key, model) if gemini_key else None
    if choice == "":
        if anthropic_key:
            return AnthropicProvider(anthropic_key, model)
        if gemini_key:
            return GeminiProvider(gemini_key, model)
        return None
    raise ValueError(
        f"unknown PCB_RAG_PROVIDER {choice!r} (expected one of {PROVIDER_CHOICES})"
    )
