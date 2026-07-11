"""Task 3: two-stage RAG evaluation — local retrieval grid, then RAGAS.

Stage 1 (grid) is LLM-free: every (chunk_size, top_k) config is scored with
hit-rate@k and MRR against each test case's annotated `relevant_doc_ids`.
Stage 2 runs RAGAS (faithfulness, answer relevancy, context precision) with a
Gemini judge, but only on the grid winner + the shipped default — the full
9-config RAGAS grid would cost ~1,000 judge calls, past the free-tier quota.

CLI:
    python -m pcb_vision.rag.evaluate --stage grid|ragas|all
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import date
from pathlib import Path

from pcb_vision.rag.generate import recommend
from pcb_vision.rag.ingest import CLASSES, build_index, default_embedding_fn
from pcb_vision.rag.retrieve import Retriever

TESTSET_PATH = Path("eval/rag_testset.jsonl")
REPORT_PATH = Path("reports/rag_evaluation.md")
CHUNK_SIZES = (500, 800, 1200)
TOP_KS = (3, 4, 6)
BASELINE = {"chunk_size": 800, "top_k": 4}  # shipped Task 1 defaults

_REQUIRED = ("id", "question", "defect_class", "ground_truth", "relevant_doc_ids")


def load_testset(path: Path) -> list[dict]:
    """Parse and validate the JSONL testset; ValueError names the bad field."""
    cases = []
    for lineno, line in enumerate(Path(path).read_text().splitlines(), start=1):
        if not line.strip():
            continue
        case = json.loads(line)
        for field in _REQUIRED:
            value = case.get(field)
            ok = bool(value) and (isinstance(value, list) or str(value).strip())
            if not ok:
                raise ValueError(f"line {lineno}: missing/empty field {field!r}")
        if case["defect_class"] not in CLASSES:
            raise ValueError(
                f"line {lineno}: unknown defect_class {case['defect_class']!r}")
        cases.append(case)
    return cases


def retrieval_metrics(retriever, cases: list[dict], top_k: int) -> dict:
    """Hit-rate@k and MRR over the testset. Rank = 1-indexed position of the
    first retrieved chunk whose doc_id is in the case's relevant_doc_ids."""
    hits = 0
    rr_sum = 0.0
    for case in cases:
        results = retriever.retrieve(
            case["question"], defect_class=case["defect_class"], top_k=top_k)
        relevant = set(case["relevant_doc_ids"])
        for rank, r in enumerate(results, start=1):
            if r["doc_id"] in relevant:
                hits += 1
                rr_sum += 1.0 / rank
                break
    n = len(cases)
    return {"hit_rate": hits / n, "mrr": rr_sum / n, "n": n}


def run_grid(
    kb_dir: Path,
    cases: list[dict],
    chunk_sizes=CHUNK_SIZES,
    top_ks=TOP_KS,
    work_dir: Path = Path("data/eval_indexes"),
    embedding_fn=None,
) -> list[dict]:
    """Build one index per chunk_size under work_dir, score every top_k on it.
    Indexes are left in place so Stage 2 can reuse the winner's."""
    if embedding_fn is None:
        embedding_fn = default_embedding_fn()
    rows = []
    for chunk_size in chunk_sizes:
        persist = Path(work_dir) / f"chroma_{chunk_size}"
        stats = build_index(
            kb_dir, persist, embedding_fn=embedding_fn, chunk_size=chunk_size)
        retriever = Retriever(persist, embedding_fn=embedding_fn)
        for top_k in top_ks:
            m = retrieval_metrics(retriever, cases, top_k=top_k)
            rows.append({
                "chunk_size": chunk_size, "top_k": top_k,
                "n_chunks": stats["n_chunks"],
                "hit_rate": m["hit_rate"], "mrr": m["mrr"],
            })
    return rows


def choose_config(rows: list[dict]) -> dict:
    """Best hit_rate, then best MRR, then the *smaller* top_k: hit-rate@k is
    monotone in k, so on a tie the tighter context wins (less noise for the
    generator, fewer judge tokens)."""
    return max(rows, key=lambda r: (r["hit_rate"], r["mrr"], -r["top_k"]))


def build_ragas_samples(cases, retriever, provider, top_k: int = 4) -> list[dict]:
    """One RAGAS sample per case, generated through the production recommend()
    path. Keys follow ragas SingleTurnSample field names exactly."""
    samples = []
    for case in cases:
        hits = retriever.retrieve(
            case["question"], defect_class=case["defect_class"], top_k=top_k)
        result = recommend(
            case["defect_class"], retriever, provider,
            question=case["question"], top_k=top_k)
        samples.append({
            "user_input": case["question"],
            "retrieved_contexts": [h["text"] for h in hits],
            "response": result["answer"],
            "reference": case["ground_truth"],
        })
    return samples


