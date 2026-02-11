# 빠른 실행 스크립트 도입 계획 (2026-02-11)

## 배경
- 현재 개발 실행 절차가 백엔드/프론트엔드/인프라 명령으로 분리되어 있어, 처음 실행 시 실수가 발생하기 쉽습니다.
- 요청사항: "간단하게 실행할 수 있는 스크립트"를 제공해 한 번에 개발 서버를 띄울 수 있게 합니다.

## 목표
- `./scripts/dev_up.sh` 한 번으로 로컬 개발 환경을 실행합니다.

## 비목표
- 프로덕션 배포 자동화는 이번 범위에 포함하지 않습니다.
- Celery Worker/Beat 자동 실행은 이번 범위에 포함하지 않습니다.

## 영향 범위
- 추가: 개발용 실행 스크립트 1개
- 문서: README 빠른 시작 섹션에 스크립트 사용법 반영
- 기존 API/DB 스키마/애플리케이션 동작 변경 없음

## 구현 설계
- 백엔드 가상환경(`.venv`)이 없으면 생성하고 의존성 설치
- 프론트엔드 `node_modules`가 없으면 `npm ci` 실행
- `docker-compose up -d db redis`로 필수 인프라 실행
- 백엔드(`uvicorn`)를 백그라운드로 띄우고, 프론트엔드(`npm run dev`)를 포그라운드로 실행
- 종료 시 백그라운드 백엔드 프로세스를 함께 정리(trap)

## 검증 계획
1. `bash -n scripts/dev_up.sh` 문법 검사
2. `make fmt && make lint && make test` 백엔드 자동 검사
3. `cd frontend && npm run format && npm run lint && npm run type-check && npm run build` 프론트엔드 자동 검사

## 롤백 전략
- 스크립트와 README 변경만 되돌리면 원복됩니다.
- 필요 시 기존 수동 실행 절차(`README` 기존 명령)로 즉시 복귀 가능합니다.
