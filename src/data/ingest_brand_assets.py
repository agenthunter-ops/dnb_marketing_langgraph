"""Utilities to ingest and normalize Brand Centre assets."""
from __future__ import annotations

import datetime as dt
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .brand_center_client import BrandAsset, BrandCenterClient

logger = logging.getLogger(__name__)


@dataclass
class NormalizedChunk:
    """Represents a normalized text chunk ready for indexing."""

    chunk_id: str
    text: str
    metadata: Dict[str, object]


class BrandAssetIngestor:
    """Ingests assets from Brand Centre and persists normalized JSON chunks."""

    def __init__(
        self,
        client: BrandCenterClient,
        output_dir: Path | str = Path("data/raw"),
        *,
        chunk_size: int = 800,
        chunk_overlap: int = 120,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self._client = client
        self._output_dir = Path(output_dir)
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def ingest_brand(
        self,
        brand: str,
        *,
        locale: Optional[str] = None,
        modified_since: Optional[dt.datetime] = None,
    ) -> List[Path]:
        paths: List[Path] = []
        for asset in self._client.stream_assets(
            brand=brand,
            locale=locale,
            modified_since=modified_since,
        ):
            try:
                text = self._client.download_asset_text(asset)
            except Exception:  # pragma: no cover - network failure
                logger.exception("Failed to download asset %s", asset.asset_id)
                continue
            chunks = list(self._chunk_asset(asset, text))
            if not chunks:
                continue
            path = self._persist_chunks(brand, asset.asset_id, chunks)
            paths.append(path)
        if paths:
            logger.info("Ingested %s assets for %s", len(paths), brand)
        else:
            logger.warning("No assets ingested for %s", brand)
        return paths

    def _chunk_asset(self, asset: BrandAsset, text: str) -> Iterable[NormalizedChunk]:
        clean_text = text.strip()
        if not clean_text:
            logger.debug("Asset %s returned empty content", asset.asset_id)
            return []

        segments = self._split_text(clean_text)
        for index, segment in enumerate(segments):
            metadata = {
                "brand": asset.brand,
                "asset_id": asset.asset_id,
                "title": asset.title,
                "locale": asset.locale,
                "compliance_tags": asset.compliance_tags,
                "source_url": asset.content_url,
                "chunk_index": index,
                "chunk_count": len(segments),
                "updated_at": asset.updated_at.isoformat(),
            }
            metadata.update(asset.metadata)
            yield NormalizedChunk(
                chunk_id=f"{asset.asset_id}:{index}",
                text=segment,
                metadata=metadata,
            )

    def _split_text(self, text: str) -> List[str]:
        if len(text) <= self._chunk_size:
            return [text]
        chunks: List[str] = []
        start = 0
        while start < len(text):
            end = min(len(text), start + self._chunk_size)
            chunk = text[start:end]
            chunks.append(chunk)
            if end == len(text):
                break
            start = max(0, end - self._chunk_overlap)
        return chunks

    def _persist_chunks(self, brand: str, asset_id: str, chunks: List[NormalizedChunk]) -> Path:
        brand_dir = self._output_dir / brand
        brand_dir.mkdir(parents=True, exist_ok=True)
        path = brand_dir / f"{asset_id}.json"
        payload = [
            {
                "id": chunk.chunk_id,
                "text": chunk.text,
                "metadata": chunk.metadata,
            }
            for chunk in chunks
        ]
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        return path
