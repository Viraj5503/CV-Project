"""Tests for the Phase 2 RAG generation layer: provider selection + grounded
recommendations with citations.

Providers are mocked (a recording stub satisfying the LLMProvider protocol) so
the suite stays fast, offline, and key-free — live generation is verified
against whichever real key exists (Gemini expected), mirroring the
stub-then-verify-live pattern of test_rag.py / rag_smoke.py.
"""

from __future__ import annotations

import pytest
from test_rag import StubEmbedding, make_kb

from pcb_vision.rag.generate import recommend
from pcb_vision.rag.ingest import build_index
from pcb_vision.rag.providers import (
    AnthropicProvider,
    GeminiProvider,
    provider_from_env,
)
from pcb_vision.rag.retrieve import Retriever

# ---------------------------------------------------------------- fixtures


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Isolate provider selection from the ambient shell / .env."""
    for var in ("PCB_RAG_PROVIDER", "PCB_RAG_MODEL", "GEMINI_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture()
def retriever(tmp_path):
    build_index(make_kb(tmp_path), tmp_path / "chroma", embedding_fn=StubEmbedding())
    return Retriever(tmp_path / "chroma", embedding_fn=StubEmbedding())


class MockProvider:
    """Records prompts, returns a canned answer. Satisfies LLMProvider."""

    model = "mock-model"

    def __init__(self, reply: str = "Bridge the break with a jumper wire [1]."):
        self.reply = reply
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        return self.reply


# ---------------------------------------------------------------- provider_from_env


def test_provider_from_env_none_is_extractive(monkeypatch):
    monkeypatch.setenv("PCB_RAG_PROVIDER", "none")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")  # explicit none wins over keys
    assert provider_from_env() is None


def test_provider_from_env_gemini(monkeypatch):
    monkeypatch.setenv("PCB_RAG_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    p = provider_from_env()
    assert isinstance(p, GeminiProvider)
    assert "gemini" in p.model


def test_provider_from_env_anthropic(monkeypatch):
    monkeypatch.setenv("PCB_RAG_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    p = provider_from_env()
    assert isinstance(p, AnthropicProvider)
    assert "claude" in p.model


def test_provider_from_env_missing_key_degrades_to_none(monkeypatch):
    monkeypatch.setenv("PCB_RAG_PROVIDER", "gemini")  # asked for gemini, no key
    assert provider_from_env() is None
    monkeypatch.setenv("PCB_RAG_PROVIDER", "anthropic")  # asked for anthropic, no key
    assert provider_from_env() is None


def test_provider_from_env_unset_autodetects(monkeypatch):
    assert provider_from_env() is None  # no keys at all

    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    assert isinstance(provider_from_env(), GeminiProvider)  # only gemini key

    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")  # anthropic is default-in-code
    assert isinstance(provider_from_env(), AnthropicProvider)


def test_provider_from_env_model_override(monkeypatch):
    monkeypatch.setenv("PCB_RAG_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setenv("PCB_RAG_MODEL", "gemini-custom-123")
    assert provider_from_env().model == "gemini-custom-123"


def test_provider_from_env_rejects_unknown_value(monkeypatch):
    monkeypatch.setenv("PCB_RAG_PROVIDER", "openai")
    with pytest.raises(ValueError, match="openai"):
        provider_from_env()


# ---------------------------------------------------------------- recommend: extractive


def test_recommend_extractive_mode(retriever):
    out = recommend("open_circuit", retriever, provider=None, top_k=3)

    assert out["mode"] == "extractive"
    assert out["model"] is None
    assert out["citations"], "extractive mode must still cite retrieved chunks"
    for c in out["citations"]:
        assert set(c) == {"chunk_id", "doc_id", "title", "section"}
    assert "[1]" in out["answer"], "passages must be numbered like generative citations"
    # verbatim: the top chunk's text appears in the answer
    top = retriever.retrieve("open circuit repair", defect_class="open_circuit", top_k=1)[0]
    assert top["doc_id"] in {c["doc_id"] for c in out["citations"]}


def test_recommend_not_covered_when_nothing_retrieved(tmp_path):
    # KB with a single short doc and no general docs -> spur filter matches nothing
    kb = tmp_path / "kb"
    kb.mkdir()
    (kb / "short_overview.md").write_text(
        "---\ntitle: Short overview\ndefect_class: short\ndoc_type: overview\n---\n"
        "## What it is\nAn unintended copper bridge between conductors.\n"
    )
    build_index(kb, tmp_path / "chroma", embedding_fn=StubEmbedding())
    r = Retriever(tmp_path / "chroma", embedding_fn=StubEmbedding())

    provider = MockProvider()
    out = recommend("spur", r, provider=provider)

    assert "not covered by the knowledge base" in out["answer"].lower()
    assert out["citations"] == []
    assert provider.calls == [], "no context -> LLM must not be called"


def test_recommend_rejects_unknown_class(retriever):
    with pytest.raises(ValueError, match="solder_bridge"):
        recommend("solder_bridge", retriever, provider=None)


# ---------------------------------------------------------------- recommend: generative


def test_recommend_generative_mode(retriever):
    provider = MockProvider(reply="Scrape mask, tin pads, lay jumper wire [1][2].")
    out = recommend("open_circuit", retriever, provider=provider, top_k=2)

    assert out["mode"] == "generative"
    assert out["model"] == "mock-model"
    assert out["answer"] == "Scrape mask, tin pads, lay jumper wire [1][2]."
    assert len(out["citations"]) == 2, "one citation per numbered context chunk"
    assert len(provider.calls) == 1


def test_recommend_prompt_contract(retriever):
    provider = MockProvider()
    recommend(
        "open_circuit",
        retriever,
        provider=provider,
        question="How do I fix a broken trace?",
        top_k=2,
    )

    system, user = provider.calls[0]
    # grounding contract lives in the system prompt
    assert "only" in system.lower() and "context" in system.lower()
    assert "not covered by the knowledge base" in system.lower()
    assert "cite" in system.lower()
    # user prompt carries the numbered chunks + the question
    assert "[1]" in user and "[2]" in user
    assert "How do I fix a broken trace?" in user


def test_recommend_default_question_mentions_class(retriever):
    provider = MockProvider()
    recommend("open_circuit", retriever, provider=provider)

    _, user = provider.calls[0]
    assert "open circuit" in user.lower(), "default question must name the defect"


def test_recommend_default_question_uses_readable_label(retriever):
    # "short" alone is a weak retrieval query (adjective, not the defect name);
    # the default question itself must spell out "short circuit"
    provider = MockProvider()
    recommend("short", retriever, provider=provider)

    _, user = provider.calls[0]
    question = user.split("Question:")[-1]
    assert "short circuit" in question.lower()


def test_recommend_citations_follow_retrieval_order(retriever):
    provider = MockProvider()
    out = recommend("open_circuit", retriever, provider=provider, top_k=3)

    hits = retriever.retrieve(
        provider.calls[0][1].split("Question:")[-1].strip() or "open circuit",
        defect_class="open_circuit",
        top_k=3,
    )
    # citation [n] maps to the n-th retrieved chunk
    assert [c["chunk_id"] for c in out["citations"]] == [h["chunk_id"] for h in hits]
