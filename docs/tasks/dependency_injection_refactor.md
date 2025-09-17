# 서비스 의존성 주입 개선 작업 문서

## 1. PRD(요구사항)
- **목표**: 서비스 레이어 간 강한 결합을 줄이고, 테스트/교체가 쉬운 구조로 개선한다.
- **사용자 가치**: 신뢰성 높은 서비스 운영(테스트 용이)과 기능 확장 시 빠른 대응.
- **완료 조건**: 핵심 서비스(`PDFProcessor`, `OCRProcessor`, `MarkdownConverter`, `ConversionOrchestrator`)가 인터페이스 기반으로 주입되고, 테스트 시 모킹이 가능하다.

## 2. 아키텍처 명세
- 서비스 인터페이스 정의(`src/services/types.ts`).
- 서비스 인스턴스를 생성/보관하는 `ServiceRegistry` 또는 factory 구현.
- 훅과 오케스트레이터는 registry에서 의존성 주입.

## 3. UI/UX 명세
- UI 변화 없음. 내부 구조 변경만 수행.

## 4. 기술 스택 명세
- TypeScript interface + 명시적 factory 함수.
- React Context 활용 가능 (필요 시).

## 5. 기능 명세
1. `ServiceRegistry` 유틸 생성: 기본 서비스들을 등록하고 가져오는 함수 제공.
2. `ConversionOrchestrator`를 인스턴스 의존 주입 방식으로 수정.
3. `usePDFConversion` 등에서 registry 경유로 서비스 사용.
4. 테스트 목적으로 registry 교체 가능하도록 API 제공.
5. docs/todo.md 및 문서 업데이트.

## 6. API 명세
- `registerService(name, instance)` / `getService(name)` / `withServiceOverrides(overrides, callback)` 등.

## 7. ERD / 테이블 명세
- 변경 없음.

## 8. TODO / TASK
- [x] 서비스 타입 정의 및 registry 모듈 작성
- [x] 기존 서비스 인스턴스를 registry로 등록
- [x] 훅/오케스트레이터에서 registry 기반 의존성 사용
- [x] 자동화 검사 수행
- [x] docs/todo.md 반영

## 9. 버전 이력
- **2025-01-28**: 의존성 주입 개선 계획 수립.
- **2025-01-28**: 서비스 registry 도입 및 오케스트레이터/훅 주입 구조 개선 완료.
