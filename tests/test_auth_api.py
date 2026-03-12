from fastapi.testclient import TestClient

from app.main import app
import app.core.config as config_module


client = TestClient(app)


def test_login_token_uses_configured_expiry(monkeypatch):
    monkeypatch.setenv("APP_ACCESS_TOKEN_EXPIRE_MINUTES", "10080")
    config_module._settings_cache = None

    try:
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "testuser", "password": "testpass"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["expires_in"] == 10080 * 60
    finally:
        config_module._settings_cache = None


def test_me_includes_privileged_flag_for_test_accounts():
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "onlycan17@gmail.com", "password": "testpass"},
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    profile_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert profile_response.status_code == 200
    assert profile_response.json() == {
        "id": "onlycan17@gmail.com",
        "email": "onlycan17@gmail.com",
        "is_privileged": True,
    }
