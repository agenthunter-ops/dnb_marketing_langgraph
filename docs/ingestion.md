# Brand knowledge ingestion workflow

This document outlines the process for synchronising assets from Brand Centre, normalising
their contents, and keeping the retrieval index fresh for downstream experiences.

## Components

1. **Brand Centre client (`src/data/brand_center_client.py`)**
   * Handles Azure AD authentication (client secret or default credentials).
   * Provides helpers to enumerate assets and download their contents.
2. **Ingestion pipeline (`src/data/ingest_brand_assets.py`)**
   * Streams assets for a brand/locale combination.
   * Chunks textual content into JSON structures enriched with metadata such as locale and
     compliance tags.
   * Persists the resulting data under `data/raw/<brand>/`.
3. **Vector store (`src/retrieval/vector_store.py`)**
   * Generates deterministic embeddings for each chunk.
   * Stores the vectors and metadata per brand to support retrieval workflows.
4. **Refresh CLI (`scripts/refresh_brand_knowledge.py`)**
   * Command-line interface to orchestrate ingestion and indexing for selected brands.
   * Exposed via the `refresh-brand-knowledge` entry point (see `pyproject.toml`).

## Running a manual refresh

```bash
export BRAND_CENTER_BASE_URL="https://brand-centre.example.com"
export BRAND_CENTER_TENANT_ID="<tenant>"
export BRAND_CENTER_CLIENT_ID="<client-id>"
export BRAND_CENTER_CLIENT_SECRET="<client-secret>"
refresh-brand-knowledge --brand retail --brand wealth --locale en-GB
```

Optional flags:

* `--since`: ISO timestamp to limit ingestion to recently modified assets.
* `--output-dir`: Alternative destination for raw JSON chunks.
* `--index-dir`: Destination for the vector index.

## Scheduling considerations

* **Frequency**: Align refresh cadence with content publishing cycles. Daily refreshes are
  typical for marketing content, while critical compliance updates might warrant hourly runs.
* **Incremental updates**: Use the `--since` flag to limit ingestion to the delta since the
  last successful run. Persist the latest timestamp in your scheduler (e.g. Airflow XCom,
  Azure Data Factory variable) to support idempotent execution.
* **Concurrency**: The CLI processes brands sequentially to simplify rate limiting. Parallel
  execution is possible by spawning multiple processes for disjoint brand sets if the API
  allows higher throughput.

## Monitoring and alerting

* **Logging**: Standard logs go to stdout/stderr. Capture them via your scheduler and forward
  to the organisation-wide logging platform (e.g. Azure Monitor, Datadog).
* **Metrics**: Track counts of assets ingested, chunk counts, and index sizes per run. These
  can be exported by wrapping the CLI with a lightweight metrics collector.
* **Failure handling**: The ingestion pipeline logs exceptions per asset and continues with
  the remaining items. Configure alerting on non-zero exit codes from the CLI so failures are
  surfaced quickly.

## Storage layout

```
data/
  raw/
    <brand>/
      <asset-id>.json
  vector_store/
    <brand>.json
```

The raw JSON files contain arrays of chunks with text and metadata. Vector store artefacts
store the embedding alongside the chunk metadata for fast retrieval.
