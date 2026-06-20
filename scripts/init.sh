#!/usr/bin/env bash
# One-shot project initializer: env + venv + docker stack.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Initializing TODO app"
bash scripts/create_venv.sh

echo "==> Bringing up docker stack (app + postgres + redis)"
docker compose up -d --build --wait

echo "==> Stack is healthy. API: http://localhost:8000/docs"
