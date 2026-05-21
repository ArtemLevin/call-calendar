#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"
PIP_INDEX_URL="${PIP_INDEX_URL:-}"
PIP_EXTRA_INDEX_URL="${PIP_EXTRA_INDEX_URL:-}"

if [[ -z "${PIP_INDEX_URL}" ]]; then
  echo "ERROR: PIP_INDEX_URL is not set."
  echo "Example: PIP_INDEX_URL=https://pypi.my-company.local/simple"
  exit 2
fi

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

python -m pip install --upgrade pip setuptools wheel

PIP_ARGS=("--index-url" "${PIP_INDEX_URL}")
if [[ -n "${PIP_EXTRA_INDEX_URL}" ]]; then
  PIP_ARGS+=("--extra-index-url" "${PIP_EXTRA_INDEX_URL}")
fi

python -m pip install "${PIP_ARGS[@]}" -r requirements.txt -r requirements-dev.txt
python -m pip check

echo "Dependencies installed successfully via mirror: ${PIP_INDEX_URL}"
