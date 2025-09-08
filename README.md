# PDF to EPUB 변환기

PDF 문서를 EPUB 전자책으로 자동 변환하는 웹 애플리케이션입니다. OCR 기술과 LLM을 활용하여 텍스트 추출 및 문맥 연결을 지원합니다.

## 🚀 주요 기능

- **PDF 파일 업로드**: 드래그 앤 드롭으로 간편한 파일 업로드
- **자동 텍스트 추출**: PDF에서 텍스트를 자동으로 추출
- **OCR 지원**: 스캔본 PDF의 텍스트 인식 (한국어/영어)
- **LLM 문맥 연결**: DeepSeek-V3.1을 활용한 자연스러운 문맥 연결
- **EPUB 생성**: 표준 EPUB 3.0 형식으로 변환
- **프리미엄 기능**: 대용량 파일, 고해상도 이미지 처리
- **사용량 모니터링**: 실시간 사용량 추적 및 제한 관리

## 🛠 기술 스택

### 프론트엔드
- **React 18** - 사용자 인터페이스
- **TypeScript** - 타입 안전성
- **Vite** - 빌드 도구
- **Tailwind CSS** - 스타일링

### 백엔드
- **Supabase** - 데이터베이스 및 인증
- **OpenRouter** - LLM API (DeepSeek-V3.1)
- **Tesseract.js** - OCR 엔진

### 기타
- **Stripe** - 결제 처리
- **Google AdSense** - 광고 수익화

## 📋 사전 준비사항

1. **Node.js 설치** (버전 18 이상)
2. **Supabase 계정** 생성
3. **OpenRouter API 키** 발급
4. **Stripe 계정** (프리미엄 기능용)

## 🚀 설치 및 실행

### 1. 프로젝트 클론
```bash
git clone https://github.com/onlycan17/pdf_change_epub.git
cd pdf_change_epub
```

### 2. 의존성 설치
```bash
npm install
```

### 3. 환경 변수 설정
`.env` 파일을 생성하고 다음 변수를 설정하세요:

```env
# Supabase 설정
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key

# OpenRouter API 설정
VITE_OPENROUTER_API_KEY=your_openrouter_api_key

# Stripe 설정 (프리미엄 기능용)
VITE_STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
```

### 4. Supabase 데이터베이스 설정
1. Supabase 대시보드에서 새 프로젝트 생성
2. SQL 편집기에서 `docs/database_schema.sql` 실행
3. Storage 버킷 설정 (pdf-files, epub-files)

### 5. 개발 서버 실행
```bash
npm run dev
```

브라우저에서 `http://localhost:5173`으로 접속하세요.

## 📁 프로젝트 구조

```
src/
├── components/          # 재사용 가능한 컴포넌트
│   ├── common/         # 공통 컴포넌트 (Button, Input 등)
│   ├── layout/         # 레이아웃 컴포넌트 (Header, Footer)
│   ├── pdf/            # PDF 관련 컴포넌트
│   └── conversion/     # 변환 관련 컴포넌트
├── pages/              # 페이지 컴포넌트
│   ├── Home.tsx        # 홈 페이지
│   ├── Upload.tsx      # 파일 업로드 페이지
│   ├── Conversion.tsx  # 변환 진행 페이지
│   └── Download.tsx    # 다운로드 페이지
├── hooks/              # 커스텀 훅
├── services/           # API 서비스
│   ├── supabase.ts     # Supabase 클라이언트
│   ├── openrouter.ts   # OpenRouter API
│   └── stripe.ts       # Stripe 결제
├── utils/              # 유틸리티 함수
├── styles/             # 전역 스타일
└── assets/             # 정적 자산
```

## 🔧 사용 가능한 스크립트

- `npm run dev` - 개발 서버 실행
- `npm run build` - 프로덕션 빌드
- `npm run preview` - 빌드 결과 미리보기
- `npm run lint` - ESLint 실행

## 📊 데이터베이스 스키마

### 주요 테이블
- **users**: 사용자 정보 및 프리미엄 상태
- **conversions**: 변환 기록 및 상태 추적
- **usage_tracking**: DeepSeek-V3.1 Free 사용량 모니터링
- **file_metadata**: 파일 메타데이터 저장

### Storage 버킷
- **pdf-files**: 업로드된 PDF 파일 저장
- **epub-files**: 변환된 EPUB 파일 저장

## 🔐 보안 및 개인정보 보호

- 모든 파일은 24시간 후 자동 삭제
- 사용자 데이터는 최소한으로 수집
- HTTPS를 통한 암호화된 통신
- Row Level Security (RLS) 적용

## 📈 성능 목표

- **일반 PDF** (50페이지 이하): 30초 이내 변환
- **대용량 PDF** (100페이지 이상): 1분 이내 변환
- **OCR 처리**: 페이지당 2초 이내
- **동시 처리**: 최대 10개 파일 동시 변환 지원

## 🚀 배포

### Vercel 배포 (프론트엔드)
```bash
npm install -g vercel
vercel --prod
```

### Supabase 배포 (백엔드)
Supabase 대시보드에서 자동 배포되며, 추가 설정 필요 없음.

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 📞 지원

문의사항이 있으시면 GitHub Issues를 이용해주세요.

---

**개발자**: PDF to EPUB 변환기 팀
**버전**: 1.0.0
**마지막 업데이트**: 2024년 9월