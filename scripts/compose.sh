#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT_DIR}"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  exec docker compose "$@"
fi

if command -v docker-compose >/dev/null 2>&1; then
  echo "[WARN] Using docker-compose v1 (EOL)."
  echo "[WARN] On newer Docker Engine versions, 'docker-compose up' may fail with KeyError: 'ContainerConfig'."
  echo "[WARN] Prefer installing Compose v2 plugin so 'docker compose' is available."
  exec docker-compose "$@"
fi

echo "[ERROR] Neither 'docker compose' (v2 plugin) nor 'docker-compose' (v1) is available."
exit 127
