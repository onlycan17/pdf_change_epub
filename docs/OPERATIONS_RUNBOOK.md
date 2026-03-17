# 운영 서버 기동/중지/재기동 런북

이 문서는 `pdf-epub.kr` / `www.pdf-epub.kr` 운영 서버를 안전하게
기동(start), 중지(stop), 재기동(restart)하기 위한 실행 절차입니다.

자동화 스크립트:

```bash
chmod +x scripts/prod_restart.sh scripts/prod_start.sh scripts/prod_stop.sh scripts/compose.sh
```

간편 명령:

```bash
# 시작
scripts/prod_start.sh

# 중지
scripts/prod_stop.sh

# 재기동 (기본: Docker 기반 운영)
scripts/prod_restart.sh --mode restart
```

기본 동작은 `docker-compose.prod.yml` 기반의 Docker 재배포입니다.
스크립트는 내부적으로 `scripts/compose.sh`를 사용해 환경에 따라
`docker compose` 또는 `docker-compose`를 자동 선택합니다.

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

- `scripts/compose.sh -f docker-compose.prod.yml ps`가 동작하고
  `web`, `caddy` 등이 보이면:
  - **Docker 기반 운영** (이 문서의 2번 절차 사용, 현재 기본값)
- Compose 명령을 사용할 수 없고 `caddy`만 active이면:
  - **호스트 기반 운영** (이 문서의 1번 절차는 예외 대응용)

---

## 1) 호스트 기반 운영 (예외 대응용)

호스트 기반 운영은 Docker Compose를 사용할 수 없거나,
긴급 우회가 필요한 경우에만 사용합니다.

현재 구조 예시:

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

## 2) Docker 기반 운영 (현재 운영 기본값)

`docker-compose.prod.yml`을 사용하는 경우 절차입니다.

중요: 운영 명령은 직접 `docker compose` / `docker-compose`를 쓰기보다
`scripts/compose.sh`를 사용하세요. 이 스크립트가 환경에 맞는 Compose 명령을 선택합니다.
일부 환경에서는 `docker compose` 플러그인이 없고 `docker-compose`만 동작할 수 있습니다.

```bash
scripts/compose.sh version
```

### 2-1. 시작

```bash
cd /home/jinseok/workspaces/sideprojects/pdf_change_epub
scripts/compose.sh -f docker-compose.prod.yml up -d --build
```

### 2-2. 중지

```bash
cd /home/jinseok/workspaces/sideprojects/pdf_change_epub
scripts/compose.sh -f docker-compose.prod.yml down
```

### 2-3. 재기동

```bash
cd /home/jinseok/workspaces/sideprojects/pdf_change_epub
scripts/prod_restart.sh --mode restart
```

### 2-4. 상태 검증

```bash
scripts/compose.sh -f docker-compose.prod.yml ps
scripts/compose.sh -f docker-compose.prod.yml logs --tail=100 web
scripts/compose.sh -f docker-compose.prod.yml logs --tail=100 caddy
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
scripts/prod_restart.sh --mode start
scripts/prod_restart.sh --mode stop
scripts/prod_restart.sh --mode restart --docker
scripts/prod_restart.sh --mode restart --host
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
- Docker 운영으로 전환한 뒤에는 호스트의 `127.0.0.1:8000` 검사는 의미가 없을 수 있습니다.
  외부 도메인 기준 또는 `scripts/compose.sh ... logs` 기준으로 확인하세요.
- Caddy 재기동은 root 권한이 필요할 수 있습니다.
