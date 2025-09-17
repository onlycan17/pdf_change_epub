## 프로젝트 개요

__PDF to EPUB 변환&#xAE30;__&#xB294; PDF 문서를 자동으로 EPUB 전자책 형식으로 변환하는 웹 애플리케이션입니다. OCR 기술과 LLM을 활용하여 텍스트 추출 및 문맥 연결을 지원하며, 프리미엄/무료 모델로 구성된 SaaS 서비스입니다.

### 핵심 가치

- __접근성__: 로그인 없이 기본 변환 기능 제공
- __고급 처리__: DeepSeek-V3.1과 Tesseract.js를 활용한 AI 기반 변환
- __사용자 경험__: 실시간 진행 상황 표시와 직관적인 UI/UX
- __비즈니스 모델__: 광고 수익 + 프리미엄 구독 모델

---

## 🛠 기술 스택

### 프론트엔드

- __React 18__ - 사용자 인터페이스 구축
- __TypeScript__ - 타입 안전성 보장
- __Vite__ - 빠른 개발 서버 및 빌드 도구
- __React Router DOM__ - 페이지 라우팅 관리
- __Lucide React__ - 아이콘 컴포넌트
- __Custom CSS Design System__ - 일관된 디자인 시스템

### 백엔드

- __FastAPI__ - 고성능 Python 웹 프레임워크 (Python 3.10+)
- __Pydantic__ - 데이터 검증 및 직렬화
- __Uvicorn__ - ASGI 서버
- __PostgreSQL__ - 주 데이터베이스
- __Redis__ - 캐싱 및 세션 관리
- __Supabase__ - 실시간 데이터 동기화

### 핵심 라이브러리

- __PDF.js__ - 프론트엔드 PDF 텍스트 및 이미지 추출
- __Tesseract.js v6.0+__ - 프론트엔드 OCR 엔진 (영어 95%, 한글 90% 정확도)
- __PyMuPDF__ - 백엔드 PDF 처리 (고성능)
- __python-magic__ - 파일 타입 자동 감지
- __epub-gen__ - 프론트엔드 EPUB 파일 생성
- __OpenAI API__ - 텍스트 분류 및 요약 (선택적)
- __@supabase/supabase-js__ - Supabase 클라이언트

---

## 📁 프로젝트 구조

