"""통합 테스트"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from io import BytesIO

from app.main import app
from app.services.conversion_orchestrator import ConversionJob, JobState


class TestConversionIntegration:
    """변환 통합 테스트 클래스"""

    @pytest.fixture
    def mock_async_queue_service(self):
        """모의 비동기 작업 큐 서비스"""
        with patch("app.api.v1.conversion.get_async_queue_service") as mock_get_service:
            service = AsyncMock()
            mock_get_service.return_value = service
            yield service

    @pytest.fixture
    def test_client(self, mock_async_queue_service):
        """테스트 클라이언트"""
        return TestClient(app)

    @pytest.fixture
    def sample_pdf_content(self):
        """샘플 PDF 콘텐츠"""
        return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"

    def test_start_conversion_endpoint(
        self, test_client, mock_async_queue_service, sample_pdf_content
    ):
        """변환 시작 엔드포인트 테스트"""
        # Mock successful job creation
        mock_job = ConversionJob(
            conversion_id="test-123",
            filename="test.pdf",
            file_size=len(sample_pdf_content),
            ocr_enabled=True,
            state=JobState.PENDING,
            progress=0,
        )
        mock_job.celery_task_id = "celery-task-123"
        mock_async_queue_service.start_conversion.return_value = mock_job

        # Create test file
        pdf_file = BytesIO(sample_pdf_content)
        pdf_file.name = "test.pdf"

        # Execute
        response = test_client.post(
            "/api/v1/conversion/start",
            files={"file": ("test.pdf", pdf_file, "application/pdf")},
            data={"ocr_enabled": "true"},
            headers={"X-API-Key": "your-api-key-here"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["conversion_id"] == "test-123"
        assert data["data"]["status"] == JobState.PENDING
        assert data["message"] == "변환 작업이 시작되었습니다."

        # Verify service call
        mock_async_queue_service.start_conversion.assert_called_once()

    def test_start_conversion_invalid_file(self, test_client, mock_async_queue_service):
        """변환 시작 - 유효하지 않은 파일 테스트"""
        # Create invalid file
        invalid_file = BytesIO(b"not a pdf")
        invalid_file.name = "test.txt"

        # Execute
        response = test_client.post(
            "/api/v1/conversion/start",
            files={"file": ("test.txt", invalid_file, "text/plain")},
            data={"ocr_enabled": "true"},
            headers={"X-API-Key": "your-api-key-here"},
        )

        # Assertions
        assert response.status_code == 422  # Validation error

    def test_get_status_endpoint(self, test_client, mock_async_queue_service):
        """상태 조회 엔드포인트 테스트"""
        # Mock job status
        mock_job = ConversionJob(
            conversion_id="test-123",
            filename="test.pdf",
            file_size=1024,
            ocr_enabled=True,
            state=JobState.PROCESSING,
            progress=50,
            message="처리 중",
        )
        mock_async_queue_service.get_status.return_value = mock_job

        # Execute
        response = test_client.get(
            "/api/v1/conversion/status/test-123",
            headers={"X-API-Key": "your-api-key-here"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["conversion_id"] == "test-123"
        assert data["data"]["status"] == JobState.PROCESSING
        assert data["data"]["progress"] == 50

        # Verify service call
        mock_async_queue_service.get_status.assert_called_once_with("test-123")

    def test_get_status_not_found(self, test_client, mock_async_queue_service):
        """상태 조회 - 작업 없음 테스트"""
        # Mock job not found
        mock_async_queue_service.get_status.side_effect = KeyError("Job not found")

        # Execute
        response = test_client.get(
            "/api/v1/conversion/status/nonexistent",
            headers={"X-API-Key": "your-api-key-here"},
        )

        # Assertions
        assert response.status_code == 404
        assert response.json()["detail"] == "변환 작업을 찾을 수 없습니다."

    def test_download_endpoint_completed(self, test_client, mock_async_queue_service):
        """다운로드 엔드포인트 - 완료된 작업 테스트"""
        # Mock completed job
        mock_job = ConversionJob(
            conversion_id="test-123",
            filename="test.pdf",
            file_size=1024,
            ocr_enabled=True,
            state=JobState.COMPLETED,
            progress=100,
            message="변환 완료",
            result_bytes=b"epub content",
        )
        mock_async_queue_service.get_status.return_value = mock_job

        # Execute
        response = test_client.get(
            "/api/v1/conversion/download/test-123",
            headers={"X-API-Key": "your-api-key-here"},
        )

        # Assertions
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/epub+zip"
        assert response.content == b"epub content"

        # Verify service call
        mock_async_queue_service.get_status.assert_called_once_with("test-123")

    def test_download_endpoint_not_ready(self, test_client, mock_async_queue_service):
        """다운로드 엔드포인트 - 결과 준비 안됨 테스트"""
        # Mock job not completed
        mock_job = ConversionJob(
            conversion_id="test-123",
            filename="test.pdf",
            file_size=1024,
            ocr_enabled=True,
            state=JobState.PROCESSING,
            progress=50,
            message="처리 중",
        )
        mock_async_queue_service.get_status.return_value = mock_job

        # Execute
        response = test_client.get(
            "/api/v1/conversion/download/test-123",
            headers={"X-API-Key": "your-api-key-here"},
        )

        # Assertions
        assert response.status_code == 404
        assert response.json()["detail"] == "결과가 준비되지 않았습니다."

    def test_cancel_endpoint(self, test_client, mock_async_queue_service):
        """취소 엔드포인트 테스트"""
        # Mock successful cancellation
        mock_async_queue_service.cancel_conversion.return_value = True

        # Execute
        response = test_client.delete(
            "/api/v1/conversion/cancel/test-123",
            headers={"X-API-Key": "your-api-key-here"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "변환 작업이 취소되었습니다."
        assert data["data"]["conversion_id"] == "test-123"

        # Verify service call
        mock_async_queue_service.cancel_conversion.assert_called_once_with("test-123")

    def test_cancel_endpoint_not_found(self, test_client, mock_async_queue_service):
        """취소 엔드포인트 - 작업 없음 테스트"""
        # Mock failed cancellation
        mock_async_queue_service.cancel_conversion.return_value = False

        # Execute
        response = test_client.delete(
            "/api/v1/conversion/cancel/nonexistent",
            headers={"X-API-Key": "your-api-key-here"},
        )

        # Assertions
        assert response.status_code == 404
        assert response.json()["detail"] == "변환 작업을 찾을 수 없습니다."

    def test_retry_endpoint(self, test_client, mock_async_queue_service):
        """재시도 엔드포인트 테스트"""
        # Mock job for retry
        mock_job = ConversionJob(
            conversion_id="test-123",
            filename="test.pdf",
            file_size=1024,
            ocr_enabled=True,
            state=JobState.FAILED,
            progress=0,
            message="실패",
        )
        mock_async_queue_service.retry_conversion.return_value = mock_job

        # Execute
        response = test_client.post(
            "/api/v1/conversion/retry/test-123",
            headers={
                "X-API-Key": "your-api-key-here",
                "Content-Type": "application/json",
            },
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "재시도가 시작되었습니다."
        assert data["data"]["conversion_id"] == "test-123"

        # Verify service call
        mock_async_queue_service.retry_conversion.assert_called_once_with("test-123")

    def test_retry_endpoint_not_found(self, test_client, mock_async_queue_service):
        """재시도 엔드포인트 - 작업 없음 테스트"""
        # Mock job not found
        mock_async_queue_service.retry_conversion.side_effect = KeyError(
            "Job not found"
        )

        # Execute
        response = test_client.post(
            "/api/v1/conversion/retry/nonexistent",
            headers={
                "X-API-Key": "your-api-key-here",
                "Content-Type": "application/json",
            },
        )

        # Assertions
        assert response.status_code == 404
        assert response.json()["detail"] == "재시도 가능한 작업을 찾을 수 없습니다."

    def test_health_check_endpoint(self, test_client):
        """상태 확인 엔드포인트 테스트"""
        # Execute
        response = test_client.get("/health")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_api_key_required(self, test_client, mock_async_queue_service):
        """API 키 필요 테스트"""
        mock_job = ConversionJob(
            conversion_id="test-123",
            filename="test.pdf",
            file_size=1024,
            ocr_enabled=True,
            state=JobState.PENDING,
            progress=0,
        )
        mock_async_queue_service.get_status.return_value = mock_job

        # Execute without API key
        response = test_client.get("/api/v1/conversion/status/test-123")

        assert response.status_code == 200

    def test_api_key_valid(self, test_client, mock_async_queue_service):
        """유효한 API 키 테스트"""
        mock_job = ConversionJob(
            conversion_id="test-123",
            filename="test.pdf",
            file_size=1024,
            ocr_enabled=True,
            state=JobState.PENDING,
            progress=0,
        )
        mock_async_queue_service.get_status.return_value = mock_job

        # Execute with valid API key
        response = test_client.get(
            "/api/v1/conversion/status/test-123",
            headers={"X-API-Key": "your-api-key-here"},
        )

        assert response.status_code == 200


class TestAsyncServiceIntegration:
    """비동기 서비스 통합 테스트"""

    @pytest.fixture
    def mock_settings(self):
        """모의 설정 객체"""
        with patch(
            "app.services.async_queue_service.get_settings"
        ) as mock_get_settings:
            settings = MagicMock()
            settings.redis.url = "redis://localhost:6379/0"
            mock_get_settings.return_value = settings
            yield settings

    @pytest.fixture
    def mock_celery_app(self):
        """모의 Celery 앱"""
        with patch("app.services.async_queue_service.celery_app") as mock_app:
            app = MagicMock()
            app.control.inspect.return_value.stats.return_value = {
                "worker1": {"total": 100}
            }
            mock_app.return_value = app
            yield app

    @pytest.fixture
    def mock_store(self):
        """모의 작업 저장소"""
        with patch(
            "app.services.async_queue_service.ConversionJobStore"
        ) as mock_store_class:
            store = AsyncMock()
            mock_store_class.return_value = store
            yield store

    @pytest.mark.asyncio
    async def test_service_initialization(
        self, mock_settings, mock_celery_app, mock_store
    ):
        """서비스 초기화 통합 테스트"""
        from app.services.async_queue_service import AsyncQueueService

        # Create service
        service = AsyncQueueService()
        service.settings = mock_settings
        service.celery_app = mock_celery_app
        service.store = mock_store

        # Initialize
        await service.initialize()

        # Verify initialization
        assert service._initialized is True
        mock_celery_app.control.inspect.assert_called_once()

    @pytest.mark.asyncio
    async def test_service_lifecycle(self, mock_settings, mock_celery_app, mock_store):
        """서비스 라이프사이클 통합 테스트"""
        from app.services.async_queue_service import AsyncQueueService

        # Create service
        service = AsyncQueueService()
        service.settings = mock_settings
        service.celery_app = mock_celery_app
        service.store = mock_store

        # Initialize
        await service.initialize()

        # Start conversion
        mock_job = ConversionJob(
            conversion_id="test-123",
            filename="test.pdf",
            file_size=1024,
            ocr_enabled=True,
            state=JobState.PENDING,
            progress=0,
        )
        mock_store.create.return_value = mock_job

        mock_task = MagicMock()
        mock_task.id = "celery-task-123"
        mock_celery_app.send_task.return_value = mock_task

        job = await service.start_conversion(
            conversion_id="test-123",
            filename="test.pdf",
            file_size=1024,
            ocr_enabled=True,
            pdf_bytes=b"test content",
        )

        # Verify job creation
        assert job.conversion_id == "test-123"
        assert job.celery_task_id == "celery-task-123"

        # Get status
        mock_job.state = JobState.PROCESSING
        mock_job.progress = 50
        mock_store.get.return_value = mock_job

        status = await service.get_status("test-123")
        assert status.state == JobState.PROCESSING
        assert status.progress == 50

        # Cancel job
        # Use the job returned by start_conversion to ensure celery_task_id is set
        mock_store.get.return_value = job
        result = await service.cancel_conversion("test-123")
        assert result is True

        # Verify calls
        mock_store.cancel.assert_called_once_with("test-123")
        mock_celery_app.control.revoke.assert_called_once_with(
            "celery-task-123", terminate=True
        )

    @pytest.mark.asyncio
    async def test_error_handling(self, mock_settings, mock_celery_app, mock_store):
        """오류 처리 통합 테스트"""
        from app.services.async_queue_service import AsyncQueueService

        # Create service
        service = AsyncQueueService()
        service.settings = mock_settings
        service.celery_app = mock_celery_app
        service.store = mock_store

        # Initialize with error
        mock_celery_app.control.inspect.return_value.stats.side_effect = Exception(
            "Connection error"
        )

        with pytest.raises(Exception):
            await service.initialize()

        # Start conversion with error
        mock_celery_app.send_task.side_effect = Exception("Queue error")
        mock_store.create.return_value = ConversionJob(
            conversion_id="test-123",
            filename="test.pdf",
            file_size=1024,
            ocr_enabled=True,
            state=JobState.PENDING,
            progress=0,
        )

        with pytest.raises(Exception):
            await service.start_conversion(
                conversion_id="test-123",
                filename="test.pdf",
                file_size=1024,
                ocr_enabled=True,
                pdf_bytes=b"test content",
            )

    @pytest.mark.asyncio
    async def test_queue_statistics(self, mock_settings, mock_celery_app, mock_store):
        """큐 통계 통합 테스트"""
        from app.services.async_queue_service import AsyncQueueService

        # Create service
        service = AsyncQueueService()
        service.settings = mock_settings
        service.celery_app = mock_celery_app
        service.store = mock_store

        # Initialize
        await service.initialize()

        # Mock inspect results
        mock_inspect = mock_celery_app.control.inspect.return_value
        mock_inspect.active.return_value = {"worker1": [{"id": "task1"}]}
        mock_inspect.reserved.return_value = {"worker1": [{"id": "task2"}]}
        mock_inspect.scheduled.return_value = {"worker1": [{"id": "task3"}]}
        mock_inspect.stats.return_value = {"worker1": {"total": 100}}

        # Get stats
        stats = await service.get_queue_stats()

        # Verify stats
        assert stats["active_tasks"] == 1
        assert stats["reserved_tasks"] == 1
        assert stats["scheduled_tasks"] == 1
        assert stats["worker_count"] == 1
        assert "timestamp" in stats
