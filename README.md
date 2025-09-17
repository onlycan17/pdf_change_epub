# Python PDF → EPUB 변환기 (재구축 중)

이 저장소는 기존 Node.js/Vite 기반 웹 앱을 정리하고, **파이썬**으로 변환 파이프라인을 다시 구현하기 위한 초기화 상태입니다. 특히 한국어 처리에 최적화되고 React 기반 웹 인터페이스를 제공합니다.

## 프로젝트 개요
PDF → EPUB 변환기는 스캔된 문서를 포함한 PDF 파일을 EPUB 전자책 형식으로 변환하는 도구입니다. OCR 기술과 머신러닝을 활용하여 텍스트 추출 및 문맥 연결을 지원하며, 특히 한국어 문서에 대한 높은 정확도를 목표로 합니다.

### 주요 특징
- **한국어 최적화**: Tesseract OCR과 한국어 언어팩을 사용하여 한국어 문서의 높은 인식 정확도 제공
- **다중 인터페이스**: CLI, REST API, 웹 인터페이스(React) 제공
- **고급 처리**: 텍스트 기반 PDF와 스캔된 PDF 모두 처리 가능
- **확장 가능성**: 마이크로서비스 아키텍처를 기반으로 한 확장 가능한 구조

## 현재 상태
- [x] 레거시 프런트엔드/타입스크립트 코드 제거
- [x] 파이썬 프로젝트 골격(`app/`) 생성
- [ ] PDF 파서 및 OCR 모듈 구현
- [ ] EPUB 빌더 구현
- [ ] CLI/REST 인터페이스 제공
- [ ] React 기반 웹 프론트엔드 개발

## 개발 환경
- Python 3.12 이상
- Node.js 18+ (React 프론트엔드용)
- (예정) 가상환경 예시: `python -m venv .venv && source .venv/bin/activate`
- 종속성 관리: `requirements.txt` (백엔드), `package.json` (프론트엔드)

## 문서
- [제품 요구사항 문서 (PRD)](docs/improved_PRD.md)
- [기능 명세서](docs/functional_spec.md)
- [UI/UX 명세서](docs/ui_spec.md)
- [기술 스택 명세서](docs/tech_stack.md)
- [아키텍처 설계서](docs/architecture.md)
- [데이터베이스 스키마](docs/database_schema.sql)
- [개발 계획](docs/development_plan.md)

## 다음 단계
1. `docs/functional_spec.md` 기반으로 모듈 뼈대 작성
2. PyPDF2/pdfminer.six로 텍스트 및 이미지 추출 실험
3. pytesseract를 이용한 OCR 프로토타입 구현 (한국어 언어팩 포함)
4. ebooklib을 활용한 EPUB 패키징 PoC 작성
5. FastAPI 기반 REST API 개발
6. React 기반 웹 프론트엔드 개발

## 품질 검사 명령
1. `pip install -r requirements.txt`로 품질 도구를 설치합니다.
2. `make fmt` — 코드 정렬 도구 `black(설명: 코드 모양을 통일해 주는 도구)`과 `ruff` 자동 수정으로 스타일을 맞춥니다.
3. `make test` — `pytest(설명: 파이썬 테스트를 자동으로 실행해 주는 도구)`로 단위 테스트를 실행합니다.
4. `make lint` — `ruff` 정적 분석과 `mypy(설명: 자료형 검사를 수행하는 도구)`로 잠재적인 문제를 점검합니다.

## 기여하기
1. 이 저장소를 포크합니다.
2. 새 기능 브랜치를 만듭니다: `git checkout -b feature/새로운기능`
3. 변경 사항을 커밋합니다: `git commit -am '새로운 기능 추가'`
4. 브랜치에 푸시합니다: `git push origin feature/새로운기능`
5. 풀 리퀘스트를 생성합니다.

---
문의/작업 로그는 `docs/todo.md` 및 `docs/refactoring_changes.md`에 기록해 주세요.
