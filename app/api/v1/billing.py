"""Stripe Billing API"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    OneTimeCheckoutRequest,
    OneTimeCheckoutResponse,
    PortalSessionRequest,
    PortalSessionResponse,
)
from app.services.stripe_service import StripeService, get_stripe_service

router = APIRouter()


@router.post("/checkout/session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    stripe_service: StripeService = Depends(get_stripe_service),
) -> CheckoutSessionResponse:
    """구독 또는 결제 Checkout 세션 생성"""

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
        message="Stripe checkout session created",
    )


@router.post("/checkout/one-time", response_model=OneTimeCheckoutResponse)
async def create_one_time_checkout(
    request: OneTimeCheckoutRequest,
    stripe_service: StripeService = Depends(get_stripe_service),
) -> OneTimeCheckoutResponse:
    """단일 결제 Checkout 세션 생성"""

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
        message="Stripe one-time checkout session created",
    )


@router.post("/portal/session", response_model=PortalSessionResponse)
async def create_portal_session(
    request: PortalSessionRequest,
    stripe_service: StripeService = Depends(get_stripe_service),
) -> PortalSessionResponse:
    """청구 포털 세션 생성"""

    session = stripe_service.create_portal_session(
        customer_id=request.customer_id,
        return_url=request.return_url,
    )

    return PortalSessionResponse(
        data={"portal_url": session.url},
        message="Stripe billing portal session created",
    )
