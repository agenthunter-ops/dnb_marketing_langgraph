#!/usr/bin/env bash
set -euo pipefail

PYTHON_VERSION="${PYTHON_VERSION:-3.10}"
VENV_DIR="${VENV_DIR:-.venv}"

if ! command -v python${PYTHON_VERSION} >/dev/null 2>&1; then
  echo "Python ${PYTHON_VERSION} is required but not installed." >&2
  exit 1
fi

python${PYTHON_VERSION} -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

python -m pip install --upgrade pip
python -m pip install '.[test,typecheck,lint]'

echo "Virtual environment ready in ${VENV_DIR}. Activate it with 'source ${VENV_DIR}/bin/activate'."