```javascript
pdf-to-epub/
├── frontend/                    # React 프론트엔드
│   ├── public/                 # 정적 파일
│   │   ├── favicon.ico
│   │   └── manifest.json
│   ├── src/                    # 소스 코드
│   │   ├── components/         # 재사용 가능한 컴포넌트
│   │   │   ├── common/         # 공통 컴포넌트
│   │   │   │   ├── Button.tsx  # 다양한 스타일의 버튼
│   │   │   │   ├── FileUpload.tsx # 파일 업로드 컴포넌트
│   │   │   │   ├── ProgressTracker.tsx # 진행 상황 추적
│   │   │   │   └── LoadingSpinner.tsx # 로딩 애니메이션
│   │   │   ├── layout/         # 레이아웃 컴포넌트
│   │   │   │   ├── Header.tsx  # 헤더 네비게이션
│   │   │   │   └── MainLayout.tsx # 메인 레이아웃
│   │   │   ├── conversion/     # 변환 관련 컴포넌트
│   │   │   │   ├── PDFViewer.tsx # PDF 미리보기
│   │   │   │   └── EPUBPreview.tsx # EPUB 미리보기
│   │   │   └── premium/        # 프리미엄 관련 컴포넌트
│   │   ├── pages/              # 페이지 컴포넌트
│   │   │   ├── Home.tsx        # 홈 페이지
│   │   │   ├── UploadPage.tsx  # 파일 업로드 페이지
│   │   │   ├── ConvertPage.tsx # 변환 진행 페이지
│   │   │   ├── DownloadPage.tsx # 다운로드 페이지
│   │   │   └── PremiumPage.tsx # 프리미엄 플랜 페이지
│   │   ├── services/           # API 서비스 레이어
│   │   │   ├── api.ts          # Axios API 클라이언트 설정
│   │   │   ├── authService.ts  # 인증 API
│   │   │   └── conversionService.ts # 변환 API
│   │   ├── hooks/              # 커스텀 React 훅
│   │   │   ├── useAuth.ts      # 인증 관리 훅
│   │   │   └── useConversion.ts # 변환 로직 훅
│   │   ├── contexts/           # React Context
│   │   │   └── AppContext.tsx  # 전역 상태 관리
│   │   ├── utils/              # 유틸리티 함수
│   │   │   ├── validators.ts   # 데이터 검증 유틸리티
│   │   │   └── formatters.ts   # 데이터 포맷터
│   │   ├── types/              # TypeScript 타입 정의
│   │   │   └── api.ts          # API 관련 타입
│   │   ├── constants/          # 상수 정의
│   │   │   └── endpoints.ts    # API 엔드포인트
│   │   ├── styles/             # 전역 스타일시트
│   │   │   ├── index.css       # 기본 CSS
│   │   │   └── globals.css     # 전역 변수
│   │   ├── tests/              # 테스트 파일
│   │   │   └── utils/
│   │   └── vite.config.ts      # Vite 설정 파일
│   ├── package.json            # 패키지 매니저 설정
│   └── tsconfig.json           # TypeScript 설정 파일
├── backend/                    # FastAPI 백엔드
│   ├── app/                    # 애플리케이션 코드
│   │   ├── api/                # API 라우트
│   │   │   ├── v1/
│   │   │   │   ├── auth.py     # 인증 API
│   │   │   │   └── conversion.py # 변환 API
│   │   ├── core/               # 핵심 설정
│   │   │   ├── config.py       # 애플리케이션 설정
│   │   │   ├── security.py     # 보안 관련
│   │   │   └── database.py     # 데이터베이스 설정
│   │   ├── services/           # 비즈니스 로직 서비스
│   │   │   ├── pdf_service.py  # PDF 처리 서비스
│   │   │   ├── ocr_service.py  # OCR 처리 서비스
│   │   │   └── conversion_service.py # 변환 오케스트레이션
│   │   ├── models/             # 데이터 모델 (Pydantic)
│   │   │   ├── user.py         # 사용자 모델
│   │   │   └── conversion.py   # 변환 모델
│   │   ├── repositories/       # 데이터 접근 계층
│   │   │   └── conversion_repository.py # 변환 데이터 접근
│   │   ├── tasks/              # 백그라운드 작업 (Celery)
│   │   │   └── conversion_tasks.py # 변환 비동기 작업
│   │   ├── utils/              # 유틸리티 함수
│   │   │   └── file_utils.py   # 파일 처리 유틸리티
│   │   └── main.py             # FastAPI 애플리케이션 엔트리포인트
│   ├── tests/                  # 테스트 파일
│   │   └── api/
│   ├── requirements.txt        # Python 의존성
│   └── alembic.ini            # 데이터베이스 마이그레이션 설정
├── docs/                       # 프로젝트 문서
│   ├── API.md                 # API 명세서
│   ├── DEPLOYMENT.md          # 배포 가이드
│   └── CONTRIBUTING.md        # 기여 가이드
├── .github/                    # GitHub 워크플로우
│   └── workflows/
│       ├── ci.yml             # CI 파이프라인
│       └── deploy.yml         # 배포 파이프라인
├── docker/                     # Docker 설정
│   ├── frontend.Dockerfile     # 프론트엔드 빌드 파일
│   └── backend.Dockerfile      # 백엔드 빌드 파일
├── .env.example               # 환경 변수 예시
├── docker-compose.yml        # Docker Compose 설정
└── README.md                 # 프로젝트 설명서
```

---

## 🎯 아키텍처 원칙

### 1. 계층형 구조 (Layered Architecture)

__프론트엔드__

```javascript
┌─────────────────┐
│   Presentation  │ ← React 컴포넌트 (UI/UX)
├─────────────────┤
│    Business     │ ← Custom Hooks, Services (로직 처리)
├─────────────────┤
│      Data       │ ← API 클라이언트, Context (데이터 관리)
└─────────────────┘
```

__백엔드__

```javascript
┌─────────────────┐
│   API Layer    │ ← FastAPI 라우트, 인터페이스 정의
├─────────────────┤
│ Business Logic │ ← Services, 비즈니스 로직 처리
├─────────────────┤
│   Data Access  │ ← Repositories, 데이터 접근 계층
├─────────────────┤
│ Infrastructure │ ← Database, Cache, 외부 서비스 연동
└─────────────────┘
```

