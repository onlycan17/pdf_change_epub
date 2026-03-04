FROM node:18-alpine AS frontend_builder

WORKDIR /app/frontend

COPY frontend/package.json ./
COPY frontend/package-lock.json ./

RUN npm ci

COPY frontend/ ./

RUN npm run build


FROM caddy:2-alpine

COPY --from=frontend_builder /app/frontend/dist/ /srv/
COPY docker/Caddyfile /etc/caddy/Caddyfile
