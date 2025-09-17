# XSS 방지 조치 계획

## 배경
- `MarkdownPreview` 컴포넌트가 직접 문자열 치환으로 HTML을 생성하고 `dangerouslySetInnerHTML`에 삽입하고 있습니다.
- 현재는 `<script>` 태그나 이벤트 핸들러(`onclick` 등)를 제거하지 않기 때문에 잠재적인 XSS(설명: 악성 스크립트를 주입해 사용자 브라우저에서 실행시키는 공격) 위험이 존재합니다.
- TODO 리스트의 "보안 강화 → XSS 방지 조치" 항목을 이행하기 위해 신뢰 가능한 살균 라이브러리 도입이 필요합니다.

## 목표
1. DOMPurify(설명: 브라우저 환경에서 HTML을 깨끗하게 정화하는 오픈소스 라이브러리)를 사용하여 Markdown에서 생성된 HTML을 안전하게 살균합니다.
2. 살균 로직을 util 레이어로 추출해 재사용 가능하고 테스트 가능한 구조를 만듭니다.
3. Vitest 기반 단위 테스트를 추가하여 기본적인 XSS 페이로드가 차단되는지 검증합니다.
4. README 및 todo 문서를 업데이트하여 보안 조치가 적용되었음을 명시합니다.

## 작업 범위
- `dompurify` 패키지 설치 및 타입 정의 확인
- `src/utils` 아래에 `sanitizeHtml.ts` 유틸 생성
  - DOMPurify의 기본 설정을 적용하고 필요한 경우 `ALLOWED_URI_REGEXP` 등 화이트리스트 조정
  - 서버 사이드 실행 대비를 위해 `window` 존재 여부 체크
- `MarkdownPreview`에서 HTML 생성 후 `sanitizeHtml`을 거쳐 렌더링
- 테스트: `tests/utils/sanitizeHtml.test.ts` 작성, 스크립트·이벤트 제거 확인
- 관련 문서 업데이트 (TODO 체크, README 보안 섹션 보강)

## 리스크 및 대응
- SSR 환경이 아닐 경우 DOMPurify가 `window` 필요 → lazy import 혹은 `createDOMPurify` 사용으로 해결 (이번 프로젝트는 브라우저 중심이라 직접 사용 가능하지만 예외처리 추가)
- DOMPurify 기본 설정이 너무 엄격/느슨할 수 있음 → 테스트로 필요한 HTML 태그가 유지되는지 확인
- 번들 사이즈 영향 → 라이브러리 크기가 작아 영향 미미, 추후 번들 분석 시 확인

## 검증
1. `npm run test` → `tests/utils/sanitizeHtml.test.ts` 포함 4개 테스트 통과
2. `npm run check` → 포맷/린트/타입 검사 성공
3. 수동 검증 가이드: Markdown 입력창에 `<script>alert('xss')</script>` 삽입 시 미리보기에서 스크립트가 제거됨을 확인
