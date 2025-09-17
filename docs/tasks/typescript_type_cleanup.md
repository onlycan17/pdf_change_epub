# TypeScript 타입 정리 계획

## 배경
- 최근 리팩토링 과정에서 서비스 계층의 타입 선언이 여러 위치로 분산되었고, 일부 인덱스 파일이 잘못된 경로를 참조하면서 TypeScript 컴파일 오류가 발생했습니다.
- `ConversionOrchestrator` 관련 인터페이스 파일에서 필요한 타입이 정의되지 않았고, OCR 서비스의 인덱스 파일은 상위 모듈을 정확히 다시 내보내지 못하고 있습니다.

## 문제 정의
- `ConversionOptions`, `ConversionResult` 타입을 찾을 수 없다는 오류로 빌드가 중단됩니다.
- `ocrProcessor` 폴더의 인덱스 파일이 잘못된 경로를 참조하여 순환 의존성 오류가 발생합니다.
- 인터페이스 파일과 구현 파일 사이에 타입 중복과 경로 부정확성이 존재합니다.

## 목표
1. 변환 오케스트레이터 타입 선언을 단일 소스(`conversionOrchestrator.interface.ts`)로 통합하고, 구현 파일이 이를 재사용하도록 정리합니다.
2. OCR 서비스 인덱스와 인터페이스 파일이 올바른 위치에서 타입과 구현을 불러오도록 경로를 수정합니다.
3. 관련 테스트 및 품질 검사(`npm run lint`, `npm run typecheck`)를 통해 오류가 재발하지 않도록 검증합니다.

## 작업 항목
- [x] `conversionOrchestrator.interface.ts`에 `ConversionOptions`, `ConversionProgress`, `ConversionResult` 타입 선언 추가 및 다른 모듈에서 사용할 수 있도록 내보내기.
- [x] `conversionOrchestrator.ts`에서 중복 타입 선언을 제거하고 인터페이스 파일을 참조하도록 수정.
- [x] `src/services/ocrProcessor/index.interface.ts`의 import 경로를 실제 구현 파일 위치로 수정.
- [x] `src/services/ocrProcessor/index.ts`에서 필요한 항목을 상위 모듈(`../ocrProcessor`)에서 재수출하도록 수정하여 순환 정의 제거.
- [x] 관련 문서(`docs/todo.md`)에 작업 진행 상황 반영.
- [x] `npm run lint`, `npm run typecheck` 실행으로 품질 상태 확인.

## 리스크 및 대응
- 타입 이동 시 다른 모듈이 신규 경로를 참조하지 않아 컴파일 오류가 발생할 수 있음 → 검색으로 기존 사용 위치 확인하고 일괄 치환.
- OCR 서비스 모듈이 브라우저 환경을 가정하므로 서버 측 테스트 실행 시 전역 객체 의존성 문제가 생길 수 있음 → 이번 작업에서는 경로 수정에 집중하고, 추가 목(mock) 필요 시 별도 작업으로 분리.

## 검증 방법
1. `npm run lint`
2. `npm run typecheck`
3. 오류 미발생 시 `docs/todo.md` 갱신 및 결과 보고
