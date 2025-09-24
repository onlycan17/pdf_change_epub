"""Stripe 결제 서비스"""

from __future__ import annotations

from typing import Dict, Optional, Any

try:  # pragma: no cover - import guard
    import stripe  # type: ignore
except ImportError:  # pragma: no cover
    stripe = None
from fastapi import Depends, HTTPException, status

from app.core.config import Settings, get_settings


class StripeService:
    """Stripe SDK 래퍼"""

    def __init__(self, settings: Settings) -> None:
        if stripe is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stripe SDK가 설치되어 있지 않습니다.",
            )

        if not settings.stripe_secret_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stripe secret key is not configured",
            )
        self.settings = settings
        stripe.api_key = settings.stripe_secret_key

    def _resolve_price_id(
        self, plan_code: Optional[str], price_id: Optional[str]
    ) -> str:
        if price_id:
            return price_id

        mapping: Dict[str, Optional[str]] = {
            "basic": self.settings.stripe_price_basic,
            "pro": self.settings.stripe_price_pro,
        }
        if plan_code and mapping.get(plan_code):
            resolved = mapping[plan_code]
            if resolved:
                return resolved
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효한 Stripe price가 설정되지 않았습니다.",
        )

    def create_checkout_session(
        self,
        *,
        plan_code: Optional[str],
        price_id: Optional[str],
        mode: str,
        success_url: Optional[str],
        cancel_url: Optional[str],
        customer_id: Optional[str],
        metadata: Optional[Dict[str, str]],
    ) -> Any:
        resolved_price_id = self._resolve_price_id(plan_code, price_id)

        params: Dict[str, Any] = {
            "mode": mode,
            "line_items": [
                {
                    "price": resolved_price_id,
                    "quantity": 1,
                }
            ],
            "success_url": success_url or self.settings.stripe_success_url,
            "cancel_url": cancel_url or self.settings.stripe_cancel_url,
        }

        if metadata:
            params["metadata"] = metadata

        if customer_id:
            params["customer"] = customer_id

        try:
            return stripe.checkout.Session.create(**params)
        except stripe.error.StripeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Stripe 세션 생성 실패: {exc.user_message or str(exc)}",
            ) from exc

    def create_one_time_session(
        self,
        *,
        price_id: Optional[str],
        amount_cents: Optional[int],
        currency: str,
        quantity: int,
        success_url: Optional[str],
        cancel_url: Optional[str],
        customer_id: Optional[str],
        metadata: Optional[Dict[str, str]],
        product_name: Optional[str],
    ) -> Any:
        params: Dict[str, Any] = {
            "mode": "payment",
            "success_url": success_url or self.settings.stripe_success_url,
            "cancel_url": cancel_url or self.settings.stripe_cancel_url,
        }

        if customer_id:
            params["customer"] = customer_id

        if metadata:
            params["metadata"] = metadata

        if price_id:
            params["line_items"] = [
                {
                    "price": price_id,
                    "quantity": quantity,
                }
            ]
        else:
            if not amount_cents:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="amount_cents가 필요합니다.",
                )
            params["line_items"] = [
                {
                    "price_data": {
                        "currency": currency,
                        "unit_amount": amount_cents,
                        "product_data": {
                            "name": product_name or "One-time purchase",
                        },
                    },
                    "quantity": quantity,
                }
            ]

        try:
            return stripe.checkout.Session.create(**params)
        except stripe.error.StripeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Stripe 세션 생성 실패: {exc.user_message or str(exc)}",
            ) from exc

    def create_portal_session(
        self,
        *,
        customer_id: str,
        return_url: Optional[str],
    ) -> Any:
        params = {
            "customer": customer_id,
            "return_url": return_url or self.settings.stripe_success_url,
        }
        try:
            return stripe.billing_portal.Session.create(**params)
        except stripe.error.StripeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Stripe 포털 세션 생성 실패: {exc.user_message or str(exc)}",
            ) from exc


def get_stripe_service(settings: Settings = Depends(get_settings)) -> StripeService:
    return StripeService(settings)