### 2. 프론트엔드 컴포넌트 설계 원칙

- __단일 책임 원칙__: 각 컴포넌트는 하나의 명확한 역할만 수행
- __재사용성__: 공통 컴포넌트는 다양한 페이지에서 재사용 가능하도록 설계
- __상태 관리__: 로컬 상태는 useState, 전역 상태는 Context API 사용
- __성능 최적화__: React.memo, useMemo, useCallback을 통한 렌더링 최적화

### 3. 백엔드 API 설계 원칙

- __RESTful API__: 표준 REST API 설계 가이드라인 준수
- __의존성 주입__: 테스트 용이성을 위해 의존성 주입 패턴 적용
- __비동기 처리__: Celery를 활용한 백그라운드 작업 처리
- __에러 핸들링__: 중앙 집중식 에러 처리 및 로깅

---

## 🚀 개발 가이드라인

### 1. 프론트엔드 컴포넌트 작성 규칙

```typescript
// ✅ 좋은 예시: 명확한 props 타입 정의 및 기본값 설정
interface ButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'base' | 'lg';
  onClick?: () => void;
  disabled?: boolean;
}

const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'base',
  onClick,
  disabled = false
}) => {
  return (
    <button
      className={`btn btn-${variant} btn-${size}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};
```

### 2. 백엔드 API 엔드포인트 작성 규칙

```python
# ✅ 좋은 예시: 명확한 인터페이스 정의 및 에러 처리
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List
from app.services.conversion_service import ConversionService
from app.models.conversion import ConversionRequest, ConversionResponse, ConversionStatus

router = APIRouter(prefix="/api/v1/conversion", tags=["conversion"])

@router.post("/start", response_model=ConversionResponse)
async def start_conversion(
    request: ConversionRequest,
    conversion_service: ConversionService = Depends()
):
    """
    PDF to EPUB 변환 시작 API
    
    - 요청받은 파일을 비동기로 처리
    - 변환 상태를 반환하고 진행률 추적 가능
    """
    try:
        conversion_id = await conversion_service.start_conversion(request)
        return {
            "conversion_id": conversion_id,
            "status": ConversionStatus.PENDING,
            "message": "변환 작업이 시작되었습니다."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="변환 시작 중 오류가 발생했습니다.")

@router.get("/status/{conversion_id}", response_model=ConversionResponse)
async def get_conversion_status(
    conversion_id: str,
    conversion_service: ConversionService = Depends()
):
    """
    변환 상태 조회 API
    
    - 진행 중인 변환 작업의 현재 상태 반환
    - 완료 시 다운로드 링크 제공
    """
    try:
        result = await conversion_service.get_conversion_status(conversion_id)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="변환 작업을 찾을 수 없습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail="상태 조회 중 오류가 발생했습니다.")
```

### 3. 프론트엔드 상태 관리 규칙

- __로컬 상태__: 컴포넌트 내부에서만 사용되는 상태는 `useState` 사용
- __전역 상태__: 여러 컴포넌트에서 공유되는 상태는 `Context API` 사용
- __서버 상태__: 서버와 동기화되는 데이터는 `React Query` 활용
- __파생 데이터__: 계산된 값은 `useMemo`를 통해 최적화

### 4. 백엔드 의존성 주입 및 서비스 패턴

```python
# ✅ 좋은 예시: 의존성 주입을 통한 테스트 용이성 확보
from fastapi import Depends
from app.repositories.conversion_repository import ConversionRepository
from app.services.pdf_service import PDFService

class ConversionService:
    def __init__(
        self,
        pdf_service: PDFService = Depends(),
        conversion_repository: ConversionRepository = Depends()
    ):
        self.pdf_service = pdf_service
        self.conversion_repository = conversion_repository
    
    async def start_conversion(self, request: ConversionRequest) -> str:
        """변환 작업 시작"""
        # 비즈니스 로직 처리
        conversion_id = await self.conversion_repository.create_conversion(request)
        
        # 백그라운드 작업 예약
        conversion_task.delay(conversion_id)
        
        return conversion_id

# 서비스 테스트 시 모의 객체 주입 가능
def test_conversion_service():
    mock_pdf_service = MockPDFService()
    mock_repository = MockConversionRepository()
    
    service = ConversionService(
        pdf_service=mock_pdf_service,
        conversion_repository=mock_repository
    )
    
    # 테스트 수행
