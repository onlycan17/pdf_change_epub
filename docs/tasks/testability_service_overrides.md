# 테스트 용이성 향상 계획 (서비스 의존성 오버라이드)

## 배경
- 서비스 레이어가 Web Worker, Tesseract.js 등 브라우저 전용 기능에 의존하고 있어 순수 함수 단위 테스트 작성이 어렵습니다.
- 기존 `registry.ts`는 서비스 인스턴스를 주입할 수 있는 구조지만, 테스트에서 간편하게 사용할 수 있는 InMemory(설명: 실제 외부 의존성을 제거하고 메모리에서만 동작하는 가짜 구현) 버전이 존재하지 않습니다.
- TODO 리스트의 "테스트 용이성 향상" 항목은 테스트 환경에서 쉽게 교체 가능한 경량 구현과 스왑 도구 마련을 요구합니다.

## 목표
1. PDF/OCR/Markdown 서비스 각각에 대해 테스트 친화적인 InMemory 구현을 제공하고, 실제 서비스와 동일한 타입을 따르도록 합니다.
2. 테스트 코드에서 원하는 조합을 간단하게 주입할 수 있도록 헬퍼(`createTestServiceRegistry`, `withTestServices`)를 추가합니다.
3. 레지스트리 초기화 및 복구 시 부작용을 방지하기 위한 안전장치를 마련합니다.
4. Vitest(설명: Vite 기반 테스트 러너) 도입을 고려한 기본 테스트 예제를 작성해 서비스 스왑 방법을 문서화합니다.

## 작업 범위
- `src/services/testing/` 디렉터리 신설하여 InMemory 서비스 구현 추가
  - `inMemoryPdfProcessor.ts`
  - `inMemoryOcrProcessor.ts`
  - `inMemoryMarkdownConverter.ts`
  - 공통 헬퍼: `testServices.ts`
- `registry.ts`에 테스트 헬퍼와의 연동을 고려한 보조 함수 추가 (필요 시)
- 예시 테스트 파일(`tests/services/conversionOrchestrator.test.ts`) 작성하여 서비스 교체 사용법 시연
- NPM 스크립트에 `test` 명령 추가 및 Vitest 초기 설정 파일(`vitest.config.ts`) 생성
- 문서 업데이트: TODO 항목 상태 변경, 테스트 실행 가이드 README 보강

## 작업 항목
- [x] InMemory PDF Processor 구현 (페이지/메타데이터를 고정 데이터로 반환)
- [x] InMemory OCR Processor 구현 (입력 문자열을 간단히 가공)
- [x] InMemory Markdown Converter 구현 (페이지 텍스트를 합쳐 간단한 마크다운 생성)
- [x] 테스트용 서비스 레지스트리 헬퍼 작성
- [x] Vitest 설정 및 샘플 테스트 추가
- [x] NPM 스크립트/문서 업데이트 (README, todo.md)
- [x] `npm run check` + `npm run test` 실행으로 검증

## 리스크
- 브라우저 전용 API(`document`, `URL.createObjectURL`)가 테스트 환경에서 사용되면 실패할 수 있음 → InMemory 구현에서는 해당 API를 사용하지 않고 순수 함수로 구성.
- Vitest 도입 시 tsconfig 경로와 충돌 가능 → `tsconfig.node.json`을 확장하여 해결.
- 테스트가 실제 워커/외부 의존성을 호출하지 않도록 주의 → InMemory 인스턴스로만 구성하고, 문서화로 개발자 실수를 방지.

## 검증 계획
1. `npm run test` 명령으로 샘플 테스트 통과 확인
2. `npm run check`로 기존 포맷/린트/타입 검사 유지 확인
3. README에 추가한 테스트 가이드에 따라 신규 개발자가 환경 구성 가능한지 자체 점검
