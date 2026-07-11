"""Task 3: RAG evaluation — testset loading, retrieval metrics, grid, RAGAS mapping.

Mechanics are tested with fakes (no network, no judge LLM): a canned retriever
for metric math, the stub word-hash embedding for the grid, and a recording
provider for RAGAS sample assembly. The live RAGAS run with the Gemini judge
is verified in-session (Stage 2), mirroring Task 1/2's mock-then-verify-live
pattern.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pytest
from chromadb import Documents, EmbeddingFunction, Embeddings

from pcb_vision.rag.ingest import CLASSES
from pcb_vision.rag.evaluate import (
    ThrottledProvider,
    build_ragas_samples,
    choose_config,
    load_testset,
    retrieval_metrics,
    run_grid,
    write_report,
)

REPO_ROOT = Path(__file__).parents[1]
TESTSET_PATH = REPO_ROOT / "eval" / "rag_testset.jsonl"


class StubEmbedding(EmbeddingFunction):
    """Deterministic 64-dim word-hash bag vectors (same as test_rag.py)."""

    DIM = 64

    def __init__(self):
        pass

    @staticmethod
    def name() -> str:
        return "stub_word_hash"

    def get_config(self) -> dict:
        return {}

    @staticmethod
    def build_from_config(config: dict) -> "StubEmbedding":
        return StubEmbedding()

    def __call__(self, input: Documents) -> Embeddings:
        return [self._embed(text) for text in input]

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * self.DIM
        for word in text.lower().split():
            bucket = int(hashlib.md5(word.encode()).hexdigest(), 16) % self.DIM
            vec[bucket] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


class FakeRetriever:
    """Returns canned hits per question; records nothing, embeds nothing."""

    def __init__(self, hits_by_question: dict[str, list[dict]]):
        self._hits = hits_by_question

    def retrieve(self, query: str, defect_class=None, top_k: int = 4) -> list[dict]:
        return self._hits.get(query, [])[:top_k]


class RecordingProvider:
    model = "mock-model"

    def __init__(self, answer: str = "Trim the spur back to the outline [1]."):
        self.answer = answer
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        return self.answer


def _hit(doc_id: str, text: str = "chunk text") -> dict:
    return {
        "chunk_id": f"{doc_id}::000",
        "text": text,
        "score": 0.9,
        "doc_id": doc_id,
        "title": doc_id,
        "defect_class": "spur",
        "doc_type": "rework",
        "section": "Procedure",
    }


def _write_case(path: Path, **overrides) -> None:
    case = {
        "id": "sp_rework",
        "question": "How do I trim a spur?",
        "defect_class": "spur",
        "ground_truth": "Trim it back to the parent conductor outline.",
        "relevant_doc_ids": ["spur_rework"],
    }
    case.update(overrides)
    path.write_text(json.dumps(case) + "\n")


# --- load_testset ---


def test_load_testset_reads_shipped_file():
    cases = load_testset(TESTSET_PATH)
    assert len(cases) == 30
    assert {c["defect_class"] for c in cases} == set(CLASSES)
    for c in cases:
        assert c["question"].strip()
        assert c["ground_truth"].strip()
        assert c["relevant_doc_ids"]


def test_load_testset_rejects_unknown_class(tmp_path):
    p = tmp_path / "ts.jsonl"
    _write_case(p, defect_class="bent_pin")
    with pytest.raises(ValueError, match="bent_pin"):
        load_testset(p)


def test_load_testset_rejects_missing_field(tmp_path):
    p = tmp_path / "ts.jsonl"
    _write_case(p, ground_truth="")
    with pytest.raises(ValueError, match="ground_truth"):
        load_testset(p)


def test_load_testset_rejects_empty_relevant_docs(tmp_path):
    p = tmp_path / "ts.jsonl"
    _write_case(p, relevant_doc_ids=[])
    with pytest.raises(ValueError, match="relevant_doc_ids"):
        load_testset(p)


# --- retrieval_metrics ---


def test_retrieval_metrics_math():
    cases = [
        {"id": "a", "question": "qa", "defect_class": "spur",
         "ground_truth": "g", "relevant_doc_ids": ["d1"]},
        {"id": "b", "question": "qb", "defect_class": "spur",
         "ground_truth": "g", "relevant_doc_ids": ["d2"]},
        {"id": "c", "question": "qc", "defect_class": "spur",
         "ground_truth": "g", "relevant_doc_ids": ["d3"]},
    ]
    retriever = FakeRetriever({
        "qa": [_hit("d1"), _hit("dx")],                 # rank 1 -> rr 1
        "qb": [_hit("dx"), _hit("dy"), _hit("d2")],     # rank 3 -> rr 1/3
        "qc": [_hit("dx"), _hit("dy"), _hit("dz")],     # miss  -> rr 0
    })
    m = retrieval_metrics(retriever, cases, top_k=3)
    assert m["n"] == 3
    assert m["hit_rate"] == pytest.approx(2 / 3)
    assert m["mrr"] == pytest.approx((1 + 1 / 3 + 0) / 3)


def test_retrieval_metrics_rank_is_first_matching_chunk():
    cases = [{"id": "a", "question": "qa", "defect_class": "spur",
              "ground_truth": "g", "relevant_doc_ids": ["d2"]}]
    retriever = FakeRetriever({"qa": [_hit("dx"), _hit("d2"), _hit("d2")]})
    m = retrieval_metrics(retriever, cases, top_k=3)
    assert m["mrr"] == pytest.approx(1 / 2)


# --- run_grid ---

KB_DOC = """\
---
title: "{title}"
defect_class: {defect_class}
doc_type: {doc_type}
---
## Section one
{body}

