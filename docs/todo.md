# PDF to EPUB 변환기 TODO 리스트 (Python 재구축 초기화)

## 현재 상태
- [ ] 파이썬 기반 아키텍처 설계 확정 (M0)
- [ ] 핵심 변환 파이프라인 구현 사전 조사 (M1 사전 단계)

## 현재 작업
### 품질 인프라 구축
- [x] 품질 도구 버전 결정 및 `requirements.txt` 반영 (2025-02-18)
- [x] `Makefile`으로 `fmt/test/lint/check` 타깃 정의 (2025-02-18)
- [x] README 및 관련 문서에 사용법 정리 (2025-02-18)
- [x] `make fmt && make test && make lint` 검증 로그 기록 (2025-02-18)

## 완료된 작업
- [x] 레거시 Node.js 코드 제거 및 Python 스켈레톤 생성 (2025-02-17)
- [x] 품질 인프라 1차 구축 (Makefile, 테스트, 린트) (2025-02-18)

## 다음 단계 후보
### 설계 및 연구
- [ ] PDF 파서 및 OCR 라이브러리 후보 평가 (PyPDF2, pdfminer.six, Tesseract 등)
- [ ] EPUB 생성 파이프라인 구성요소 정의 (ebooklib 등)
- [ ] 최소 기능 명세에 맞춘 CLI/서비스 API 결정

---

> 이 TODO 파일은 새로운 파이썬 프로젝트를 위한 기본 뼈대입니다. 모든 작업은 위 항목에 세분화하여 기록해 주세요.
