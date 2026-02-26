# 토스 구독 결제(자동결제/빌링) 연동

## 목적
우리 서비스의 "월간/연간 구독"을 토스페이먼츠의 자동결제(빌링) 방식으로 처리합니다.

비유로 설명하면,
- 결제창에서 카드를 한번 등록해 "자동이체 카드"로 만들어 두고(= 빌링키 발급)
- 이후에는 카드 번호를 다시 묻지 않고 "등록된 카드"로 매달 자동 결제하는 구조입니다.

## 중요한 전제(현실적인 제한)
- 토스의 자동결제(빌링)는 별도 계약/리스크 검토가 필요한 경우가 있습니다.
- 개발/테스트 환경에서는 동작하지만, 운영 적용 전 토스 계약 상태를 확인해야 합니다.

## 용어 정리(쉬운 설명)
- customerKey: 우리 서비스에서 "구매자"를 식별하는 고유 키(사용자 ID 같은 것)
- authKey: 결제창에서 카드 등록이 끝난 뒤 리다이렉트 URL로 돌아올 때 받는 일회용 인증 키
- billingKey: 카드 정보를 대신하는 "자동결제용 키" (이 값을 저장해두고 반복 결제)

## 전체 흐름(카드 등록 + 첫 결제)
1) 프론트에서 구독 버튼 클릭
2) 백엔드에서 customerKey 생성 및 플랜(plan_code) 임시 저장
3) 프론트에서 Toss SDK `requestBillingAuth()` 호출
4) 성공 시 `authKey` + `customerKey`가 리다이렉트 URL로 전달됨
5) 프론트가 백엔드에 `authKey/customerKey` 전달
6) 백엔드가 토스 API로 billingKey 발급
7) 백엔드가 billingKey로 "첫 결제"를 승인(월간/연간 금액)
8) 성공하면 백엔드가 새 JWT 토큰(구독 플랜 반영)을 발급 → 프론트가 저장

## 우리 API 설계
- POST `/api/v1/billing/toss/billing-auth/start`
  - 입력: `{ plan_code: "monthly" | "yearly" }`
  - 출력: `{ client_key, customer_key, success_url, fail_url }`

- POST `/api/v1/billing/toss/billing-auth/complete`
  - 입력: `{ customer_key, auth_key }`
  - 동작: billingKey 발급 + 첫 결제 승인 + 구독 토큰 발급
  - 출력: `{ access_token, token_type, expires_in, plan_code }`

## 후속(정기 결제 스케줄링)
토스가 스케줄링을 대신해주지 않기 때문에,
"다음 결제일"에 우리가 스케줄러(Celery beat/cron)를 통해 billingKey 결제를 호출해야 합니다.
현재 구현은 "첫 결제 + 구독 상태 반영"까지 포함하며,
정기 결제 재시도/해지/연체 처리 등은 후속 작업으로 확장 가능합니다.
