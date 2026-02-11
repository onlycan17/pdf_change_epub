# 프론트 환경변수 예시 파일 동기화 계획 (2026-02-11)

## 배경
- 프론트는 `VITE_API_KEY`가 필요하지만 `frontend/.env.example`이 없어 초기 설정 실수가 발생하기 쉬움
- 사용자 요청: 다음 단계로 환경 설정 흐름을 정리

## 목표
- `frontend/.env.example`를 추가해 프론트 필수 환경변수를 명확히 제공
- README 수동 실행 절차에 프론트 `.env` 준비 단계를 반영

## 비목표
- 실제 비밀키를 저장소에 포함하지 않음
- 백엔드 `.env` 구조 개편은 이번 범위에 포함하지 않음

## 영향 범위
- 추가: `frontend/.env.example`
- 수정: `README.md`
- 문서 동기화: 본 계획 문서

## 구현 설계
- `VITE_API_KEY=your-api-key-here` 기본 템플릿 제공
- 안내 주석으로 백엔드 `SECURITY_API_KEY`와 동일 값 사용을 명시
- README에 `cp frontend/.env.example frontend/.env` 단계 추가

## 검증 계획
1. 프론트엔드: `npm run format && npm run lint && npm run type-check && npm run build`
2. 백엔드: `make PYTHON=.venv/bin/python fmt && make PYTHON=.venv/bin/python lint && make PYTHON=.venv/bin/python test`

## 롤백 전략
- `frontend/.env.example`, `README.md`, 본 문서 변경만 되돌리면 즉시 원복 가능
