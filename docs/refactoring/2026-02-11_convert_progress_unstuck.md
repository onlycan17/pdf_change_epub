# 변환 진행률 45% 고정 문제 수정 계획 (2026-02-11)

## 배경
- 사용자 피드백: 변환 버튼 클릭 후 진행률이 45%에서 멈추고 더 이상 올라가지 않음
- 조사 결과: `ConvertPage` 진행률/상태 텍스트가 하드코딩(고정 문자열)되어 있어 실제 변화가 없음

## 목표
- 변환 진행률이 시간에 따라 증가하도록 상태 기반 로직으로 전환
- 100% 도달 시 완료 화면(`/download`)으로 자동 이동
- 선택한 파일명/크기를 진행/완료 화면에서 일관되게 표시

## 비목표
- 백엔드 실시간 진행률 API 연동은 이번 범위에 포함하지 않음
- 실제 EPUB 파일 다운로드 구현은 포함하지 않음

## 영향 범위
- 수정: `frontend/src/pages/ConvertPage.tsx`
- 수정: `frontend/src/pages/DownloadPage.tsx`
- 문서 동기화: 본 계획 문서

## 구현 설계
- `useState` + `useEffect`로 진행률(0~100) 증가 타이머 구현
- 진행 단계(텍스트 추출/이미지 처리/EPUB 생성)를 진행률 구간별로 갱신
- 100% 시 `navigate('/download')`로 파일 정보 전달
- `DownloadPage`는 전달된 파일 정보를 표시하고, 없으면 기본값 사용

## 검증 계획
1. 프론트엔드: `npm run format && npm run lint && npm run type-check && npm run build`
2. 백엔드: `make PYTHON=.venv/bin/python fmt && make PYTHON=.venv/bin/python lint && make PYTHON=.venv/bin/python test`

## 롤백 전략
- `frontend/src/pages/ConvertPage.tsx`, `frontend/src/pages/DownloadPage.tsx`, 본 문서 변경만 되돌리면 원복 가능