```

### 5. 프론트엔드 API 통합 패턴

```typescript
// ✅ 좋은 예시: 중앙화된 API 클라이언트 설정
import axios, { AxiosInstance } from 'axios';

class ApiClient {
  private client: AxiosInstance;
  
  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_URL,
      timeout: 30000,
    });
    
    // 요청 인터셉터
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
    
    // 응답 인터셉터
    this.client.interceptors.response.use(
      (response) => response.data,
      (error) => {
        if (error.response?.status === 401) {
          // 인증 실패 시 처리
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }
  
  // 변환 관련 API 메서드
  async startConversion(file: File, options?: ConversionOptions): Promise<ApiResponse<StartConversionResponse>> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (options) {
      Object.entries(options).forEach(([key, value]) => {
        formData.append(key, String(value));
      });
    }
    
    return this.client.post('/api/v1/conversion/start', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }
  
  async getConversionStatus(conversionId: string): Promise<ApiResponse<ConversionStatusResponse>> {
    return this.client.get(`/api/v1/conversion/status/${conversionId}`);
  }
}

export const apiClient = new ApiClient();
```

### 6. 에러 처리 규칙

```typescript
// ✅ 프론트엔드 구체적인 에러 타입과 사용자 친화적 메시지
enum ConversionErrorType {
  INVALID_FILE = 'INVALID_FILE',
  FILE_TOO_LARGE = 'FILE_TOO_LARGE',
  PROCESSING_FAILED = 'PROCESSING_FAILED',
  NETWORK_ERROR = 'NETWORK_ERROR'
}

class ConversionError extends Error {
  constructor(
    public type: ConversionErrorType,
    public message: string,
    public details?: any
  ) {
    super(message);
    this.name = 'ConversionError';
  }
}

async function startPDFConversion(file: File) {
  try {
    if (!file.type.includes('pdf')) {
      throw new ConversionError(
        ConversionErrorType.INVALID_FILE,
        'PDF 파일만 업로드 가능합니다.'
      );
    }
    
    if (file.size > 50 * 1024 * 1024) { // 50MB 제한
      throw new ConversionError(
        ConversionErrorType.FILE_TOO_LARGE,
        '파일 크기는 50MB를 초과할 수 없습니다.'
      );
    }
    
    const response = await apiClient.startConversion(file);
    return response.data;
  } catch (error) {
    if (error instanceof ConversionError) {
      // 사용자에게 보여줄 친화적 메시지
      alert(error.message);
    } else if (error.response) {
      // 서버 응답 에러
      alert('서비스에 문제가 발생했습니다. 나중에 다시 시도해주세요.');
    } else {
      // 네트워크 에러
      alert('네트워크 연결에 문제가 있습니다.');
    }
    
    // 에러 로깅
    logger.error('PDF 변환 실패', { error, file });
  }
}
```

```python
# ✅ 백엔드 구체적인 에러 타입과 처리
from fastapi import HTTPException
from enum import Enum

class ConversionErrorCode(str, Enum):
  INVALID_FILE_FORMAT = "INVALID_FILE_FORMAT"
  FILE_TOO_LARGE = "FILE_TOO_LARGE"
  PROCESSING_FAILED = "PROCESSING_FAILED"
  STORAGE_ERROR = "STORAGE_ERROR"

class ConversionException(HTTPException):
    def __init__(self, status_code: int, code: ConversionErrorCode, detail: str):
        super().__init__(status_code=status_code, detail={
            "code": code,
            "message": detail,
            "timestamp": datetime.utcnow().isoformat()
        })

# API 라우트에서의 사용 예시
@router.post("/start")
async def start_conversion(request: ConversionRequest):
    try:
        # 파일 형식 검증
        if not request.file_type.endswith('.pdf'):
            raise ConversionException(
                status_code=400,
                code=ConversionErrorCode.INVALID_FILE_FORMAT,
                detail="PDF 파일만 업로드 가능합니다."
            )
        
        # 파일 크기 검증
        if request.file_size > 50 * 1024 * 1024:  # 50MB
            raise ConversionException(
                status_code=400,
                code=ConversionErrorCode.FILE_TOO_LARGE,
                detail="파일 크기는 50MB를 초과할 수 없습니다."
            )
        
        # 변환 서비스 호출
        conversion_id = await conversion_service.start_conversion(request)
        return {"conversion_id": conversion_id}
        
    except ConversionException:
        raise  # 이미 적절한 형태이므로 그대로 전달
    except Exception as e:
        # 예상치 못한 에러
        logger.error("변환 시작 실패", error=str(e))
        raise ConversionException(
            status_code=500,
            code=ConversionErrorCode.PROCESSING_FAILED,
            detail="변환 처리 중 오류가 발생했습니다."
        )
```

---

## 🔧 개발 환경 설정

### 사전 요구사항

- __Node.js 18+__ (프론트엔드)
- __Python 3.10+__ (백엔드)
- __npm 또는 yarn__
- __VS Code__ (권장 확장자: ESLint, Prettier, Python)
- __Docker__ (개발 환경 구성용)

### 설치 절차

백엔드 설정:

```bash
# 1. 백엔드 디렉토리로 이동
cd backend

# 2. Python 가상 환경 생성
python -m venv venv

# 3. 가상 환경 활성화
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate     # Windows

# 4. 의존성 설치
pip install -r requirements.txt

# 5. 데이터베이스 마이그레이션
alembic upgrade head

# 6. 백엔드 서버 실행 (개발 모드)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

프론트엔드 설정:

```bash
# 1. 프론트엔드 디렉토리로 이동
cd frontend

# 2. 의존성 설치
npm install

# 3. 환경 변수 설정 (예시)
cp .env.example .env
# .env 파일에 필요한 변수 설정

# 4. 개발 서버 실행
npm run dev

# 5. 빌드 (프로덕션용)
npm run build
```

전체 애플리케이션 실행 (Docker):

```bash
# 1. Docker Compose로 전체 서비스 시작
docker-compose up -d

# 2. 로그 확인
docker-compose logs -f

# 3. 서비스 스톱
docker-compose down
```

### 코드 품질 관리

프론트엔드:

```bash
# 코드 형식화 및 린팅 실행 (프론트엔드)
cd frontend
npm run check

# 개발 중 실시간 코드 검사
npm run lint -- --watch

# 타입 체크만 실행
npm run typecheck

# 테스트 실행
npm test
```

백엔드:

```bash
# 코드 형식화 및 린팅 실행 (백엔드)
cd backend

# 코드 스타일 검사
flake8 app/

# 정적 타입 분석 (mypy 사용)
mypy app/

# 테스트 실행
pytest tests/

# 보안 취약점 스캔 (bandit 사용)
bandit -r app/
```

---

## 📊 성능 최적화 전략

### 1. 프론트엔드 최적화

- __코드 스플리팅__: `React.lazy`와 `Suspense`를 통한 라우트별 코드 분할
- __이미지 최적화__: `next/image` 대신 `react-lazyload`와 WebP 형식 변환
- __가상 렌더링__: 긴 목록은 `react-window`로 가상 렌더링
- __캐싱 전략__: `React Query`를 활용한 API 응답 캐싱

### 2. 백엔드 최적화

- __비동기 처리__: Celery를 활용한 백그라운드 작업
- __DB 인덱싱__: 쿼리 성능 향상을 위한 적절한 인덱스 생성
- __캐싱__: Redis를 활용한 자주 사용되는 데이터 캐싱
- __미들웨어 최적화__: 요청/응답 압축 및 지연 시간 측정

### 3. API 성능 최적화

- __요청 취소__: 컴포넌트 언마운트 시 진행 중인 요청 취소 (AbortController)
- __로딩 상태__: 사용자 경험을 위한 스켈레톤 UI 제공
- __에러 리트라이__: 일시적 네트워크 오류 시 자동 재시도 (axios-retry)
- __배치 처리__: 여러 작업을 한 번에 요청하여 오버헤드 감소

---

## 🔐 보안 및 개인정보 보호

### 1. 프론트엔드 보안

- __XSS 방어__: 사용자 입력 값은 항상 이스케이프 처리
- __CSRF 보호__: 백엔드와의 통신 시 CSRF 토큰 사용
- __민감한 데이터__: `localStorage` 대신 `sessionStorage` 사용 및 만료 시간 설정
- __파일 보안__: 업로드된 파일의 크기 및 형식 제한 및 검증

### 2. 백엔드 보안

- __입력 검증__: Pydantic을 통한 모든 요청 데이터의 유효성 검사
- __SQL 인젝션 방어__: ORM 사용 (SQLAlchemy) 또는 파라미터화된 쿼리
- __인증/권한__: JWT 토큰 기반 인증 및 RBAC 권한 모델
- __파일 처리__: 안전한 파일 저장소 사용 및 악의적인 파일 검사

### 3. 통신 보안

- __HTTPS__: 모든 API 통신은 HTTPS를 통한 암호화 강제
- __CORS__: 적절한 CORS 정책 설정 (프론트엔드 도메인 허용)
- __Rate Limiting__: API 엔드포인트별 요청 빈도 제한
- __헤더 보안__: security 관련 HTTP 헤더 설정 (CSP, HSTS 등)

---

## 📈 모니터링 및 로깅

### 1. 로깅 전략

```typescript
// ✅ 프론트엔드 구조화된 로깅 예시 (React 커스텀 훅)
import { useCallback } from 'react';

interface LogData {
  action: string;
  category?: string;
  metadata?: Record<string, any>;
}

export function useLogger() {
  const logEvent = useCallback((data: LogData) => {
    if (process.env.NODE_ENV === 'development') {
      console.group(`[Event] ${data.action}`);
      console.log('Category:', data.category);
      console.log('Metadata:', data.metadata);
      console.log('Timestamp:', new Date().toISOString());
      console.groupEnd();
    }
    
    // 프로덕션 환경에서는 Analytics 서비스로 전송
    if (process.env.NODE_ENV === 'production') {
      analytics.track(data.action, data);
    }
  }, []);
  
  return { logEvent };
}
```

```python
# ✅ 백엔드 구조화된 로깅 예시 (Python Structured Logging)
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def log_conversion_start(conversion_id: str, file_info: dict):
    """변환 시작 로깅"""
    logger.info(
        "Conversion task started",
        extra={
            "task_id": conversion_id,
            "file_name": file_info.get("filename"),
            "file_size": file_info.get("size"),
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

def log_conversion_error(conversion_id: str, error: Exception):
    """변환 오류 로깅"""
    logger.error(
        "Conversion task failed",
        extra={
            "task_id": conversion_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat(),
        },
        exc_info=True  # 스택 트레이스 포함
    )
```

### 2. 성능 모니터링

- __프론트엔드__: Web Vitals 메트릭 추적 (LCP, FID, CLS)
- __백엔드__: Prometheus를 통한 요청 처리 시간 및 에러율 모니터링
- __인프라__: CPU, 메모리, 디스크 사용량 모니터링
- __사용자 경험__: Core Web Vitals 개선 및 사용자 행동 분석

### 3. 에러 추적

```typescript
// ✅ 프론트엔드 global error boundary
class ErrorBoundary extends React.Component<{ children: React.ReactNode }> {
  state = { hasError: false, errorInfo: null as Error | null };
  
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, errorInfo: error };
  }
  
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // 에러 추적 서비스에 전송
    logErrorToService(error, errorInfo);
    
    // 개발 환경에서는 콘솔에 에러 표시
    if (process.env.NODE_ENV === 'development') {
      console.error('Error caught by ErrorBoundary:', error, errorInfo);
    }
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorFallbackComponent error={this.state.errorInfo} />;
    }
    
    return this.props.children;
  }
}
```

---

## 🚀 배포 전략

### 1. 프론트엔드 배포

```bash
# 프로덕션 빌드 (프론트엔드)
cd frontend
npm run build

# Vite 기반 배포 (정적 파일 생성)
vite build --mode production

# 결과물: dist/ 디렉토리
```

### 2. 백엔드 배포

```bash
# 프로덕션 빌드 (백엔드)
cd backend

# Docker 이미지 빌드
docker build -t pdf-to-epub-backend:latest .

# Python 패키징 (선택 사항)
pip install -r requirements.txt
pyinstaller --onefile app/main.py

# 결과물: main.exe (Windows) 또는 main (Linux/macOS)
```

### 3. Docker Compose를 통한 전체 배포

```yaml
# docker-compose.yml 예시
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    environment:
      - VITE_API_URL=http://backend:8000
    depends_on:
      - backend
    
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/pdf_to_epub
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: pdf_to_epub
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

---

## 🤝 기여 가이드라인

### 1. 브랜치 전략

```javascript
main (프로덕션)
├── develop (개발 브랜치, 기본 개발 진행 지점)
├── feature/기능이름 (새로운 기개발 브랜치)
├── bugfix/버그수정 (버그 수정 브랜치)
├── hotfix/긴급수정 (긴급 버그 수정 브랜치)
└── release/버전명 (릴리스 준비 브랜치)
```

### 2. 커밋 메시지 규칙 (한글)

```bash
# ✅ 좋은 예시: 타입과 설명이 명확한 커밋 메시지 (한글)
기능(pdf-processor): 스캔된 PDF 파일의 OCR 처리 기능 추가
버그(conversion): 빈 페이지 처리 시 발생하는 오류 수정
문서(readme): 설치 및 설정 방법 갱신
스타일(ui): 버튼 디자인 및 애니메이션 개선
테스트(api): 변환 API 단위 테스트 추가
코드관리(deps): tesseract.js 라이브러리 업데이트

# ❌ 나쁜 예시: 모호한 커밋 메시지
수정
변경사항 적용
새 기능 추가
```

### 3. 커밋 메시지 타입 접두사 (한글)

- __기능__: 새로운 기능 추가
- __버그__: 버그 수정
- __문서__: 문서 변경
- __스타일__: 코드 포맷팅, 세미콜론 추가 등 변경
- __리팩토링__: 코드 리팩토링 (기능 변경 없음)
- __테스트__: 테스트 코드 추가/수정
- __코드관리__: 의존성 업데이트, 설정 변경 등

### 4. PR (Pull Request) 작성 규칙 (한글)

```markdown
## 제목: [기능] PDF 처리에 OCR 기능 추가

### 변경 사항
- Tesseract.js v6.0+를 통한 OCR 처리 기능 추가
- 스캔된 PDF 문서의 텍스트 추출 지원
- 한국어/영어 OCR 정확도 개선
- 사용자 설정에서 OCR 언어 옵션 추가

### 테스트 방법
1. 한글 영문이 섞인 스캔된 PDF 파일 업로드
2. 한국어/영어 옵션별 텍스트 추출 결과 확인
3. 복잡한 레이아웃의 PDF에서 텍스트 정확도 검증

### 관련 이슈
- Fixes #123
- Related to #456
- Requires backend changes in auth service

### 리뷰어 요청
@frontend-developer @backend-developer

### 체크리스트
- [ ] 테스트 코드 작성 및 통과 확인
- [ ] 기존 기능에 영향이 없는지 테스트
- [ ] 코드 스타일 가이드라인 준수 확인
- [ ] 필요한 문서 업데이트 완료
```

### 5. PR 상태 규칙

- __🟢 리뷰 요청__: 코드 완성되어 리뷰 요청 가능
- __🟡 개발 중__: 개발 중인 상태 (리뷰 요청 불가)
- __🔴 수정 필요__: 수정 필요 사항 있음
- __⏳ 피드백 대기__: 리뷰어 피드백 대기 중

### 6. 브랜치 명명 규칙

```bash
# ✅ 좋은 예시: 의미 있는 브랜치 이름 (한글)
feature/ocr-처리-기능추가
bugfix/빈-페이지-오류수정
hotfix/보안-취약점-패치

# ❌ 나쁜 예시: 모호한 브랜치 이름
new-feature
bugfix
update
```

### 7. 코드 리뷰 가이드라인

1. __코드 품질__: ESLint, Prettier (프론트엔드) / flake8, black (백엔드) 규칙 준수 여부 확인
2. __기능 검증__: 요구사항에 맞게 기능이 구현되었는지 확인
3. __성능 고려__: 불필요한 렌더링, 중복 계산 등 성능 문제 확인
4. __보안__: 민감한 정보 노출, 보안 취약점 등 확인
5. __테스트__: 단위/통합 테스트 코드가 포함되어 있는지 확인
6. __문서__: API 문서, 주석 등 필요한 문서가 업데이트되었는지 확인

### 8. 릴리스 프로세스 (한글)

```bash
# 1. feature 브랜치에서 개발 완료
git checkout -b feature/ocr-처리 develop

# 2. 개발 완료 후 PR 생성 및 병합
git checkout develop
git merge --no-ff feature/ocr-처리

# 3. 테스트 완료 후 release 브랜치 생성
git checkout -b release/v1.2.0 develop

# 4. 릴리스 브랜치에서 최종 테스트 후 main 병합
git checkout main
git merge --no-ff release/v1.2.0

# 5. 태그 생성 (한글 메시지)
git tag -a v1.2.0 -m "릴리스: OCR 처리 기능 추가"

# 6. hotfix 브랜치는 main에서 직접 생성
git checkout -b hotfix/보안-수정 main
```

### 9. 이슈 (Issue) 작성 규칙 (한글)

```markdown
## 제목: [버그] PDF 변환 시 빈 페이지 처리 오류

### 재현 단계
1. 특정 PDF 파일 업로드 (빈 페이지 포함)
2. 변환 시작 버튼 클릭
3. 빈 페이지 처리 과정에서 오류 발생

### 기대 결과
- 빈 페이지가 정상적으로 처리되어 변환 완료

### 실제 결과
- 오류 메시지: "Cannot process empty page"
- 변환 프로세스 중단

### 환경 정보
- OS: macOS 12.0
- 브라우저: Chrome 96.0
- 백엔드 버전: v1.1.2
- 프론트엔드 버전: v1.3.0

### 추가 정보
[첨부 파일: 오류가 발생한 PDF 파일]
```

### 10. GitHub Actions 워크플로우

```yaml
# .github/workflows/ci.yml 예시 (프론트엔드 + 백엔드 CI)
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ develop ]

