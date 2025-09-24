import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.tasks.conversion_tasks import (
    start_conversion,
    cleanup_old_jobs,
    get_queue_stats,
    health_check,
)


class TestConversionTasks:
    """Celery 변환 작업 테스트"""

    @pytest.mark.asyncio
    async def test_start_conversion_success_uses_sample_pdf(
        self, sample_pdf_content: bytes
    ):
        """
        정상 경로: 샘플 PDF 바이트(픽스처)를 hex로 변환하여 전달하면
        오케스트레이터가 호출되고 성공 상태가 반환된다.
        """
        # Arrange
        mock_job = MagicMock()
        mock_job.conversion_id = "conv-1"
        mock_job.state = "pending"

        async def mock_start(**kwargs):
            return mock_job

        mock_orch = MagicMock()
        mock_orch.start = AsyncMock(side_effect=mock_start)

        # conversion_tasks 모듈에서 직접 import 한 get_orchestrator를 패치해야 함
        with patch(
            "app.tasks.conversion_tasks.get_orchestrator", return_value=mock_orch
        ), patch("app.tasks.conversion_tasks.logger"):
            result = start_conversion.run(
                conversion_id="conv-1",
                filename="test.pdf",
                file_size=len(sample_pdf_content),
                ocr_enabled=True,
                pdf_bytes=sample_pdf_content.hex(),  # 실제 파일 대신 픽스처를 사용
            )

        # Assert
        assert result == {"conversion_id": "conv-1", "state": "pending"}
        mock_orch.start.assert_awaited_once()

    def test_cleanup_old_jobs_success(self):
        """
        cleanup_old_jobs가 큐 서비스의 정리 로직을 호출하고 수치를 반환한다.
        """
        mock_service = MagicMock()
        mock_service.cleanup_old_jobs = AsyncMock(return_value=3)

        with patch(
            "app.tasks.conversion_tasks.get_async_queue_service",
            return_value=mock_service,
        ):
            count = cleanup_old_jobs(days=7)

        assert count == 3
        mock_service.cleanup_old_jobs.assert_awaited_once_with(7)

    def test_cleanup_old_jobs_invalid_days(self):
        """
        days가 1 미만이면 ValueError가 발생해야 한다.
        """
        with pytest.raises(ValueError):
            cleanup_old_jobs(days=0)

    def test_get_queue_stats(self):
        """
        get_queue_stats가 큐 서비스의 통계를 반환한다.
        """
        stats = {"queued": 2, "processing": 1}
        mock_service = MagicMock()
        mock_service.get_queue_stats = AsyncMock(return_value=stats)

        with patch(
            "app.tasks.conversion_tasks.get_async_queue_service",
            return_value=mock_service,
        ):
            result = get_queue_stats()

        assert result == stats
        mock_service.get_queue_stats.assert_awaited_once()

    def test_health_check_healthy(self):
        """
        큐 서비스 통계 조회가 성공하면 healthy 상태를 반환한다.
        """
        stats = {"queued": 0, "processing": 0}
        mock_service = MagicMock()
        mock_service.get_queue_stats = AsyncMock(return_value=stats)

        with patch(
            "app.tasks.conversion_tasks.get_async_queue_service",
            return_value=mock_service,
        ):
            result = health_check()

        assert result["status"] == "healthy"
        assert result["queue_stats"] == stats

    def test_health_check_unhealthy(self):
        """
        큐 서비스 통계 조회 중 예외가 발생하면 unhealthy 상태와 에러 메시지를 반환한다.
        """
        mock_service = MagicMock()
        mock_service.get_queue_stats = AsyncMock(side_effect=RuntimeError("boom"))

        with patch(
            "app.tasks.conversion_tasks.get_async_queue_service",
            return_value=mock_service,
        ):
            result = health_check()

        assert result["status"] == "unhealthy"
        assert "boom" in result.get("error", "")
