# 2026-02-11 paddlepaddle 설치 호환성 수정 계획

## 배경
- Python 3.11/macOS 환경에서 `paddlepaddle==2.6.1` 설치가 실패했습니다.
- `pip` 인덱스 기준으로 2.x 계열은 `2.6.2`가 제공되며, `2.6.1`은 현재 환경에서 사용 가능한 배포본(미리 빌드된 설치 파일)이 없습니다.

## 목표
- 의존성 설치 실패를 해소하여 개발 환경을 안정적으로 재현합니다.
- OCR 파이프라인의 기존 동작을 유지합니다.

## 변경 범위
- `requirements.txt`
  - `paddlepaddle==2.6.1` → `paddlepaddle==2.6.2`

## 검증 계획
1. 백엔드 자동 검사
- `PYTHON=.venv311/bin/python make fmt`
- `PYTHON=.venv311/bin/python make lint`
- `PYTHON=.venv311/bin/python make test`

2. 프론트엔드 자동 검사(회귀 확인)
- `cd frontend && npm run lint`
- `cd frontend && npm run type-check`
- `cd frontend && npm run build`
- `cd frontend && npx prettier --check .`

## 영향도
- 패키지 마이너 패치 버전(문제 수정 수준의 작은 버전) 상향으로 설치 호환성만 개선됩니다.
- API/DB 스키마 및 애플리케이션 기능 동작에는 직접 영향이 없습니다.
