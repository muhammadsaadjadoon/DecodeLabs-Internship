#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/backend"

if [[ ! -f .venv/bin/activate ]]; then
  echo "Virtual environment not found. Run scripts/setup_unix.sh first." >&2
  exit 1
fi

source .venv/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000
