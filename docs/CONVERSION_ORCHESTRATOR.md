# 변환 오케스트레이션 설계서

설명: PDF → EPUB 변환 전 과정을 단계별로 조율하는 통합 관리자(오케스트레이터)를 설계/구현합니다. 한마디로 “주방장” 역할로, 재료(PDF)를 받아 순서대로 손질(분석/추출), 조리(OCR/합성), 플레이팅(EPUB 생성/검증)까지 지휘합니다.

## 목표(요구사항, PRD)
- PDF 업로드 후 비동기 처리로 변환 작업을 시작한다.
- 진행 상태(대기, 처리중, 완료, 실패, 취소)와 세부 단계 진행률을 조회할 수 있다.
- 텍스트 기반 PDF와 스캔 PDF를 자동 구분하고, 스캔 PDF는 OCR/LLM 경로로 처리한다.
- 결과 EPUB은 EPUB3 최소 요건을 만족하고, 간단한 구조 검증을 통과한다.
- 최초 구현은 인메모리 상태 저장으로 시작하고, 후속에 Redis/DB로 대체 가능해야 한다.

용어(설명: 쉬운 말 풀이)
- 오케스트레이션(설명: 여러 작업을 정해진 순서로 잘 맞춰 진행하는 지휘)
- 비동기 처리(설명: 기다리지 않고 다른 일도 하면서 뒤에서 계속 작업하는 방식)
- 인메모리 저장소(설명: 일단 서버 메모리에만 저장하는 가벼운 임시 보관함)

## 아키텍처 개요
- Service: `ConversionOrchestrator`
  - 단계: 분석 → 추출 → (옵션)OCR/LLM 합성 → EPUB 생성 → 검증
  - 상태 저장: `ConversionJobStore`(인메모리)
  - 결과물: EPUB 바이트, 메타정보, 진행률
- API: `app/api/v1/conversion.py`
  - `POST /start`: 파일 업로드 → 작업 생성/시작 → `conversion_id` 반환
  - `GET /status/{id}`: 작업 상태/진행률 조회
  - `GET /download/{id}`: 완료된 EPUB 다운로드
  - `DELETE /cancel/{id}`: 작업 취소

## 단계 정의(파이프라인)
1) 분석(설명: PDF가 글 중심인지, 스캔 이미지인지 파악)
2) 추출(설명: 글 중심이면 텍스트를, 스캔이면 이미지 추출)
3) OCR/LLM(옵션, 설명: 스캔이면 글자 인식과 이미지 설명 합성)
4) EPUB 생성(설명: 장/페이지를 XHTML로 묶어 전자책 만들기)
5) 검증(설명: EPUB 기본 구조가 맞는지 빠른 점검)

## 데이터 모델(간단)
- JobState: `PENDING | PROCESSING | COMPLETED | FAILED | CANCELLED`
- ConversionJob: `id, filename, size, ocr_enabled, state, progress, message, created_at, updated_at, steps[], result_bytes?`

## 확장/대체 계획
- 인메모리 저장소 → Redis/DB 저장소로 교체 가능한 인터페이스 유지.
- 백그라운드 실행: 현재는 `asyncio.create_task`, 후속에 Celery/RQ로 대체.
- 상태 브로드캐스트: 후속에 WebSocket/SSE로 반영.

## 품질/테스트
- `make fmt && make lint && make test` 모두 녹색 상태 유지.
- mypy/ruff 기준을 지키는 타입 명시와 간결한 함수(단일 책임) 설계.

## API 계약 요약
- 시작 응답: `{ success, message, data: { conversion_id, status, progress } }`
- 상태 응답: `{ success, data: { status, progress, current_step, error_message? } }`
- 다운로드: `application/epub+zip` 스트리밍, 헤더에 유효성 정보 포함.

