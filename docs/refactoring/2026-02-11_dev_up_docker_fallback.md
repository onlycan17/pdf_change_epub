# dev_up 도커 미설치 대응 개선 계획 (2026-02-11)

## 배경
- 사용자 환경에서 `./scripts/dev_up.sh` 실행 시 `docker-compose 또는 docker compose가 필요합니다` 오류로 즉시 종료되었습니다.
- 개발 시작 스크립트는 가능한 넓은 환경에서 동작해야 하므로, 인프라 도구 미설치 상황에서도 최소 실행(백엔드/프론트엔드)을 지원해야 합니다.

## 목표
- 도커 명령이 없어도 `dev_up.sh`가 강제 종료되지 않고 개발 서버 실행을 계속하도록 개선합니다.

## 비목표
- Redis/DB 없이도 모든 기능이 정상 동작하도록 보장하는 것은 이번 범위에 포함하지 않습니다.
- 운영 배포 스크립트 개선은 포함하지 않습니다.

## 영향 범위
- 수정: `scripts/dev_up.sh` (도커 fallback 로직 추가)
- 수정: `README.md` (환경변수 기반 실행 옵션 안내)
- API/DB 스키마/핵심 비즈니스 로직 영향 없음

## 구현 설계
- `run_compose`는 compose 명령이 없을 때 종료하지 않고 상태 코드만 반환
- 기본 동작: compose를 못 찾거나 인프라 실행 실패 시 경고를 출력하고 계속 진행
- 엄격 모드: `REQUIRE_INFRA=1`이면 인프라 준비 실패 시 즉시 종료
- 사용자가 의도적으로 인프라 시작을 건너뛰려면 `SKIP_INFRA=1` 지원

## 검증 계획
1. `bash -n scripts/dev_up.sh && bash -n scripts/dev_down.sh` 문법 검사
2. 백엔드 자동 검사: `make PYTHON=.venv/bin/python fmt && make PYTHON=.venv/bin/python lint && make PYTHON=.venv/bin/python test`
3. 프론트엔드 자동 검사: `cd frontend && npm run format && npm run lint && npm run type-check && npm run build`

## 롤백 전략
- `scripts/dev_up.sh`, `README.md`, 본 문서 변경만 되돌리면 즉시 원복됩니다.
