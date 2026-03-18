# 기술 스택 명세서

## 1. 개요
이 문서는 현재 코드베이스를 기준으로 PDF를 EPUB으로 변환하는 서비스에 실제 사용 중인 기술 스택과 보조 기술을 정리합니다.

## 2. 프론트엔드 (Frontend)
- **프레임워크**: React 18+
- **언어**: TypeScript
- **빌드 도구**: Vite
- **상태 관리**: React Context API
- **스타일링**: Tailwind CSS + 커스텀 글로벌 스타일
- **라우팅**: React Router DOM
- **데이터 통신**: 브라우저 `fetch` 기반 API 호출
- **인증 UI**: Google Identity Services 버튼 렌더링

## 3. 백엔드 (Backend)

### 3.1. API / 애플리케이션 계층
- **언어**: Python 3.11+
- **웹 프레임워크**: FastAPI
- **설정 관리**: Pydantic Settings
- **인증 방식**:
  - 이메일/비밀번호 로그인
  - Google 간편로그인
  - 서비스 API 키 검증
  - 쿠키 기반 세션 상태 유지

### 3.2. 변환 / 처리 계층
- **비동기 작업**: Celery + Redis
- **PDF 처리**: PyMuPDF, pdfminer.six, pypdf
- **OCR 처리**: Tesseract OCR 런타임 연동
- **EPUB 생성**: ebooklib
- **텍스트 후처리**:
  - 문맥 보정 LLM 호출
  - 번역 옵션(`translate_to_korean`) 지원
  - 수식/이미지/텍스트 정리용 서비스 모듈 분리

### 3.3. 데이터 저장
- **기본 DB**: SQLite (`pdf_to_epub.db`)
- **선택적 DB 설정**: PostgreSQL 연결 가능
- **파일 저장 디렉터리**:
  - 업로드: `uploads/`
  - 결과물: `results/`
  - 임시 파일: `temp/`

### 3.4. 운영 기능
- **운영자 대시보드**: 최근 변환, 실패 현황, 사용자/요청 요약
- **대용량 요청 관리**: 최대 500MB 요청 접수 및 운영자 처리
- **결제 준비 기능**:
  - Stripe / Toss 관련 서비스와 API가 준비되어 있음
  - 기본 설정에서는 `billing_enabled=false`로 비활성화

## 4. 개발 및 운영 (DevOps)
- **컨테이너화**: Docker
- **CI/CD**: GitHub Actions
- **코드 품질**:
    - **Frontend**: ESLint, Prettier
    - **Backend**: black, ruff, mypy
- **테스트**:
    - **Frontend**: 빌드/린트 중심 검증
    - **Backend**: Pytest
- **개발 실행 스크립트**:
    - `scripts/dev_up.sh`
    - `scripts/dev_down.sh`
    - `scripts/smoke_conversion.sh`

## 5. 기술 선택 이유 요약
- **FastAPI + 서비스 모듈 분리**: 인증, 변환, 운영 기능을 명확히 나누어 유지보수성을 높입니다.
- **Celery + Redis**: 오래 걸리는 PDF 변환을 웹 요청과 분리해 사용자 대기 경험을 개선합니다.
- **React + Tailwind CSS**: 빠르게 화면을 조립하면서도 반응형 UI를 세밀하게 다듬기 좋습니다.
- **Google 로그인 + 자체 인증 병행**: 일반 로그인과 간편로그인을 함께 제공해 진입 장벽을 낮춥니다.
- **OpenRouter 계열 LLM 활용**: 문맥 보정과 번역 품질을 개선하면서 모델 교체 여지를 남깁니다.
- **Tesseract OCR 런타임 연동**: 스캔 PDF 처리를 위한 범용 OCR 경로를 확보합니다.
