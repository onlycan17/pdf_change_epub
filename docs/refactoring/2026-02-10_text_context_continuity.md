# 2026-02-10 텍스트 문맥 연속성 개선 계획

## 배경
- 현재 텍스트 기반 PDF는 청크(덩어리)로 추출한 뒤 단순 병합(`join`)하여 EPUB을 생성합니다.
- 이 방식은 청크 경계에서 문장이나 문단이 어색하게 끊길 수 있습니다.
- 스캔 PDF 경로에는 OCR/LLM 보완이 있으나, 텍스트 기반 PDF 경로의 문맥 보정은 상대적으로 약합니다.

## 목표
- 텍스트 기반/혼합 PDF에 대해 청크 경계 문맥 보정 단계를 추가합니다.
- 이전/다음 청크 일부를 함께 전달하여 현재 청크를 자연스럽게 교정합니다.
- API 키 미설정 또는 호출 실패 시 기존 동작(원문 유지)으로 안전하게 폴백(실패 시 기본 동작으로 복귀)합니다.

## 비목표
- 문서 전체를 한 번에 재작성하는 고비용 LLM 파이프라인은 도입하지 않습니다.
- 스캔 PDF 전용 OCR 파이프라인 구조는 변경하지 않습니다.

## 영향 범위
- `app/services/text_context_service.py` 신규: 문맥 보정 전담 서비스
- `app/services/conversion_orchestrator.py` 수정: 텍스트 청크 병합 단계에 보정 서비스 연결
- `tests/test_text_context_service.py` 신규: 보정 서비스 단위 테스트
- `tests/test_conversion_orchestrator.py` 수정: 오케스트레이터 연동 테스트

## 검증 계획
1. 백엔드 포맷/린트/타입/테스트 실행
- `PYTHON=.venv311/bin/python make fmt`
- `PYTHON=.venv311/bin/python make lint`
- `PYTHON=.venv311/bin/python make test`

2. 프론트엔드 자동 검사 재실행(회귀 확인)
- `cd frontend && npm run lint`
- `cd frontend && npm run type-check`
- `cd frontend && npm run build`
- `cd frontend && npx prettier --check .`

## 롤백 전략
- 오케스트레이터에서 보정 호출부를 제거하면 즉시 기존 `join` 방식으로 복귀 가능합니다.
- 신규 서비스 파일은 독립 모듈이므로 문제 시 파일 단위 롤백이 쉽습니다.
