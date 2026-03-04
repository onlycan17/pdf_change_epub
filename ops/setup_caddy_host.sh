#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/home/jinseok/workspaces/sideprojects/pdf_change_epub"
FRONTEND_DIST_SRC="$REPO_ROOT/frontend/dist"
CADDYFILE_SRC="$REPO_ROOT/ops/Caddyfile"
WEB_ROOT="/var/www/pdf-epub/dist"

if [[ "${EUID}" -ne 0 ]]; then
  echo "ERROR: run as root (use: sudo bash ops/setup_caddy_host.sh)" >&2
  exit 1
fi

if [[ ! -f "$CADDYFILE_SRC" ]]; then
  echo "ERROR: missing $CADDYFILE_SRC" >&2
  exit 1
fi

if [[ ! -f "$FRONTEND_DIST_SRC/index.html" ]]; then
  echo "ERROR: missing frontend build at $FRONTEND_DIST_SRC" >&2
  echo "Run: cd frontend && npm ci && npm run build" >&2
  exit 1
fi

echo "[1/4] Installing Caddy (apt)..."
apt-get update -y
apt-get install -y caddy

echo "[2/4] Deploying frontend dist -> $WEB_ROOT"
mkdir -p "$WEB_ROOT"
# Copy built assets
rm -rf "${WEB_ROOT:?}"/*
cp -a "$FRONTEND_DIST_SRC"/. "$WEB_ROOT"/

# Ensure caddy can read
chown -R caddy:caddy "/var/www/pdf-epub"
chmod -R u=rwX,g=rX,o=rX "/var/www/pdf-epub"

echo "[3/4] Installing Caddyfile -> /etc/caddy/Caddyfile"
install -D -m 0644 "$CADDYFILE_SRC" /etc/caddy/Caddyfile

echo "[4/4] Restarting Caddy"
systemctl enable --now caddy
systemctl restart caddy

echo "OK"
echo "- Check listeners: ss -lntp | grep -E ':(80|443)\\b'"
echo "- Check local http: curl -I http://localhost/"
