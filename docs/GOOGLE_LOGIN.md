# 구글 간편 로그인 추가

## 목표
사용자가 비밀번호 없이 Google 계정으로 로그인할 수 있게 합니다.

## 방식(쉽게 설명)
- 프론트에서 구글 로그인 버튼을 누르면 구글이 "이 사람이 진짜 구글 계정 주인"인지 확인하고,
  그 결과로 `id_token`(신분증 같은 토큰)을 내려줍니다.
- 백엔드는 그 `id_token`이 진짜인지 검증한 뒤, 우리 서비스용 JWT(출입증)를 발급합니다.

## 환경변수
백엔드(서버):
- `APP_GOOGLE_CLIENT_ID`: 구글 OAuth 클라이언트 ID (id_token의 audience 검증에 사용)

프론트(브라우저, Vite):
- `VITE_GOOGLE_CLIENT_ID`: 구글 로그인 버튼 초기화에 사용
- `VITE_API_KEY`: 기존과 동일(백엔드 `SECURITY_API_KEY`와 일치)

## 플로우
1) 사용자가 `frontend/src/pages/LoginPage.tsx`에서 Google 버튼 클릭
2) Google Identity Services가 `id_token`을 프론트로 전달
3) 프론트가 `POST /api/v1/auth/google`로 `id_token`을 전달
4) 백엔드가 `id_token`을 검증(위조 방지)하고 사용자 정보(email, sub 등) 추출
5) 백엔드가 우리 서비스용 JWT를 발급해 응답
6) 프론트가 JWT를 `localStorage`에 저장하고 `/upload`로 이동

## 보안 주의
- `APP_GOOGLE_CLIENT_ID`는 공개되어도 큰 문제는 없지만, 운영에서는 정확히 설정해야 검증이 안전합니다.
- `APP_SECRET_KEY`(JWT 서명키)는 절대 노출되면 안 됩니다.
- 이 구현은 "로그인"까지만 포함하며, 사용자 DB 저장/계정 연결(회원가입) 기능은 후속 확장 포인트입니다.
