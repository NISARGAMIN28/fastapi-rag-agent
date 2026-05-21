#!/usr/bin/env bash
# One command: check setup → start API on http://127.0.0.1:8000
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -d .venv ]]; then
  echo "Creating virtualenv..."
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi

source .venv/bin/activate

if [[ ! -f .env ]]; then
  echo "No .env file. Copying .env.example → .env"
  cp .env.example .env
  echo "Edit .env with your keys, then run this script again."
  exit 1
fi

python scripts/check_setup.py || {
  echo ""
  echo "Quick fix if DB is empty:"
  echo "  python -m src.ingest"
  exit 1
}

echo "Starting API → http://127.0.0.1:8000"
echo "  Demo UI:  http://127.0.0.1:8000/demo"
echo "  API docs: http://127.0.0.1:8000/docs"
echo ""
exec uvicorn src.api:app --reload --host 127.0.0.1 --port 8000
