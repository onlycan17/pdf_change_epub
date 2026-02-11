# 2026-02-11 Conversion E2E Smoke Script

## [배경]
- 현재 변환/다운로드 기능은 화면에서 동작하지만, 로컬 실행 환경에서 "실제 EPUB 생성 + 다운로드"를 한 번에 검증하는 전용 스크립트가 없습니다.
- 수동 확인은 반복 비용이 크고, 실패 지점을 추적하기 어렵습니다.

## [계획]
- `scripts/smoke_conversion.sh`를 추가해 아래 순서로 자동 점검합니다.
  1. `/api/v1/conversion/start`로 PDF 업로드
  2. `/api/v1/conversion/status/{id}` 폴링으로 완료/실패 판별
  3. `/api/v1/conversion/download/{id}`로 결과 다운로드
  4. 다운로드 파일의 EPUB 필수 구조(압축 파일, `mimetype`, `META-INF/container.xml`) 검증
- 실패 시 API 응답 원문과 상태를 출력해 원인 파악 시간을 단축합니다.
- README에 실행 방법을 추가해 문서/코드 동기화를 유지합니다.

## [영향도]
- 애플리케이션 런타임 로직에는 영향이 없습니다.
- 개발/검증 편의성만 향상됩니다.
- CI와 독립적으로 로컬 점검이 가능해집니다.
