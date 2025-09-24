# Stripe 결제 연동 설계

## 1. 목표
- PDF to EPUB 서비스의 유료 기능(사용량 기반/구독형)을 Stripe로 결제 가능하게 한다.
- Supabase를 단일 데이터 레이어로 사용하며, 결제 정보/이벤트는 Stripe Webhook → Supabase Edge Function → Postgres 순으로 동기화한다.
- MVP 단계에서는 카드 결제, 구독, 결제 상태 모니터링을 우선 지원한다.

## 2. 아키텍처 개요
```
[React Web] --Stripe Checkout/Portal--> [Stripe]
      |                                   |
      | (success/cancel)                  |
      v                                   v
[FastAPI Backend] <-- Webhook -- [Supabase Edge Function]
      |                                    |
      |  usage_cost 계산 / 주문 생성       |
      v                                    v
[Supabase Postgres: billing_invoice, customer_profile, one_time_order]
```

- **React**: Stripe.js + Elements로 Checkout 세션 생성/리디렉션.
- **FastAPI**: `/api/v1/billing/checkout` 등 API를 통해 Stripe 세션 생성, Supabase에 임시 레코드 작성.
- **Stripe Webhook**: Supabase Edge Function에서 수신, 결제 완료/실패 이벤트를 Postgres 테이블에 반영 후 FastAPI에 알림(optional).

## 3. 데이터 모델 (Supabase)
```sql
CREATE TABLE public.customer_profile (
    user_id uuid PRIMARY KEY,
    stripe_customer_id text NOT NULL,
    plan_code text DEFAULT 'free',
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE TABLE public.billing_invoice (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES public.customer_profile(user_id),
    stripe_invoice_id text,
    amount_total numeric(10,2) NOT NULL,
    currency text DEFAULT 'usd',
    status text NOT NULL,
    usage_cost numeric(10,2),
    period_start timestamptz,
    period_end timestamptz,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE public.one_time_order (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES public.customer_profile(user_id),
    stripe_payment_intent_id text,
    product_code text NOT NULL,
    amount numeric(10,2) NOT NULL,
    currency text DEFAULT 'usd',
    status text NOT NULL,
    created_at timestamptz DEFAULT now()
);
```
- `usage_cost`는 `docs/pricing_model.md`의 사용량 계산 결과를 저장.
- 월말 Edge Function이 `conversion_usage` 테이블을 합산하여 Stripe 청구서를 생성.

## 4. API 설계 (FastAPI)
| Method | Path | 설명 |
| ------ | ---- | ---- |
| POST | `/api/v1/billing/checkout/session` | 구독 플랜 또는 일회성 상품에 대한 Stripe Checkout 세션 생성 |
| POST | `/api/v1/billing/portal/session` | 사용자가 청구 내역을 관리할 수 있는 Stripe Portal 세션 생성 |
| POST | `/api/v1/billing/usage/finalize` | 월말 사용량을 기반으로 청구서 생성 (관리자/배치 용) |
| POST | `/api/v1/billing/one-time` | 변환 크레딧 등 단일 결제 상품에 대한 Checkout 세션 생성 |

- 응답 모델: `DataResponse` 포맷으로 `checkout_url`, `portal_url` 등을 반환.
- 보안: API 키/로그인 사용자 검증 후 Stripe 비공개 키는 FastAPI에서만 사용.

## 5. Webhook 흐름 (Supabase Edge Function)
1. Stripe → `https://<project>.functions.supabase.co/stripe-webhook`
2. Edge Function에서 시그니처 검증 후 이벤트 분기
   - `checkout.session.completed`: `customer_profile` 업데이트, 활성 플랜 지정
   - `invoice.payment_succeeded`: `billing_invoice` 업데이트, `status='paid'`
   - `invoice.payment_failed`: 알림 발송, `status='failed'`
3. 필요한 경우 FastAPI에 추가 알림(API 호출) or Supabase Realtime으로 프론트 알림.

## 6. 환경 변수
| 변수 | 설명 |
| ---- | ---- |
| `APP_STRIPE_SECRET_KEY` | FastAPI 서버에서 Stripe API 호출 시 사용 (환경 변수 접두사 `APP_`는 `Settings` 구성에 의해 자동 적용됨) |
| `APP_STRIPE_WEBHOOK_SECRET` | Edge Function에서 Stripe Webhook 검증용 비밀 값 |
| `APP_STRIPE_PRICE_BASIC` / `APP_STRIPE_PRICE_PRO` | Stripe Dashboard에서 생성한 구독 가격 ID |
| `APP_STRIPE_SUCCESS_URL` / `APP_STRIPE_CANCEL_URL` | Checkout 완료/취소 후 리디렉션 URL |

## 7. 작업 로드맵
1. Stripe Dashboard에서 제품/가격(Price) 및 Webhook 엔드포인트 생성
2. FastAPI에 `stripe` Python SDK 추가 및 Billing API 구현
3. Supabase Edge Function(`stripe-webhook`) 생성, 이벤트 처리 로직 작성
4. Supabase 테이블(`customer_profile`, `billing_invoice`, `one_time_order`) 배포 및 RLS 정책 적용
5. React에서 Stripe Elements/Checkout 연동 및 테스트 카드 결제 시나리오 검증
6. 월말 배치(Edge Function schedule 또는 FastAPI Cron)로 usage 기반 청구 프로세스 연결

## 8. 테스트 전략
- Stripe 테스트 모드(샌드박스)에서 카드/구독/취소 시나리오 수행
- Webhook 이벤트 재전송(Stripe Dashboard)으로 에러 처리 확인
- Supabase Postgres에 기록된 인보이스/사용량이 pricing_model의 계산과 일치하는지 검증

## 9. 향후 확장
- 한국 결제 수단(포트원) 병행 도입 시, `customer_profile`에 `payment_provider` 필드 추가하여 Stripe/PortOne 선택 가능하게 설계
- 기업 고객용 결제(Invoice, Wire Transfer) 지원 시 Stripe Billing의 수동 인보이스 기능 활용
- 환불/부분 환불 정책 정의 및 자동화
