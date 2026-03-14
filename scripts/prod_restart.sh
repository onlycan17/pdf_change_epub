#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
FRONTEND_DIST_DIR="$FRONTEND_DIR/dist"
WEB_ROOT_DIR="/var/www/pdf-epub/dist"
VENV_UVICORN="$ROOT_DIR/venv/bin/uvicorn"
COMPOSE_FILE="$ROOT_DIR/docker-compose.prod.yml"
COMPOSE_WRAPPER="$ROOT_DIR/scripts/compose.sh"
BACKEND_LOG="/tmp/pdf_epub_backend_prod.log"
BACKEND_PORT="8000"
HEALTH_URL="https://www.pdf-epub.kr/health"
LOCAL_HEALTH_URL="http://127.0.0.1:8000/health"

MODE="restart"
FORCE_MODE=""
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: scripts/prod_restart.sh [options]

Options:
  --mode <start|stop|restart>  Control mode (default: restart)
  --host                        Force host-based mode
  --docker                      Force Docker Compose mode
  --dry-run                     Print commands without executing
  -h, --help                    Show help

Examples:
  scripts/prod_restart.sh
  scripts/prod_restart.sh --mode restart --host
  scripts/prod_restart.sh --mode stop --docker
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --host)
      FORCE_MODE="host"
      shift
      ;;
    --docker)
      FORCE_MODE="docker"
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[ERROR] Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ "$MODE" != "start" && "$MODE" != "stop" && "$MODE" != "restart" ]]; then
  echo "[ERROR] --mode must be one of: start, stop, restart"
  exit 1
fi

run_cmd() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[DRY-RUN] $*"
  else
    eval "$*"
  fi
}

compose_available() {
  [[ -f "$COMPOSE_WRAPPER" ]] || return 1
  bash "$COMPOSE_WRAPPER" version >/dev/null 2>&1
}

compose_cmd() {
  bash "$COMPOSE_WRAPPER" -f "$COMPOSE_FILE" "$@"
}

detect_mode() {
  if [[ -n "$FORCE_MODE" ]]; then
    echo "$FORCE_MODE"
    return
  fi

  if [[ -f "$COMPOSE_FILE" ]] && compose_available; then
    echo "docker"
    return
  fi

  echo "host"
}

SUDO=""
if [[ "${EUID}" -ne 0 ]]; then
  SUDO="sudo"
fi

restart_host_backend() {
  run_cmd "pkill -f 'uvicorn app.main:app' || true"
  run_cmd "nohup '$VENV_UVICORN' app.main:app --host 0.0.0.0 --port $BACKEND_PORT > '$BACKEND_LOG' 2>&1 &"
}

start_host_backend() {
  run_cmd "nohup '$VENV_UVICORN' app.main:app --host 0.0.0.0 --port $BACKEND_PORT > '$BACKEND_LOG' 2>&1 &"
}

stop_host_backend() {
  run_cmd "pkill -f 'uvicorn app.main:app' || true"
}

reload_caddy() {
  run_cmd "caddy reload --config /etc/caddy/Caddyfile || $SUDO -n caddy reload --config /etc/caddy/Caddyfile || true"
  run_cmd "systemctl restart caddy || $SUDO -n systemctl restart caddy || true"
}

deploy_frontend_host() {
  run_cmd "npm run build --prefix '$FRONTEND_DIR'"
  run_cmd "mkdir -p '$WEB_ROOT_DIR' || $SUDO -n mkdir -p '$WEB_ROOT_DIR'"
  run_cmd "rsync -av --delete '$FRONTEND_DIST_DIR/' '$WEB_ROOT_DIR/' || $SUDO -n rsync -av --delete '$FRONTEND_DIST_DIR/' '$WEB_ROOT_DIR/'"
}

run_health_check() {
  run_cmd "for i in 1 2 3 4 5; do code=\$(curl -sS -o /dev/null -w '%{http_code}' '$HEALTH_URL' || true); if [ \"\$code\" = \"200\" ]; then echo 200; exit 0; fi; sleep 1; done; echo \"[WARN] health check failed\"; echo \"\$code\""
}

wait_for_local_backend() {
  run_cmd "for i in 1 2 3 4 5 6 7 8 9 10; do code=\$(curl -sS -o /dev/null -w '%{http_code}' '$LOCAL_HEALTH_URL' || true); if [ \"\$code\" = \"200\" ]; then exit 0; fi; sleep 1; done; echo '[WARN] local backend did not become healthy in time'"
}

run_host_mode() {
  echo "[INFO] Mode: host"

  if [[ ! -x "$VENV_UVICORN" ]]; then
    echo "[ERROR] Missing uvicorn binary: $VENV_UVICORN"
    exit 1
  fi

  case "$MODE" in
    start)
      deploy_frontend_host
      start_host_backend
      wait_for_local_backend
      reload_caddy
      ;;
    stop)
      stop_host_backend
      ;;
    restart)
      deploy_frontend_host
      restart_host_backend
      wait_for_local_backend
      reload_caddy
      ;;
  esac

  if [[ "$MODE" != "stop" ]]; then
    run_health_check
  fi
}

run_docker_mode() {
  echo "[INFO] Mode: docker"
  if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo "[ERROR] Missing compose file: $COMPOSE_FILE"
    exit 1
  fi
  if ! compose_available; then
    echo "[ERROR] Docker Compose command unavailable. Expected $COMPOSE_WRAPPER to resolve either 'docker compose' or 'docker-compose'."
    exit 1
  fi

  case "$MODE" in
    start)
      stop_host_backend
      run_cmd "bash '$COMPOSE_WRAPPER' -f '$COMPOSE_FILE' up -d --build"
      ;;
    stop)
      run_cmd "bash '$COMPOSE_WRAPPER' -f '$COMPOSE_FILE' down"
      stop_host_backend
      ;;
    restart)
      stop_host_backend
      run_cmd "bash '$COMPOSE_WRAPPER' -f '$COMPOSE_FILE' down"
      run_cmd "bash '$COMPOSE_WRAPPER' -f '$COMPOSE_FILE' up -d --build"
      ;;
  esac

  if [[ "$MODE" != "stop" ]]; then
    run_health_check
  fi
}

MODE_DETECTED="$(detect_mode)"
if [[ "$MODE_DETECTED" == "docker" ]]; then
  run_docker_mode
else
  run_host_mode
fi

echo "[DONE] prod_restart completed (mode=$MODE, backend=$MODE_DETECTED)"
