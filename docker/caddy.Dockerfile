FROM node:18-alpine AS frontend_builder

WORKDIR /app/frontend

ARG VITE_GOOGLE_CLIENT_ID
ARG APP_GOOGLE_CLIENT_ID
ARG VITE_API_KEY

ENV VITE_GOOGLE_CLIENT_ID=${VITE_GOOGLE_CLIENT_ID}
ENV APP_GOOGLE_CLIENT_ID=${APP_GOOGLE_CLIENT_ID}
ENV VITE_API_KEY=${VITE_API_KEY}

COPY frontend/package.json ./
COPY frontend/package-lock.json ./

RUN npm ci

COPY frontend/ ./

RUN npm run build


FROM caddy:2-alpine

COPY --from=frontend_builder /app/frontend/dist/ /srv/
COPY docker/Caddyfile /etc/caddy/Caddyfile
