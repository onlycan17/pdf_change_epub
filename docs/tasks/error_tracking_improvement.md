# 에러 추적 시스템 개선 작업 문서

## 1. PRD(요구사항)
- **목표**: 사용자 환경에서 발생한 예외를 일관되게 수집하고, 재현이 어려운 오류를 빠르게 파악할 수 있도록 한다.
- **사용자 가치**: 오류 발생 시 개발팀이 즉시 대응할 수 있어 서비스 신뢰도가 향상된다.
- **성공 조건**: 핵심 에러 지점에서 공통 추적 모듈로 예외가 전송되고, 웹훅(URL) 설정 시 원격 수집이 가능하다.

## 2. 아키텍처 명세
- `errorTracker` 유틸을 신설하여 초기화/예외 전송/메시지 전송 API 제공.
- 환경 변수(`VITE_ERROR_WEBHOOK_URL`) 기반으로 fetch 웹훅 전송, 미설정 시 콘솔로 graceful fallback.
- 기존 로거/에러 경계/변환 훅에서 tracker 호출.

## 3. UI/UX 명세
- 최종 사용자 UI 변화 없음. 단, 에러 발생 시 내부적으로 추적 요청을 보낸다.
- 실패 시 사용자에게 추가 노출 없이 fallback (콘솔 로그) 처리.

## 4. 기술 스택 명세
- Fetch API + AbortController(타임아웃 3초) 활용.
- 브라우저 호환성을 위해 progressive enhancement: 지원하지 않는 환경에서는 콘솔 로깅으로 대체.

## 5. 기능 명세
1. `src/utils/errorTracker.ts` 작성: 초기화, 예외/메시지 전송, 브라우저 환경 체크, 타임아웃 처리.
2. 앱 초기화(`src/main.tsx`) 시 트래커 초기화.
3. `GlobalErrorBoundary`와 `usePDFConversion` 등 주요 catch 지점에서 `errorTracker.captureException` 호출.
4. `logAndGetStandardizedMessage`/`logAndGetUserMessage`에서 옵션으로 트래커 연계 지원.
5. 환경 변수 `.env.example` 업데이트 및 문서 TODO/작업 문서 반영.

## 6. API 명세
- `initializeErrorTracker(options)`: webhook URL, 릴리스 정보 등 설정.
- `captureException(error, context?)` / `captureMessage(message, context?)` 함수 제공.

## 7. ERD / 테이블 명세
- 서버/DB 변경 없음.

## 8. TODO / TASK
- [x] errorTracker 유틸 모듈 작성
- [x] 앱 초기화 시 트래커 설정
- [x] 주요 에러 지점에서 트래커 호출
- [x] 자동화 검사 수행
- [x] docs/todo.md 및 관련 문서 최신화

## 9. 버전 이력
- **2025-01-28**: 에러 추적 개선 계획 수립.
- **2025-01-28**: Webhook 기반 에러 트래커 적용, 주요 지점 연동 및 문서 업데이트 완료.
