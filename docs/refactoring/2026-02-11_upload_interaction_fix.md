# 업로드 상호작용(드래그/파일선택) 무반응 문제 수정 계획 (2026-02-11)

## 배경
- 사용자 피드백: 업로드 화면에서 파일 드래그 또는 파일 선택 버튼 클릭 시 반응이 없음
- 조사 결과: `UploadPage`에 실제 파일 입력(input)과 드래그 이벤트 처리 로직이 없음

## 목표
- 드래그 앤 드롭과 파일 선택 버튼 클릭이 실제 파일 선택으로 동작하도록 수정
- 선택된 파일 정보를 화면에 표시하고, "변환 시작" 버튼이 유효하게 동작하도록 연결

## 비목표
- 실제 백엔드 업로드 API 연동은 이번 범위에 포함하지 않음
- 변환 진행률 실시간 연동은 포함하지 않음

## 영향 범위
- 수정: `frontend/src/pages/UploadPage.tsx`
- 수정: `frontend/src/pages/ConvertPage.tsx` (선택 파일명/크기 표시)
- 문서 동기화: 본 계획 문서

## 구현 설계
- 숨김 파일 입력(`input[type=file]`) + 버튼 클릭 트리거
- 드래그 상태 시각화(`isDragActive`) 및 drop 이벤트 처리
- 파일 검증: PDF 확장자/타입, 최대 100MB
- 유효 파일 선택 시 파일명/크기 표시
- "변환 시작" 클릭 시 `/convert`로 파일 정보 전달

## 검증 계획
1. 프론트엔드: `npm run format && npm run lint && npm run type-check && npm run build`
2. 백엔드: `make PYTHON=.venv/bin/python fmt && make PYTHON=.venv/bin/python lint && make PYTHON=.venv/bin/python test`

## 롤백 전략
- `frontend/src/pages/UploadPage.tsx`, `frontend/src/pages/ConvertPage.tsx`, 본 문서 변경만 되돌리면 즉시 원복 가능
