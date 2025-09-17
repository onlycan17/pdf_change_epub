# KILO_CODE.md

## 프로젝트 개요

**PDF to EPUB 변환기**는 PDF 문서를 자동으로 EPUB 전자책 형식으로 변환하는 웹 애플리케이션입니다. OCR 기술과 LLM을 활용하여 텍스트 추출 및 문맥 연결을 지원하며, 프리미엄/무료 모델로 구성된 SaaS 서비스입니다.

### 핵심 가치
- **접근성**: 로그인 없이 기본 변환 기능 제공
- **고급 처리**: DeepSeek-V3.1과 Tesseract.js를 활용한 AI 기반 변환
- **사용자 경험**: 실시간 진행 상황 표시와 직관적인 UI/UX
- **비즈니스 모델**: 광고 수익 + 프리미엄 구독 모델

---

## 🛠 기술 스택

### 프론트엔드
- **React 18** - 사용자 인터페이스 구축
- **TypeScript** - 타입 안전성 보장
- **Vite** - 빠른 개발 서버 및 빌드 도구
- **React Router DOM** - 페이지 라우팅 관리
- **Lucide React** - 아이콘 컴포넌트
- **Custom CSS Design System** - 일관된 디자인 시스템

### 백엔드 인프라
- **Supabase** - 데이터베이스, 인증, 파일 스토리지
- **OpenRouter API** - DeepSeek-V3.1 LLM 모델 연동
- **Stripe** - 결제 처리 시스템

### 핵심 라이브러리
- **PDF.js** - PDF 텍스트 및 이미지 추출
- **Tesseract.js v6.0+** - OCR 엔진 (영어 95%, 한글 90% 정확도)
- **epub-gen** - EPUB 파일 생성
- **@supabase/supabase-js** - Supabase 클라이언트

---

## 📁 프로젝트 구조

```
src/
├── components/               # 재사용 가능한 컴포넌트
│   ├── common/             # 공통 컴포넌트
│   │   ├── Button.tsx      # 다양한 스타일의 버튼 컴포넌트
│   │   ├── FileUpload.tsx  # 파일 업로드 컴포넌트
│   │   ├── ProgressTracker.tsx # 진행 상황 추적 컴포넌트
│   │   └── UsageIndicator.tsx  # 사용량 표시 컴포넌트
│   ├── layout/             # 레이아웃 컴포넌트
│   │   ├── Header.tsx      # 헤더 네비게이션
│   │   └── MainLayout.tsx  # 메인 레이아웃 템플릿
│   └── conversion/         # 변환 관련 컴포넌트
├── pages/                  # 페이지 컴포넌트
│   ├── Home.tsx           # 홈 페이지 (진입점)
│   ├── FileUpload.tsx     # 파일 업로드 페이지
│   ├── ConversionProgress.tsx # 변환 진행 상황
│   ├── Download.tsx       # 다운로드 페이지
│   └── Premium.tsx        # 프리미엄 플랜 페이지
├── services/              # API 서비스 레이어
│   ├── pdfProcessor.ts    # PDF 처리 엔진
│   ├── conversionOrchestrator.ts # 변환 오케스트레이션
│   ├── ocrProcessor.ts    # OCR 처리 서비스
│   ├── markdownConverter.ts # 마크다운 변환기
│   └── supabase.ts        # Supabase 클라이언트
├── hooks/                 # 커스텀 React 훅
│   ├── useAuth.ts         # 인증 관리 훅
│   └── usePDFConversion.ts # PDF 변환 로직 훅
├── contexts/              # React Context
│   ├── AuthContext.tsx    # 사용자 인증 컨텍스트
│   └── ThemeContext.tsx   # 테마 관리 컨텍스트
├── utils/                 # 유틸리티 함수
│   ├── logger.ts          # 로깅 유틸리티
│   ├── error.ts           # 에러 처리 유틸리티
│   └── mappers.ts         # 데이터 매핑 유틸리티
├── types/                 # TypeScript 타입 정의
│   └── conversion.ts      # 변관련 타입 인터페이스
├── constants/             # 상수 정의
│   ├── status.ts          # 상태 코드 및 메시지
│   └── stripe.ts          # Stripe 관련 상수
├── styles/                # 전역 스타일시트
│   ├── index.css          # 기본 CSS
│   ├── design-system.css  # 디자인 시스템
│   ├── dark-mode.css      # 다크 모드 스타일
│   └── responsive.css     # 반응형 디자인
└── App.tsx                # 메인 앱 컴포넌트
```

---

