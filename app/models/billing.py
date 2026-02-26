"""Stripe 결제 관련 Pydantic 모델"""

from __future__ import annotations

from typing import Optional, Dict

from pydantic import BaseModel, Field, field_validator, ValidationInfo

from app.models.conversion import DataResponse


class CheckoutSessionRequest(BaseModel):
    """구독/일회성 결제 세션 생성 요청"""

    plan_code: Optional[str] = Field(
        default=None, description="구독 플랜 코드 (monthly, yearly, free)"
    )
    price_id: Optional[str] = Field(
        default=None, description="직접 결제 금액(원) 지정 시 사용(숫자 문자열)"
    )
    mode: Optional[str] = Field(
        default="subscription",
        description="결제 모드 (subscription|payment)",
    )
    success_url: Optional[str] = Field(
        default=None, description="결제 성공 리디렉션 URL"
    )
    cancel_url: Optional[str] = Field(
        default=None, description="결제 취소 리디렉션 URL"
    )
    customer_id: Optional[str] = Field(
        default=None, description="기존 Stripe Customer ID"
    )
    metadata: Optional[Dict[str, str]] = Field(
        default=None, description="세션에 저장할 메타데이터"
    )

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        if value not in {"subscription", "payment"}:
            raise ValueError("mode must be 'subscription' or 'payment'")
        return value

    @field_validator("price_id", mode="after")
    @classmethod
    def validate_price_or_plan(
        cls, price_id: Optional[str], info: ValidationInfo
    ) -> Optional[str]:
        plan_code = info.data.get("plan_code")
        if not price_id and not plan_code:
            raise ValueError("price_id 또는 plan_code 중 하나는 반드시 제공해야 합니다")
        return price_id


class CheckoutSessionResponse(DataResponse[Dict[str, str]]):
    """구독/일회성 Checkout 세션 생성 응답"""


class PortalSessionRequest(BaseModel):
    """청구 포털 세션 생성 요청"""

    customer_id: str = Field(..., description="고객 식별자")
    return_url: Optional[str] = Field(
        default=None, description="포털 종료 후 돌아갈 URL"
    )


class PortalSessionResponse(DataResponse[Dict[str, str]]):
    """청구 포털 세션 응답"""


class OneTimeCheckoutRequest(BaseModel):
    """단일 결제 Checkout 생성 요청"""

    price_id: Optional[str] = Field(default=None, description="Stripe Price ID")
    product_name: Optional[str] = Field(
        default=None, description="상품명 (metadata 용)"
    )
    amount_cents: Optional[int] = Field(
        default=None,
        description="즉시 결제 금액(원). price_id가 없을 때 사용",
        ge=1,
    )
    currency: Optional[str] = Field(
        default="usd", description="통화 (price_id 없이 amount 지정 시 필수)"
    )
    quantity: int = Field(default=1, ge=1, description="결제 수량")
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None
    customer_id: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None

    @field_validator("price_id", mode="after")
    @classmethod
    def validate_price_or_amount(
        cls, price_id: Optional[str], info: ValidationInfo
    ) -> Optional[str]:
        amount = info.data.get("amount_cents")
        if not price_id and not amount:
            raise ValueError(
                "price_id 또는 amount_cents 중 하나는 반드시 지정해야 합니다"
            )
        return price_id


class OneTimeCheckoutResponse(DataResponse[Dict[str, str]]):
    """단일 결제 Checkout 응답"""


class BillingPlanData(BaseModel):
    """구독 플랜 목록 응답 항목"""

    code: str
    label: str
    upload_limit_bytes: int
    upload_limit_mb: int
    monthly_price_won: int
    yearly_price_won: int
    is_subscribed: bool
    recommended: bool
    annual_discount_rate: float
    features: list[str]


class BillingPlansResponse(DataResponse[Dict[str, list[BillingPlanData]]]):
    """구독 플랜 목록 응답"""


class BillingErrorResponse(DataResponse[Dict[str, str]]):
    """결제 처리 실패 응답"""

    success: bool = False


class TossBillingAuthStartRequest(BaseModel):
    plan_code: str = Field(..., description="구독 플랜 코드 (monthly|yearly)")


class TossBillingAuthStartData(BaseModel):
    client_key: str
    customer_key: str
    success_url: str
    fail_url: str


class TossBillingAuthStartResponse(DataResponse[TossBillingAuthStartData]):
    pass


class TossBillingAuthCompleteRequest(BaseModel):
    customer_key: str = Field(..., description="Toss customerKey")
    auth_key: str = Field(..., description="Toss authKey")


class TossBillingAuthCompleteData(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    plan_code: str


class TossBillingAuthCompleteResponse(DataResponse[TossBillingAuthCompleteData]):
    pass
