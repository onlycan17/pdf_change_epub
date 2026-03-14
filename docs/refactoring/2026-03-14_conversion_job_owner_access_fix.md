[배경]
- 운영자 계정은 변환 상태 조회와 다운로드가 가능하지만, 일반 사용자 계정은 같은 흐름에서 `작업 접근 권한을 확인할 수 없습니다.` 오류가 발생했습니다.
- 조사 결과, 변환 시작 시점에는 `owner_user_id`(작업 주인 사용자 ID)를 생성하지만 Celery 작업 등록 단계에서 이 값을 작업 인자와 결과 상태에 함께 전달하지 않았습니다.
- 그 결과 일반 사용자의 작업은 큐를 거친 뒤 소유자 정보가 비어 있는 상태로 복원되었고, 접근 검사에서 자기 작업도 확인할 수 없었습니다.

[문제 원인]
- `app/services/async_queue_service.py`
  - `_build_celery_task_kwargs`가 `owner_user_id`를 누락했습니다.
  - `_queue_conversion_job`과 재시도 경로도 같은 누락을 그대로 사용했습니다.
- `app/tasks/conversion_tasks.py`
  - Celery 태스크가 작업 시작 시 소유자 정보를 오케스트레이터에 넘기지 않으면, 이후 상태 payload에도 주인 정보가 남지 않습니다.
- `app/api/v1/conversion.py`
  - 접근 검사 `_ensure_job_access`는 소유자 정보가 비어 있으면 즉시 403을 반환하므로, 일반 사용자가 가장 먼저 영향을 받습니다.

[수정 목표]
- Celery 큐 경로와 직접 실행 경로 모두에서 `owner_user_id`를 일관되게 보존합니다.
- 상태 조회, 다운로드, 취소, 재시도에서 일반 사용자가 자신의 작업에 정상 접근할 수 있도록 합니다.
- 다른 사용자의 작업 차단 규칙은 그대로 유지합니다.

[변경 계획]
- `app/services/async_queue_service.py`
  - Celery 작업 인자 생성 시 `owner_user_id`를 포함합니다.
  - 큐 등록과 재시도 경로에서 소유자 ID가 빠지지 않도록 연결합니다.
- `app/tasks/conversion_tasks.py`
  - 태스크 시작 시 오케스트레이터에 `owner_user_id`를 전달합니다.
- `tests/`
  - Celery 경로에서 소유자 정보가 전달되는지 검증하는 테스트를 추가합니다.
  - 일반 사용자가 자기 작업에는 접근 가능하고, 소유자 정보가 비어 있을 때만 차단되는 흐름을 회귀 테스트로 보강합니다.

[검증 계획]
- `python3 -m pytest tests/test_async_queue_service.py tests/test_integration.py`
- `python3 -m black app tests`
- `python3 -m ruff check app tests`
- `python3 -m mypy app tests`
