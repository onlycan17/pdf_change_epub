# 2026-03-14 Async Queue Celery 재연결 냉각 시간 개선 계획

## 배경
- 개발 환경에서 Redis/Celery가 떠 있지 않으면 `AsyncQueueService.initialize()`가 실패하고 직접 실행 모드로 전환됩니다.
- 하지만 직접 실행 모드로 내려간 뒤에도 상태 조회 같은 요청마다 다시 `initialize(force=True)`가 호출되어 Celery 연결을 반복 확인합니다.
- 그 결과 같은 Redis 연결 실패 스택 트레이스가 수초 간격으로 계속 찍혀 로그 가독성이 크게 떨어집니다.

## 목표
- Celery 연결 실패 후 일정 시간은 재연결을 다시 시도하지 않도록 냉각 시간(cooldown, 잠시 쉬는 시간)을 둡니다.
- 직접 실행 모드 동작은 유지하면서 로그 경고 반복만 줄입니다.
- 냉각 시간이 지나면 다시 Celery 복구를 확인할 수 있도록 자동 재시도 여지는 남깁니다.

## 비목표
- Redis/Celery 프로세스를 자동으로 띄우지는 않습니다.
- 운영 환경의 큐 구조나 Celery 브로커 설정 자체는 바꾸지 않습니다.

## 영향 범위
- `app/services/async_queue_service.py`
  - 최근 Celery 연결 실패 시각 저장
  - 냉각 시간 동안 강제 재초기화 생략
  - 필요 시 디버그 로그만 남기고 경고 스팸 방지
- `tests/test_async_queue_service.py`
  - 냉각 시간 내 재초기화 생략 테스트
  - 냉각 시간 경과 후 재시도 테스트

## 설계 메모
- 비유하면, 지금은 문이 잠겨 있는지 확인하려고 매번 손잡이를 세게 돌리며 경보를 울리는 상태입니다.
- 수정 후에는 “방금 잠겨 있음을 확인했으니 30초 정도는 다시 흔들지 말자”는 식으로 동작합니다.

## 검증 계획
1. 백엔드 포맷
- `make fmt PYTHON=./.venv311/bin/python`

2. 백엔드 린트/타입 검사
- `make lint PYTHON=./.venv311/bin/python`

3. 백엔드 테스트
- `make test PYTHON=./.venv311/bin/python`

4. 프론트엔드 린트
- `cd frontend && npm run lint`

5. 프론트엔드 타입 검사
- `cd frontend && npm run type-check`

6. 프론트엔드 테스트
- `cd frontend && npm run test`

7. 프론트엔드 빌드
- `cd frontend && npm run build`

8. 프론트엔드 포맷 검사
- `cd frontend && npx prettier --check .`

## 롤백 전략
- `async_queue_service.py`의 냉각 시간 조건만 제거하면 즉시 기존 동작으로 되돌릴 수 있습니다.
