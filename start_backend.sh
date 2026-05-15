#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT_DIR"

echo "Installing backend dependencies into user site packages..."
"$PYTHON_BIN" -m pip install --user -r backend/requirements.txt

echo "Starting FastAPI at http://127.0.0.1:8000"
exec "$PYTHON_BIN" -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
