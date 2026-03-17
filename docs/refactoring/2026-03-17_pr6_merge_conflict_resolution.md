# PR #6 충돌 해결 계획

## 배경

- PR #6 브랜치(`codex/fix-conversion-owner-access`)는 변환 작업의 소유자 정보를 큐, 폴백 실행, 재시도 경로까지 유지하도록 보완합니다.
- `origin/main`에는 같은 흐름을 다루는 후속 수정이 이미 반영되어 있어, 같은 파일을 서로 다른 방향으로 손본 상태입니다.
- Git 충돌은 같은 문단에 서로 다른 수정 메모가 겹친 상황과 비슷하므로, 두 변경의 의도를 모두 살리는 기준이 필요합니다.

## 충돌 예상 파일

- `app/services/async_queue_service.py`
- `app/services/conversion_orchestrator.py`
- `app/tasks/conversion_tasks.py`
- `tests/test_async_queue_service.py`
- `tests/test_celery_tasks.py`

## 병합 원칙

1. 작업 소유자(`owner_user_id`)는 큐 등록, Celery 실행, 직접 폴백, 재시도 흐름 전체에서 유지합니다.
2. `origin/main`에 있는 최신 운영 안정화 변경은 유지합니다.
3. 테스트는 두 브랜치의 의도를 모두 검증하도록 합칩니다.
4. 문서와 코드의 설명이 어긋나지 않도록, 병합 후 검증 결과까지 함께 반영합니다.

## 검증 계획

- `pytest tests/test_async_queue_service.py tests/test_celery_tasks.py tests/test_config.py tests/test_integration.py tests/test_scan_pdf_processor.py`
- 가능하면 프로젝트의 정적 검사 명령도 함께 실행합니다.
