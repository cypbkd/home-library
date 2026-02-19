#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_PYTHON="${PROJECT_ROOT}/venv/bin/python"

if [[ ! -x "${VENV_PYTHON}" ]]; then
  echo "Error: ${VENV_PYTHON} not found."
  echo "Create the virtualenv and install dependencies first:"
  echo "  cd ${PROJECT_ROOT}"
  echo "  python3 -m venv venv"
  echo "  ./venv/bin/pip install -r requirements.txt"
  echo "  ./venv/bin/pip install pytest"
  exit 1
fi

cd "${PROJECT_ROOT}"

if [[ $# -eq 0 ]]; then
  exec "${VENV_PYTHON}" -m pytest -q tests
fi

exec "${VENV_PYTHON}" -m pytest -q "$@"
