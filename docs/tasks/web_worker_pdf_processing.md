# Web Worker 기반 PDF 처리 작업 문서

## 1. PRD (요구사항)
- **목표**: PDF 파싱과 이미지 추출 같은 무거운 연산을 Web Worker로 이동해 메인 스레드 렌더링 지연을 최소화한다.
- **사용자 가치**: 대용량 PDF를 처리할 때도 UI가 끊기지 않고 반응성을 유지한다.
- **완료 조건**: 변환 흐름이 Worker를 통해 실행되고, Lighthouse TBT(총 블로킹 시간) 지표가 기존 대비 개선된다.

## 2. 아키텍처 명세
- **구성 요소**:
  - `PDFProcessorCore`: 실제 PDF 처리 로직(텍스트/이미지 추출, 메타데이터 수집)을 담당하는 순수 모듈.
  - `pdfWorker`: Worker 스레드 엔트리. Core를 호출해 결과를 반환.
  - `pdfProcessor` 퍼사드: 메인 스레드에서 Worker와 통신하는 래퍼.
- **통신 방식**: Comlink를 사용하여 RPC 스타일로 Worker 함수를 호출.
- **데이터 이동**: `ArrayBuffer`를 `Comlink.transfer`로 이동하여 복사 비용 최소화.

## 3. UI/UX 명세
- Worker 전환은 비동기이므로 기존 Progress UI를 유지. 메인 스레드 로딩 스피너는 `LoadingView` 재사용.
- 사용자 체감 성능 개선이 목표이며, 변환 결과 UI는 동일.

## 4. 기술 스택 명세
- **Comlink**: Worker와 메인 스레드 간 메시징 추상화.
- **Vite Worker**: `new Worker(new URL(...), { type: 'module' })` 패턴으로 번들.
- **PDF.js**: 기존 로직 유지, 단 Core 모듈로 분리.

## 5. 기능 명세
1. `pdfProcessorCore.ts`에서 기존 PDF 처리 로직 분리 및 Worker 친화적으로 캔버스 처리 개선.
2. `pdfProcessor.ts`는 Worker를 생성하고 Comlink로 API 호출. 유효성 검사/전처리는 메인 스레드에서 수행.
3. `pdfWorker.ts`는 Core를 사용해 `processPDF` 실행 후 결과 반환.
4. Worker에 전달되는 파일은 `ArrayBuffer`와 메타데이터를 이용해 재구성.
5. 기존 오케스트레이터(`conversionOrchestrator`)는 API 변경 없이 작동.

## 6. API 명세
- Worker API: `processPDF(buffer: ArrayBuffer, meta: { name: string; type: string; lastModified: number }) => PDFProcessingResult`
- 퍼사드 API: `pdfProcessor.processPDF(file: File)` (기존 시그니처 유지)

## 7. ERD / 테이블 명세
- 데이터베이스 영향 없음.

## 8. TODO / TASK
- [x] Core 모듈 분리 및 Worker 호환 코드 정리
- [x] Worker 엔트리 및 Comlink 통신 계층 구현
- [x] Conversion 오케스트레이터 연동 및 회귀 테스트
- [x] 자동화 검사 수행
- [x] docs/todo.md 반영

## 9. 버전 이력
- **2025-01-28**: Worker 기반 PDF 처리 설계 문서 초안 작성.
- **2025-01-28**: PDF 처리 Web Worker 적용, 자동화 검사 및 TODO 반영 완료.
