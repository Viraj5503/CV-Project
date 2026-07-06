"""Knowledge-base ingestion: markdown docs -> chunks -> persistent ChromaDB index.

Each `knowledge_base/*.md` doc has YAML frontmatter (title, defect_class,
doc_type) and `##` sections. Chunking is header-aware so every chunk stays a
coherent statement about one topic, and carries the doc's metadata for
class-filtered retrieval.

Rebuild the index anytime with: python -m pcb_vision.rag.ingest
"""

from __future__ import annotations

import argparse
import os
from collections import Counter
from pathlib import Path

import chromadb
import yaml
from dotenv import load_dotenv
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

load_dotenv()  # PCB_KB_DIR / PCB_CHROMA_DIR / PCB_EMBED_MODEL from .env

CLASSES = (
    "missing_hole",
    "mouse_bite",
    "open_circuit",
    "short",
    "spur",
    "spurious_copper",
)
GENERAL = "general"
DOC_TYPES = ("overview", "acceptability", "rework")

KB_DIR = Path(os.environ.get("PCB_KB_DIR", "knowledge_base"))
CHROMA_DIR = Path(os.environ.get("PCB_CHROMA_DIR", "data/chroma"))
EMBED_MODEL = os.environ.get("PCB_EMBED_MODEL", "all-MiniLM-L6-v2")
COLLECTION = "pcb_kb"


def default_embedding_fn():
    """Local, free sentence-transformers embeddings (downloads model on first use)."""
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

    return SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)


def load_kb_docs(kb_dir: Path) -> list[dict]:
    """Parse every kb_dir/*.md into {doc_id, title, defect_class, doc_type, text}."""
    docs = []
    for path in sorted(Path(kb_dir).glob("*.md")):
        if path.name.upper() == "SOURCES.MD":
            continue  # provenance notes, not retrieval content
        raw = path.read_text(encoding="utf-8")
        if not raw.startswith("---"):
            raise ValueError(f"{path.name}: missing YAML frontmatter")
        try:
            _, frontmatter, body = raw.split("---", 2)
        except ValueError:
            raise ValueError(f"{path.name}: malformed YAML frontmatter") from None
        meta = yaml.safe_load(frontmatter) or {}
        missing = {"title", "defect_class", "doc_type"} - meta.keys()
        if missing:
            raise ValueError(f"{path.name}: frontmatter missing {sorted(missing)}")
        if meta["defect_class"] not in CLASSES + (GENERAL,):
            raise ValueError(f"{path.name}: unknown defect_class {meta['defect_class']!r}")
        if meta["doc_type"] not in DOC_TYPES:
            raise ValueError(f"{path.name}: unknown doc_type {meta['doc_type']!r}")
        docs.append(
            {
                "doc_id": path.stem,
                "title": str(meta["title"]),
                "defect_class": meta["defect_class"],
                "doc_type": meta["doc_type"],
                "text": body.strip(),
            }
        )
    return docs


def chunk_docs(docs: list[dict], chunk_size: int = 800, chunk_overlap: int = 120) -> list[dict]:
    """Header-aware chunking; every chunk carries full doc metadata + its section."""
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("##", "section")], strip_headers=True
    )
    size_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = []
    for doc in docs:
        i = 0
        for section_doc in header_splitter.split_text(doc["text"]):
            section = section_doc.metadata.get("section", "")
            for piece in size_splitter.split_text(section_doc.page_content):
                chunks.append(
                    {
                        "chunk_id": f"{doc['doc_id']}::{i:03d}",
                        "text": piece,
                        "metadata": {
                            "doc_id": doc["doc_id"],
                            "title": doc["title"],
                            "defect_class": doc["defect_class"],
                            "doc_type": doc["doc_type"],
                            "section": section,
                        },
                    }
                )
                i += 1
    return chunks


def build_index(
    kb_dir: Path,
    persist_dir: Path,
    collection_name: str = COLLECTION,
    embedding_fn=None,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> dict:
    """(Re)build the ChromaDB index from the knowledge base. Idempotent: drops
    and recreates the collection, so re-ingesting never duplicates chunks."""
    docs = load_kb_docs(kb_dir)
    chunks = chunk_docs(docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if embedding_fn is None:
        embedding_fn = default_embedding_fn()

    client = chromadb.PersistentClient(path=str(persist_dir))
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass  # first build: nothing to drop
    collection = client.create_collection(
        collection_name,
        configuration={"hnsw": {"space": "cosine"}},
        embedding_function=embedding_fn,
    )
    collection.add(
        ids=[c["chunk_id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )

    per_class = Counter(c["metadata"]["defect_class"] for c in chunks)
    return {"n_docs": len(docs), "n_chunks": len(chunks), "per_class": dict(per_class)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the PCB repair-advisor KB index")
    parser.add_argument("--kb-dir", type=Path, default=KB_DIR)
    parser.add_argument("--persist-dir", type=Path, default=CHROMA_DIR)
    args = parser.parse_args()

    stats = build_index(args.kb_dir, args.persist_dir)
    print(f"Indexed {stats['n_docs']} docs -> {stats['n_chunks']} chunks at {args.persist_dir}")
    for cls, n in sorted(stats["per_class"].items()):
        print(f"  {cls:18s} {n:3d} chunks")


if __name__ == "__main__":
    main()
