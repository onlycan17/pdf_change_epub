# 개발 계획 (MVP)

## 1. 개요
이 문서는 React, FastAPI, Supabase 스택을 기반으로 PDF→EPUB 변환기 MVP를 구축하기 위한 개발 계획을 정의합니다.

## 2. 마일스톤 및 타임라인

### 마일스톤 1: 프로젝트 설정 및 Supabase 연동 (1주)
**목표**: 개발 환경을 구축하고 프론트엔드와 Supabase의 기본 연동을 완료합니다.

- [ ] **프론트엔드**: Vite + React + TypeScript 프로젝트 설정
- [ ] **Supabase**: 프로젝트 생성, 데이터베이스 스키마(`conversion_jobs`) 적용
- [ ] **인증**: Supabase Auth를 이용한 이메일 기반 회원가입 및 로그인 기능 구현
- [ ] **스토리지**: Supabase Storage에 PDF 파일을 업로드하는 기능 구현
- [ ] **데이터베이스**: 파일 업로드 시 `conversion_jobs` 테이블에 작업 레코드를 생성하는 로직 구현

### 마일스톤 2: 핵심 변환 로직 개발 (2주)
**목표**: FastAPI를 사용하여 PDF를 EPUB으로 변환하는 핵심 처리 서비스를 구현합니다.

- [ ] **FastAPI**: 프로젝트 기본 설정 및 API 엔드포인트(`/convert`) 설계
- [ ] **PDF 파싱**: PyPDF2/pdfminer.six를 이용해 PDF 텍스트 및 이미지 추출 모듈 구현
- [ ] **OCR 통합**: PaddleOCR을 연동하여 스캔된 이미지에서 한국어 텍스트를 추출하는 모듈 구현
- [ ] **EPUB 생성**: ebooklib을 사용하여 추출된 콘텐츠로 EPUB 파일을 만드는 모듈 구현
- [ ] **통합 테스트**: FastAPI 서비스가 Supabase Storage URL을 받아 파일을 처리하고, 결과를 다시 Storage에 저장하는 전체 흐름을 테스트합니다.

### 마일스톤 3: 프론트엔드-백엔드 연동 및 UI 완성 (2주)
**목표**: 프론트엔드, Supabase, FastAPI 서비스를 모두 연동하여 사용자에게 완전한 변환 경험을 제공합니다.

- [ ] **트리거 설정**: Supabase Edge Function을 사용하여 파일 업로드 시 FastAPI 변환 API를 자동 호출하도록 설정
- [ ] **실시간 상태 표시**: 프론트엔드에서 Supabase Realtime Subscription을 사용하여 `conversion_jobs` 테이블의 상태 변경(예: 'processing', 'completed')을 실시간으로 감지하고 UI에 반영
- [ ] **UI 구현**: 파일 업로드, 변환 진행률 표시, 결과 다운로드 등 `ui_spec.md`에 명시된 주요 UI 컴포넌트 완성
- [ ] **에러 처리**: 변환 실패 시 Supabase DB에 기록된 에러 메시지를 사용자에게 명확하게 표시

### 마일스톤 4: 품질 향상 및 배포 준비 (1주)
**목표**: 테스트를 강화하고, 문서를 정리하며, 배포를 준비합니다.

- [ ] **단위/통합 테스트**: Pytest와 React Testing Library를 사용하여 테스트 커버리지 확보
- [ ] **문서 정리**: 최종 아키텍처와 기술 스택에 맞게 모든 `docs` 내 문서를 최종 검토하고 정리
- [ ] **컨테이너화**: FastAPI 처리 서비스를 Dockerize하여 배포 일관성 확보
- [ ] **CI/CD**: GitHub Actions를 사용하여 테스트 및 빌드 자동화 파이프라인 구축

## 3. 리스크 관리
- **기술 리스크**: OCR 정확도, 대용량 PDF 처리 성능 → **대응**: PaddleOCR 모델 튜닝 및 스트리밍 처리 방식 연구.
- **일정 리스크**: Supabase 신규 기능 학습 곡선 → **대응**: 공식 문서 및 커뮤니티를 적극 활용하고, 복잡한 기능은 초기 MVP 범위에서 제외.
