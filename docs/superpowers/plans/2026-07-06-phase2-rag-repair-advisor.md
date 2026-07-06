# RAG-Powered Repair Advisor (Phase 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When a defect is detected, retrieve the relevant section from a self-authored PCB quality/repair knowledge base and generate a grounded repair recommendation with source citations — adding RAG + vector DB + LLM-evaluation to the shipped Phase 1 project.

**Architecture:** A `knowledge_base/` of self-authored markdown docs (tagged by defect class) is chunked and embedded locally (sentence-transformers) into a persistent ChromaDB index. A `Retriever` does hybrid retrieval: metadata filter by detected defect class + semantic top-k. A pluggable LLM provider (Anthropic default-in-code / Gemini free tier / extractive fallback) generates answer-only-from-context recommendations with citations. RAGAS scores the pipeline on a hand-built test set. New `/recommend` FastAPI endpoint + Streamlit "Repair Advisor" tab.

**Tech Stack:** chromadb (persistent), sentence-transformers (`all-MiniLM-L6-v2`, local/free), langchain-text-splitters (header-aware chunking), google-genai (Gemini free tier) + anthropic (pluggable), RAGAS, existing FastAPI/Streamlit/Docker stack.

## Global Constraints

- **Phase 1 stays fully functional standalone.** No behavior changes to existing modules; all RAG code lives in `src/pcb_vision/rag/`; existing 20 tests must stay green every session.
- **No active Anthropic API key.** Nothing in Phase 2 may *require* one at build/test/demo time. Generation goes through a provider layer: `PCB_RAG_PROVIDER` = `anthropic` | `gemini` | `none` (extractive fallback: retrieved passages + citations verbatim). Anthropic stays the default *in code*; Gemini free-tier key (AI Studio, no card) is the working generator + RAGAS judge.
- **Licensing:** NEVER scrape or reproduce IPC-A-610 / IPC-7711/21 text. The knowledge base is self-authored markdown written from general, publicly documented PCB engineering practice, in IPC-*style* framing (Class 1/2/3 concepts described, never quoted). `knowledge_base/SOURCES.md` documents the approach; README gets a licensing note in Task 5.
- Defect classes (canonical, from Phase 1): `missing_hole, mouse_bite, open_circuit, short, spur, spurious_copper`; cross-cutting docs use `general`.
- Embeddings local + free: `all-MiniLM-L6-v2` via `PCB_EMBED_MODEL`; index at `data/chroma/` (`PCB_CHROMA_DIR`, gitignored, rebuilt via `python -m pcb_vision.rag.ingest`); KB at `knowledge_base/` (`PCB_KB_DIR`, committed).
- Env: `.venv` (Python 3.11). Commits in Viraj's plain style, **no Claude attribution**. Each task ends: run full test suite → verify → commit → update Status log.
- One task per session (Viraj's cadence). Quality bar = Phase 1: quantified metrics, citations visible in UI, faithfulness is the headline number.

---

### Task 1: Knowledge base — curate, ingest, retrieve (chunking, embeddings, ChromaDB, smoke tests)

**Files:**
- Create: `knowledge_base/` — 21 self-authored markdown docs (list below) + `knowledge_base/SOURCES.md`
- Create: `src/pcb_vision/rag/__init__.py`, `src/pcb_vision/rag/ingest.py`, `src/pcb_vision/rag/retrieve.py`
- Create: `scripts/rag_smoke.py`
- Test: `tests/test_rag.py`
- Modify: `requirements.txt` (chromadb>=1.0, sentence-transformers>=3.0, langchain-text-splitters>=0.3), `.gitignore` (+`data/chroma/`), `.env.example` (+`PCB_KB_DIR`, `PCB_CHROMA_DIR`, `PCB_EMBED_MODEL`)
- Output (committed): `reports/rag_retrieval_smoke.md`; Output (gitignored): `data/chroma/`

**KB doc format** — YAML frontmatter + markdown body (~400–700 words), one `##` section per topic so the header-aware splitter yields coherent chunks:

```markdown
---
title: "Open circuit: rework and repair procedure"
defect_class: open_circuit        # one of the 6 classes, or "general"
doc_type: rework                  # overview | acceptability | rework
---
## Repair feasibility
...
```

**KB doc list (3 per class: overview-and-causes, acceptability, rework; + 3 general):** `missing_hole_{overview,acceptability,rework}.md`, `mouse_bite_{...}.md`, `open_circuit_{...}.md`, `short_{...}.md`, `spur_{...}.md`, `spurious_copper_{...}.md`, `general_inspection_criteria.md`, `general_rework_practices.md`, `general_bareboard_process_defects.md`.

**Interfaces (produces — Tasks 2–4 depend on these exact signatures):**
- `pcb_vision.rag.ingest.CLASSES: tuple[str, ...]` (6 canonical) and `GENERAL = "general"`
- `load_kb_docs(kb_dir: Path) -> list[dict]` — `{"doc_id": <filename stem>, "title": str, "defect_class": str, "doc_type": str, "text": str}`; `ValueError` on missing/invalid frontmatter or unknown `defect_class`/`doc_type`
- `chunk_docs(docs: list[dict], chunk_size: int = 800, chunk_overlap: int = 120) -> list[dict]` — `{"chunk_id": f"{doc_id}::{i:03d}", "text": str, "metadata": {doc_id, title, defect_class, doc_type, section}}`; header-aware (MarkdownHeaderTextSplitter on `##`) then RecursiveCharacterTextSplitter for oversize sections; every chunk carries full metadata
- `build_index(kb_dir: Path, persist_dir: Path, collection_name: str = "pcb_kb", embedding_fn=None) -> dict` — drops + recreates collection (idempotent rebuild), returns stats `{"n_docs", "n_chunks", "per_class": {...}}`; `embedding_fn=None` → SentenceTransformer(`PCB_EMBED_MODEL`); CLI: `python -m pcb_vision.rag.ingest [--kb-dir ... --persist-dir ...]`
- `pcb_vision.rag.retrieve.Retriever(persist_dir: Path, collection_name: str = "pcb_kb", embedding_fn=None)` with `.retrieve(query: str, defect_class: str | None = None, top_k: int = 4) -> list[dict]` — `{"chunk_id", "text", "score" (1 − cosine distance), "doc_id", "title", "defect_class", "doc_type", "section"}`; when `defect_class` given, Chroma `where={"defect_class": {"$in": [defect_class, "general"]}}`

**Steps:**

- [x] Add the 3 new deps to `requirements.txt`; `pip install` into `.venv`; verify `import chromadb, sentence_transformers, langchain_text_splitters`
- [x] TDD (mechanics tested with a deterministic stub embedding function — real model is exercised in the smoke step, mirroring Phase 1's mock-YOLO-then-verify-live pattern). Write failing tests in `tests/test_rag.py`: frontmatter parsing (incl. invalid-class rejection), chunk metadata propagation + oversize-section splitting, build→retrieve round trip in `tmp_path`, class filter returns only `{class, general}` chunks, rebuild idempotency (same chunk count, no dupes)
- [x] Run tests → verify they fail (module not found)
- [x] Implement `rag/ingest.py`, run tests
- [x] Implement `rag/retrieve.py`, run tests → all green
- [x] Author the 21 KB docs + `SOURCES.md` (self-authored, IPC-style-not-IPC-text; each doc's `##` sections align with the questions the advisor must answer: what/causes, when acceptable/reject, how to rework)
- [x] `python -m pcb_vision.rag.ingest` → real index at `data/chroma/` with real MiniLM embeddings; record stats
- [x] `python scripts/rag_smoke.py` — for each of the 6 classes run 2 canned queries ("How do I repair …", "When is … acceptable?"), assert top-1 chunk's class ∈ {class, general}, write results table → `reports/rag_retrieval_smoke.md`
- [x] `.gitignore` + `.env.example` updates; full suite (`pytest`) → 20 old + new all green
- [x] Update Status log below; commit (plain style)

### Task 2: RAG chain — provider layer + grounded generation with citations

**Files:** Create `src/pcb_vision/rag/providers.py`, `src/pcb_vision/rag/generate.py`; Test `tests/test_rag_generate.py`; Modify `requirements.txt` (+`google-genai`), `.env.example` (+`PCB_RAG_PROVIDER`, `GEMINI_API_KEY`, `PCB_RAG_MODEL`)

**Interfaces:**
- Consumes: `Retriever.retrieve()` from Task 1
- Produces: `LLMProvider` protocol — `complete(system: str, user: str) -> str`; `AnthropicProvider`, `GeminiProvider`, `provider_from_env() -> LLMProvider | None` (`None` → extractive mode); `recommend(defect_class: str, retriever: Retriever, provider: LLMProvider | None, question: str | None = None, top_k: int = 4) -> dict` → `{"answer": str, "citations": [{"chunk_id","doc_id","title","section"}], "mode": "generative"|"extractive", "model": str|None}`
- Prompt contract: answer ONLY from the numbered context chunks, cite as [1]…[k], say "not covered by the knowledge base" when context is insufficient (this is what RAGAS faithfulness measures in Task 3). Tests mock providers; live verification with whichever key exists (Gemini expected).

### Task 3: RAGAS evaluation + retrieval tuning

**Files:** Create `eval/rag_testset.jsonl` (~30 hand-written {question, defect_class, ground_truth} covering all 6 classes + acceptability + rework), `src/pcb_vision/rag/evaluate.py`; Output (committed): `reports/rag_evaluation.md`

**Interfaces:** Consumes `recommend()`; runs RAGAS faithfulness, answer relevancy, context precision with Gemini as judge LLM + local embeddings; grid over chunk_size {500, 800, 1200} × top_k {3, 4, 6} (rerank pass optional if scores are weak); writes metric table + chosen config to `reports/rag_evaluation.md` and bakes winners into defaults. Add `ragas` to requirements. Faithfulness is the README headline number.

### Task 4: Integration — `/recommend` endpoint, Streamlit Repair Advisor tab, Docker

**Files:** Modify `src/pcb_vision/api.py` (add `POST /recommend`: body = detection output `{"detections":[{class_name,confidence,box_xyxy}]}` → per-unique-class recommendation cards), `app/streamlit_app.py` ("Repair Advisor" tab: per-defect recommendation cards with visible citations; read `frontend-design` skill first — keep PCB-material theme), `Dockerfile` (run ingest at build so the image ships with the index), `docker-compose.yml`, `tests/test_api.py` (+`/recommend` tests, provider mocked)

**Interfaces:** `POST /recommend` → `{"recommendations": [{"defect_class", "answer", "citations": [...], "mode"}], "kb_stats": {...}}`; degrades to `mode: "extractive"` with no key — same philosophy as Phase 1's `report_error`. Verify: full suite, live uvicorn, `docker compose up` end-to-end (detect → recommend with citations). HF Spaces deploy only if Viraj wants it (Phase 1 shipped as Docker + GitHub; decide in-session).

### Task 5: Polish — README, architecture diagram, resume bullets

**Files:** Modify `README.md` (Mermaid diagram gains detection → retrieval → recommendation flow; RAGAS metrics table; KB sources & licensing section; updated quickstart incl. `rag.ingest`), `docs/resume_bullets.md` (add RAG bullets: vector DB, hybrid retrieval, RAGAS numbers, provider-agnostic LLM layer)

**Verify:** fresh-clone quickstart still works end-to-end; push; confirm GitHub rendering. Tag release v1.1.0 if weights/index distribution changes warrant it.

## Status log

- 2026-07-06: Plan written (Phase 2 spec from Viraj, 2026-07-06; no-Anthropic-key constraint baked into Global Constraints). Task 1 starting this session.
- 2026-07-06: **Task 1 COMPLETE.** Deps installed (chromadb 1.5.9, sentence-transformers 5.6.0, langchain-text-splitters 1.1.2). `rag/ingest.py` + `rag/retrieve.py` built TDD (9 new tests, stub word-hash embeddings for mechanics; chroma cosine space via `configuration` param — verified both API forms work on 1.5.9). 21 KB docs + `SOURCES.md` authored (licensing approach documented). Real ingest: **21 docs → 104 chunks** (14–17 per class) at `data/chroma/`, MiniLM downloaded and cached. Smoke test **12/12 passed** (`reports/rag_retrieval_smoke.md`): top-1 in correct class for all queries; 10/12 also hit the ideal doc_type — mouse_bite queries top out on its overview chunk and "repair a short" hits general_rework_practices first (both still in-class; candidates for Task 3 tuning). Full suite **29/29** (Phase 1's 20 untouched). `.gitignore` (+`data/chroma/`), `.env.example` (+3 RAG vars). Next: Task 2 (provider layer + grounded generation with citations; needs a Gemini free-tier key from AI Studio for live verification — code paths mockable without it).
