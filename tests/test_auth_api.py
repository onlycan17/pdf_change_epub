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
