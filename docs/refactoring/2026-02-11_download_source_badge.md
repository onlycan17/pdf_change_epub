# 다운로드 소스 배지 표시 개선 계획 (2026-02-11)

## 배경
- 현재 다운로드 버튼은 실제 결과 파일과 샘플 폴백을 모두 지원하지만, 사용자는 어떤 파일이 내려받아졌는지 구분하기 어렵습니다.
- 사용자 요청: 실제 EPUB 변환 결과 여부를 UI에서 명확히 표시

## 목표
- 다운로드 후 파일 소스를 `실제 변환 파일` 또는 `샘플 대체 파일`로 구분해 표시
- 폴백이 발생한 경우 이유를 함께 안내

## 비목표
- 다운로드 API 자체 구조 변경은 이번 범위에 포함하지 않음
- 백엔드 응답 스키마 변경은 포함하지 않음

## 영향 범위
- 수정: `frontend/src/pages/DownloadPage.tsx`
- 문서 동기화: 본 계획 문서

## 구현 설계
- 다운로드 실행 결과를 `{source: 'actual' | 'sample', fallbackReason?: string}` 형태로 상태 저장
- 버튼 아래 상태 배지 표시
  - 실제 파일: 초록 배지
  - 샘플 파일: 노란 배지 + 폴백 사유 문구

## 검증 계획
1. 프론트엔드: `npm run format && npm run lint && npm run type-check && npm run build`
2. 백엔드: `make PYTHON=.venv/bin/python fmt && make PYTHON=.venv/bin/python lint && make PYTHON=.venv/bin/python test`

## 롤백 전략
- `frontend/src/pages/DownloadPage.tsx`와 본 문서 변경만 되돌리면 원복 가능
