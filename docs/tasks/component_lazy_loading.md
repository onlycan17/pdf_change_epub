# 컴포넌트 지연 로딩 작업 문서

## 1. PRD (요구사항)
- **목표**: 초기 번들 크기를 줄이고 첫 화면 진입 속도를 개선하기 위해 프리미엄 전용/후순위 페이지를 지연 로딩한다.
- **대상 페이지**: `Premium`, `Payment`, `Download` (사용 빈도가 낮거나 프리미엄 플로우에만 해당)
- **성공 기준**: Vite 번들 분석 기준 해당 페이지 코드가 별도 청크로 분리되고, 초기 번들 크기가 감소한다.

## 2. 아키텍처 명세
- **기술 선택**: React.lazy + Suspense 조합, fallback 으로 공용 로딩 컴포넌트 사용.
- **라우팅 구조**: 기존 `AppRoutes` 내부에서 lazy 컴포넌트를 import 하도록 변경, Suspense 래퍼 추가.
- **추가 요소**: 공용 로딩 UI를 `components/common` 폴더에 배치하여 재사용.

## 3. UI/UX 명세
- **로딩 UX**: 지연 로딩 시 전체 화면 중앙 정렬 스피너 표시 (기존 ProtectedRoute 로딩과 동일한 톤 유지)
- **일관성**: 라이트/다크 모드 모두 대응하도록 Tailwind utility 적용.

## 4. 기술 스택 명세
- **React.lazy**: 동적 import 로 코드 스플리팅 수행.
- **Suspense**: fallback UI 제공.
- **번들 분석**: `rollup-plugin-visualizer` 추가 검토(추후 작업) — 현재는 브라우저 devtools coverage로 확인.

## 5. 기능 명세
1. `App.tsx`에서 `Premium`, `Payment`, `Download`를 lazy import 로 변경.
2. 메인 라우트 블록을 `React.Suspense`로 감싸고 공용 fallback 컴포넌트 지정.
3. 공용 로딩 컴포넌트 `LoadingView` (가칭) 구현 — 재사용 가능하도록 props 설계.
4. 기존 Protected/Public Route 로딩 UI와 충돌 없도록 스타일 통일.
5. TODO 문서 및 작업 현황 업데이트.

## 6. API 명세
- 외부 API 호출 변화 없음.

## 7. ERD / 테이블 명세
- 영향 없음.

## 8. TODO / TASK
- [x] LoadingView 컴포넌트 설계/구현
- [x] App.tsx lazy import 및 Suspense 적용
- [x] 번들 분리 확인 (빌드 결과 별도 청크 생성 확인)
- [x] 자동화 검사 수행
- [x] docs/todo.md 업데이트

## 9. 버전 이력
- **2025-01-28**: 작업 문서 초안 작성 및 구현 계획 수립.
- **2025-01-28**: lazy 로딩 구현, 빌드 결과 확인 및 자동화 검사 완료.