## Section two
{body} again with more words about {topic}.
"""


def _mini_kb(tmp_path: Path) -> Path:
    kb = tmp_path / "kb"
    kb.mkdir()
    (kb / "spur_rework.md").write_text(KB_DOC.format(
        title="Spur rework", defect_class="spur", doc_type="rework",
        body="Trim the spur filament back to the parent conductor outline with a scalpel.",
        topic="trimming spurs safely"))
    (kb / "short_overview.md").write_text(KB_DOC.format(
        title="Short overview", defect_class="short", doc_type="overview",
        body="A short is an unintended copper bridge connecting two isolated nets.",
        topic="copper bridges between nets"))
    return kb


def test_run_grid_produces_row_per_config(tmp_path):
    cases = [
        {"id": "sp", "question": "trim the spur filament with a scalpel",
         "defect_class": "spur", "ground_truth": "g",
         "relevant_doc_ids": ["spur_rework"]},
        {"id": "sh", "question": "unintended copper bridge connecting nets",
         "defect_class": "short", "ground_truth": "g",
         "relevant_doc_ids": ["short_overview"]},
    ]
    rows = run_grid(
        kb_dir=_mini_kb(tmp_path),
        cases=cases,
        chunk_sizes=[400, 800],
        top_ks=[1, 2],
        work_dir=tmp_path / "indexes",
        embedding_fn=StubEmbedding(),
    )
    assert [(r["chunk_size"], r["top_k"]) for r in rows] == [
        (400, 1), (400, 2), (800, 1), (800, 2)]
    for r in rows:
        assert r["n_chunks"] > 0
        assert 0.0 <= r["hit_rate"] <= 1.0
        assert 0.0 <= r["mrr"] <= 1.0
    # each query's vocabulary is lifted verbatim from exactly one doc: the
    # word-hash stub must rank that doc first -> perfect scores at any config
    assert all(r["hit_rate"] == 1.0 for r in rows)


# --- choose_config ---


def _row(chunk_size, top_k, hit_rate, mrr):
    return {"chunk_size": chunk_size, "top_k": top_k, "n_chunks": 100,
            "hit_rate": hit_rate, "mrr": mrr}


def test_choose_config_picks_best_hit_rate():
    rows = [_row(500, 6, 0.80, 0.70), _row(800, 3, 0.90, 0.60)]
    assert choose_config(rows) is rows[1]


def test_choose_config_breaks_ties_by_mrr_then_smaller_top_k():
    rows = [_row(800, 6, 0.90, 0.70), _row(800, 3, 0.90, 0.70),
            _row(500, 4, 0.90, 0.65)]
    assert choose_config(rows) is rows[1]  # tie on hit_rate+mrr -> smaller k


# --- build_ragas_samples ---


def test_build_ragas_samples_maps_recommend_output():
    case = {"id": "sp_rework", "question": "How do I trim a spur?",
            "defect_class": "spur",
            "ground_truth": "Trim it back to the parent conductor outline.",
            "relevant_doc_ids": ["spur_rework"]}
    hits = [_hit("spur_rework", text="Trim with a scalpel."),
            _hit("general_rework_practices", text="Verify electrically.")]
    retriever = FakeRetriever({case["question"]: hits})
    provider = RecordingProvider()

    samples = build_ragas_samples([case], retriever, provider, top_k=2)

    assert len(samples) == 1
    s = samples[0]
    assert s["user_input"] == case["question"]
    assert s["retrieved_contexts"] == ["Trim with a scalpel.", "Verify electrically."]
    assert s["response"] == provider.answer
    assert s["reference"] == case["ground_truth"]
    assert len(provider.calls) == 1  # one generation per case


# --- ThrottledProvider ---


class FlakyProvider:
    """Fails with a rate-limit error n times, then succeeds."""

    model = "flaky-model"

    def __init__(self, failures: int):
        self.failures = failures
        self.calls = 0

    def complete(self, system: str, user: str) -> str:
        self.calls += 1
        if self.calls <= self.failures:
            raise RuntimeError("429 RESOURCE_EXHAUSTED: rate limit")
        return "ok [1]"


def test_throttled_provider_retries_rate_limits():
    inner = FlakyProvider(failures=2)
    provider = ThrottledProvider(inner, min_interval=0.0, max_retries=4, base_wait=0.0)
    assert provider.complete("sys", "user") == "ok [1]"
    assert inner.calls == 3
    assert provider.model == "flaky-model"  # protocol field passes through


def test_throttled_provider_gives_up_after_max_retries():
    inner = FlakyProvider(failures=99)
    provider = ThrottledProvider(inner, min_interval=0.0, max_retries=2, base_wait=0.0)
    with pytest.raises(RuntimeError, match="429"):
        provider.complete("sys", "user")
    assert inner.calls == 3  # initial call + 2 retries


# --- write_report ---


def test_write_report_renders_grid_and_metrics(tmp_path):
    rows = [_row(500, 3, 0.83, 0.71), _row(800, 4, 0.93, 0.82)]
    chosen = rows[1]
    ragas_rows = [
        {"config": "winner (chunk_size=800, top_k=4)", "faithfulness": 0.91,
         "answer_relevancy": 0.87, "context_precision": 0.78, "n": 30},
    ]
    out = tmp_path / "rag_evaluation.md"
    write_report(out, rows, chosen, ragas_rows)
    text = out.read_text()
    assert "| 800 | 4 |" in text          # grid table row
    assert "0.93" in text                  # winning hit rate
    assert "chunk_size=800" in text        # chosen config stated
    assert "faithfulness" in text.lower()  # headline metric present
    assert "0.91" in text
