"""Vector store helpers for indexing brand knowledge."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

try:  # pragma: no cover - optional dependency
    import faiss  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    faiss = None

from ..models.embeddings import SimpleEmbeddingModel

logger = logging.getLogger(__name__)


@dataclass
class ChunkRecord:
    """Represents a chunk stored in the vector index."""

    chunk_id: str
    text: str
    metadata: dict


class VectorStore:
    """Indexes chunks using embeddings for retrieval."""

    def __init__(
        self,
        *,
        storage_dir: Path | str = Path("data/vector_store"),
        embedding_model: Optional[SimpleEmbeddingModel] = None,
    ) -> None:
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._embedding_model = embedding_model or SimpleEmbeddingModel()

    def refresh_brand(self, brand: str, chunks: Sequence[ChunkRecord]) -> Path:
        """Replace the index for ``brand`` with the provided chunks."""

        logger.info("Refreshing vector index for brand %s with %s chunks", brand, len(chunks))
        embeddings = self._embedding_model.embed_documents([chunk.text for chunk in chunks])
        index_payload = [
            {
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "metadata": chunk.metadata,
                "embedding": vector,
            }
            for chunk, vector in zip(chunks, embeddings)
        ]
        path = self._storage_dir / f"{brand}.json"
        path.write_text(json.dumps(index_payload, ensure_ascii=False))
        return path

    def refresh_from_raw(self, brand: str, raw_dir: Path | str = Path("data/raw")) -> Path:
        """Load normalized JSON chunks for a brand and update the index."""

        brand_dir = Path(raw_dir) / brand
        if not brand_dir.exists():
            raise FileNotFoundError(f"No raw data found for brand {brand} at {brand_dir}")

        chunks: List[ChunkRecord] = []
        for json_file in brand_dir.glob("*.json"):
            try:
                payload = json.loads(json_file.read_text())
            except json.JSONDecodeError:  # pragma: no cover - defensive
                logger.exception("Failed to parse %s", json_file)
                continue
            for item in payload:
                chunks.append(
                    ChunkRecord(
                        chunk_id=item["id"],
                        text=item["text"],
                        metadata=item.get("metadata", {}),
                    )
                )
        return self.refresh_brand(brand, chunks)

    def search(self, brand: str, query: str, *, top_k: int = 5) -> List[ChunkRecord]:
        """Search the brand index for the most relevant chunks."""

        index_path = self._storage_dir / f"{brand}.json"
        if not index_path.exists():
            raise FileNotFoundError(f"No vector index found for brand {brand}")

        payload = json.loads(index_path.read_text())
        embeddings = [item["embedding"] for item in payload]
        records = [
            ChunkRecord(chunk_id=item["chunk_id"], text=item["text"], metadata=item["metadata"])
            for item in payload
        ]
        query_embedding = self._embedding_model.embed_query(query)
        scores = self._similarities(query_embedding, embeddings)
        ranked = sorted(zip(scores, records), key=lambda pair: pair[0], reverse=True)
        return [record for _, record in ranked[:top_k]]

    def _similarities(self, query: Sequence[float], vectors: Sequence[Sequence[float]]) -> List[float]:
        if faiss:
            return self._faiss_similarity(query, vectors)
        return [self._cosine_similarity(query, vector) for vector in vectors]

    def _faiss_similarity(
        self, query: Sequence[float], vectors: Sequence[Sequence[float]]
    ) -> List[float]:  # pragma: no cover - requires faiss
        dimension = len(query)
        index = faiss.IndexFlatIP(dimension)
        import numpy as np  # type: ignore

        matrix = np.array(vectors, dtype="float32")
        index.add(matrix)
        scores, _ = index.search(np.array([query], dtype="float32"), len(vectors))
        return scores[0].tolist()

    @staticmethod
    def _cosine_similarity(query: Sequence[float], vector: Sequence[float]) -> float:
        dot = sum(q * v for q, v in zip(query, vector))
        norm_query = sum(q * q for q in query) ** 0.5 or 1.0
        norm_vector = sum(v * v for v in vector) ** 0.5 or 1.0
        return dot / (norm_query * norm_vector)


__all__ = ["ChunkRecord", "VectorStore"]
