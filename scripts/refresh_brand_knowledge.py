"""CLI utility to refresh brand knowledge assets and vector indexes."""
from __future__ import annotations

import argparse
import datetime as dt
import logging
import os
from typing import Iterable, List, Optional

from src.data.brand_center_client import BrandCenterClient
from src.data.ingest_brand_assets import BrandAssetIngestor
from src.retrieval.vector_store import VectorStore

logger = logging.getLogger(__name__)


def _parse_datetime(value: str) -> dt.datetime:
    normalized = value.strip().replace("Z", "+00:00")
    return dt.datetime.fromisoformat(normalized)


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--brand",
        dest="brands",
        action="append",
        required=True,
        help="Brand identifier to refresh. Repeat for multiple brands.",
    )
    parser.add_argument("--locale", help="Locale filter (e.g. en-GB)")
    parser.add_argument(
        "--since",
        help="Only ingest assets modified since the ISO timestamp (e.g. 2024-01-01T00:00:00Z)",
    )
    parser.add_argument(
        "--output-dir",
        default="data/raw",
        help="Directory to persist normalized chunks",
    )
    parser.add_argument(
        "--index-dir",
        default="data/vector_store",
        help="Directory to store the vector index",
    )
    parser.add_argument(
        "--log-level",
        default=os.environ.get("LOG_LEVEL", "INFO"),
        help="Logging level",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def build_client_from_env() -> BrandCenterClient:
    base_url = os.environ.get("BRAND_CENTER_BASE_URL")
    tenant_id = os.environ.get("BRAND_CENTER_TENANT_ID")
    client_id = os.environ.get("BRAND_CENTER_CLIENT_ID")
    client_secret = os.environ.get("BRAND_CENTER_CLIENT_SECRET")
    scope = os.environ.get("BRAND_CENTER_SCOPE")

    if not base_url:
        raise RuntimeError("BRAND_CENTER_BASE_URL environment variable must be set")

    return BrandCenterClient(
        base_url=base_url,
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
    )


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    modified_since = _parse_datetime(args.since) if args.since else None
    brands: List[str] = args.brands

    with build_client_from_env() as client:
        ingestor = BrandAssetIngestor(client, output_dir=args.output_dir)
        store = VectorStore(storage_dir=args.index_dir)

        for brand in brands:
            logger.info("Refreshing knowledge base for %s", brand)
            ingestor.ingest_brand(brand, locale=args.locale, modified_since=modified_since)
            store.refresh_from_raw(brand, raw_dir=args.output_dir)

    logger.info("Completed refresh for %s brand(s)", len(brands))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
