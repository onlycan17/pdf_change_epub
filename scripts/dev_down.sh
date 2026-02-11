#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PORT="8000"
FRONTEND_PORT_PRIMARY="3000"
FRONTEND_PORT_FALLBACK="5173"

run_compose() {
  if command -v docker-compose >/dev/null 2>&1; then
    (cd "${ROOT_DIR}" && docker-compose "$@")
    return
  fi

  if command -v docker >/dev/null 2>&1; then
    (cd "${ROOT_DIR}" && docker compose "$@")
    return
  fi

  echo "[경고] docker-compose 또는 docker compose를 찾지 못해 인프라 중지를 건너뜁니다."
}

kill_by_port() {
  local port="$1"
  local label="$2"
  local pids=""

  if ! command -v lsof >/dev/null 2>&1; then
    echo "[경고] lsof가 없어 ${label} 종료를 건너뜁니다."
    return
  fi

  pids="$(lsof -ti tcp:"${port}" || true)"
  if [ -z "${pids}" ]; then
    echo "[정보] ${label} 실행 프로세스가 없습니다."
    return
  fi

  echo "[종료] ${label} 프로세스 종료 (port: ${port})"
  # shellcheck disable=SC2086
  kill ${pids} >/dev/null 2>&1 || true
}

echo "[1/3] 백엔드 종료 시도"
kill_by_port "${BACKEND_PORT}" "백엔드(uvicorn)"

echo "[2/3] 프론트엔드 종료 시도"
kill_by_port "${FRONTEND_PORT_PRIMARY}" "프론트엔드(vite)"
kill_by_port "${FRONTEND_PORT_FALLBACK}" "프론트엔드(vite, fallback)"

echo "[3/3] 개발 인프라(db, redis) 중지"
run_compose stop db redis

echo "개발 환경 종료가 완료되었습니다."
