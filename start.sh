#!/usr/bin/env bash
# Jedno polecenie dla jurora: buduje UI i serwuje API+frontend na :8000
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  echo "Docker: http://127.0.0.1:8000"
  exec docker compose up --build
fi

echo "Bez Dockera — venv + npm (http://127.0.0.1:8000)"
python3 -m venv "$ROOT/backend/.venv"
# shellcheck disable=SC1091
source "$ROOT/backend/.venv/bin/activate"
pip install -q -r "$ROOT/backend/requirements.txt"
(cd "$ROOT/frontend" && npm install && NEXT_EXPORT=1 npm run build)
export PYTHONPATH="$ROOT/backend"
exec python3 -m uvicorn app.main:app --app-dir "$ROOT/backend" --host 0.0.0.0 --port 8000
