# 개발 종료 스크립트 도입 계획 (2026-02-11)

## 배경
- 현재 `scripts/dev_up.sh`로 개발 환경 시작은 간단해졌지만, 종료는 수동으로 정리해야 합니다.
- 요청사항: 종료도 한 번에 처리하는 간단한 스크립트 제공

## 목표
- `./scripts/dev_down.sh` 한 번으로 관련 개발 프로세스와 인프라를 정리합니다.

## 비목표
- 운영(프로덕션) 서버 중지는 이번 범위에 포함하지 않습니다.
- 로그 파일 정리/캐시 삭제 같은 청소 작업은 포함하지 않습니다.

## 영향 범위
- 추가: 종료 스크립트 1개 (`scripts/dev_down.sh`)
- 수정: README 빠른 시작 섹션에 종료 명령 추가
- API/DB 스키마/비즈니스 로직 영향 없음

## 구현 설계
- 8000 포트(백엔드 uvicorn) 점유 프로세스 종료 시도
- 5173 포트(프론트엔드 Vite) 점유 프로세스 종료 시도
- `docker-compose stop db redis`로 개발 인프라 중지
- 일부 프로세스가 이미 없더라도 실패 없이 종료되도록 설계

## 검증 계획
1. `bash -n scripts/dev_down.sh` 문법 검사
2. 백엔드 자동 검사: `make PYTHON=.venv/bin/python fmt && make PYTHON=.venv/bin/python lint && make PYTHON=.venv/bin/python test`
3. 프론트엔드 자동 검사: `cd frontend && npm run format && npm run lint && npm run type-check && npm run build`

## 롤백 전략
- `scripts/dev_down.sh` 파일 및 README 변경만 되돌리면 즉시 원복됩니다.
- 기존 수동 종료 방식(`Ctrl+C`, docker-compose stop)을 계속 사용할 수 있습니다.
