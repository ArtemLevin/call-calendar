#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"
WHEELHOUSE_DIR="${WHEELHOUSE_DIR:-wheelhouse}"

if [[ ! -d "${WHEELHOUSE_DIR}" ]]; then
  echo "ERROR: wheelhouse directory not found: ${WHEELHOUSE_DIR}"
  echo "Build it first: ./scripts/build_wheelhouse.sh"
  exit 2
fi

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

python -m pip install --no-index --find-links "${WHEELHOUSE_DIR}" -r requirements.txt -r requirements-dev.txt
python -m pip check

echo "Dependencies installed from local wheelhouse: ${WHEELHOUSE_DIR}"