## 🎯 아키텍처 원칙

### 1. 계층형 구조 (Layered Architecture)
```
┌─────────────────┐
│   Presentation  │ ← React 컴포넌트 (UI/UX)
├─────────────────┤
│    Business     │ ← Services, Hooks (로직 처리)
├─────────────────┤
│      Data       │ ← Supabase, APIs (데이터 관리)
└─────────────────┘
```

### 2. 컴포넌트 설계 원칙
- **단일 책임 원칙**: 각 컴포넌트는 하나의 명확한 역할만 수행
- **재사용성**: 공통 컴포넌트는 다양한 페이지에서 재사용 가능하도록 설계
- **상태 관리**: 로컬 상태는 useState, 전역 상태는 Context API 사용

### 3. 서비스 레이어 설계
- **의존성 주입**: 테스트 용이성을 위해 의존성 주입 패턴 적용
- **싱글톤 패턴**: 서비스 인스턴스는 싱글톤으로 관리
- **에러 핸들링**: 중앙 집중식 에러 처리 및 로깅

---

## 🚀 개발 가이드라인

### 1. 컴포넌트 작성 규칙
```typescript
// ✅ 좋은 예시: 명확한 props 타입 정의 및 기본값 설정
interface ButtonProps {
  children: React.ReactNode
  variant?: 'primary' | 'secondary'
  size?: 'sm' | 'base' | 'lg'
  onClick?: () => void
}

const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'base',
  onClick
}) => {
  // 컴포넌트 로직
}
```

### 2. 서비스 레이어 작성 규칙
```typescript
// ✅ 좋은 예시: 명확한 인터페이스 정의 및 에러 처리
export interface ConversionOptions {
  useOCR?: boolean
  ocrLanguage?: string
  markdownOptions?: MarkdownOptions
}

export class ConversionService {
  async convertFile(
    fileId: string,
    options: ConversionOptions
  ): Promise<ConversionResult> {
    try {
      // 비즈니스 로직
      return result
    } catch (error) {
      logger.error('변환 실패', error)
      throw new Error(`변환 실패: ${error.message}`)
    }
  }
}
```

### 3. 상태 관리 규칙
- **로컬 상태**: 컴포넌트 내부에서만 사용되는 상태는 `useState` 사용
- **전역 상태**: 여러 컴포넌트에서 공유되는 상태는 `Context API` 사용
- **파생 데이터**: 계산된 값은 `useMemo`를 통해 최적화

### 4. 에러 처리 규칙
```typescript
// ✅ 좋은 예시: 구체적인 에러 타입과 사용자 친화적 메시지
try {
  const result = await pdfProcessor.processPDF(file)
} catch (error) {
  if (error instanceof ValidationError) {
    // 사용자 입력 오류
    setError('올바른 PDF 파일을 선택해주세요.')
  } else if (error instanceof ProcessingError) {
    // 처리 중 오류
    setError('파일 처리 중 문제가 발생했습니다.')
  } else {
    // 기타 오류
    setError('알 수 없는 오류가 발생했습니다.')
  }
}
```

---

## 🔧 개발 환경 설정

### 사전 요구사항
- **Node.js 18+** (LTS 버전 권장)
- **npm 또는 yarn**
- **VS Code** (권장 확장자: ESLint, Prettier, TypeScript)

### 설치 절차
```bash
# 1. 프로젝트 클론
git clone <repository-url>
cd pdf-to-epub

# 2. 의존성 설치
npm install

# 3. 환경 변수 설정 (예시)
cp .env.example .env
# .env 파일에 필요한 변수 설정

# 4. 개발 서버 실행
npm run dev
```

### 코드 품질 관리
```bash
# 코드 형식화 및 린팅 실행
npm run check

# 개발 중 실시간 코드 검사
npm run lint -- --watch

# 타입 체크만 실행
npm run typecheck
```

---

## 📊 성능 최적화 전략

### 1. PDF 처리 최적화
- **스트리밍 처리**: 대용량 파일(300MB)은 페이지별 스트리밍 처리
- **메모리 관리**: Web Workers를 활용한 백그라운드 처리
- **캐싱 전략**: 중간 결과물의 캐싱으로 재처리 방지

### 2. UI 성능 최적화
- **가상 렌더링**: 긴 목록은 `react-window`로 가상 렌더링
- **이미지 최적화**: 추출된 이미지는 WebP 형식으로 변환
- **코드 스플리팅**: 라우트별 코드 분할로 초기 로딩 속도 개선

