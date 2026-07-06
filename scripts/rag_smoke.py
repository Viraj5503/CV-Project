"""Retrieval smoke test against the real knowledge base + real embeddings.

For every defect class, runs two canned advisor-style queries and checks that
the top-1 retrieved chunk comes from that class (or a `general` doc). Writes
the results table to reports/rag_retrieval_smoke.md and exits non-zero on any
failure — the live counterpart to the stub-embedding unit tests.

Run after ingestion:  python -m pcb_vision.rag.ingest && python scripts/rag_smoke.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from pcb_vision.rag.ingest import CHROMA_DIR, CLASSES, GENERAL
from pcb_vision.rag.retrieve import Retriever

REPORT = Path("reports/rag_retrieval_smoke.md")

QUERY_TEMPLATES = (
    "How do I repair a {label} defect on a PCB?",
    "When is a {label} acceptable on a bare board?",
)


def main() -> int:
    retriever = Retriever(CHROMA_DIR)
    rows, failures = [], 0

    for cls in CLASSES:
        label = cls.replace("_", " ")
        for template in QUERY_TEMPLATES:
            query = template.format(label=label)
            hits = retriever.retrieve(query, defect_class=cls, top_k=3)
            top = hits[0]
            ok = top["defect_class"] in (cls, GENERAL)
            failures += 0 if ok else 1
            rows.append(
                {
                    "query": query,
                    "top_chunk": f"`{top['chunk_id']}` ({top['doc_type']}, {top['defect_class']})",
                    "score": f"{top['score']:.3f}",
                    "also_retrieved": ", ".join(f"`{h['doc_id']}`" for h in hits[1:]),
                    "ok": "✅" if ok else "❌",
                }
            )
            status = "ok " if ok else "FAIL"
            print(f"[{status}] {query}  ->  {top['chunk_id']}  (score {top['score']:.3f})")

    lines = [
        "# RAG retrieval smoke test",
        "",
        f"Index: `{CHROMA_DIR}` ({retriever.count()} chunks) — real `all-MiniLM-L6-v2` "
        "embeddings, class-filtered retrieval (`defect_class` ∈ {class, general}), top-3.",
        "",
        "| Query | Top-1 chunk | Score | Also retrieved | Pass |",
        "|---|---|---|---|---|",
    ]
    lines += [
        f"| {r['query']} | {r['top_chunk']} | {r['score']} | {r['also_retrieved']} | {r['ok']} |"
        for r in rows
    ]
    lines += ["", f"**Result: {len(rows) - failures}/{len(rows)} queries passed.**", ""]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n{len(rows) - failures}/{len(rows)} passed — report written to {REPORT}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
