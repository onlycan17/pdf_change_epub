# 2026-03-17 한글 OCR 개선 계획

## 배경
- 현재 스캔 PDF 경로의 OCR 읽기 엔진은 실제 구현 기준으로 `pytesseract`입니다.
- 한글 문서는 Tesseract 단독 인식 품질이 낮아, 글자를 처음부터 잘못 읽는 경우가 자주 발생합니다.
- 이후 LLM이 문맥을 다듬더라도, 원문 글자를 잘못 읽은 상태에서는 품질 회복에 한계가 있습니다.
- README와 일부 문서에는 PaddleOCR가 적혀 있지만 실제 코드와 불일치합니다.

## 목표
- 기본 OCR 읽기 엔진을 `PaddleOCR 우선, Tesseract 폴백` 구조로 전환합니다.
- OCR 신뢰도(얼마나 자신 있게 읽었는지)가 낮은 결과만 선택적으로 LLM 보정을 추가합니다.
- OCR 엔진이 일부 환경에서 준비되지 않아도 변환 전체가 멈추지 않도록 안전한 폴백 경로를 유지합니다.
- 설정, 테스트, 문서를 실제 구현과 맞춥니다.

## 비목표
- 모든 페이지를 멀티모달 LLM으로 직접 읽게 바꾸지 않습니다.
- 이미지 설명용 멀티모달 분석을 전면 제거하지 않습니다.
- EPUB 렌더링 구조 자체를 이번 변경에서 다시 설계하지 않습니다.

## 설계 요약
### 1. OCR 엔진 선택
- OCR 엔진 어댑터(연결 부품) 계층을 도입합니다.
- 기본 엔진은 `paddle`, 폴백 엔진은 `tesseract`로 둡니다.
- PaddleOCR import 또는 초기화에 실패하면 자동으로 Tesseract로 내려갑니다.

### 2. OCR 결과 표준화
- 엔진이 달라도 결과는 같은 구조로 맞춥니다.
- 공통 출력:
  - `text`
  - `confidence`
  - `bounding_boxes`
  - `equation_images`
  - `engine`

### 3. 저신뢰 LLM 보정
- OCR confidence가 설정값보다 낮고, 멀티모달 LLM이 활성화된 경우에만 보정을 시도합니다.
- 입력값은 `페이지 이미지 + OCR 원문`입니다.
- 출력은 "뜻을 바꾸지 않고 읽기 오류만 고친 텍스트"로 제한합니다.
- LLM 실패 시 즉시 OCR 원문을 유지합니다.

### 4. 설정
- `OCR_ENGINE`: 기본 OCR 엔진
- `OCR_FALLBACK_ENGINE`: 폴백 엔진
- `OCR_LLM_CORRECTION_THRESHOLD`: 저신뢰 LLM 보정 임계값
- `OCR_LLM_MAX_PAGES_PER_DOCUMENT`: 문서당 LLM 보정 최대 페이지 수

## 영향 범위
- `app/services/agent_service.py`
  - OCR 엔진 추상화 적용
  - Paddle/Tesseract 선택 및 폴백
  - 저신뢰 OCR LLM 보정 추가
- `app/core/config.py`
  - OCR 엔진/보정 설정 추가
- `tests/test_scan_pdf_processor.py`
  - 엔진 선택, 폴백, 저신뢰 보정 테스트 추가
- `tests/test_config.py`
  - 새 OCR 설정 기본값/환경변수 테스트 추가
- `README.md`
  - 실제 OCR 동작 구조를 반영해 설명 수정
- `requirements.txt`
  - PaddleOCR 의존성 반영

## 검증 계획
1. `make fmt`
2. `make lint`
3. `make test`
4. `cd frontend && npm run lint`
5. `cd frontend && npm run type-check`
6. `cd frontend && npm run build`
7. `cd frontend && npx prettier --check .`

## 롤백 전략
- OCR 엔진 기본값을 `tesseract`로 되돌리면 즉시 이전 방식으로 복귀할 수 있습니다.
- 저신뢰 LLM 보정은 임계값 또는 최대 페이지 수를 조정해 쉽게 비활성화할 수 있습니다.
