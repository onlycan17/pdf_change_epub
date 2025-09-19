# VSCode Python 환경 설정 TODO

## 작업 목표
PDF to EPUB 변환기 프로젝트의 Python 개발 환경을 VSCode에서 최적화합니다.

## 진행 상황
- [ ] .vscode 디렉토리 생성
- [ ] Python 확장자 설정 파일 작성 (settings.json)
- [ ] 디버깅 설정 파일 작성 (launch.json)
- [ ] 테스트 실행 설정 파일 작성 (tasks.json)
- [ ] Python 개발 환경 검증 및 테스트
- [ ] 프로젝트 문서에 설정 완료 기록

## 세부 작업 내용

### 1. .vscode 디렉토리 생성
- [ ] 프로젝트 루트에 .vscode 디렉토리 생성

### 2. Python 설정 (settings.json)
- [ ] Prettier/Black 코드 포맷팅 적용
- [ ] mypy 타입 검사 설정 추가
- [ ] pytest 테스트 실행 환경 설정
- [ ] Python linting (flake8) 설정 추가
- [ ] Intellisense 및 자동 완성 최적화

### 3. 디버깅 설정 (launch.json)
- [ ] FastAPI 애플리케이션 디버깅 설정
- [ ] 환경 변수 로딩 설정 추가
- [ ] 디버그 포트 및 실행 옵션 설정

### 4. 작업 실행 설정 (tasks.json)
- [ ] Python 가상 환경 활성화 태스크
- [ ] 테스트 실행 자동화 태스크
- [ ] 코드 포맷팅 및 린팅 실행 태스크

### 5. Python 확장자 권장 설정
- [ ] 프로젝트 루트에 `.vscode/settings.json` 에 Python 확장자 기본 설정 추가
- [ ] 모든 개발자가 동일한 환경에서 작업할 수 있도록 설정

## 검증 항목
- [ ] VSCode에서 Python 개발 환경 정상 로드 확인
- [ ] 코드 포맷팅이 Prettier/Black 규칙에 맞게 동작하는지 확인
- [ ] 타입 검사(mypy)가 VSCode에서 실시간으로 동작하는지 확인
- [ ] 디버깅 설정이 FastAPI 애플리케이션에서 정상 동작하는지 확인
- [ ] 테스트 실행이 VSCode 태스크에서 정상 동작하는지 확인
