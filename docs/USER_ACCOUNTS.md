# 사용자 계정 저장(구글 로그인 연동)

## 목표
구글로 로그인한 사용자를 "우리 서비스 사용자"로 저장(지속성, persistence)합니다.
즉, 서버를 껐다 켜도 사용자 정보(이메일/가입 시각 등)가 남아 있어야 합니다.

비유로 설명하면,
- 구글이 발급해준 `id_token`은 "신분 확인"이고
- 우리 DB에 사용자를 저장하는 것은 "회원 명부에 이름을 적어두는 것"입니다.

## 저장 정책(데이터 최소화)
- provider: `google`
- provider_sub: 구글에서 내려주는 고유 식별자(`sub`)
- email: 구글 이메일(필수)
- name, picture: 있으면 저장(선택)

## 우리 서비스 user_id 규칙
- `google:{sub}` 형태로 저장합니다.
  - 예: `google:103984...`
- JWT의 `sub`도 이 값을 사용합니다.

## 중복/충돌 처리
- 같은 `provider_sub`로 들어오면 같은 user_id로 업데이트(upsert)
- 같은 email로 다른 sub가 들어오는 경우는 충돌로 보고 409로 처리(보수적)

## 저장소
- 현재 프로젝트는 ORM(SQLAlchemy) 없이 동작하므로, 표준 라이브러리 `sqlite3`로 구현합니다.
- DB 위치는 `DB_URL`(pydantic Settings)로 설정하며, 기본은 `sqlite:///./pdf_to_epub.db` 입니다.

## /api/v1/auth/me 동작 변경
- JWT의 `sub`로 DB에서 사용자를 조회해서 실제 email을 반환합니다.
- DB에 없으면 기존처럼 임시(fallback) 이메일로 응답합니다(테스트 계정/레거시 호환).
