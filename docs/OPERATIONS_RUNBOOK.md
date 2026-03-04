# 운영 서버 기동/중지/재기동 런북

이 문서는 `pdf-epub.kr` / `www.pdf-epub.kr` 운영 서버를 안전하게
기동(start), 중지(stop), 재기동(restart)하기 위한 실행 절차입니다.

자동화 스크립트:

```bash
chmod +x scripts/prod_restart.sh scripts/prod_start.sh scripts/prod_stop.sh
```

간편 명령:

```bash
# 시작
scripts/prod_start.sh

# 중지
scripts/prod_stop.sh

# 재기동
scripts/prod_restart.sh --mode restart
```

`--host` 모드의 `start`/`restart`는 자동으로 아래를 수행합니다.

- 프론트 `npm run build`
- `/var/www/pdf-epub/dist`로 `rsync --delete` 반영
- 백엔드(uvicorn) 시작/재시작
- Caddy reload/restart 시도

## 0) 현재 운영 방식 확인 (중요)

먼저 서버가 Docker 기반인지, 호스트 서비스 기반인지 확인합니다.

```bash
# Docker 기반 여부
docker ps

# Caddy(systemd) 여부
systemctl is-active caddy

# 백엔드 포트(8000) 점유 프로세스 확인
lsof -iTCP:8000 -sTCP:LISTEN -t | xargs -r ps -fp
```

### 판정 기준

- Docker 명령이 없거나 컨테이너가 없고 `caddy`만 active이면:
  - **호스트 기반 운영** (이 문서의 1번 절차 사용)
- `docker compose -f docker-compose.prod.yml ps`에 `web`, `caddy` 등이 있으면:
  - **Docker 기반 운영** (이 문서의 2번 절차 사용)

---

## 1) 호스트 기반 운영 (현재 서버 기준 권장)

현재 확인된 운영 구조:

- 프록시: `caddy` (systemd)
- 백엔드: `uvicorn` (포트 8000)
- 프론트: `/var/www/pdf-epub/dist` 정적 파일 제공

### 1-1. 코드 반영 + 프론트 빌드

```bash
cd /home/jinseok/workspaces/sideprojects/pdf_change_epub
git pull

cd frontend
npm ci
npm run build

sudo mkdir -p /var/www/pdf-epub/dist
sudo rsync -av --delete dist/ /var/www/pdf-epub/dist/
```

### 1-2. 백엔드 시작

```bash
cd /home/jinseok/workspaces/sideprojects/pdf_change_epub
nohup /home/jinseok/workspaces/sideprojects/pdf_change_epub/venv/bin/uvicorn \
  app.main:app --host 0.0.0.0 --port 8000 \
  > /tmp/pdf_epub_backend_prod.log 2>&1 &
```

### 1-3. 백엔드 중지

```bash
pkill -f "uvicorn app.main:app" || true
```

### 1-4. 백엔드 재기동

```bash
pkill -f "uvicorn app.main:app" || true
nohup /home/jinseok/workspaces/sideprojects/pdf_change_epub/venv/bin/uvicorn \
  app.main:app --host 0.0.0.0 --port 8000 \
  > /tmp/pdf_epub_backend_prod.log 2>&1 &
```

### 1-5. Caddy 적용/재기동

권한이 있으면 아래 순서 권장:

```bash
sudo caddy reload --config /etc/caddy/Caddyfile
sudo systemctl restart caddy
```

권한이 제한된 환경이면(예: root 비밀번호 미입력 환경) `caddy reload`만 가능할 수 있습니다.

### 1-6. 상태 검증

```bash
# 로컬 프로세스
lsof -iTCP:8000 -sTCP:LISTEN -t | xargs -r ps -fp
systemctl is-active caddy

# 도메인 응답
curl -I https://www.pdf-epub.kr/
curl -sS -o /dev/null -w "%{http_code}\n" https://www.pdf-epub.kr/health
```

정상 기준:

- `systemctl is-active caddy` = `active`
- `/` 응답 = `200`
- `/health` 응답 = `200` (GET 기준)

---

## 2) Docker 기반 운영 (필요 시)

`docker-compose.prod.yml`을 사용하는 경우 절차입니다.

### 2-1. 시작

```bash
cd /home/jinseok/workspaces/sideprojects/pdf_change_epub
docker compose -f docker-compose.prod.yml up -d --build
```

### 2-2. 중지

```bash
cd /home/jinseok/workspaces/sideprojects/pdf_change_epub
docker compose -f docker-compose.prod.yml down
```

### 2-3. 재기동

```bash
cd /home/jinseok/workspaces/sideprojects/pdf_change_epub
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

### 2-4. 상태 검증

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=100 web
docker compose -f docker-compose.prod.yml logs --tail=100 caddy
curl -I https://www.pdf-epub.kr/
curl -sS -o /dev/null -w "%{http_code}\n" https://www.pdf-epub.kr/health
```

---

## 3) 장애 대응 체크리스트

### 3-1. Caddy는 active인데 도메인 장애

```bash
systemctl status caddy --no-pager
journalctl -u caddy -n 200 --no-pager
```

확인 포인트:

- DNS 레코드(A/AAAA) 유효 여부
- 80/443 방화벽 허용 여부
- 인증서 발급 에러(ACME)

### 3-2. 도메인은 뜨는데 API만 장애

```bash
lsof -iTCP:8000 -sTCP:LISTEN -t | xargs -r ps -fp
tail -n 200 /tmp/pdf_epub_backend_prod.log
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/health
```

### 3-3. 배포 후 프론트가 옛 화면으로 보일 때

```bash
cd /home/jinseok/workspaces/sideprojects/pdf_change_epub/frontend
npm run build
sudo rsync -av --delete dist/ /var/www/pdf-epub/dist/
sudo caddy reload --config /etc/caddy/Caddyfile
```

---

## 4) 운영자가 자주 쓰는 원라인

### 스크립트 방식 (권장)

```bash
cd /home/jinseok/workspaces/sideprojects/pdf_change_epub
scripts/prod_restart.sh --mode restart
```

옵션:

```bash
scripts/prod_restart.sh --mode start --host
scripts/prod_restart.sh --mode stop --host
scripts/prod_restart.sh --mode restart --docker
scripts/prod_restart.sh --mode restart --dry-run
```

### 호스트 기반 즉시 재기동 원라인

```bash
cd /home/jinseok/workspaces/sideprojects/pdf_change_epub && \
pkill -f "uvicorn app.main:app" || true; \
nohup /home/jinseok/workspaces/sideprojects/pdf_change_epub/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/pdf_epub_backend_prod.log 2>&1 & \
&& sudo caddy reload --config /etc/caddy/Caddyfile \
&& curl -sS -o /dev/null -w "%{http_code}\n" https://www.pdf-epub.kr/health
```

---

## 5) 주의사항

- 운영 중에는 `pkill -f uvicorn` 명령이 다른 uvicorn 프로세스까지 종료할 수 있으므로,
  서버에 다중 프로젝트가 있으면 프로세스 경로를 함께 확인하고 종료하세요.
- `/health`는 GET 기준으로 검증하세요. 환경에 따라 HEAD는 `405`가 나올 수 있습니다.
- Caddy 재기동은 root 권한이 필요할 수 있습니다.
