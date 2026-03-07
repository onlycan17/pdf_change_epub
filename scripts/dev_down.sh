#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PORT="8000"
FRONTEND_PORT_PRIMARY="3000"
FRONTEND_PORT_FALLBACK="5173"
CELERY_WORKER_PIDFILE="${ROOT_DIR}/.tmp/dev_celery_worker.pid"

run_compose() {
  if [ -x "${ROOT_DIR}/scripts/compose.sh" ]; then
    "${ROOT_DIR}/scripts/compose.sh" "$@"
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

kill_by_pattern() {
  local pattern="$1"
  local label="$2"
  local pids=""

  if ! command -v pgrep >/dev/null 2>&1; then
    echo "[경고] pgrep가 없어 ${label} 종료를 건너뜁니다."
    return
  fi

  pids="$(pgrep -f "${pattern}" || true)"
  if [ -z "${pids}" ]; then
    echo "[정보] ${label} 실행 프로세스가 없습니다."
    return
  fi

  echo "[종료] ${label} 프로세스 종료"
  # shellcheck disable=SC2086
  kill ${pids} >/dev/null 2>&1 || true
}

kill_by_pidfile() {
  local pidfile="$1"
  local label="$2"
  local pid=""

  if [ ! -f "${pidfile}" ]; then
    echo "[정보] ${label} PID 파일이 없습니다."
    return 1
  fi

  pid="$(cat "${pidfile}" 2>/dev/null || true)"
  if [ -z "${pid}" ]; then
    echo "[경고] ${label} PID 파일이 비어 있습니다."
    rm -f "${pidfile}" >/dev/null 2>&1 || true
    return 1
  fi

  if ! kill -0 "${pid}" >/dev/null 2>&1; then
    echo "[정보] ${label} 프로세스가 이미 종료되었습니다."
    rm -f "${pidfile}" >/dev/null 2>&1 || true
    return 0
  fi

  echo "[종료] ${label} 프로세스 종료 (pid: ${pid})"
  kill "${pid}" >/dev/null 2>&1 || true
  sleep 1
  if kill -0 "${pid}" >/dev/null 2>&1; then
    kill -9 "${pid}" >/dev/null 2>&1 || true
  fi
  rm -f "${pidfile}" >/dev/null 2>&1 || true
  return 0
}

echo "[1/4] 백엔드 종료 시도"
kill_by_port "${BACKEND_PORT}" "백엔드(uvicorn)"

echo "[2/4] 프론트엔드 종료 시도"
kill_by_port "${FRONTEND_PORT_PRIMARY}" "프론트엔드(vite)"
kill_by_port "${FRONTEND_PORT_FALLBACK}" "프론트엔드(vite, fallback)"

echo "[3/4] Celery 워커 종료 시도"
if ! kill_by_pidfile "${CELERY_WORKER_PIDFILE}" "Celery 워커"; then
  kill_by_pattern "${ROOT_DIR}/scripts/run_celery_worker.py" "Celery 워커(패턴 폴백)"
fi

echo "[4/4] 개발 인프라(db, redis) 중지"
run_compose stop db redis

echo "개발 환경 종료가 완료되었습니다."
