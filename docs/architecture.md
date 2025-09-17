# 아키텍처 설계서 (MVP v2)

## 1. 개요
이 문서는 PDF to EPUB 변환 서비스의 아키텍처를 정의합니다. 사용자 등급(무료/유료)을 도입하고, LLM을 활용한 변환 품질 향상을 목표로 합니다.

## 2. 전체 아키텍처

```mermaid
graph TD
    subgraph Client
        A[React Web App]
    end

    subgraph "BaaS (Supabase)"
        B[Auth]
        C[Storage]
        D[Postgres DB]
        E[Edge Function]
    end

    subgraph Backend
        F[FastAPI Processing Service]
        G[LLM API]
        H[Intermediate<br>Markdown Storage]
    end

    A -- Login (Optional) --> B
    A -- Upload PDF --> C
    A -- Write Job Record --> D

    C -- on:upload trigger --> E
    E -- HTTP Request --> F

    F -- 1. Get Job Info --> D
    F -- 2. Read PDF --> C
    F -- 3. Write MD --> H
    F -- 4. Read MD --> H
    F -- 5. Send to LLM --> G
    G -- 6. Return Corrected Text --> F
    F -- 7. Write Corrected MD --> H
    F -- 8. Read Final MD --> H
    F -- 9. Write EPUB --> C
    F -- 10. Update Job Status --> D
```

### 데이터 흐름 (Data Flow)

1.  **사용자 및 파일 업로드**:
    *   **로그인 사용자**: React 앱에서 Supabase Auth로 인증합니다.
    *   **익명 사용자**: 별도 인증 없이 진행합니다.
    *   사용자는 PDF 파일을 Supabase Storage에 업로드하고, 클라이언트는 `conversion_jobs` 테이블에 작업 레코드를 생성합니다. (익명 사용자의 경우 `user_id`는 NULL, `session_id`에 클라이언트 생성 UUID 저장)

2.  **변환 작업 트리거**:
    *   Supabase Edge Function이 Storage 업로드 이벤트를 감지하여 FastAPI 처리 서비스의 API(`/convert`)를 호출합니다. 작업 ID(job_id)를 전달합니다.

3.  **FastAPI 처리 파이프라인**:
    1.  **PDF 분석**: 전달받은 `job_id`로 DB에서 작업 정보를 조회합니다. PDF가 텍스트 기반인지 스캔본인지 분석합니다.
    2.  **1차 추출 (PDF → Markdown)**: PDF를 분석하여 텍스트와 이미지를 추출하고, 중간 단계인 마크다운(.md) 파일로 `Intermediate Markdown Storage`에 저장합니다. 이 때 사용자의 OCR 선택 옵션을 반영합니다.
    3.  **2차 보정 (LLM 호출)**: 저장된 마크다운의 텍스트 콘텐츠를 **LLM API**에 전송하여 문맥 교정 및 OCR 오타 수정을 요청합니다.
    4.  **마크다운 업데이트**: LLM으로부터 받은 보정된 텍스트로 마크다운 파일을 업데이트합니다.
    5.  **최종 생성 (Markdown → EPUB)**: 보정된 마크다운 파일을 기반으로 최종 EPUB 파일을 생성합니다.
    6.  **결과 저장 및 상태 업데이트**: 생성된 EPUB을 Supabase Storage에 업로드하고, `conversion_jobs` 테이블의 `epub_file_url`과 `status`('completed')를 업데이트합니다.

4.  **결과 확인**: React 앱은 Supabase Realtime으로 작업 상태 변경을 감지하고, 'completed' 상태가 되면 사용자에게 다운로드 링크를 제공합니다.

## 3. 컴포넌트 상세

### 3.1. 백엔드 서비스 (Supabase)
- **Database (PostgreSQL)**: 익명 사용자를 지원하도록 스키마가 확장됩니다. RLS 정책은 `user_id`가 일치하거나, `user_id`가 NULL이고 `session_id`가 일치하는 경우에만 접근을 허용하도록 수정됩니다.

### 3.2. 처리 서비스 (FastAPI)
- **역할**: LLM 연동을 포함한 전체 변환 파이프라인을 오케스트레이션합니다.
- **주요 기능**:
    - PDF 분석 및 마크다운으로 1차 변환.
    - **LLM 연동**: 외부 LLM API(예: OpenAI, Gemini)와 통신하여 텍스트 보정.
    - 보정된 마크다운을 EPUB으로 최종 변환.

### 3.3. LLM API
- **역할**: 텍스트의 문맥을 자연스럽게 연결하고 OCR 과정에서 발생한 오타를 수정하여 변환 품질을 향상시킵니다.

## 4. 데이터베이스 스키마 (Supabase)

```sql
-- 변환 작업을 관리하는 테이블
CREATE TABLE public.conversion_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL, -- 익명 사용자를 위해 NULL 허용
    session_id TEXT, -- 익명 사용자를 위한 세션 식별자
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'analyzing', 'processing', 'correcting', 'generating', 'completed', 'failed')),
    progress INTEGER NOT NULL DEFAULT 0,
    file_name TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    original_pdf_url TEXT,
    epub_file_url TEXT,
    intermediate_md_path TEXT, -- 중간 마크다운 파일 경로
    ocr_user_choice TEXT NOT NULL DEFAULT 'auto' CHECK (ocr_user_choice IN ('auto', 'force', 'off')), -- 사용자 OCR 선택
    llm_used BOOLEAN NOT NULL DEFAULT FALSE, -- LLM 보정 사용 여부
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- 익명 사용자 추적을 위한 session_id 인덱스
CREATE INDEX idx_jobs_session_id ON public.conversion_jobs (session_id);

-- Row Level Security (RLS) 활성화
ALTER TABLE public.conversion_jobs ENABLE ROW LEVEL SECURITY;

-- 정책: 로그인 사용자는 자신의 작업만, 익명 사용자는 자신의 세션 작업만 관리 가능
CREATE POLICY "User can manage their own conversion jobs"
ON public.conversion_jobs FOR ALL
USING (
  (auth.uid() = user_id) OR
  (user_id IS NULL AND session_id = current_setting('request.headers.x-session-id', true))
);

-- updated_at 필드 자동 갱신 트리거 (기존과 동일)
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at
BEFORE UPDATE ON public.conversion_jobs
FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();
```

## 5. 보안
- **익명 사용자 접근**: 익명 사용자의 요청은 클라이언트에서 생성한 고유 `session_id`를 HTTP 헤더(`x-session-id`)에 담아 전송하고, RLS 정책을 통해 해당 세션 ID를 가진 작업에만 접근하도록 제한합니다.
- **API 비용 제어**: 무료 사용자의 LLM 및 OCR API 호출 횟수와 사용량을 제한하는 로직을 FastAPI 서비스 내에 구현합니다.
