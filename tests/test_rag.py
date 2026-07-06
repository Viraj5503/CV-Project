"""Tests for the Phase 2 RAG layer: KB loading, chunking, indexing, retrieval.

Mechanics are tested with a deterministic stub embedding function (word-hash
bag vectors) so the suite stays fast and offline — the real MiniLM model is
exercised by scripts/rag_smoke.py against the real knowledge base, mirroring
Phase 1's mock-YOLO-then-verify-live pattern.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

import pytest
from chromadb import Documents, EmbeddingFunction, Embeddings

from pcb_vision.rag.ingest import CLASSES, GENERAL, build_index, chunk_docs, load_kb_docs
from pcb_vision.rag.retrieve import Retriever

# ---------------------------------------------------------------- fixtures


class StubEmbedding(EmbeddingFunction):
    """Deterministic 64-dim word-hash bag vectors: shared vocabulary between
    query and chunk -> high cosine similarity. Stable across processes
    (hashlib, not the salted builtin hash)."""

    DIM = 64

    def __init__(self):  # explicit: chromadb deprecation-warns on implicit __init__
        pass

    @staticmethod
    def name() -> str:  # ditto for name() and get_config()
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


OPEN_CIRCUIT_DOC = """\
---
title: "Open circuit: rework and repair procedure"
defect_class: open_circuit
doc_type: rework
---
## Repair feasibility
An open circuit trace break can be bridged with a jumper wire soldered across
the gap, or filled with conductive epoxy for narrow interruptions.

## Procedure
Scrape solder mask back to bright copper on both sides of the break, tin the
exposed pads, then lay the jumper wire and flow solder over each end.
"""

SHORT_DOC = """\
---
title: "Short circuit: description and causes"
defect_class: short
doc_type: overview
---
## What it is
A short is an unintended copper bridge connecting two conductors that should
remain electrically isolated, usually from incomplete etching residue.

