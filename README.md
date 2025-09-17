# Python PDF → EPUB 변환기 (재구축 중)

이 저장소는 기존 Node.js/Vite 기반 웹 앱을 정리하고, **파이썬**으로 변환 파이프라인을 다시 구현하기 위한 초기화 상태입니다.

## 현재 상태
- [x] 레거시 프런트엔드/타입스크립트 코드 제거
- [x] 파이썬 프로젝트 골격(`app/`) 생성
- [ ] PDF 파서 및 OCR 모듈 구현
- [ ] EPUB 빌더 구현
- [ ] CLI/REST 인터페이스 제공

## 개발 환경
- Python 3.12 이상
- (예정) 가상환경 예시: `python -m venv .venv && source .venv/bin/activate`
- 종속성 관리: `requirements.txt` (추후 poetry/uv로 전환 가능)

## 다음 단계
1. `docs/functional_spec.md` 기반으로 모듈 뼈대 작성
2. PyPDF2/pdfminer.six로 텍스트 및 이미지 추출 실험
3. pytesseract를 이용한 OCR 프로토타입 구현
4. ebooklib을 활용한 EPUB 패키징 PoC 작성

## 품질 검사 명령
1. `pip install -r requirements.txt`로 품질 도구를 설치합니다.
2. `make fmt` — 코드 정렬 도구 `black(설명: 코드 모양을 통일해 주는 도구)`과 `ruff` 자동 수정으로 스타일을 맞춥니다.
3. `make test` — `pytest(설명: 파이썬 테스트를 자동으로 실행해 주는 도구)`로 단위 테스트를 실행합니다.
4. `make lint` — `ruff` 정적 분석과 `mypy(설명: 자료형 검사를 수행하는 도구)`로 잠재적인 문제를 점검합니다.

---
문의/작업 로그는 `docs/todo.md` 및 `docs/refactoring_changes.md`에 기록해 주세요.
