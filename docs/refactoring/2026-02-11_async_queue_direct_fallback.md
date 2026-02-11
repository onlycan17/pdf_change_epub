# 실제 EPUB 다운로드를 위한 AsyncQueueService 폴백 개선 계획 (2026-02-11)

## 배경
- 현재 변환 흐름은 Celery 중심으로 구성되어 있으나, 로컬 개발 환경에서 워커 미실행 시 실제 결과 바이트가 다운로드까지 이어지지 않는 문제가 있음
- 사용자 요구: 실제 변환 결과 EPUB 다운로드 가능 상태로 개선

## 목표
- Celery 초기화 실패(워커 미연결) 시 자동으로 오케스트레이터 직접 실행 모드로 전환
- `/start -> /status -> /download` 흐름에서 실제 `result_bytes`가 생성/조회되도록 보장

## 비목표
- 분산 환경에서의 완전한 큐 내구성 보장은 이번 범위에 포함하지 않음
- Celery 결과 백엔드 구조 개편은 포함하지 않음

## 영향 범위
- 수정: `app/services/async_queue_service.py`
- 수정: 관련 테스트(`tests/test_integration.py`) 중 폴백 동작 기대치
- 문서 동기화: 본 계획 문서

## 구현 설계
- `AsyncQueueService`에 오케스트레이터 인스턴스 참조 추가
- 초기화 실패 시 예외를 그대로 던지는 대신, `use_celery=False`로 전환하고 직접 모드 활성화
- 직접 모드에서 `start/status/cancel/retry`는 오케스트레이터 메서드를 직접 사용
- 큐 통계는 직접 모드 시 간단 통계(활성 작업 수 등)를 반환

## 검증 계획
1. 백엔드: `make PYTHON=.venv/bin/python fmt && make PYTHON=.venv/bin/python lint && make PYTHON=.venv/bin/python test`
2. 프론트엔드: `cd frontend && npm run format && npm run lint && npm run type-check && npm run build`

## 롤백 전략
- `async_queue_service.py` 및 관련 테스트 변경을 되돌리면 즉시 원복 가능
