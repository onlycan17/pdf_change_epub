# 비로그인 사용을 위한 진입 흐름 개선 계획 (2026-02-11)

## 배경
- 사용자 피드백: 앱이 로그인 페이지부터 보여 사용이 막힌 것으로 느껴짐
- 목표는 메인 페이지를 기본 진입점으로 고정하고, 로그인 없이도 변환 기능 접근이 가능하도록 하는 것

## 목표
- 앱 진입 시 기본 화면을 메인(`/`)으로 고정
- 로그인 페이지에 비로그인 사용자용 즉시 진입 동선 제공
- 로그인 없이 주요 기능(업로드/변환/다운로드/프리미엄) 접근 가능 상태 유지

## 비목표
- 실제 인증 API 연동/권한 정책 변경은 이번 범위에 포함하지 않음
- 백엔드 인증 로직 수정은 포함하지 않음

## 영향 범위
- 수정: `frontend/src/App.tsx` 라우터 구조 정리
- 수정: `frontend/src/pages/LoginPage.tsx` 비로그인 진입 버튼 추가
- 문서/코드 동기화: 본 문서로 변경 의도와 검증 방법 기록

## 구현 설계
- `MainLayout` 기반 공개 라우트를 명시적으로 선언
- 와일드카드 경로는 `Navigate`로 메인(`/`)으로 리다이렉트
- 로그인 페이지에서 `홈으로 이동`, `로그인 없이 변환 시작` 버튼 제공

## 검증 계획
1. 프론트엔드: `npm run format && npm run lint && npm run type-check && npm run build`
2. 백엔드: `make PYTHON=.venv/bin/python fmt && make PYTHON=.venv/bin/python lint && make PYTHON=.venv/bin/python test`

## 롤백 전략
- `frontend/src/App.tsx`, `frontend/src/pages/LoginPage.tsx`, 본 문서 변경을 되돌리면 원복 가능
