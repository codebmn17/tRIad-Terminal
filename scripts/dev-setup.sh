#!/usr/bin/env bash
set -euo pipefail

PY=${PY:-python3}
VENV=".venv"

if [ ! -d "$VENV" ]; then
  echo "[+] Creating virtual environment in $VENV"
  $PY -m venv "$VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"

python -m pip install --upgrade pip
pip install ruff black pre-commit

pre-commit install

echo "[+] Dev environment ready. Activate with: source $VENV/bin/activate"
echo "[+] Run linters: ruff check . && black --check ."