jobs:
  # 프론트엔드 테스트
  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          
      - name: Install dependencies
        working-directory: ./frontend
        run: npm install
        
      - name: Run frontend tests
        working-directory: ./frontend
        run: npm test
        
      - name: Build frontend
        working-directory: ./frontend
        run: npm run build
        
      - name: Run linting (프론트엔드)
        working-directory: ./frontend
        run: npm run lint

  # 백엔드 테스트
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        working-directory: ./backend
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          
      - name: Run backend tests
        working-directory: ./backend
        run: pytest
        
      - name: Check types (mypy)
        working-directory: ./backend
        run: mypy app/
        
      - name: Security scan (bandit)
        working-directory: ./backend
        run: bandit -r app/

  # 통합 테스트
  integration-test:
    needs: [frontend-test, backend-test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run integration tests
        run: |
          # 통합 테스트 실행 스크립트
          echo "Running integration tests..."
          
      - name: Build Docker images
        run: |
          docker-compose build
          
      - name: Run smoke tests with Docker
        run: |
          docker-compose up -d
          sleep 10
          # 간단한 API 테스트 실행
          curl -f http://localhost:8000/api/v1/health || exit 1
```

### 11. 코드 컨벤션 강제 도구

프론트엔드:

```json
// package.json scripts 예시
{
  "scripts": {
    "lint": "eslint src --ext .ts,.tsx",
    "lint:fix": "eslint src --ext .ts,.tsx --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx,json,css,md}\"",
    "format:check": "prettier --check \"src/**/*.{ts,tsx,json,css,md}\"",
    "type-check": "tsc --noEmit"
  }
}

// .prettierrc 예시
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2
}

// .eslintrc.cjs 예시
module.exports = {
  extends: [
    'eslint:recommended',
    '@typescript-eslint/recommended',
    'plugin:react-hooks/recommended'
  ],
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint'],
  env: {
    browser: true,
    node: true
  },
  rules: {
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'react-hooks/exhaustive-deps': 'warn'
  }
};
```

백엔드:

```ini
# pyproject.toml 예시 (modern Python)
[tool.black]
line-length = 88
target-version = ['py310']
include = '.pyi?$'
extend-exclude = '''
/(
  # directories
  .eggs
  | .git
  | .hg
  | .mypy_cache
  | .tox
  | .venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.flake8]
max-line-length = 88
extend-ignore = ["E203", "W503"]
exclude = [
    ".git",
    "__pycache__",
    "build",
    "dist",
    ".venv"
]
```

### 12. 보안 규칙

1. __비밀 키 관리__: GitHub Secrets를 통한 민감 정보 관리
2. __의존성 취약점__: Dependabot을 통한 자동 보안 업데이트
3. __코드 스캔__: CodeQL을 통한 취약점 자동 검사
4. __권한 관리__: Collaborator 권한 최소 원칙 적용
5. __CI/CD 보안__: 환경 변수 및 액세스 토큰 관리
