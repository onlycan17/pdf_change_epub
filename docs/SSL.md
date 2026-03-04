# SSL (HTTPS) Setup Guide (Free)

This project can run behind a reverse proxy that terminates TLS.

Recommended approach: Caddy (Let's Encrypt) on ports 80/443.

## Why Caddy

- Free certificates (Let's Encrypt) with automatic renewal.
- Simple config for SPA static hosting + API reverse proxy.
- Good defaults for HTTPS and redirects.

## Prerequisites

- DNS A/AAAA records point to your server public IP:
  - pdf-epub.kr
  - pdf-epub.co.kr
  - (optional) www.pdf-epub.kr, www.pdf-epub.co.kr
- Inbound ports 80 and 443 are allowed (firewall / security group).
- Nothing else is listening on 80/443.

## Option A (Recommended): Host-level Caddy

1) Build frontend for production and place it on the server

```bash
cd frontend
npm ci
npm run build
sudo mkdir -p /var/www/pdf-epub
sudo rsync -a --delete dist/ /var/www/pdf-epub/dist/
```

2) Run backend on localhost only (not publicly exposed)

Example (systemd is recommended in real production):

```bash
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

3) Install Caddy and configure

Create `/etc/caddy/Caddyfile`:

```caddyfile
pdf-epub.kr, pdf-epub.co.kr {
  encode zstd gzip

  @backend path /api/* /docs* /openapi.json /redoc* /health*
  handle @backend {
    reverse_proxy 127.0.0.1:8000
  }

  handle {
    root * /var/www/pdf-epub/dist
    try_files {path} /index.html
    file_server
  }
}
```

Restart Caddy:

```bash
sudo systemctl reload caddy
```

4) Verify

```bash
curl -I https://pdf-epub.kr/
curl -I https://pdf-epub.co.kr/
curl -I https://pdf-epub.kr/api/v1/health || true
```

## Option B: Docker Compose (Caddy in container)

This repo includes a production compose file and a Caddy-based frontend image.

Files:

- `docker-compose.prod.yml`
- `docker/Caddyfile`
- `docker/caddy.Dockerfile`

Run:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

## Post-HTTPS Checklist

- Google OAuth: add `https://pdf-epub.kr` and/or `https://pdf-epub.co.kr` to Authorized JavaScript origins and redirect URIs.
- App CORS/origins: allow the https origins in backend settings.
- Add HSTS only after everything is stable (avoid `preload` initially).
