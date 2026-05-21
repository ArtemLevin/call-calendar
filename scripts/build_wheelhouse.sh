#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
WHEELHOUSE_DIR="${WHEELHOUSE_DIR:-wheelhouse}"
PIP_INDEX_URL="${PIP_INDEX_URL:-}"
PIP_EXTRA_INDEX_URL="${PIP_EXTRA_INDEX_URL:-}"

mkdir -p "${WHEELHOUSE_DIR}"

PIP_ARGS=()
if [[ -n "${PIP_INDEX_URL}" ]]; then
  PIP_ARGS+=("--index-url" "${PIP_INDEX_URL}")
fi
if [[ -n "${PIP_EXTRA_INDEX_URL}" ]]; then
  PIP_ARGS+=("--extra-index-url" "${PIP_EXTRA_INDEX_URL}")
fi

"${PYTHON_BIN}" -m pip download "${PIP_ARGS[@]}" -r requirements.txt -r requirements-dev.txt -d "${WHEELHOUSE_DIR}"

echo "Wheelhouse prepared at: ${WHEELHOUSE_DIR}"
