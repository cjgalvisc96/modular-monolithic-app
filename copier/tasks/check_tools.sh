#!/usr/bin/env bash
set -euo pipefail

answers="${1:-.copier-answers.yml}"
selected() { grep -qE "^${1}:[[:space:]]*true" "$answers" 2>/dev/null; }

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "missing required tool: $1"; exit 1; }
}

require uv
selected include_docker && require docker || true
selected include_k8s && { require kubectl; require helm; } || true
selected include_terraform && require terraform || true

echo "tool check passed"
