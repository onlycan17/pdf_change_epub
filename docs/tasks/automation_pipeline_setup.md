# 자동화 파이프라인 구축 계획

## 개요
- `make fmt`, `make test`, `make lint` 명령을 제공하여 코드 정렬, 테스트, 정적 분석을 한 번에 수행할 수 있는 기반을 만듭니다.
- Python 개발 흐름에 맞게 `black`, `ruff`, `mypy`, `pytest`를 사용합니다.

## 요구사항 정리
- `fmt` 명령: `black`과 `ruff format`으로 코드 스타일을 자동 정리합니다.
- `test` 명령: `pytest`로 단위 테스트(설명: 기능을 작은 조각으로 나눠서 검사하는 방법)를 수행합니다.
- `lint` 명령: `ruff` 정적 분석(설명: 코드를 실행하지 않고 문제를 찾아내는 방법)과 `mypy` 타입 검사(설명: 변수의 자료형이 올바른지 확인하는 방법)를 실행합니다.
- 모든 명령은 프로젝트 루트에서 실행되며, 실패하면 0이 아닌 종료 코드를 반환합니다.

## 작업 계획 (대분류 → 중분류 → 소분류)
1. 환경 정의
   1.1. `requirements.txt`에 품질 도구 의존성 추가
2. 빌드 스크립트 작성
   2.1. `Makefile` 생성
   2.2. 가독성을 위한 변수 및 `.PHONY` 선언 구성
   2.3. `fmt`, `test`, `lint`, `check` 타깃 정의 (`check`는 세 명령을 순차 실행)
3. 문서 및 TODO 업데이트
   3.1. `docs/todo.md`에 자동화 작업 항목 추가 및 상태 반영
   3.2. `docs/refactoring_changes.md`에 변경 이력 추가
   3.3. `README.md`에 새로운 명령 사용법 안내 추가
4. 검증
   4.1. 가상환경에서 `pip install -r requirements.txt`로 도구 설치
   4.2. `make fmt`, `make test`, `make lint` 순서대로 실행해 성공 여부 확인

## 검증 기준
- 세 가지 `make` 명령이 모두 성공적으로 종료
- 새로 추가한 문서와 기존 문서 내용이 일치
- 변경 사항이 Git 상태에 정확히 반영됨

## 진행 상황 요약 (2025-02-18)
- [x] `requirements.txt`에 품질 도구 버전을 추가했습니다.
- [x] `Makefile`에서 `fmt`, `test`, `lint`, `check` 타깃을 정의했습니다.
- [x] README와 TODO 등 문서를 최신 상태로 정리했습니다.
- [x] Husky(설명: Git 커밋 전에 자동으로 실행되는 스크립트를 관리하는 도구) `pre-commit` 및 `pre-push` 스크립트를 Python 품질 검사로 교체했습니다.
- [x] `.venv` 가상환경에서 `make fmt && make test && make lint`를 실행해 모두 성공함을 확인했습니다.
