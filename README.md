# DNB Marketing LangGraph

## Prerequisites

- Python 3.10+
- A virtual environment tool such as `python -m venv`

## Setting up the development environment

```bash
# Clone the repository
git clone <repo-url>
cd dnb_marketing_langgraph

# Create and activate a virtual environment
python3.10 -m venv .venv
source .venv/bin/activate

# Install dependencies
make install-dev
# or use the helper script
./scripts/setup_env.sh
```

## Configuration

Environment variables can be used to adjust runtime behaviour. Key variables include:

- `APP_ENV`: current environment name (defaults to `development`).
- `APP_DEBUG`: enable verbose logging when set to `1`, `true`, `yes`, or `on`.
- `FASTAPI_HOST` / `FASTAPI_PORT`: network interface and port for the FastAPI app.
- `STREAMLIT_PORT`: port for the Streamlit app.
- `AZURE_STORAGE_ACCOUNT_URL` and `AZURE_BLOB_CONTAINER`: Azure Storage configuration.

## Running the applications

### FastAPI

```bash
make run-fastapi
```

The command expects an ASGI application at `app.main:app`. Adjust the target module in the `Makefile` once your API is implemented.

### Streamlit

```bash
make run-streamlit
```

This command starts Streamlit with `app/streamlit_app.py`. Update the path when your Streamlit entry point is available.

## Quality checks

Run the standard tooling from the project root:

```bash
make lint       # Ruff linting
make format     # Ruff formatting
make typecheck  # Mypy static type checks
make test       # Pytest test suite
```