### 3. API 성능 최적화
- **요청 취소**: 컴포넌트 언마운트 시 진행 중인 요청 취소
- **로디 상태**: 사용자 경험을 위한 스켈레톤 UI 제공
- **에러 리트라이**: 일시적 네트워크 오류 시 자동 재시도

---

## 🔐 보안 및 개인정보 보호

### 1. 파일 처리 보안
- **임시 저장**: 업로드된 파일은 24시간 후 자동 삭제
- **파일 검증**: 업로드 전 파일 형식 및 크기 검사
- **접근 제어**: 사용자별 파일 접근 권한 관리

### 2. API 보안
- **인증**: Supabase Auth를 통한 안전한 사용자 인증
- **권한 관리**: Row Level Security(RLS) 적용
- **API 키**: 민감한 API 키는 서버 사이드에서만 관리

### 3. 개인정보 보호
- **최소 수집**: 사용자 데이터는 서비스 제공에 필요한 최소한으로 수집
- **암호화 통신**: HTTPS를 통한 모든 통신 암호화
- **GDPR 준수**: 개인정보 처리 방침 명시 및 동의 획득

---

## 📈 모니터링 및 로깅

### 1. 로깅 전략
```typescript
// ✅ 구조화된 로깅 예시
logger.info('PDF 처리 시작', {
  fileName: file.name,
  fileSize: file.size,
  userId: user?.id,
  timestamp: new Date().toISOString()
})

logger.error('변환 실패', {
  error: error.message,
  stack: error.stack,
  context: { fileId, conversionId }
})
```

### 2. 성능 모니터링
- **처리 시간**: 각 단계별 처리 시간 측정
- **메모리 사용**: 웹키퍼 메모리 사용량 모니터링
- **에러율**: 변환 실패율 추적 및 알림

### 3. 사용자 행동 분석
- **사용량 추적**: 무료/프리미엄 사용자별 기능 사용 패턴
- **이탈률**: 특정 단계에서의 이탈률 분석
- **성과 지표**: 변환 성공률, 평균 처리 시간 등

---

## 🚀 배포 전략

### 1. 프론트엔드 배포
```bash
# 프로덕션 빌드
npm run build

# Vercel 배포 (권장)
npm install -g vercel
vercel --prod
```

### 2. 백엔드 배포
- **Supabase**: 자동 배포되며, SQL 스크립트로 초기 설정
- **배포 파이프라인**: GitHub Actions를 통한 자동 배포

### 3. 환경별 설정
- **개발**: 디버깅용 로깅 활성화, 개인정보 가명화
- **스테이징**: 프로덕션과 동일한 환경, 테스트용 가상 데이터
- **프로덕션**: 최소 로깅, 성능 모니터링 활성화

---

## 🤝 기여 가이드라인

### 1. 브랜치 전략
```
main (프로덕션)
├── develop (개발 브랜치)
├── feature/기능이름
├── bugfix/버그수정
└── hotfix/긴급수정
```

### 2. 커밋 메시지 규칙
```bash
# ✅ 좋은 예시: 타입과 설명이 명확한 커밋 메시지
feat(pdf-processor): add OCR processing for scanned PDFs
fix(conversion): handle empty text pages gracefully
docs(readme): update installation instructions
style(button): adjust primary button hover state
test(conversion): add unit tests for markdown conversion
chore(deps): update tesseract.js to v6.0.1
```

### 3. 코드 리뷰 프로세스
1. **PR 생성**: 명확한 설명과 테스트 결과 포함
2. **리뷰 요청**: 관련 기능 영역의 개발자에게 리뷰 요청
3. **수정 및 병합**: 피드백 반영 후 메인 브랜치에 병합

---

## 📞 지원 및 문의

### 기술 지원 채널
- **GitHub Issues**: 버그 리포트 및 기능 요청
- **이메일**: 개발팀 연락처 (문서 참조)
- **커뮤니티**: 사용자 그룹 및 토론 포럼

### 문서 업데이트
- **PRD**: 제품 요구사항은 `docs/PRD.md`에 관리
- **기능 명세**: 기술적 세부사항은 `docs/functional_spec.md`에 관리
- **UI 명세**: 디자인 가이드는 `docs/ui_spec.md`에 관리

---

## 📝 명명 규칙 (Naming Conventions)

### 1. 변수명 (Variable Names)
- **카멜 케이스 사용**: `firstName`, `userProfile`, `pdfFilePath`
- **의미 있는 이름**: `isProcessing` (boolean), `conversionProgress` (number)
- **배열 변수명**: `userList`, `fileArray`, `conversionResults`
- **객체 변수명**: `userInfo`, `pdfSettings`, `conversionOptions`
- **상수는 대문자 스네이크 케이스**: `MAX_FILE_SIZE`, `API_BASE_URL`

