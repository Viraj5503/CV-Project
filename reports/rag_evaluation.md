# RAG Evaluation — Phase 2 Task 3

_Generated 2026-07-11 by `python -m pcb_vision.rag.evaluate`._

Two-stage evaluation: the chunk_size × top_k grid is tuned with local,
LLM-free retrieval metrics (hit-rate@k / MRR against hand-annotated
`relevant_doc_ids`); RAGAS with a Gemini judge then scores the winning
config against the shipped default. A full RAGAS grid (~1,000 judge
calls) does not fit the Gemini free-tier quota.

## Stage 1 — Retrieval grid (local, LLM-free)

| chunk_size | top_k | n_chunks | hit_rate@k | MRR |
|---:|---:|---:|---:|---:|
| 500 | 3 | 160 | 0.97 | 0.89 |
| 500 | 4 | 160 | 1.00 | 0.90 |
| 500 | 6 | 160 | 1.00 | 0.90 |
| 800 | 3 | 104 | 1.00 | 0.96 |
| 800 | 4 | 104 | 1.00 | 0.96 |
| 800 | 6 | 104 | 1.00 | 0.96 |
| 1200 | 3 | 89 | 1.00 | 0.98 | ◀
| 1200 | 4 | 89 | 1.00 | 0.98 |
| 1200 | 6 | 89 | 1.00 | 0.98 |

**Chosen config:** chunk_size=1200, top_k=3 (best hit_rate, ties broken by MRR, then smaller top_k — hit-rate@k is monotone in k, so the tighter context wins a tie).

## Stage 2 — RAGAS (Gemini judge, local embeddings)

| config | n | faithfulness | answer_relevancy | context_precision |
|---|---:|---:|---:|---:|
| winner (chunk_size=1200, top_k=3) | 30 | 0.97 | 0.81 | 0.79 |
| baseline (chunk_size=800, top_k=4) | 30 | 0.98 | 0.83 | 0.76 |

## Conclusion — shipped config stays chunk_size=800, top_k=4

Stage 1's retrieval-only winner (1200×3, MRR 0.98 vs 0.96) does not carry
through to generation quality: at n=30 the RAGAS deltas (−0.02 faithfulness,
−0.02 relevancy, +0.03 context precision) are within noise, and the shipped
default edges it on the headline metric. Switching defaults would add churn
with no measurable end-to-end benefit, so the Task 1 defaults stand.
**Headline: faithfulness 0.98** on the production configuration.

## Provenance

- Generator (system under test): `GeminiProvider` default `gemini-flash-lite-latest`
  (→ gemini-3.1-flash-lite), the production default — eval and prod paths match.
- Judge: `gemini-flash-lite-latest`; `ResponseRelevancy(strictness=1)` because
  lite models reject multi-candidate requests. Embeddings: local all-MiniLM-L6-v2.
- Samples: `reports/rag_samples_{winner,baseline}.jsonl` (30 each, kept locally).
- Free-tier reality (probed live, 2026-07-11): flagship flash models
  (2.5-flash, 3.5-flash) are 20 requests/day; 2.0-line is 0; 2.5-flash-lite is
  retired (404). The lite line (15 RPM, RPD ≥ ~500 observed) is the only
  practical free backend — hence the rolling `gemini-flash-lite-latest` default.
