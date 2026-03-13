from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
import app.core.config as config_module
import app.repositories.user_repository as user_repository_module
import app.services.async_queue_service as async_queue_service_module
import app.services.conversion_metrics_service as conversion_metrics_service_module
import app.services.free_usage_limit_service as free_usage_limit_service_module
import app.services.large_file_request_service as large_file_request_service_module
from app.services.conversion_orchestrator import ConversionJob, JobState


client = TestClient(app)


def _reset_service_state() -> None:
    config_module._settings_cache = None
    user_repository_module._user_repository = None
    async_queue_service_module._async_queue_service = None
    conversion_metrics_service_module._service_instance = None
    free_usage_limit_service_module._service_instance = None
    large_file_request_service_module._service_instance = None


def test_admin_dashboard_returns_usage_snapshot(monkeypatch, tmp_path):
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DB_URL", f"sqlite:///{tmp_path / 'admin_dashboard.db'}")
    monkeypatch.setenv("APP_USE_CELERY", "false")
    _reset_service_state()

    try:
        settings = config_module.get_settings()
        user_repository = user_repository_module.get_user_repository(settings)
        user_repository.create_local_user(
            email="member@example.com",
            name="일반 회원",
            password_hash="hashed-password",
        )
        user_repository.upsert_google_user(
            provider_sub="google-admin-test",
            email="another-google@example.com",
            name="구글 회원",
        )

        free_usage_service = (
            free_usage_limit_service_module.get_free_usage_limit_service(
                settings.database.url
            )
        )
        assert free_usage_service.try_consume("member@example.com") is True
        assert free_usage_service.try_consume("member@example.com") is True

        large_file_request_service = (
            large_file_request_service_module.get_large_file_request_service()
        )
        request_record = large_file_request_service.create_request(
            requester_user_id="local:member@example.com",
            requester_email="member@example.com",
            request_note="스캔 PDF 요청",
            bank_transfer_note="입금 예정",
            attachment_filename="sample.pdf",
            attachment_bytes=b"%PDF-1.4 test",
        )
        large_file_request_service.mark_conversion_started(
            request_id=request_record.request_id,
            conversion_id="conversion-processing",
            handled_by_email="onlycan17@gmail.com",
        )

        async_queue_service = async_queue_service_module.get_async_queue_service()
        async_queue_service._activate_direct_mode()
        store = async_queue_service.store

        import asyncio

        asyncio.run(
            store.create(
                ConversionJob(
                    conversion_id="job-processing",
                    filename="runtime-processing.pdf",
                    file_size=1_024,
                    ocr_enabled=True,
                    state=JobState.PROCESSING,
                    progress=45,
                    current_step="ocr",
                )
            )
        )
        asyncio.run(
            store.create(
                ConversionJob(
                    conversion_id="job-completed",
                    filename="runtime-completed.pdf",
                    file_size=2_048,
                    ocr_enabled=False,
                    state=JobState.COMPLETED,
                    progress=100,
                    current_step="done",
                )
            )
        )
        asyncio.run(
            store.create(
                ConversionJob(
                    conversion_id="job-failed",
                    filename="runtime-failed.pdf",
                    file_size=3_072,
                    ocr_enabled=True,
                    state=JobState.FAILED,
                    progress=83,
                    current_step="failed",
                    error_message="OCR timeout",
                )
            )
        )

        login_response = client.post(
            "/api/v1/auth/token",
            data={"username": "onlycan17@gmail.com", "password": "testpass"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v1/admin/dashboard",
            headers={
                "Authorization": f"Bearer {token}",
                "X-API-Key": settings.SECURITY_API_KEY,
            },
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["summary"]["total_users"] == 2
        assert payload["summary"]["local_users"] == 1
        assert payload["summary"]["google_users"] == 1
        assert payload["summary"]["today_free_conversions"] == 2
        assert payload["summary"]["total_large_file_requests"] == 1
        assert payload["summary"]["processing_large_file_requests"] == 1
        assert payload["summary"]["runtime_processing_jobs"] == 1
        assert payload["summary"]["runtime_completed_jobs"] == 1
        assert payload["summary"]["runtime_failed_jobs"] == 1
        assert payload["summary"]["persisted_total_conversions"] == 3
        assert payload["summary"]["persisted_failed_conversions"] == 1
        assert payload["summary"]["persisted_completed_conversions"] == 1
        assert len(payload["daily_free_usage"]) == 7
        assert len(payload["daily_conversion_counts"]) == 30
        assert payload["recent_large_file_requests"][0]["requester_email"] == (
            "member@example.com"
        )
        assert payload["recent_runtime_conversions"][0]["conversion_id"] in {
            "job-processing",
            "job-completed",
            "job-failed",
        }
        assert payload["recent_failed_conversions"][0]["conversion_id"] == "job-failed"
        assert payload["recent_failed_conversions"][0]["error_message"] == "OCR timeout"
        assert payload["failure_category_counts"][0]["code"] == "ocr"
        assert payload["failure_category_counts"][0]["count"] == 1
    finally:
        _reset_service_state()


def test_admin_dashboard_rejects_non_privileged_user(monkeypatch, tmp_path):
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv(
        "DB_URL", f"sqlite:///{tmp_path / 'admin_dashboard_forbidden.db'}"
    )
    monkeypatch.setenv("APP_USE_CELERY", "false")
    _reset_service_state()

    try:
        settings = config_module.get_settings()
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "일반 사용자",
                "email": "member@example.com",
                "password": "testpass123",
            },
            headers={"X-API-Key": settings.SECURITY_API_KEY},
        )
        assert response.status_code == 201

        login_response = client.post(
            "/api/v1/auth/token",
            data={"username": "member@example.com", "password": "testpass123"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        dashboard_response = client.get(
            "/api/v1/admin/dashboard",
            headers={
                "Authorization": f"Bearer {token}",
                "X-API-Key": settings.SECURITY_API_KEY,
            },
        )

        assert dashboard_response.status_code == 403
    finally:
        _reset_service_state()
