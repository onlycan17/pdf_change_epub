from fastapi.testclient import TestClient

from app.main import app
import app.core.config as config_module
import app.repositories.user_repository as user_repository_module


client = TestClient(app)


def test_login_token_uses_configured_expiry(monkeypatch):
    monkeypatch.setenv("APP_ACCESS_TOKEN_EXPIRE_MINUTES", "10080")
    config_module._settings_cache = None

    try:
        with TestClient(app) as local_client:
            response = local_client.post(
                "/api/v1/auth/token",
                data={"username": "testuser", "password": "testpass"},
            )
            assert response.status_code == 200
            payload = response.json()
            assert payload["expires_in"] == 10080 * 60
            assert response.cookies.get("pdf_to_epub_session") == "1"
            assert response.cookies.get("pdf_to_epub_plan") == "free"
    finally:
        config_module._settings_cache = None


def test_me_includes_privileged_flag_for_test_accounts():
    with TestClient(app) as local_client:
        login_response = local_client.post(
            "/api/v1/auth/token",
            data={"username": "onlycan17@gmail.com", "password": "testpass"},
        )
        assert login_response.status_code == 200

        profile_response = local_client.get("/api/v1/auth/me")

        assert profile_response.status_code == 200
        assert profile_response.json() == {
            "id": "onlycan17@gmail.com",
            "email": "onlycan17@gmail.com",
            "is_privileged": True,
        }


def test_logout_clears_auth_cookies():
    with TestClient(app) as local_client:
        login_response = local_client.post(
            "/api/v1/auth/token",
            data={"username": "testuser", "password": "testpass"},
        )
        assert login_response.status_code == 200

        logout_response = local_client.post("/api/v1/auth/logout")

        assert logout_response.status_code == 200
        set_cookie_header = ",".join(logout_response.headers.get_list("set-cookie"))
        assert "pdf_to_epub_access_token=" in set_cookie_header
        assert "pdf_to_epub_session=" in set_cookie_header
        assert "Max-Age=0" in set_cookie_header


def test_register_then_login_with_local_account(monkeypatch, tmp_path):
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DB_URL", f"sqlite:///{tmp_path / 'auth_test.db'}")
    config_module._settings_cache = None
    user_repository_module._user_repository = None

    try:
        settings = config_module.get_settings()
        repo = user_repository_module.get_user_repository(settings)
        repo._db_path  # ensure repository initialized under new settings

        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "테스트 사용자",
                "email": "localuser@example.com",
                "password": "testpass123",
            },
            headers={"X-API-Key": settings.SECURITY_API_KEY},
        )
        assert register_response.status_code == 201
        assert register_response.json()["email"] == "localuser@example.com"

        login_response = client.post(
            "/api/v1/auth/token",
            data={"username": "localuser@example.com", "password": "testpass123"},
        )
        assert login_response.status_code == 200
        payload = login_response.json()
        assert payload["token_type"] == "bearer"
        assert payload["access_token"]
    finally:
        config_module._settings_cache = None
        user_repository_module._user_repository = None


def test_register_rejects_duplicate_email(monkeypatch, tmp_path):
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DB_URL", f"sqlite:///{tmp_path / 'auth_dup.db'}")
    config_module._settings_cache = None
    user_repository_module._user_repository = None

    try:
        settings = config_module.get_settings()
        headers = {"X-API-Key": settings.SECURITY_API_KEY}
        payload = {
            "name": "중복 사용자",
            "email": "dup@example.com",
            "password": "testpass123",
        }
        first_response = client.post(
            "/api/v1/auth/register", json=payload, headers=headers
        )
        assert first_response.status_code == 201

        second_response = client.post(
            "/api/v1/auth/register",
            json=payload,
            headers=headers,
        )
        assert second_response.status_code == 409
    finally:
        config_module._settings_cache = None
        user_repository_module._user_repository = None
