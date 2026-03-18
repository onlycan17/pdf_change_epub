# PDF → EPUB 변환기

PDF 문서를 EPUB 전자책으로 변환하는 웹 서비스입니다.  
백엔드는 FastAPI/Celery, 프론트엔드는 React/Vite 기반으로 구성되어 있습니다.

## 현재 구현 상태
- 백엔드 API: 인증, 변환, 운영자 대시보드, 대용량 요청, 결제 준비용 라우터 구현
- 변환 파이프라인: PDF 분석, OCR/LLM 처리, EPUB 생성 오케스트레이션 구현
- 비동기 처리: Redis + Celery 큐 기반 작업 처리 구현
- 프론트엔드: 홈, 업로드, 변환 진행, 다운로드, 후원, 도움말, 문의, 로그인/회원가입, 운영자 화면 구현
- 로그인: 이메일/비밀번호 로그인, Google 간편로그인 지원
- 운영 기능: 대용량 요청 접수/처리, 운영자 대시보드 제공
- 테스트: 백엔드 단위/통합 테스트 포함

## 업로드 정책
- 일반 로그인 사용자: 직접 변환 최대 25MB, 하루 2회 무료 변환
- 운영자(특별 권한) 계정: 직접 변환 최대 500MB
- 일반 사용자의 25MB 초과 문서: 대용량 요청 페이지에서 최대 500MB까지 별도 접수 가능
- 프론트엔드에는 월간/연간 플랜 정보가 준비되어 있지만, 현재 백엔드 결제 기능은 기본적으로 비활성화되어 있습니다.

## 수익화(현재)
- 결제 기능은 추후 도입 예정이며, 현재는 무료 기능으로 시장 반응을 확인합니다.
- 운영 비용은 광고와 후원으로 충당합니다. 자세한 내용은 `docs/monetization_free_only.md`를 참고하세요.

## 주요 기능
- PDF → EPUB 변환 시작 및 진행률 조회
- OCR 옵션을 사용한 스캔 PDF 처리
- 영문 텍스트 한글 번역 옵션(백엔드 지원)
- 변환 완료 후 실제 파일 또는 샘플 EPUB 다운로드
- 이메일/비밀번호 회원가입 및 로그인
- Google 간편로그인
- 대용량 변환 요청 접수 및 운영자 처리 화면
- 운영자 대시보드(최근 사용량, 실패 현황, 사용자/요청 요약)
- 공개 안내 페이지(서비스 안내, 도움말 센터, 문의, 약관, 개인정보처리방침)
- 모바일 웹 반응형 UI

## 기술 스택
- 백엔드: FastAPI, Pydantic, Celery, Redis
- 저장소: 기본 SQLite, 선택적 PostgreSQL 설정
- PDF/OCR/EPUB: PyMuPDF, pdfminer.six, pypdf, PaddleOCR, Tesseract OCR 런타임, ebooklib
- AI/텍스트 처리: OpenRouter 계열 LLM, 문맥 보정/번역 폴백 모델
- 프론트엔드: React 18, TypeScript, Vite, Tailwind CSS, ESLint, Prettier

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
스캔 PDF는 `PaddleOCR 우선, Tesseract 폴백` 구조로 동작하며, OCR 신뢰도가 낮은 페이지만 멀티모달 LLM이 추가 보정합니다.

Google 로그인을 사용한다면 백엔드용 `APP_GOOGLE_CLIENT_ID`와 프론트 빌드용 `VITE_GOOGLE_CLIENT_ID`를 함께 설정하세요.
로컬 개발에서는 `VITE_GOOGLE_ALLOWED_ORIGINS`를 비워 두어도 `localhost`/`127.0.0.1` 기본 주소를 자동 허용합니다. 운영 환경에서는 허용 원본을 명시적으로 관리하는 방식을 유지합니다.

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
- [기술 스택](docs/tech_stack.md)
- [개발 계획](docs/development_plan.md)
- [UI 명세](docs/ui_spec.md)
- [Google 로그인](docs/GOOGLE_LOGIN.md)
- [무료 운영 정책](docs/monetization_free_only.md)
- [배포 가이드](docs/DEPLOYMENT.md)
- [운영 런북(기동/중지/재기동)](docs/OPERATIONS_RUNBOOK.md)
- [리팩토링 계획서(2026-02-09)](docs/refactoring/2026-02-09_sync_plan.md)
