#!/usr/bin/env bash
# Quick smoke demo (requires .env configured and ingestion complete)
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== Health ==="
curl -s http://127.0.0.1:8000/health | python3 -m json.tool

echo ""
echo "=== Ask ==="
curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I use dependency injection in FastAPI?"}' \
  | python3 -m json.tool
