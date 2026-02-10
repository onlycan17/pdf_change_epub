# PDF → EPUB 변환기

PDF 문서를 EPUB 전자책으로 변환하는 웹 서비스입니다.  
백엔드는 FastAPI/Celery, 프론트엔드는 React/Vite 기반으로 구성되어 있습니다.

## 현재 구현 상태
- 백엔드 API: 인증, 변환, 결제 라우터 구현
- 변환 파이프라인: PDF 분석, OCR/LLM 처리, EPUB 생성 오케스트레이션 구현
- 비동기 처리: Redis + Celery 큐 기반 작업 처리 구현
- 프론트엔드: 라우팅/페이지 UI 구현 (홈, 업로드, 변환, 다운로드, 프리미엄 등)
- 테스트: 백엔드 단위/통합 테스트 포함

## 기술 스택
- 백엔드: FastAPI, Pydantic, Celery, Redis
- PDF/OCR/EPUB: pypdf, pdfminer.six, PyMuPDF, PaddleOCR, ebooklib
- 프론트엔드: React 18, TypeScript, Vite, ESLint, Prettier

## 빠른 시작
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
cd ..
```

3. 로컬 인프라 실행
```bash
docker-compose up -d db redis
```

4. 서버 실행
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
