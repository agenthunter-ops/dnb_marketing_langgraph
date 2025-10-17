.PHONY: install install-dev lint typecheck test format run-fastapi run-streamlit

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

install:
	$(PIP) install .

install-dev:
	$(PIP) install .[test,typecheck,lint]

lint:
	ruff check src

format:
	ruff format src

typecheck:
	mypy src

test:
	pytest

run-fastapi:
	uvicorn app.main:app --host $${FASTAPI_HOST:-0.0.0.0} --port $${FASTAPI_PORT:-8000}

run-streamlit:
	streamlit run app/streamlit_app.py --server.port=$${STREAMLIT_PORT:-8501}

