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
- `VITE_GOOGLE_ALLOWED_ORIGINS`: 선택 사항. 허용할 접속 주소를 쉼표로 구분해 지정
- `VITE_API_KEY`: 기존과 동일(백엔드 `SECURITY_API_KEY`와 일치)

로컬 개발 참고:
- `VITE_GOOGLE_ALLOWED_ORIGINS`가 비어 있더라도 개발 환경에서는 아래 기본 주소를 자동 허용합니다.
  - `http://localhost:3000`
  - `http://127.0.0.1:3000`
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`
- 운영 환경에서는 허용 원본을 명시적으로 설정하는 방식을 유지합니다.

## Google Cloud Console 설정(필수)

`400 오류: origin_mismatch`가 뜨면 아래 설정이 빠진 경우가 대부분입니다.

### 1) OAuth 클라이언트(웹) - Authorized JavaScript origins

Google Identity Services는 현재 접속한 **출처(origin)** 가 OAuth 클라이언트 설정에 등록되어 있어야 합니다.

- Console: `APIs & Services` -> `Credentials` -> `OAuth 2.0 Client IDs` -> (해당 Client)
- `Authorized JavaScript origins`에 아래처럼 **스킴/호스트/포트만** 추가합니다 (경로는 넣지 않음)

예시(운영):
- `https://www.pdf-epub.kr`
- `https://pdf-epub.kr`
- `https://www.pdf-epub.co.kr`
- `https://pdf-epub.co.kr`

예시(개발):
- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:5173`
- `http://127.0.0.1:5173`

주의:
- `http://`는 일반적으로 `localhost` 외에는 허용되지 않습니다. 운영은 `https://`를 사용하세요.
- 실제로 접속하는 주소와 1글자라도 다르면(origin이 다르면) `origin_mismatch`가 납니다.

### 2) OAuth 동의 화면 - Authorized domains

Console: `APIs & Services` -> `OAuth consent screen`

- `Authorized domains`에 `pdf-epub.kr` (필요 시 `pdf-epub.co.kr`)을 추가합니다.

## 플로우
1) 사용자가 `frontend/src/pages/LoginPage.tsx`에서 Google 버튼 클릭
2) Google Identity Services가 `id_token`을 프론트로 전달
3) 프론트가 `POST /api/v1/auth/google`로 `id_token`을 전달
4) 백엔드가 `id_token`을 검증(위조 방지)하고 사용자 정보(email, sub 등) 추출
5) 백엔드가 우리 서비스용 JWT를 발급해 응답
6) 백엔드가 인증 쿠키를 설정하고, 프론트는 현재 사용자 정보를 다시 조회한 뒤 `/upload` 등 다음 화면으로 이동

## 보안 주의
- `APP_GOOGLE_CLIENT_ID`는 공개되어도 큰 문제는 없지만, 운영에서는 정확히 설정해야 검증이 안전합니다.
- `APP_SECRET_KEY`(JWT 서명키)는 절대 노출되면 안 됩니다.
- 현재 구현은 Google 사용자 정보를 내부 사용자 저장소에 반영하고, 이후 일반 로그인과 동일한 인증 상태로 처리합니다.