### 2. 함수명 (Function Names)
- **카멜 케이스 사용**: `getUserData()`, `processPDF()`, `convertToEPUB()`
- **동사로 시작**: `calculateTotal()`, `validateInput()`, `handleUpload()`
- **이벤트 핸들러**: `handleButtonClick()`, `onFileChange()`
- **비동기 함수**: `fetchUserData()`, `processPDFAsync()`, `convertToEPUBAsync()`
- **콜백 함수**: `onComplete()`, `onError()`, `onProgress()`

### 3. 클래스명 (Class Names)
- **파스칼 케이스 사용**: `PDFProcessor`, `UserManager`, `ConversionService`
- **명사로 시작**: `FileUploader`, `DataValidator`, `APIClient`
- **추상 클래스는 'Abstract' 접두사**: `AbstractConverter`, `BaseProcessor`
- **인터페이스는 'I' 접두사 또는 명사**: `IUserService`, `ConversionInterface`

### 4. 컴포넌트명 (Component Names)
- **파스칼 케이스 사용**: `UserProfile`, `FileUpload`, `ConversionProgress`
- **명사로 시작**: `ProgressBar`, `ButtonGroup`, `FileList`
- **페이지 컴포넌트**: `HomePage`, `UploadPage`, `DownloadPage`
- **모달 컴포넌트**: `ConfirmModal`, `ErrorDialog`, `InfoPopup`

### 5. 파일명 (File Names)
- **카멜 케이스 또는 하이픈 사용**: `user-service.ts`, `file-processor.js`
- **의미 있는 이름**: `pdf-converter.ts`, `auth-manager.ts`
- **테스트 파일**: `user-service.test.ts`, `pdf-converter.spec.js`
- **컴포넌트 파일**: `UserProfile.tsx`, `FileUpload.jsx`

### 6. 인터페이스명 (Interface Names)
- **파스칼 케이스 사용**: `ConversionOptions`, `UserCredentials`
- **명사로 시작**: `FileMetadata`, `APIClientConfig`
- **타입 별칭은 'Type' 접두사**: `ConversionResultType`, `UserDataType`

### 7. 타입명 (Type Names)
- **파스칼 케이스 사용**: `ConversionStatus`, `FileType`
- **열거형은 'Enum' 접두사**: `FileFormatEnum`, `ProcessingStatusEnum`

### 8. 상수명 (Constant Names)
- **대문자 스네이크 케이스**: `MAX_FILE_SIZE`, `API_TIMEOUT`
- **그룹화된 상수는 객체로 관리**:
```typescript
export const API_CONFIG = {
  BASE_URL: 'https://api.example.com',
  TIMEOUT: 30000,
  RETRY_COUNT: 3
}
```

### 9. 이벤트명 (Event Names)
- **카멜 케이스 사용**: `fileUploaded`, `conversionComplete`
- **동사로 시작**: `onProgressUpdate`, `onErrorOccurred`

### 10. CSS 클래스명 (CSS Class Names)
- **하이픈 케이스 사용**: `user-profile`, `file-upload`
- **BEM 방식 권장**:
```css
/* Block */
.user-profile {}

/* Element */
.user-profile__avatar {}
.user-profile__name {}

/* Modifier */
.user-profile--active {}
.user-profile__avatar--large {}
```

---

## 🐙 GitHub 사용 규칙

### 1. 브랜치 관리 규칙
```
main (프로덕션 브랜치, 항상 안정 상태)
├── develop (개발 브랜치, 다음 릴리스를 위한 기능 통합)
├── feature/기능이름 (새로운 기개발 브랜치)
├── bugfix/버그수정 (버그 수정 브랜치)
├── hotfix/긴급수정 (긴급 버그 수정 브랜치)
└── release/버전명 (릴리스 준비 브랜치)
```

### 2. 커밋 메시지 규칙
```bash
# ✅ 좋은 예시: 타입과 설명이 명확한 커밋 메시지
feat(pdf-processor): add OCR processing for scanned PDFs
fix(conversion): handle empty text pages gracefully
docs(readme): update installation instructions
style(button): adjust primary button hover state
test(conversion): add unit tests for markdown conversion
chore(deps): update tesseract.js to v6.0.1

# ❌ 나쁜 예시: 모호한 커밋 메시지
Fix stuff
Update code
Add new features
```

