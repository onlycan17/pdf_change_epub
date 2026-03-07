from fastapi.testclient import TestClient

from app.main import app
from app.services.stripe_service import get_stripe_service
from app.api.v1.auth import create_access_token
from app.api.v1.billing import get_toss_subscription_service_factory
import app.core.config as config_module


class FakeStripeObject:
    def __init__(self, url: str, session_id: str = "sess_123"):
        self.url = url
        self.id = session_id


class FakeStripeService:
    def create_checkout_session(self, **kwargs):
        return FakeStripeObject("https://stripe.test/checkout")

    def create_one_time_session(self, **kwargs):
        return FakeStripeObject("https://stripe.test/one-time")

    def create_portal_session(self, **kwargs):
        return FakeStripeObject("https://stripe.test/portal")


client = TestClient(app)


def override_stripe_service():
    return FakeStripeService()


def setup_module() -> None:
    app.dependency_overrides[get_stripe_service] = override_stripe_service


def teardown_module() -> None:
    app.dependency_overrides.pop(get_stripe_service, None)
    app.dependency_overrides.pop(
        get_toss_subscription_service_factory,
        None,
    )


def test_create_checkout_session():
    response = client.post(
        "/api/v1/billing/checkout/session",
        json={"plan_code": "basic"},
    )
    assert response.status_code == 503


def test_get_billing_plans():
    response = client.get("/api/v1/billing/plans")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    plans = data["data"]["plans"]
    assert isinstance(plans, list)
    assert {plan["code"] for plan in plans} == {"free"}


def test_create_one_time_session():
    response = client.post(
        "/api/v1/billing/checkout/one-time",
        json={"price_id": "price_test"},
    )
    assert response.status_code == 503


def test_create_portal_session():
    response = client.post(
        "/api/v1/billing/portal/session",
        json={"customer_id": "cus_test"},
    )
    assert response.status_code == 503


class FakeTossSubscriptionService:
    def __init__(self) -> None:
        self.started: list[tuple[str, str]] = []
        self.completed: list[tuple[str, str]] = []

    def start_billing_auth(self, *, user_id: str, plan_code: str) -> dict[str, str]:
        self.started.append((user_id, plan_code))
        return {
            "client_key": "test_ck",
            "customer_key": "cust_test",
            "success_url": "",
            "fail_url": "",
        }

    def complete_billing_auth_and_subscribe(self, *, customer_key: str, auth_key: str):
        self.completed.append((customer_key, auth_key))
        return ("testuser", "monthly")


_fake_toss_service = FakeTossSubscriptionService()


def override_toss_service():
    return _fake_toss_service


def test_toss_billing_auth_start_requires_login():
    response = client.post(
        "/api/v1/billing/toss/billing-auth/start",
        json={"plan_code": "monthly"},
    )
    assert response.status_code == 503


def test_toss_billing_auth_start_and_complete_flow():
    config_module._settings_cache = None
    app.dependency_overrides[get_toss_subscription_service_factory] = (
        lambda: lambda: _fake_toss_service
    )
    token = create_access_token({"sub": "testuser", "plan": "free"})

    response = client.post(
        "/api/v1/billing/toss/billing-auth/start",
        json={"plan_code": "monthly"},
        headers={"Authorization": f"Bearer {token}", "Origin": "http://localhost:3000"},
    )
    assert response.status_code == 503


def test_toss_billing_auth_complete_uses_configured_expiry(monkeypatch):
    monkeypatch.setenv("APP_BILLING_ENABLED", "true")
    monkeypatch.setenv("APP_ACCESS_TOKEN_EXPIRE_MINUTES", "10080")
    config_module._settings_cache = None
    app.dependency_overrides[get_toss_subscription_service_factory] = (
        lambda: lambda: _fake_toss_service
    )
    token = create_access_token({"sub": "testuser", "plan": "free"})

    try:
        response = client.post(
            "/api/v1/billing/toss/billing-auth/complete",
            json={"customer_key": "cust_test", "auth_key": "auth_test"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["data"]["plan_code"] == "monthly"
        assert payload["data"]["expires_in"] == 10080 * 60
    finally:
        config_module._settings_cache = None
