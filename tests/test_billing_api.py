from fastapi.testclient import TestClient

from app.main import app
from app.services.stripe_service import get_stripe_service


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


def test_create_checkout_session():
    response = client.post(
        "/api/v1/billing/checkout/session",
        json={"plan_code": "basic"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["checkout_url"] == "https://stripe.test/checkout"


def test_create_one_time_session():
    response = client.post(
        "/api/v1/billing/checkout/one-time",
        json={"price_id": "price_test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["checkout_url"] == "https://stripe.test/one-time"


def test_create_portal_session():
    response = client.post(
        "/api/v1/billing/portal/session",
        json={"customer_id": "cus_test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["portal_url"] == "https://stripe.test/portal"
