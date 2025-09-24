# 기술 스택 명세서 (MVP)

## 1. 개요
이 문서는 PDF를 EPUB으로 변환하는 서비스의 MVP(Minimum Viable Product) 구축에 사용할 기술 스택을 정의합니다.

## 2. 프론트엔드 (Frontend)
- **프레임워크**: React 18+
- **언어**: TypeScript
- **빌드 도구**: Vite
- **상태 관리**: React Context API / Zustand (경량 상태 관리)
- **UI 라이브러리**: Shadcn/UI 또는 Material-UI (디자인 시스템 기반)
- **데이터 통신**: Supabase-js (Supabase JS Client)

## 3. 백엔드 (Backend)

### 3.1. BaaS (Backend as a Service)
- **플랫폼**: Supabase
- **주요 서비스**:
    - **Authentication**: 이메일/비밀번호, 소셜 로그인을 통한 사용자 인증 및 관리.
    - **Postgres Database**: 작업 내역, 사용자 정보 등 핵심 데이터 저장.
    - **Storage**: 사용자가 업로드한 PDF 원본 및 변환된 EPUB 파일 저장.
    - **Edge Functions**: 스토리지 이벤트(파일 업로드)를 감지하여 FastAPI 처리 서비스를 호출하는 트리거 역할.

### 3.2. 처리 서비스 (Processing Service)
- **언어**: Python 3.12+
- **웹 프레임워크**: FastAPI (변환 작업을 위한 API 엔드포인트 제공)
- **핵심 라이브러리**:
    - **PDF 처리**: pypdf 또는 pdfminer.six
    - **OCR 처리**: PaddleOCR (한국어 특화 모델)
    - **EPUB 생성**: ebooklib
    - **LLM 연동**: OpenRouter (다양한 LLM 모델 접근을 위한 라우터)
        - **API Endpoint**: `https://openrouter.ai/api/v1/chat/completions`

## 4. 개발 및 운영 (DevOps)
- **컨테이너화**: Docker
- **CI/CD**: GitHub Actions
- **코드 품질**:
    - **Frontend**: ESLint, Prettier
    - **Backend**: ruff, mypy
- **테스트**:
    - **Frontend**: Jest, React Testing Library
    - **Backend**: Pytest

## 5. 기술 선택 이유 요약
- **Supabase 중심 설계**: 인증, DB, 스토리지를 Supabase로 통합하여 백엔드 인프라 구축 및 관리 복잡성을 대폭 감소시키고, 프론트엔드에서 직접 데이터를 핸들링하여 개발 속도를 높입니다.
- **FastAPI 역할 축소**: 기존의 모든 로직을 담당하던 FastAPI의 역할을 컴퓨팅 집약적인 PDF 변환 처리에만 집중시켜 서비스 구조를 단순화하고 각 부분의 책임을 명확히 합니다.
- **React & TypeScript**: 타입 안정성과 높은 생산성을 가진 최신 프론트엔드 스택을 활용하여 유지보수성이 뛰어난 UI를 구축합니다.
- **OpenRouter**: 단일 API 엔드포인트를 통해 여러 LLM 제공자의 모델(GPT, Claude, Llama 등)을 유연하게 테스트하고 비용 효율적인 모델을 선택할 수 있는 장점이 있어 채택합니다.
- **PaddleOCR**: 한국어 문서 변환이라는 핵심 요구사항을 충족하기 위해, 오픈소스이면서도 높은 한글 인식률을 제공하는 PaddleOCR을 채택합니다.