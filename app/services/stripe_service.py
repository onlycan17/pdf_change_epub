"""결제 게이트웨이 래퍼 (현재 Toss Payments 연동용)"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import Depends, HTTPException, status
import httpx

from app.core.config import Settings, get_settings
from app.services.subscription_plans import (
    ANNUAL_DISCOUNT_RATE,
    MONTHLY_PRICE_WON,
    SUBSCRIPTION_PLAN_MONTHLY,
    SUBSCRIPTION_PLAN_YEARLY,
    normalize_plan_code,
)


def _build_toss_credentials(secret_key: Optional[str]) -> str:
    if not secret_key:
        return ""
    raw = f"{secret_key}:"
    return base64.b64encode(raw.encode("utf-8")).decode("ascii")


def _safe_int(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    stripped = value.strip()
    if not stripped.isdigit():
        return None
    try:
        return int(stripped)
    except ValueError:
        return None


def _to_int_bytes(value: Optional[str]) -> Optional[int]:
    parsed = _safe_int(value)
    if parsed is None:
        return None
    if parsed <= 0:
        return None
    return parsed


def _fallback_yearly_price() -> int:
    yearly_regular = MONTHLY_PRICE_WON * 12
    discount_amount = int(yearly_regular * ANNUAL_DISCOUNT_RATE)
    return yearly_regular - discount_amount


def _extract_payment_url(response_payload: Dict[str, Any]) -> str:
    return (
        response_payload.get("checkoutPageUrl")
        or response_payload.get("checkout_url")
        or response_payload.get("checkoutUrl")
        or response_payload.get("url", "")
        or response_payload.get("redirectUrl", "")
    )


def _extract_payment_id(
    response_payload: Dict[str, Any], fallback: Optional[str] = None
) -> str:
    return (
        response_payload.get("paymentKey")
        or response_payload.get("sessionKey")
        or response_payload.get("id")
        or response_payload.get("orderId")
        or (fallback or "")
    )


@dataclass
class TossCheckoutResult:
    url: str
    payment_id: str

    def to_namespace(self) -> SimpleNamespace:
        return SimpleNamespace(url=self.url, id=self.payment_id)


class StripeService:
    """기존 이름 유지: 백엔드 결제 서비스 래퍼"""

    def __init__(self, settings: Settings) -> None:
        if not settings.toss_secret_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Toss Payments secret key가 설정되지 않았습니다.",
            )
        self.settings = settings
        self._auth_header = _build_toss_credentials(settings.toss_secret_key)

    def _resolve_plan_price(
        self, plan_code: Optional[str], price_id: Optional[str]
    ) -> int:
        if price_id:
            explicit_price = _to_int_bytes(price_id)
            if explicit_price is not None:
                return explicit_price
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Toss는 price_id 대신 금액(원) 또는 플랜 코드 기반 결제를 사용합니다.",
            )

        normalized_plan = normalize_plan_code(plan_code)
        if normalized_plan == SUBSCRIPTION_PLAN_MONTHLY:
            monthly_from_env = _to_int_bytes(self.settings.toss_price_monthly)
            return monthly_from_env or MONTHLY_PRICE_WON
        if normalized_plan == SUBSCRIPTION_PLAN_YEARLY:
            yearly_from_env = _to_int_bytes(self.settings.toss_price_yearly)
            return yearly_from_env or _fallback_yearly_price()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효한 구독 플랜이 지정되지 않았습니다.",
        )

    def _resolve_plan_name(self, plan_code: Optional[str]) -> str:
        normalized_plan = normalize_plan_code(plan_code)
        if normalized_plan == SUBSCRIPTION_PLAN_MONTHLY:
            return "월간 구독"
        if normalized_plan == SUBSCRIPTION_PLAN_YEARLY:
            return "연간 구독"
        return "구독"

    def _request_toss(
        self, method: str, path: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not self._auth_header:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Toss Payments 인증 토큰이 준비되지 않았습니다.",
            )

        url = f"{self.settings.toss_api_base_url.rstrip('/')}/{path.lstrip('/')}"
        headers = {
            "Authorization": f"Basic {self._auth_header}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            with httpx.Client(timeout=30) as client:
                response = client.request(method, url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            detail = "Toss API 응답 오류"
            try:
                error_payload = exc.response.json()
                code = error_payload.get("code", "")
                message = error_payload.get("message", "")
                detail = f"Toss API 오류 ({code}): {message}"
            except Exception:
                detail = f"Toss API 오류: {exc.response.text}"
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=detail,
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Toss API 연결 실패: {exc}",
            ) from exc

    def _build_checkout_payload(
        self,
        amount: int,
        plan_code: Optional[str],
        success_url: Optional[str],
        cancel_url: Optional[str],
        metadata: Optional[Dict[str, str]],
    ) -> Dict[str, Any]:
        order_id = str(uuid4())
        payload: Dict[str, Any] = {
            "amount": {
                "currency": "KRW",
                "value": amount,
            },
            "orderId": order_id,
            "orderName": self._resolve_plan_name(plan_code),
            "successUrl": success_url or self.settings.toss_success_url,
            "failUrl": cancel_url or self.settings.toss_cancel_url,
            "method": "CARD",
        }
        if plan_code:
            payload["customData"] = {"planCode": normalize_plan_code(plan_code)}
        if metadata:
            merged = {"requestedBy": "frontend"}
            merged.update(metadata)
            payload["customData"] = merged

        return payload

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
        del customer_id  # 호환성을 위해 유지(토스 API 스펙상 미사용)
        amount = self._resolve_plan_price(plan_code, price_id)
        payload = self._build_checkout_payload(
            amount=amount,
            plan_code=plan_code,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
        )
        response_payload = self._request_toss("POST", "/v1/payments", payload)
        payment_url = _extract_payment_url(response_payload) or (
            self.settings.toss_checkout_base_url.rstrip("/") + "/"
        )
        if not payment_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Toss 결제 URL을 생성하지 못했습니다.",
            )

        return TossCheckoutResult(
            url=payment_url,
            payment_id=_extract_payment_id(
                response_payload, fallback=payload["orderId"]
            ),
        ).to_namespace()

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
        del customer_id
        del currency
        del quantity

        price = _to_int_bytes(price_id)
        if price is None:
            if amount_cents is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="amount_cents 또는 price_id 중 하나는 필요합니다.",
                )
            price = amount_cents

        payload = self._build_checkout_payload(
            amount=price,
            plan_code=None,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
        )
        payload["orderName"] = product_name or "원단 결제"
        response_payload = self._request_toss("POST", "/v1/payments", payload)
        payment_url = _extract_payment_url(response_payload) or (
            self.settings.toss_checkout_base_url.rstrip("/") + "/"
        )
        if not payment_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Toss 결제 URL을 생성하지 못했습니다.",
            )
        return TossCheckoutResult(
            url=payment_url,
            payment_id=_extract_payment_id(response_payload),
        ).to_namespace()

    def create_portal_session(
        self,
        *,
        customer_id: str,
        return_url: Optional[str],
    ) -> Any:
        del customer_id
        del return_url
        return TossCheckoutResult(
            url=self.settings.toss_success_url
            or self.settings.stripe_success_url
            or "",
            payment_id=str(uuid4()),
        ).to_namespace()


def get_stripe_service(settings: Settings = Depends(get_settings)) -> StripeService:
    return StripeService(settings)
