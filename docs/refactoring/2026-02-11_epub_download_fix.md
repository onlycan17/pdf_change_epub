# EPUB 다운로드 미동작 수정 계획 (2026-02-11)

## 배경
- 사용자 피드백: 변환 완료 화면의 "EPUB 파일 다운로드" 버튼을 눌러도 파일이 내려받아지지 않음
- 조사 결과: 버튼에 실제 다운로드 이벤트(onClick)와 API 호출 로직이 연결되어 있지 않음

## 목표
- 다운로드 버튼 클릭 시 브라우저가 실제 `.epub` 파일 저장을 시작하도록 구현
- 변환 ID가 있으면 실제 다운로드 API(`/api/v1/conversion/download/{id}`) 사용
- 변환 ID가 없거나 결과가 준비되지 않은 경우 샘플 EPUB 다운로드로 폴백(fallback: 대체 경로)

## 비목표
- Celery 워커 기반의 실시간 백엔드 처리 보장은 이번 범위에 포함하지 않음
- 이메일 전송 기능 구현은 포함하지 않음

## 영향 범위
- 수정: `frontend/src/pages/DownloadPage.tsx`
- 수정: `frontend/src/pages/ConvertPage.tsx` (conversionId 전달)
- 수정: `app/api/v1/conversion.py` (샘플 EPUB 다운로드 엔드포인트)
- 문서 동기화: 본 계획 문서

## 구현 설계
- 프론트: 다운로드 버튼에 로딩/오류 상태 추가
- 프론트: 실제 다운로드 API 실패 시 `/api/v1/conversion/download-sample` 호출
- 백엔드: `create_mock_epub`를 활용해 유효 EPUB 샘플을 반환하는 엔드포인트 추가

## 검증 계획
1. 프론트엔드: `npm run format && npm run lint && npm run type-check && npm run build`
2. 백엔드: `make PYTHON=.venv/bin/python fmt && make PYTHON=.venv/bin/python lint && make PYTHON=.venv/bin/python test`

## 롤백 전략
- 변경 파일(`DownloadPage.tsx`, `ConvertPage.tsx`, `conversion.py`, 본 문서)만 되돌리면 즉시 원복 가능
