"""Stripe Billing API"""

from __future__ import annotations

from datetime import timedelta
from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.models.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    BillingPlanData,
    BillingPlansResponse,
    OneTimeCheckoutRequest,
    OneTimeCheckoutResponse,
    PortalSessionRequest,
    PortalSessionResponse,
    TossBillingAuthCompleteRequest,
    TossBillingAuthCompleteResponse,
    TossBillingAuthCompleteData,
    TossBillingAuthStartRequest,
    TossBillingAuthStartResponse,
    TossBillingAuthStartData,
)
from app.services.subscription_plans import all_plans
from app.services.stripe_service import StripeService, get_stripe_service
from app.services.toss_subscription_service import (
    TossSubscriptionService,
    get_toss_subscription_service,
)
from app.core.auth_session import extract_access_token, set_auth_cookies
from app.core.config import Settings, get_settings
from app.api.v1.auth import verify_token, create_access_token

router = APIRouter()


def _require_billing_enabled(settings: Settings) -> None:
    if not settings.billing_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="결제 기능은 현재 준비 중입니다. 지금은 무료 기능과 후원으로 운영합니다.",
        )


def _extract_bearer_token(request: Request) -> str | None:
    return extract_access_token(request)


def _require_user_id(request: Request) -> str:
    token = _extract_bearer_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인이 필요합니다."
        )
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰이 유효하지 않습니다."
        )
    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="사용자 정보가 없습니다."
        )
    return sub


def _get_toss_subscription_service(
    settings: Settings = Depends(get_settings),
) -> TossSubscriptionService:
    return get_toss_subscription_service(settings)


def get_toss_subscription_service_factory(
    settings: Settings = Depends(get_settings),
) -> Callable[[], TossSubscriptionService]:
    return lambda: get_toss_subscription_service(settings)


@router.post("/checkout/session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    stripe_service: StripeService = Depends(get_stripe_service),
    settings: Settings = Depends(get_settings),
) -> CheckoutSessionResponse:
    """구독 또는 결제 Checkout 세션 생성"""

    _require_billing_enabled(settings)

    session = stripe_service.create_checkout_session(
        plan_code=request.plan_code,
        price_id=request.price_id,
        mode=request.mode or "subscription",
        success_url=request.success_url,
        cancel_url=request.cancel_url,
        customer_id=request.customer_id,
        metadata=request.metadata,
    )

    return CheckoutSessionResponse(
        data={"checkout_url": session.url, "session_id": session.id},
        message="결제 세션이 생성되었습니다.",
    )


@router.get("/plans", response_model=BillingPlansResponse)
async def get_billing_plans(
    settings: Settings = Depends(get_settings),
) -> BillingPlansResponse:
    """구독 플랜 목록 반환"""

    free_only = [plan for plan in all_plans() if plan.code == "free"]
    plans = [
        BillingPlanData(
            code=plan.code,
            label=plan.label,
            upload_limit_bytes=plan.upload_limit_bytes,
            upload_limit_mb=plan.upload_limit_mb,
            monthly_price_won=plan.monthly_price_won,
            yearly_price_won=plan.yearly_price_won,
            is_subscribed=False,
            recommended=False,
            annual_discount_rate=0,
            features=list(plan.features),
        )
        for plan in free_only
    ]
    return BillingPlansResponse(
        data={"plans": plans},
        message="현재는 무료 플랜만 제공됩니다.",
    )


@router.post("/checkout/one-time", response_model=OneTimeCheckoutResponse)
async def create_one_time_checkout(
    request: OneTimeCheckoutRequest,
    stripe_service: StripeService = Depends(get_stripe_service),
    settings: Settings = Depends(get_settings),
) -> OneTimeCheckoutResponse:
    """단일 결제 Checkout 세션 생성"""

    _require_billing_enabled(settings)

    if not request.price_id and not request.amount_cents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="price_id 또는 amount_cents 중 하나는 필요합니다.",
        )

    session = stripe_service.create_one_time_session(
        price_id=request.price_id,
        amount_cents=request.amount_cents,
        currency=request.currency or "usd",
        quantity=request.quantity,
        success_url=request.success_url,
        cancel_url=request.cancel_url,
        customer_id=request.customer_id,
        metadata=request.metadata,
        product_name=request.product_name,
    )

    return OneTimeCheckoutResponse(
        data={"checkout_url": session.url, "session_id": session.id},
        message="일회성 결제 세션이 생성되었습니다.",
    )


@router.post("/portal/session", response_model=PortalSessionResponse)
async def create_portal_session(
    request: PortalSessionRequest,
    stripe_service: StripeService = Depends(get_stripe_service),
    settings: Settings = Depends(get_settings),
) -> PortalSessionResponse:
    """청구 포털 세션 생성"""

    _require_billing_enabled(settings)

    session = stripe_service.create_portal_session(
        customer_id=request.customer_id,
        return_url=request.return_url,
    )

    return PortalSessionResponse(
        data={"portal_url": session.url},
        message="결제 관리 페이지를 준비했습니다.",
    )


@router.post(
    "/toss/billing-auth/start",
    response_model=TossBillingAuthStartResponse,
)
async def toss_billing_auth_start(
    request: Request,
    body: TossBillingAuthStartRequest,
    toss_service_factory: Callable[[], TossSubscriptionService] = Depends(
        get_toss_subscription_service_factory
    ),
    settings: Settings = Depends(get_settings),
) -> TossBillingAuthStartResponse:
    _require_billing_enabled(settings)
    user_id = _require_user_id(request)
    toss_service = toss_service_factory()
    data = toss_service.start_billing_auth(user_id=user_id, plan_code=body.plan_code)
    origin = (request.headers.get("Origin") or str(request.base_url)).rstrip("/")
    success_url = f"{origin}/payment/billing/success"
    fail_url = f"{origin}/payment/billing/fail"

    return TossBillingAuthStartResponse(
        data=TossBillingAuthStartData(
            client_key=data["client_key"],
            customer_key=data["customer_key"],
            success_url=success_url,
            fail_url=fail_url,
        ),
        message="자동결제 카드 등록을 시작합니다.",
    )


@router.post(
    "/toss/billing-auth/complete",
    response_model=TossBillingAuthCompleteResponse,
)
async def toss_billing_auth_complete(
    request: Request,
    response: Response,
    body: TossBillingAuthCompleteRequest,
    toss_service_factory: Callable[[], TossSubscriptionService] = Depends(
        get_toss_subscription_service_factory
    ),
    settings: Settings = Depends(get_settings),
) -> TossBillingAuthCompleteResponse:
    _require_billing_enabled(settings)
    user_id = _require_user_id(request)
    toss_service = toss_service_factory()
    resolved_user_id, plan_code = toss_service.complete_billing_auth_and_subscribe(
        customer_key=body.customer_key,
        auth_key=body.auth_key,
    )
    if resolved_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다."
        )

    token_payload = {
        "sub": user_id,
        "is_subscribed": True,
        "subscription_active": True,
        "plan": plan_code,
    }
    access_token = create_access_token(
        token_payload,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    set_auth_cookies(
        response,
        token=access_token,
        plan_code=plan_code,
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        settings=settings,
    )
    return TossBillingAuthCompleteResponse(
        data=TossBillingAuthCompleteData(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            plan_code=plan_code,
        ),
        message="구독 결제가 완료되었습니다.",
    )
