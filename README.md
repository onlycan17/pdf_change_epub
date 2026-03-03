# PDF → EPUB 변환기

PDF 문서를 EPUB 전자책으로 변환하는 웹 서비스입니다.  
백엔드는 FastAPI/Celery, 프론트엔드는 React/Vite 기반으로 구성되어 있습니다.

## 현재 구현 상태
- 백엔드 API: 인증, 변환 라우터 구현 (결제/구독은 현재 비활성화)
- 변환 파이프라인: PDF 분석, OCR/LLM 처리, EPUB 생성 오케스트레이션 구현
- 비동기 처리: Redis + Celery 큐 기반 작업 처리 구현
- 프론트엔드: 라우팅/페이지 UI 구현 (홈, 업로드, 변환, 다운로드, 후원 등)
- 테스트: 백엔드 단위/통합 테스트 포함

## 업로드 정책
- 비로그인 또는 무료 계정: 최대 25MB
- (현재) 구독/결제 기능은 비활성화되어 모든 사용자가 무료 한도(25MB)로 동작합니다.

## 수익화(현재)
- 결제 기능은 추후 도입 예정이며, 현재는 무료 기능으로 시장 반응을 확인합니다.
- 운영 비용은 광고와 후원으로 충당합니다. 자세한 내용은 `docs/monetization_free_only.md`를 참고하세요.

## 기술 스택
- 백엔드: FastAPI, Pydantic, Celery, Redis
- PDF/OCR/EPUB: pypdf, pdfminer.six, PyMuPDF, PaddleOCR, ebooklib
- 프론트엔드: React 18, TypeScript, Vite, ESLint, Prettier

## 빠른 시작
### 가장 간단한 실행(권장)
```bash
chmod +x scripts/dev_up.sh
./scripts/dev_up.sh
```

위 명령은 백엔드/프론트엔드/필수 인프라(db, redis)를 한 번에 실행합니다.
Docker가 없으면 인프라 실행은 건너뛰고 백엔드/프론트엔드만 실행합니다.

인프라를 반드시 띄워야 하면 아래처럼 엄격 모드로 실행합니다.
```bash
REQUIRE_INFRA=1 ./scripts/dev_up.sh
```

인프라를 의도적으로 생략하려면 아래처럼 실행합니다.
```bash
SKIP_INFRA=1 ./scripts/dev_up.sh
```

종료는 아래처럼 실행합니다.
```bash
chmod +x scripts/dev_down.sh
./scripts/dev_down.sh
```

실제 변환/다운로드가 되는지 빠르게 점검하려면 아래 스모크 테스트를 실행합니다.
```bash
chmod +x scripts/smoke_conversion.sh
./scripts/smoke_conversion.sh <PDF_파일_경로>
```
예시:
```bash
./scripts/smoke_conversion.sh ./samples/test.pdf
```

### 수동 실행
1. 백엔드 의존성 설치
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. 프론트엔드 의존성 설치
```bash
cd frontend
npm ci
cp .env.example .env
cd ..
```

3. 환경 변수 설정
```bash
cp .env.example .env
```
`OPENROUTER_API_KEY`를 설정하면 문맥 보정(1차: `deepseek/deepseek-v3.2`, 2차: `nvidia/nemotron-3-nano-30b-a3b`)이 활성화됩니다.

4. 로컬 인프라 실행
```bash
docker-compose up -d db redis
```

5. 서버 실행
```bash
# 백엔드
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프론트엔드(별도 터미널)
cd frontend && npm run dev
```

## 자동 검사 명령
백엔드:
```bash
make fmt
make lint
make test
```

프론트엔드:
```bash
cd frontend
npm run lint
npm run type-check
npm run build
```

## 문서
- [PRD](docs/PRD.md)
- [아키텍처](docs/architecture.md)
- [상세 아키텍처](docs/detailed_architecture.md)
- [개발 계획](docs/development_plan.md)
- [UI 명세](docs/ui_spec.md)
- [배포 가이드](docs/DEPLOYMENT.md)
- [리팩토링 계획서(2026-02-09)](docs/refactoring/2026-02-09_sync_plan.md)
