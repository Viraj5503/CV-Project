"""Grounded repair recommendations: retrieve -> numbered context -> cited answer.

The prompt contract (what RAGAS faithfulness measures in Task 3): the model
answers ONLY from the numbered context chunks, cites them as [1]..[k], and
says "not covered by the knowledge base" when the context is insufficient.
With no provider configured we fall back to extractive mode — the retrieved
passages verbatim, numbered the same way, so citations stay meaningful.
"""

from __future__ import annotations

from pcb_vision.rag.providers import LLMProvider
from pcb_vision.rag.retrieve import Retriever

SYSTEM_PROMPT = (
    "You are a PCB fabrication repair advisor. Answer using ONLY the numbered "
    "context chunks provided — no outside knowledge. Cite the chunks that support "
    "each statement inline, e.g. [1] or [2][3]. If the context does not answer the "
    'question, reply exactly: "not covered by the knowledge base". Be concise and '
    "practical: state whether the defect is repairable, when it is acceptable "
    "as-is, and the rework steps."
)

NOT_COVERED = "Not covered by the knowledge base."

EXTRACTIVE_HEADER = (
    "No LLM provider configured — showing the most relevant knowledge-base "
    "passages verbatim:"
)


# Human-readable defect names for prompts and retrieval queries. Mostly just
# underscore-stripping, but "short" alone is a weak semantic query (reads as
# an adjective) — spelling out "short circuit" pulls the right chunks.
CLASS_LABELS = {
    "missing_hole": "missing hole",
    "mouse_bite": "mouse bite",
    "open_circuit": "open circuit",
    "short": "short circuit",
    "spur": "spur",
    "spurious_copper": "spurious copper",
}


def _default_question(defect_class: str) -> str:
    cls = CLASS_LABELS.get(defect_class, defect_class.replace("_", " "))
    return (
        f"Describe {cls} defects: when are they acceptable, and how should "
        "they be reworked?"
    )


def _numbered_context(hits: list[dict]) -> str:
    return "\n\n".join(
        f"[{i}] {h['title']} — {h['section']}\n{h['text']}"
        for i, h in enumerate(hits, 1)
    )


def recommend(
    defect_class: str,
    retriever: Retriever,
    provider: LLMProvider | None,
    question: str | None = None,
    top_k: int = 4,
) -> dict:
    """Grounded recommendation for one detected defect class.

    Returns {"answer", "citations", "mode": "generative"|"extractive",
    "model": str|None}; citations[n-1] is the chunk cited as [n].
    """
    if question is None:
        question = _default_question(defect_class)

    hits = retriever.retrieve(question, defect_class=defect_class, top_k=top_k)
    if not hits:  # nothing in-class to ground on -> never call the LLM
        return {"answer": NOT_COVERED, "citations": [], "mode": "extractive", "model": None}

    citations = [
        {"chunk_id": h["chunk_id"], "doc_id": h["doc_id"], "title": h["title"], "section": h["section"]}
        for h in hits
    ]
    context = _numbered_context(hits)

    if provider is None:
        return {
            "answer": f"{EXTRACTIVE_HEADER}\n\n{context}",
            "citations": citations,
            "mode": "extractive",
            "model": None,
        }

    user = f"Context:\n\n{context}\n\nQuestion: {question}"
    answer = provider.complete(SYSTEM_PROMPT, user)
    return {"answer": answer, "citations": citations, "mode": "generative", "model": provider.model}