## Common causes
Insufficient etchant agitation, photoresist scumming, or inadequate clearance
in the artwork all leave copper slivers spanning adjacent traces.
"""

GENERAL_DOC = """\
---
title: "General rework practices"
defect_class: general
doc_type: rework
---
## Workstation discipline
Always wear a grounded ESD wrist strap, clean residue with isopropyl alcohol,
and apply fresh flux before touching any joint with the iron.
"""


def make_kb(tmp_path: Path) -> Path:
    kb = tmp_path / "kb"
    kb.mkdir()
    (kb / "open_circuit_rework.md").write_text(OPEN_CIRCUIT_DOC)
    (kb / "short_overview.md").write_text(SHORT_DOC)
    (kb / "general_rework_practices.md").write_text(GENERAL_DOC)
    return kb


# ---------------------------------------------------------------- load_kb_docs


def test_load_kb_docs_parses_frontmatter(tmp_path):
    docs = load_kb_docs(make_kb(tmp_path))

    assert len(docs) == 3
    by_id = {d["doc_id"]: d for d in docs}
    oc = by_id["open_circuit_rework"]
    assert oc["title"] == "Open circuit: rework and repair procedure"
    assert oc["defect_class"] == "open_circuit"
    assert oc["doc_type"] == "rework"
    assert "## Repair feasibility" in oc["text"]
    assert "---" not in oc["text"].split("##")[0]  # frontmatter stripped


def test_load_kb_docs_rejects_unknown_class(tmp_path):
    kb = tmp_path / "kb"
    kb.mkdir()
    (kb / "bad.md").write_text(
        "---\ntitle: Bad\ndefect_class: solder_bridge\ndoc_type: overview\n---\n## X\nbody\n"
    )
    with pytest.raises(ValueError, match="solder_bridge"):
        load_kb_docs(kb)


def test_load_kb_docs_rejects_missing_frontmatter(tmp_path):
    kb = tmp_path / "kb"
    kb.mkdir()
    (kb / "bare.md").write_text("## No frontmatter here\njust a body\n")
    with pytest.raises(ValueError, match="bare"):
        load_kb_docs(kb)


def test_classes_constant_matches_phase1():
    assert CLASSES == (
        "missing_hole",
        "mouse_bite",
        "open_circuit",
        "short",
        "spur",
        "spurious_copper",
    )
    assert GENERAL == "general"


# ---------------------------------------------------------------- chunk_docs


def test_chunk_docs_propagates_metadata(tmp_path):
    docs = load_kb_docs(make_kb(tmp_path))
    chunks = chunk_docs(docs, chunk_size=800, chunk_overlap=120)

    assert len(chunks) >= 5  # >=2 sections per class doc + 1 general
    ids = [c["chunk_id"] for c in chunks]
    assert len(ids) == len(set(ids)), "chunk_ids must be unique"
    for c in chunks:
        assert c["text"].strip()
        meta = c["metadata"]
        for key in ("doc_id", "title", "defect_class", "doc_type", "section"):
            assert key in meta, f"missing metadata key {key}"
        assert c["chunk_id"].startswith(meta["doc_id"] + "::")
    sections = {c["metadata"]["section"] for c in chunks}
    assert "Repair feasibility" in sections


def test_chunk_docs_splits_oversize_sections(tmp_path):
    kb = tmp_path / "kb"
    kb.mkdir()
    long_body = " ".join(f"sentence number {i} about copper etching." for i in range(60))
    (kb / "spur_overview.md").write_text(
        f"---\ntitle: Spur overview\ndefect_class: spur\ndoc_type: overview\n---\n"
        f"## One long section\n{long_body}\n"
    )
    chunks = chunk_docs(load_kb_docs(kb), chunk_size=200, chunk_overlap=40)

    assert len(chunks) > 1, "oversize section must split into multiple chunks"
    assert all(len(c["text"]) <= 200 for c in chunks)
    assert all(c["metadata"]["section"] == "One long section" for c in chunks)


# ---------------------------------------------------------------- index + retrieve


def test_build_index_and_retrieve_round_trip(tmp_path):
    stats = build_index(
        make_kb(tmp_path), tmp_path / "chroma", embedding_fn=StubEmbedding()
    )
    assert stats["n_docs"] == 3
    assert stats["n_chunks"] >= 5
    assert stats["per_class"]["open_circuit"] >= 2

    r = Retriever(tmp_path / "chroma", embedding_fn=StubEmbedding())
    hits = r.retrieve(
        "bridge the trace break with a jumper wire soldered across the gap", top_k=2
    )

    assert len(hits) == 2
    top = hits[0]
    assert top["doc_id"] == "open_circuit_rework"
    for key in ("chunk_id", "text", "score", "doc_id", "title", "defect_class", "doc_type", "section"):
        assert key in top, f"missing result key {key}"
    assert hits[0]["score"] >= hits[1]["score"], "results must be sorted by score desc"


def test_retrieve_class_filter_returns_only_class_and_general(tmp_path):
    build_index(make_kb(tmp_path), tmp_path / "chroma", embedding_fn=StubEmbedding())
    r = Retriever(tmp_path / "chroma", embedding_fn=StubEmbedding())

    hits = r.retrieve("how do I repair this defect", defect_class="short", top_k=10)
    assert hits, "filter must still return the short + general chunks"
    assert {h["defect_class"] for h in hits} <= {"short", "general"}

    hits = r.retrieve("how do I repair this defect", defect_class="open_circuit", top_k=10)
    assert {h["defect_class"] for h in hits} <= {"open_circuit", "general"}


def test_build_index_rebuild_is_idempotent(tmp_path):
    kb = make_kb(tmp_path)
    first = build_index(kb, tmp_path / "chroma", embedding_fn=StubEmbedding())
    second = build_index(kb, tmp_path / "chroma", embedding_fn=StubEmbedding())

    assert first["n_chunks"] == second["n_chunks"], "rebuild must not duplicate chunks"
    r = Retriever(tmp_path / "chroma", embedding_fn=StubEmbedding())
    assert r.count() == second["n_chunks"]
