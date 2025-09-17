# 메모이제이션 최적화 작업 문서

## 1. PRD(요구사항)
- **목표**: 변환 진행 화면과 관련 훅에서 불필요한 재연산·재렌더를 줄여 사용자 반응 속도를 개선한다.
- **사용자 가치**: 긴 처리 과정에서도 UI가 덜 깜박이고, 진행률/타이머가 안정적으로 업데이트된다.
- **성공 기준**: React Profiler 기준 `ConversionProgress`의 재렌더 횟수가 옵션 변경 없이 타이머 틱마다 한 번 이하로 유지된다.

## 2. 아키텍처 명세
- `usePDFConversion`: 진행률 콜백, 상태 리셋 로직을 메모이제이션하고 스테이지 업데이트를 불변/배치 방식으로 최적화.
- `ConversionProgress`: 단계(step) 구성과 파생 값(progress, currentStep)을 `useMemo`/`useCallback`으로 감싸 재계산 최소화.
- 필요 시 `useRef`를 사용해 오케스트레이터 인스턴스를 재활용.

## 3. UI/UX 명세
- 화면 동작은 기존과 동일해야 하며, 로딩/취소/단계 안내 UX 유지.
- 타이머와 진행률 표시는 계속 초 단위로 업데이트되지만 다른 영역은 불필요한 재랜더링 없이 유지되어야 한다.

## 4. 기술 스택 명세
- React 18 hooks (`useMemo`, `useCallback`, `useRef`, `startTransition` 필요 시 검토).
- React Profiler로 사전/사후 비교 (수동 캡처 계획).

## 5. 기능 명세
1. `usePDFConversion` 내부에서 스테이지 배열 업데이트를 함수형 갱신 + `useMemo`로 변환하여 동일 progress 콜백 인스턴스 유지.
2. `ConversionProgress`에서 단계 배열을 `useMemo`로 생성하고, `updateStepStatus`를 `useCallback`으로 정의해 state 설정을 안정화.
3. 진행률/현재 단계 계산을 `useMemo`로 최적화.
4. 변경 이후 Profiler로 재렌더 횟수 확인 (수동) 및 결과 메모.

## 6. API 명세
- 외부 API 변화 없음. `usePDFConversion` 반환 타입 유지.

## 7. ERD / 테이블 명세
- 영향 없음.

## 8. TODO / TASK
- [x] usePDFConversion 스테이지 업데이트 최적화
- [x] ConversionProgress 단계/핸들러 메모이제이션
- [ ] 수동 Profiler/로그 확인 및 회귀 테스트
- [x] 자동화 검사 수행
- [x] docs/todo.md 반영

## 9. 버전 이력
- **2025-01-28**: 메모이제이션 최적화 작업 계획 수립.
