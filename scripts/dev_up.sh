#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/venv"
REQUIREMENTS_FILE="${ROOT_DIR}/requirements.txt"
FRONTEND_DIR="${ROOT_DIR}/frontend"
BACKEND_HOST="0.0.0.0"
BACKEND_PORT="8000"
FRONTEND_PORT="3000"
SKIP_INFRA="${SKIP_INFRA:-0}"
REQUIRE_INFRA="${REQUIRE_INFRA:-0}"

run_compose() {
  if command -v docker-compose >/dev/null 2>&1; then
    (cd "${ROOT_DIR}" && docker-compose "$@")
    return 0
  fi

  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    (cd "${ROOT_DIR}" && docker compose "$@")
    return 0
  fi

  return 127
}

if command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN="python3.11"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  echo "[오류] python3.11 또는 python3가 필요합니다."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[오류] npm이 필요합니다."
  exit 1
fi

echo "[1/5] 백엔드 가상환경 준비"
if [ ! -d "${VENV_DIR}" ]; then
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
pip install -r "${REQUIREMENTS_FILE}" >/dev/null

echo "[2/5] 프론트엔드 의존성 준비"
if [ ! -d "${FRONTEND_DIR}/node_modules" ]; then
  (cd "${FRONTEND_DIR}" && npm ci)
fi

echo "[3/5] 필수 인프라(db, redis) 실행"
if [ "${SKIP_INFRA}" = "1" ]; then
  echo "[정보] SKIP_INFRA=1 설정으로 인프라 실행을 건너뜁니다."
else
  if run_compose up -d db redis; then
    echo "[정보] 인프라(db, redis) 실행 완료"
  else
    if [ "${REQUIRE_INFRA}" = "1" ]; then
      echo "[오류] 인프라 준비 실패(REQUIRE_INFRA=1). 종료합니다."
      exit 1
    fi
    echo "[경고] 인프라를 시작하지 못했지만 개발 서버 실행은 계속합니다."
    echo "[경고] 인프라가 필요하면 Docker 설치 후 다시 실행하거나 REQUIRE_INFRA=1로 확인하세요."
  fi
fi

echo "[4/5] 백엔드 서버 실행"
(
  cd "${ROOT_DIR}"
  export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"
  uvicorn app.main:app --reload --host "${BACKEND_HOST}" --port "${BACKEND_PORT}"
) &
BACKEND_PID=$!

cleanup() {
  if kill -0 "${BACKEND_PID}" >/dev/null 2>&1; then
    kill "${BACKEND_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

echo "[5/5] 프론트엔드 개발 서버 실행"
echo "브라우저 접속: http://localhost:${FRONTEND_PORT}"
echo "백엔드 API: http://localhost:${BACKEND_PORT}"
cd "${FRONTEND_DIR}"
npm run dev -- --host 0.0.0.0
