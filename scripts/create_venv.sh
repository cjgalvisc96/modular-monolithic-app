#!/usr/bin/env bash
# Bootstrap the local development environment with uv.
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not installed. Install it: https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi

echo "==> Creating virtualenv (.venv)"
uv venv

echo "==> Syncing dependencies (prod + dev + test + lint)"
uv sync --group dev --group test --group lint

if [ ! -f .env ]; then
  echo "==> No .env found; copying from .env.example"
  cp .env.example .env
fi

echo "==> Done. Activate with: source .venv/bin/activate"
