"""Hybrid retrieval over the KB index: defect-class metadata filter + semantic top-k.

The class filter narrows to chunks about the detected defect (plus `general`
cross-cutting docs); semantic ranking picks the best passages within that.
"""

from __future__ import annotations

from pathlib import Path

import chromadb

from pcb_vision.rag.ingest import CLASSES, COLLECTION, GENERAL, default_embedding_fn


class Retriever:
    def __init__(
        self,
        persist_dir: Path,
        collection_name: str = COLLECTION,
        embedding_fn=None,
    ):
        if embedding_fn is None:
            embedding_fn = default_embedding_fn()
        client = chromadb.PersistentClient(path=str(persist_dir))
        self._collection = client.get_collection(collection_name, embedding_function=embedding_fn)

    def count(self) -> int:
        return self._collection.count()

    def retrieve(self, query: str, defect_class: str | None = None, top_k: int = 4) -> list[dict]:
        """Top-k chunks for a query, optionally filtered to one defect class
        (+ general docs). Results sorted by score (1 - cosine distance) desc."""
        where = None
        if defect_class is not None:
            if defect_class not in CLASSES:
                raise ValueError(f"unknown defect_class {defect_class!r}")
            where = {"defect_class": {"$in": [defect_class, GENERAL]}}

        res = self._collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        return [
            {"chunk_id": chunk_id, "text": text, "score": 1.0 - distance, **metadata}
            for chunk_id, text, metadata, distance in zip(
                res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]
            )
        ]
