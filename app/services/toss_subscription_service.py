from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

import httpx
from fastapi import HTTPException, status

from app.core.config import Settings
from app.services.subscription_plans import (
    MONTHLY_PRICE_WON,
    SUBSCRIPTION_PLAN_MONTHLY,
    SUBSCRIPTION_PLAN_YEARLY,
    normalize_plan_code,
)


def _build_basic_auth(secret_key: Optional[str]) -> str:
    if not secret_key:
        return ""
    raw = f"{secret_key}:"
    return base64.b64encode(raw.encode("utf-8")).decode("ascii")


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


@dataclass
class SubscriptionRecord:
    user_id: str
    plan_code: str
    customer_key: str
    billing_key: str
    active: bool
    started_at: datetime
    next_billing_at: datetime


class InMemorySubscriptionStore:
    def __init__(self) -> None:
        self._by_user: dict[str, SubscriptionRecord] = {}

    def upsert(self, record: SubscriptionRecord) -> None:
        self._by_user[record.user_id] = record

    def get(self, user_id: str) -> Optional[SubscriptionRecord]:
        return self._by_user.get(user_id)


class TossSubscriptionService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._auth_header = ""
        self._pending_by_customer: dict[str, dict[str, str]] = {}
        self.subscriptions = InMemorySubscriptionStore()
        self._billing_issue_path = "/v1/billing/authorizations/issue"

        if not settings.billing_enabled:
            return

        if not settings.toss_secret_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Toss Payments secret key가 설정되지 않았습니다.",
            )
        if not settings.toss_client_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Toss Payments client key가 설정되지 않았습니다.",
            )

        self._auth_header = _build_basic_auth(settings.toss_secret_key)

    def start_billing_auth(self, *, user_id: str, plan_code: str) -> dict[str, str]:
        normalized = normalize_plan_code(plan_code)
        if normalized not in (SUBSCRIPTION_PLAN_MONTHLY, SUBSCRIPTION_PLAN_YEARLY):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="plan_code는 monthly 또는 yearly 이어야 합니다.",
            )

        customer_key = str(uuid4())
        self._pending_by_customer[customer_key] = {
            "user_id": user_id,
            "plan_code": normalized,
        }

        return {
            "client_key": self.settings.toss_client_key or "",
            "customer_key": customer_key,
            "success_url": "",
            "fail_url": "",
        }

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
                resp = client.request(method, url, json=payload, headers=headers)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            detail = "Toss API 응답 오류"
            try:
                error_payload = exc.response.json()
                code = _safe_text(error_payload.get("code"))
                message = _safe_text(error_payload.get("message"))
                detail = f"Toss API 오류 ({code}): {message}".strip()
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

    def issue_billing_key(self, *, customer_key: str, auth_key: str) -> str:
        payload: Dict[str, Any] = {
            "customerKey": customer_key,
            "authKey": auth_key,
        }
        result = self._request_toss("POST", self._billing_issue_path, payload)
        billing_key = _safe_text(result.get("billingKey"))
        if not billing_key:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="billingKey를 발급받지 못했습니다.",
            )
        return billing_key

    def _resolve_amount_won(self, plan_code: str) -> int:
        normalized = normalize_plan_code(plan_code)
        if normalized == SUBSCRIPTION_PLAN_MONTHLY:
            return MONTHLY_PRICE_WON
        if normalized == SUBSCRIPTION_PLAN_YEARLY:
            monthly = MONTHLY_PRICE_WON
            yearly_regular = monthly * 12
            discount = int(yearly_regular * 0.1)
            return yearly_regular - discount
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효한 구독 플랜이 아닙니다.",
        )

    def approve_first_charge(
        self, *, customer_key: str, billing_key: str, plan_code: str
    ) -> dict[str, Any]:
        amount = self._resolve_amount_won(plan_code)
        order_id = str(uuid4())
        order_name = (
            "월간 구독" if plan_code == SUBSCRIPTION_PLAN_MONTHLY else "연간 구독"
        )
        payload: Dict[str, Any] = {
            "customerKey": customer_key,
            "amount": amount,
            "orderId": order_id,
            "orderName": order_name,
        }
        return self._request_toss("POST", f"/v1/billing/{billing_key}", payload)

    def complete_billing_auth_and_subscribe(
        self, *, customer_key: str, auth_key: str
    ) -> tuple[str, str]:
        pending = self._pending_by_customer.get(customer_key)
        if not pending:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="결제 진행 정보를 찾을 수 없습니다.",
            )

        user_id = pending["user_id"]
        plan_code = pending["plan_code"]

        billing_key = self.issue_billing_key(
            customer_key=customer_key, auth_key=auth_key
        )
        _ = self.approve_first_charge(
            customer_key=customer_key,
            billing_key=billing_key,
            plan_code=plan_code,
        )

        now = datetime.now(timezone.utc)
        next_billing_at = now + (
            timedelta(days=365)
            if plan_code == SUBSCRIPTION_PLAN_YEARLY
            else timedelta(days=30)
        )

        self.subscriptions.upsert(
            SubscriptionRecord(
                user_id=user_id,
                plan_code=plan_code,
                customer_key=customer_key,
                billing_key=billing_key,
                active=True,
                started_at=now,
                next_billing_at=next_billing_at,
            )
        )

        self._pending_by_customer.pop(customer_key, None)
        return user_id, plan_code


_toss_subscription_service: Optional[TossSubscriptionService] = None


def get_toss_subscription_service(settings: Settings) -> TossSubscriptionService:
    global _toss_subscription_service
    if _toss_subscription_service is None:
        _toss_subscription_service = TossSubscriptionService(settings)
    return _toss_subscription_service