class ThrottledProvider:
    """LLMProvider decorator for the live run: paces calls to stay under the
    free-tier RPM cap and retries rate-limit errors with linear backoff, so a
    429 mid-testset doesn't kill the whole evaluation."""

    def __init__(self, inner, min_interval: float = 7.0,
                 max_retries: int = 6, base_wait: float = 20.0):
        self._inner = inner
        self._min_interval = min_interval
        self._max_retries = max_retries
        self._base_wait = base_wait
        self._last_call = 0.0

    @property
    def model(self) -> str:
        return self._inner.model

    def complete(self, system: str, user: str) -> str:
        import time

        for attempt in range(self._max_retries + 1):
            wait = self._min_interval - (time.monotonic() - self._last_call)
            if wait > 0:
                time.sleep(wait)
            try:
                self._last_call = time.monotonic()
                return self._inner.complete(system, user)
            except Exception as exc:  # noqa: BLE001 — provider SDKs differ
                retryable = "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc)
                if not retryable or attempt == self._max_retries:
                    raise
                time.sleep(self._base_wait * (attempt + 1))
        raise AssertionError("unreachable")


class _LocalMiniLM:
    """Minimal langchain-style Embeddings adapter over our local
    sentence-transformers model, so answer relevancy stays free/offline."""

    def __init__(self):
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(
            os.environ.get("PCB_EMBED_MODEL", "all-MiniLM-L6-v2"))

    def embed_documents(self, texts):
        return self._model.encode(list(texts)).tolist()

    def embed_query(self, text):
        return self._model.encode([text])[0].tolist()


def ragas_eval(
    samples: list[dict],
    judge_model: str | None = None,
    which: tuple[str, ...] = ("faithfulness", "answer_relevancy",
                              "context_precision"),
) -> dict:
    """Score samples with RAGAS using a Gemini judge (serial, retry-heavy to
    survive free-tier 429s) + local embeddings. `which` selects metrics so an
    interrupted run can be resumed per-metric without re-spending judge quota.
    Imports are lazy: ragas pulls the whole langchain/datasets stack, which
    pytest never needs."""
    from langchain_core.embeddings import Embeddings as LCEmbeddings  # noqa: F401
    from langchain_google_genai import ChatGoogleGenerativeAI
    from ragas import EvaluationDataset, evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import (
        Faithfulness,
        LLMContextPrecisionWithReference,
        ResponseRelevancy,
    )
    from ragas.run_config import RunConfig

    judge_model = judge_model or os.environ.get(
        "PCB_RAGAS_JUDGE", "gemini-flash-lite-latest")
    judge = LangchainLLMWrapper(ChatGoogleGenerativeAI(
        model=judge_model, temperature=0,
        google_api_key=os.environ["GEMINI_API_KEY"]))
    embeddings = LangchainEmbeddingsWrapper(_LocalMiniLM())

    available = {
        "faithfulness": lambda: Faithfulness(llm=judge),
        # strictness=1: the default (3) asks Gemini for multiple candidates per
        # call, which the free-tier lite models reject with a 400
        "answer_relevancy": lambda: ResponseRelevancy(
            llm=judge, embeddings=embeddings, strictness=1),
        "context_precision": lambda: LLMContextPrecisionWithReference(llm=judge),
    }
    metrics = [available[name]() for name in which]
    dataset = EvaluationDataset.from_list(samples)
    run_config = RunConfig(max_workers=1, timeout=180, max_retries=10, max_wait=90)
    result = evaluate(dataset=dataset, metrics=metrics, run_config=run_config)

    df = result.to_pandas()
    out = {"n": len(samples)}
    for col in df.columns:
        low = col.lower()
        if "faithfulness" in low:
            out["faithfulness"] = float(df[col].mean())
        elif "relevancy" in low:
            out["answer_relevancy"] = float(df[col].mean())
        elif "context_precision" in low:
            out["context_precision"] = float(df[col].mean())
    return out


