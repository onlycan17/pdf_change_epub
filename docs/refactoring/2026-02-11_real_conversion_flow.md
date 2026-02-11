# 실제 변환 API 연동 계획 (2026-02-11)

## 배경
- 현재 프론트엔드는 업로드/변환/다운로드 흐름이 화면 시뮬레이션 중심이며, 실제 변환 작업 ID(conversionId) 기반 연동이 부족함
- 결과적으로 다운로드가 샘플 fallback에 의존하는 경우가 발생함

## 목표
- 업로드 시 `/api/v1/conversion/start`를 실제 호출해 `conversionId`를 받도록 구현
- 변환 페이지에서 `/api/v1/conversion/status/{conversionId}`를 주기적으로 조회(폴링)
- 완료 상태 시 `conversionId`를 다운로드 페이지로 전달하여 실제 결과 다운로드 성공률을 높임

## 비목표
- WebSocket/SSE 실시간 푸시 기반 상태 반영은 이번 범위에 포함하지 않음
- 결제/인증 정책 자체 변경은 포함하지 않음

## 영향 범위
- 추가: `frontend/src/utils/conversionApi.ts` (변환 API 클라이언트)
- 수정: `frontend/src/pages/UploadPage.tsx` (실제 업로드 시작)
- 수정: `frontend/src/pages/ConvertPage.tsx` (상태 폴링)
- 문서 동기화: 본 계획 문서

## 구현 설계
- 공통 API 키 헤더(`X-API-Key`)를 포함하는 변환 API 유틸 추가
- 업로드 성공 시 `conversionId`, 파일 정보를 `navigate('/convert')` state로 전달
- Convert 페이지에서 1초 간격 폴링으로 `status/progress/current_step` 반영
- 완료 시 `/download`로 이동, 실패 시 오류 메시지 표시 및 재시도 동선 안내

## 검증 계획
1. 프론트엔드: `npm run format && npm run lint && npm run type-check && npm run build`
2. 백엔드: `make PYTHON=.venv/bin/python fmt && make PYTHON=.venv/bin/python lint && make PYTHON=.venv/bin/python test`

## 롤백 전략
- 변경 파일(`conversionApi.ts`, `UploadPage.tsx`, `ConvertPage.tsx`, 본 문서)만 되돌리면 즉시 원복 가능
