# 기능 명세서 (Python 버전)

## 1. 시스템 개요
- **모듈 구조**
  - `app/` 내부에 도메인 중심 모듈 구성 예정
    - `pdf_loader`: PyPDF2/pdfminer.six 기반 텍스트 추출 및 메타데이터 수집
    - `scan_detector`: 페이지 텍스트/이미지 비율 기반 스캔 여부 판정
    - `ocr_engine`: pytesseract 또는 cloud OCR 연동
    - `normalizer`: Markdown 중간 표현 생성, 언어별 정규화 로직 포함
    - `epub_builder`: ebooklib 등으로 EPUB3 패키징, 목차/메타 반영
    - `orchestrator`: 상기 모듈 조합, 에러 처리/로깅/파이프라인 조율

## 2. 입력/출력 사양
- **입력**: 로컬 PDF 파일 경로 또는 바이너리, 옵션(JSON)
- **출력**: EPUB 바이너리(파일 저장/바이트 반환), 변환 리포트(dict)
- **옵션 예시**
  ```json
  {
    "language": "auto",
    "force_ocr": false,
    "include_images": true,
    "metadata_override": {
      "title": "Custom Title",
      "author": "Converted"
    }
  }
  ```

## 3. 모듈 상세
| 모듈 | 책임 | 주요 의존성 |
|------|------|-------------|
| `pdf_loader` | PDF 페이지 텍스트/이미지 추출, 메타 수집 | PyPDF2/pdfminer.six |
| `scan_detector` | 텍스트 길이, 이미지 수 기반 스캔본 판정 | 자체 로직 |
| `ocr_engine` | 이미지 → 텍스트 변환, 언어 선택 | pytesseract + Tesseract CLI |
| `normalizer` | Markdown 생성, 문단/표/목차 처리 | markdown-it-py 등 | 
| `epub_builder` | XHTML 템플릿 생성, EPUB 패키징 | ebooklib | 
| `orchestrator` | 전체 파이프라인 실행, 오류 수집 | 위 모듈 통합 |

## 4. 오류 처리 규칙
- 모든 모듈은 `ConversionError`(커스텀 예외) 계층 사용
- 실패 시 원인, 페이지 번호, stage 정보를 담아 상위로 전달
- OCR 실패 시 fallback: 원본 텍스트 존재 시 사용, 없으면 빈 문자열 + 경고 리포트

## 5. 로깅/모니터링
- 표준 로깅: `structlog` 또는 `logging` 구성, JSON 포맷 지원
- 주요 이벤트: 시작/종료, 스캔 감지 결과, OCR 진행률, EPUB 패키징 상태
- 향후 APM 연동 대비 추상화된 logger 인터페이스 유지

## 6. 테스트 전략
- Pytest 기반 유닛/통합 테스트
- 샘플 PDF fixture 3종 (텍스트, 스캔, 혼합)
- OCR 모듈은 Mocking + 실제 Tesseract 실행 스모크 테스트 분리
- EPUB 결과는 unzip 후 OPF/XHTML 구조 검사로 검증

## 7. 배포/실행
- 초기 단계는 CLI 진입점(`python -m app.main`) 제공
- 추후 FastAPI REST 엔드포인트 추가 시 동일 도메인 서비스 재사용
- Docker 이미지 빌드 가이드 준비(파이썬 런타임 + Tesseract 설치)

본 명세는 파이썬 전환 후 기본 구조를 정의하며, 구현이 진행되면서 세부 API 시그니처를 추가 기록합니다.
