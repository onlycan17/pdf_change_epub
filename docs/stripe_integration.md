# 토스페이먼츠 결제 연동 설계

## 1. 목표
- PDF to EPUB 서비스의 구독형 결제를 토스페이먼츠로 전환한다.
- 월 구독(`monthly`) / 연 구독(`yearly`)을 지원한다.
- 연 구독은 월 구독 대비 10% 할인 정책으로 노출한다.
- 구독별 업로드 용량을 변환 API에서 강제한다.

## 2. 아키텍처 개요
```text
[React Web] -- 플랜 선택 --> [FastAPI /api/v1/billing]
      |                                     |
      | 결제 성공/실패 URL                  |
      v                                     v
[브라우저 결제창] <- Redirect ---- [Toss Payments API]
      |
      v
[FastAPI 이벤트/웹훅 처리] --> 사용자 플랜 상태 반영
```

## 3. API 설계
| Method | Path | 설명 |
| ------ | ---- | ---- |
| GET | `/api/v1/billing/plans` | `free`/`monthly`/`yearly` 플랜 목록 조회 |
| POST | `/api/v1/billing/checkout/session` | 구독/일회성 결제 Checkout 세션 생성 |
| POST | `/api/v1/billing/one-time` | 단일 결제 Checkout 세션 생성 |
| POST | `/api/v1/billing/portal/session` | 결제 관리 URL 생성(현재 하위 호환용 고정 URL) |

## 4. 백엔드 처리 규칙
- `StripeService` 클래스명을 유지해 기존 라우트 의존성을 깨지 않게 하되 내부는 Toss API 기반으로 사용.
- 플랜 코드 정규화는 `free`, `monthly`, `yearly`로 통일.
- 월간/연간 가격 및 할인율은 `app/services/subscription_plans.py` 기준으로 계산.
- 업로드 한도는 동일 규칙으로 변환 API에서 계산:
  - free: 25MB
  - monthly: 300MB
  - yearly: 500MB

## 5. 환경 변수
- `APP_TOSS_SECRET_KEY`
- `APP_TOSS_WEBHOOK_SECRET`
- `APP_TOSS_PRICE_MONTHLY`
- `APP_TOSS_PRICE_YEARLY`
- `APP_TOSS_SUCCESS_URL`
- `APP_TOSS_CANCEL_URL`
- `APP_TOSS_API_BASE_URL`
- `APP_TOSS_CHECKOUT_BASE_URL`

## 6. 작업 체크리스트
- [x] `/api/v1/billing/plans` 추가
- [x] 결제 세션 라우트를 토스 API 연동 래퍼로 교체
- [x] 업로드 한도 플랜 기반 계산 반영
- [ ] Toss Webhook 수신/재계산 파이프라인 연결(다음 단계)
- [ ] 결제 실패/환불 정책 문서 및 상태 동기화 규칙 정립
