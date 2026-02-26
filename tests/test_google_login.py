import os
import pathlib

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_google_login_issues_jwt(monkeypatch) -> None:
    os.environ["APP_GOOGLE_CLIENT_ID"] = "test_google_client_id"
    os.environ["DB_URL"] = "sqlite:///./test_google_users.db"
    from app.core import config as config_module

    config_module._settings_cache = None

    try:
        pathlib.Path("test_google_users.db").unlink()
    except FileNotFoundError:
        pass

    from app.api.v1 import auth as auth_routes

    def fake_verify_google_id_token(*, id_token: str, client_id: str):
        assert id_token == "fake_id_token"
        assert client_id == "test_google_client_id"
        return {"sub": "google_sub_123", "email": "user@example.com"}

    monkeypatch.setattr(
        auth_routes, "verify_google_id_token", fake_verify_google_id_token
    )

    response = client.post("/api/v1/auth/google", json={"id_token": "fake_id_token"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user_id"] == "google:google_sub_123"
    assert body["email"] == "user@example.com"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]

    response2 = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"}
    )
    assert response2.status_code == 200
    me = response2.json()
    assert me["email"] == "user@example.com"

    pathlib.Path("test_google_users.db").unlink(missing_ok=True)
