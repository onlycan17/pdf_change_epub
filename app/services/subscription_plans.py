"""구독 플랜 정책 관리"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Optional

SUBSCRIPTION_PLAN_FREE = "free"
SUBSCRIPTION_PLAN_MONTHLY = "monthly"
SUBSCRIPTION_PLAN_YEARLY = "yearly"

ANNUAL_DISCOUNT_RATE = 0.10
FREE_UPLOAD_LIMIT_MB = 25
MONTHLY_UPLOAD_LIMIT_MB = 300
YEARLY_UPLOAD_LIMIT_MB = 500
MONTHLY_PRICE_WON = 9_900


def _to_bytes(megabytes: int) -> int:
    return megabytes * 1024 * 1024


def _annual_price(monthly_price_won: int) -> int:
    """연간 가격(월 결제 대비 10% 할인) 계산."""

    if monthly_price_won <= 0:
        return 0

    yearly_regular = monthly_price_won * 12
    discount_amount = int(yearly_regular * ANNUAL_DISCOUNT_RATE)
    return yearly_regular - discount_amount


@dataclass(frozen=True)
class SubscriptionPlan:
    """플랜별 정책"""

    code: str
    label: str
    upload_limit_bytes: int
    monthly_price_won: int
    yearly_price_won: int
    is_subscribed: bool
    features: tuple[str, ...]
    recommended: bool = False

    @property
    def upload_limit_mb(self) -> int:
        return int(self.upload_limit_bytes / (1024 * 1024))

    @property
    def annual_discount_rate(self) -> float:
        if self.code != SUBSCRIPTION_PLAN_YEARLY:
            return 0.0
        return ANNUAL_DISCOUNT_RATE


PLAN_ALIASES: Dict[str, str] = {
    "free": SUBSCRIPTION_PLAN_FREE,
    "basic": SUBSCRIPTION_PLAN_MONTHLY,
    "premium": SUBSCRIPTION_PLAN_MONTHLY,
    "pro": SUBSCRIPTION_PLAN_MONTHLY,
    "monthly": SUBSCRIPTION_PLAN_MONTHLY,
    "month": SUBSCRIPTION_PLAN_MONTHLY,
    "yearly": SUBSCRIPTION_PLAN_YEARLY,
    "annual": SUBSCRIPTION_PLAN_YEARLY,
    "year": SUBSCRIPTION_PLAN_YEARLY,
}


PLAN_DEFINITIONS: Dict[str, SubscriptionPlan] = {
    SUBSCRIPTION_PLAN_FREE: SubscriptionPlan(
        code=SUBSCRIPTION_PLAN_FREE,
        label="무료",
        upload_limit_bytes=_to_bytes(FREE_UPLOAD_LIMIT_MB),
        monthly_price_won=0,
        yearly_price_won=0,
        is_subscribed=False,
        features=("월 5회 변환", "기본 OCR", "표준 처리 속도"),
    ),
    SUBSCRIPTION_PLAN_MONTHLY: SubscriptionPlan(
        code=SUBSCRIPTION_PLAN_MONTHLY,
        label="월간 구독",
        upload_limit_bytes=_to_bytes(MONTHLY_UPLOAD_LIMIT_MB),
        monthly_price_won=MONTHLY_PRICE_WON,
        yearly_price_won=_annual_price(MONTHLY_PRICE_WON),
        is_subscribed=True,
        features=("대용량 파일 지원", "고급 OCR", "우선 처리", "배치 처리", "이메일 알림"),
    ),
    SUBSCRIPTION_PLAN_YEARLY: SubscriptionPlan(
        code=SUBSCRIPTION_PLAN_YEARLY,
        label="연간 구독",
        upload_limit_bytes=_to_bytes(YEARLY_UPLOAD_LIMIT_MB),
        monthly_price_won=MONTHLY_PRICE_WON,
        yearly_price_won=_annual_price(MONTHLY_PRICE_WON),
        is_subscribed=True,
        recommended=True,
        features=(
            "연간 결제 10% 할인",
            "가장 높은 업로드 용량",
            "고급 OCR",
            "우선 처리",
            "배치 처리",
            "이메일 알림",
        ),
    ),
}


def normalize_plan_code(plan_code: Optional[str]) -> str:
    """플랜 코드를 내부 표준 코드로 정규화한다."""

    if not plan_code:
        return SUBSCRIPTION_PLAN_FREE

    normalized = str(plan_code).strip().lower()
    return PLAN_ALIASES.get(normalized, normalized if normalized in PLAN_DEFINITIONS else SUBSCRIPTION_PLAN_FREE)


def get_plan(plan_code: Optional[str]) -> SubscriptionPlan:
    """코드 기반 플랜을 반환한다."""

    return PLAN_DEFINITIONS[normalize_plan_code(plan_code)]


def all_plans() -> tuple[SubscriptionPlan, ...]:
    """정렬된 플랜 목록을 반환한다."""

    return (
        PLAN_DEFINITIONS[SUBSCRIPTION_PLAN_FREE],
        PLAN_DEFINITIONS[SUBSCRIPTION_PLAN_MONTHLY],
        PLAN_DEFINITIONS[SUBSCRIPTION_PLAN_YEARLY],
    )


def resolve_plan_from_payload(payload: Optional[Mapping[str, object]]) -> str:
    """JWT payload 기준으로 정렬된 구독 플랜 코드를 반환한다."""

    if not payload:
        return SUBSCRIPTION_PLAN_FREE

    plan = payload.get("plan")
    if isinstance(plan, str):
        return normalize_plan_code(plan)

    subscription_plan = payload.get("subscription_plan")
    if isinstance(subscription_plan, str):
        return normalize_plan_code(subscription_plan)

    direct_flag = payload.get("is_subscribed") or payload.get("subscription_active")
    if isinstance(direct_flag, bool) and direct_flag:
        return SUBSCRIPTION_PLAN_MONTHLY
    if isinstance(direct_flag, str) and direct_flag.lower() in {"1", "true", "yes", "y"}:
        return SUBSCRIPTION_PLAN_MONTHLY

    return SUBSCRIPTION_PLAN_FREE
