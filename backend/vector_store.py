"""ChromaDB vector store wrapper for LexAudit."""
from __future__ import annotations

import chromadb
from chromadb.config import Settings as ChromaSettings

from config import settings
from models import Chunk


class VectorStore:
    """Singleton ChromaDB wrapper — embed + store + query document chunks."""

    def __init__(self) -> None:
        self._client = chromadb.PersistentClient(
            path=settings.chroma_persist_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    # ── Write ──────────────────────────────────────────────────────────────────

    def add_chunks(self, chunks: list[Chunk]) -> None:
        """Embed and store chunks. Skips duplicates by chunk_id."""
        if not chunks:
            return

        existing_ids = set(
            self._collection.get(ids=[c.chunk_id for c in chunks])["ids"]
        )

        new_chunks = [c for c in chunks if c.chunk_id not in existing_ids]
        if not new_chunks:
            return

        self._collection.add(
            ids=[c.chunk_id for c in new_chunks],
            documents=[c.text for c in new_chunks],
            metadatas=[
                {
                    "doc_id": c.doc_id,
                    "chunk_index": c.chunk_index,
                    "page_number": c.page_number or -1,
                    "section_title": c.section_title or "",
                }
                for c in new_chunks
            ],
        )

    def delete_doc(self, doc_id: str) -> None:
        """Remove all chunks belonging to a document."""
        results = self._collection.get(where={"doc_id": doc_id})
        if results["ids"]:
            self._collection.delete(ids=results["ids"])

    # ── Query ──────────────────────────────────────────────────────────────────

    def query_chunks(
        self,
        query_text: str,
        doc_id: str,
        n_results: int = 5,
    ) -> list[tuple[Chunk, float]]:
        """
        Return top-n chunks for query_text within a specific document.
        Returns list of (Chunk, similarity_score) tuples sorted by score desc.
        """
        results = self._collection.query(
            query_texts=[query_text],
            n_results=min(n_results, self._collection.count()),
            where={"doc_id": doc_id},
            include=["documents", "metadatas", "distances"],
        )

        chunks_with_scores: list[tuple[Chunk, float]] = []
        ids = results["ids"][0] if results["ids"] else []
        docs = results["documents"][0] if results["documents"] else []
        metas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results["distances"] else []

        for chunk_id, text, meta, distance in zip(ids, docs, metas, distances):
            # ChromaDB cosine distance → similarity: 1 - distance
            similarity = max(0.0, 1.0 - float(distance))
            chunk = Chunk(
                chunk_id=chunk_id,
                doc_id=meta.get("doc_id", doc_id),
                text=text,
                page_number=meta.get("page_number") if meta.get("page_number", -1) != -1 else None,
                section_title=meta.get("section_title") or None,
                chunk_index=meta.get("chunk_index", 0),
            )
            chunks_with_scores.append((chunk, similarity))

        return sorted(chunks_with_scores, key=lambda x: x[1], reverse=True)

    def doc_exists(self, doc_id: str) -> bool:
        results = self._collection.get(where={"doc_id": doc_id}, limit=1)
        return len(results["ids"]) > 0

    def chunk_count(self) -> int:
        return self._collection.count()


# Module-level singleton
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