def write_report(path: Path, grid_rows: list[dict], chosen: dict,
                 ragas_rows: list[dict]) -> None:
    lines = [
        "# RAG Evaluation — Phase 2 Task 3",
        "",
        f"_Generated {date.today().isoformat()} by `python -m pcb_vision.rag.evaluate`._",
        "",
        "Two-stage evaluation: the chunk_size × top_k grid is tuned with local,",
        "LLM-free retrieval metrics (hit-rate@k / MRR against hand-annotated",
        "`relevant_doc_ids`); RAGAS with a Gemini judge then scores the winning",
        "config against the shipped default. A full RAGAS grid (~1,000 judge",
        "calls) does not fit the Gemini free-tier quota.",
        "",
        "## Stage 1 — Retrieval grid (local, LLM-free)",
        "",
        "| chunk_size | top_k | n_chunks | hit_rate@k | MRR |",
        "|---:|---:|---:|---:|---:|",
    ]
    for r in grid_rows:
        marker = " ◀" if r is chosen else ""
        lines.append(
            f"| {r['chunk_size']} | {r['top_k']} | {r['n_chunks']} "
            f"| {r['hit_rate']:.2f} | {r['mrr']:.2f} |{marker}")
    lines += [
        "",
        f"**Chosen config:** chunk_size={chosen['chunk_size']}, "
        f"top_k={chosen['top_k']} "
        "(best hit_rate, ties broken by MRR, then smaller top_k — hit-rate@k is "
        "monotone in k, so the tighter context wins a tie).",
        "",
        "## Stage 2 — RAGAS (Gemini judge, local embeddings)",
        "",
    ]
    if ragas_rows:
        lines += [
            "| config | n | faithfulness | answer_relevancy | context_precision |",
            "|---|---:|---:|---:|---:|",
        ]
        for r in ragas_rows:
            lines.append(
                f"| {r['config']} | {r['n']} | {r['faithfulness']:.2f} "
                f"| {r['answer_relevancy']:.2f} | {r['context_precision']:.2f} |")
    else:
        lines.append("_Not yet run (`--stage ragas`)._")
    lines.append("")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines))


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("grid", "ragas", "all"), default="all")
    parser.add_argument("--testset", type=Path, default=TESTSET_PATH)
    parser.add_argument("--kb-dir", type=Path,
                        default=Path(os.environ.get("PCB_KB_DIR", "knowledge_base")))
    parser.add_argument("--work-dir", type=Path, default=Path("data/eval_indexes"))
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    parser.add_argument("--max-cases", type=int, default=None,
                        help="cap RAGAS cases (quota safety valve)")
    args = parser.parse_args()

    cases = load_testset(args.testset)
    print(f"testset: {len(cases)} cases")

    grid_rows = run_grid(args.kb_dir, cases, work_dir=args.work_dir)
    chosen = choose_config(grid_rows)
    for r in grid_rows:
        mark = " <-- chosen" if r is chosen else ""
        print(f"  chunk_size={r['chunk_size']:>4} top_k={r['top_k']} "
              f"hit_rate={r['hit_rate']:.2f} mrr={r['mrr']:.2f}{mark}")

    ragas_rows: list[dict] = []
    if args.stage in ("ragas", "all"):
        from pcb_vision.rag.providers import provider_from_env

        provider = provider_from_env()
        if provider is None:
            raise SystemExit("RAGAS stage needs a generation provider "
                             "(set PCB_RAG_PROVIDER / GEMINI_API_KEY)")
        provider = ThrottledProvider(provider)  # free-tier RPM pacing
        ragas_cases = cases[: args.max_cases] if args.max_cases else cases
        configs = [dict(chosen, label="winner")]
        if (chosen["chunk_size"], chosen["top_k"]) != (
                BASELINE["chunk_size"], BASELINE["top_k"]):
            base_row = next(r for r in grid_rows
                            if (r["chunk_size"], r["top_k"])
                            == (BASELINE["chunk_size"], BASELINE["top_k"]))
            configs.append(dict(base_row, label="baseline"))
        embedding_fn = default_embedding_fn()
        for cfg in configs:
            persist = args.work_dir / f"chroma_{cfg['chunk_size']}"
            retriever = Retriever(persist, embedding_fn=embedding_fn)
            print(f"RAGAS [{cfg['label']}] chunk_size={cfg['chunk_size']} "
                  f"top_k={cfg['top_k']} on {len(ragas_cases)} cases ...")
            samples_path = args.report.parent / f"rag_samples_{cfg['label']}.jsonl"
            try:
                if samples_path.exists():  # resume: reuse pre-quota-death gens
                    samples = [json.loads(l) for l in
                               samples_path.read_text().splitlines() if l.strip()]
                    print(f"  reusing {len(samples)} samples from {samples_path}")
                else:
                    samples = build_ragas_samples(
                        ragas_cases, retriever, provider, top_k=cfg["top_k"])
                    samples_path.write_text(
                        "\n".join(json.dumps(s) for s in samples) + "\n")
                scores = ragas_eval(samples)
            except Exception as exc:  # quota death: keep what we have
                print(f"  !! {cfg['label']} failed: {exc}")
                break
            scores["config"] = (f"{cfg['label']} (chunk_size={cfg['chunk_size']}, "
                                f"top_k={cfg['top_k']})")
            print(f"  -> {scores}")
            ragas_rows.append(scores)
            # checkpoint after every config — a later quota failure loses nothing
            write_report(args.report, grid_rows, chosen, ragas_rows)

    write_report(args.report, grid_rows, chosen, ragas_rows)
    print(f"report written: {args.report}")


if __name__ == "__main__":
    main()