### 3. 커밋 메시지 타입 접두사
- **feat**: 새로운 기능 추가
- **fix**: 버그 수정
- **docs**: 문서 변경
- **style**: 코드 포맷팅, 세미콜론 추가 등 변경
- **refactor**: 코드 리팩토링 (기능 변경 없음)
- **test**: 테스트 코드 추가/수정
- **chore**: 빌드, 패키지 매니저 등 설정 변경

### 4. PR (Pull Request) 작성 규칙
```markdown
## 제목: [feat] PDF 처리에 OCR 기능 추가

### 변경 사항
- Tesseract.js v6.0+를 통한 OCR 처리 기능 추가
- 스캔된 PDF 문서의 텍스트 추출 지원
- 한국어/영어 OCR 정확도 개선

### 테스트 방법
1. 스캔된 PDF 파일 업로드
2. OCR 처리 옵션 활성화
3. 텍스트 추출 결과 확인

### 관련 이슈
- Fixes #123
- Related to #456

### 리뷰어 요청
@developer1 @developer2
```

### 5. PR 상태 규칙
- **🟢 Ready for Review**: 코드 완성되어 리뷰 요청 가능
- **🟡 In Progress**: 개발 중인 상태 (리뷰 요청 불가)
- **🔴 Needs Changes**: 수정 필요 사항 있음
- **⏳ Waiting for Feedback**: 리뷰어 피드백 대기 중

### 6. 브랜치 명명 규칙
```bash
# ✅ 좋은 예시: 의미 있는 브랜치 이름
feature/ocr-processing-for-scanned-pdfs
bugfix/handle-empty-text-pages
hotfix/security-vulnerability-fix

# ❌ 나쁜 예시: 모호한 브랜치 이름
new-feature
bugfix
update
```

### 7. 코드 리뷰 가이드라인
1. **코드 품질**: ESLint, Prettier 규칙 준수 여부 확인
2. **기능 검증**: 요구사항에 맞게 기능이 구현되었는지 확인
3. **성능 고려**: 불필요한 렌더링, 중복 계산 등 성능 문제 확인
4. **보안**: 민감한 정보 노출, XSS 취약점 등 보안 문제 확인
5. **테스트**: 테스트 코드가 포함되어 있는지 확인

### 8. 릴리스 프로세스
```bash
# 1. feature 브랜치에서 개발 완료
git checkout -b feature/ocr-processing develop

# 2. 개발 완료 후 PR 생성 및 병합
git checkout develop
git merge --no-ff feature/ocr-processing

# 3. 테스트 완료 후 release 브랜치 생성
git checkout -b release/v1.2.0 develop

# 4. 릴리스 브랜치에서 최종 테스트 후 main 병합
git checkout main
git merge --no-ff release/v1.2.0

# 5. 태그 생성
git tag -a v1.2.0 -m "Release version 1.2.0"

# 6. hotfix 브랜치는 main에서 직접 생성
git checkout -b hotfix/security-fix main
```

### 9. 이슈 (Issue) 작성 규칙
```markdown
## 제목: [Bug] PDF 변환 시 빈 페이지 처리 오류

### 재현 단계
1. 특정 PDF 파일 업로드
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
- 버전: v1.1.2

### 추가 정보
[첨부 파일: error_log.txt]
```

### 10. GitHub Actions 워크플로우
```yaml
# .github/workflows/ci.yml 예시
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: npm install
        
      - name: Run tests
        run: npm test
        
      - name: Build project
        run: npm run build
        
      - name: Run linting
        run: npm run lint
```

### 11. 코드 컨벤션 강제 도구
```bash
# pre-commit 훅 설정 (husky 사용)
{
  "lint-staged": {
    "*.{ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{css,md}": [
      "prettier --write"
    ]
  }
}

# 커밋 메시지 검증 (commitlint)
{
  "extends": ["@commitlint/config-conventional"],
  "rules": {
    "type-enum": [
      2,
      "always",
      ["feat", "fix", "docs", "style", "refactor", "test", "chore"]
    ]
  }
}
```

### 12. 보안 규칙
1. **비밀 키 관리**: GitHub Secrets를 통한 민감 정보 관리
2. **의존성 취약점**: Dependabot을 통한 자동 보안 업데이트
3. **코드 스캔**: CodeQL을 통한 취약점 자동 검사
4. **권한 관리**: Collaborator 권한 최소 원칙 적용

---

**개발팀**: PDF to EPUB 변환기 팀
**최종 업데이트**: 2024년 9월
**버전**: 1.0.0
