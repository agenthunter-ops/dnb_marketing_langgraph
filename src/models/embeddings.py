"""Lightweight embedding utilities for indexing brand knowledge."""
from __future__ import annotations

import hashlib
import math
from typing import Iterable, List, Sequence


class SimpleEmbeddingModel:
    """Deterministic embedding model based on hashing.

    The implementation avoids external ML dependencies while still producing
    dense vectors that can be used with vector search backends.
    """

    def __init__(self, dimension: int = 384) -> None:
        if dimension <= 0:
            raise ValueError("Embedding dimension must be positive")
        self.dimension = dimension

    def embed(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

    def embed_documents(self, texts: Sequence[str]) -> List[List[float]]:
        embeddings: List[List[float]] = []
        for text in texts:
            normalized = text.strip().lower()
            digest = hashlib.sha256(normalized.encode("utf-8")).digest()
            buffer = bytearray(digest)
            # Expand the buffer deterministically until there are enough bytes.
            while len(buffer) < self.dimension * 4:
                digest = hashlib.sha256(buffer).digest()
                buffer.extend(digest)

            vector: List[float] = []
            for idx in range(self.dimension):
                start = idx * 4
                chunk = buffer[start : start + 4]
                value = int.from_bytes(chunk, "big")
                # Map the integer into the range [-1, 1].
                vector.append((value / 0xFFFFFFFF) * 2 - 1)
            embeddings.append(self._l2_normalize(vector))
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        return self.embed(text)

    @staticmethod
    def _l2_normalize(vector: Iterable[float]) -> List[float]:
        values = list(vector)
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]


__all__ = ["SimpleEmbeddingModel"]
