import pytest
from unittest.mock import ANY, patch, AsyncMock, MagicMock

from app.tasks.conversion_tasks import (
    start_conversion,
    cleanup_old_jobs,
    get_queue_stats,
    health_check,
)
from app.services.conversion_orchestrator import JobState


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
        mock_job.filename = "test.pdf"
        mock_job.file_size = len(sample_pdf_content)
        mock_job.ocr_enabled = True
        mock_job.owner_user_id = None
        mock_job.translate_to_korean = False
        mock_job.state = JobState.PENDING
        mock_job.progress = 0
        mock_job.message = ""
        mock_job.created_at = "2026-03-07T00:00:00+00:00"
        mock_job.updated_at = "2026-03-07T00:00:00+00:00"
        mock_job.current_step = "queued"
        mock_job.steps = []
        mock_job.result_path = "results/conv-1.epub"
        mock_job.error_message = None
        mock_job.llm_used_model = None
        mock_job.llm_attempt_count = 0
        mock_job.llm_fallback_used = False
        mock_job.attempts = 0

        mock_orch = MagicMock()
        mock_orch.run_to_completion = AsyncMock(return_value=mock_job)

        # conversion_tasks 모듈에서 직접 import 한 get_orchestrator를 패치해야 함
        with patch(
            "app.tasks.conversion_tasks.get_orchestrator", return_value=mock_orch
        ), patch("app.tasks.conversion_tasks.logger"):
            result = start_conversion.run(
                conversion_id="conv-1",
                filename="test.pdf",
                file_size=len(sample_pdf_content),
                ocr_enabled=True,
                owner_user_id="user-123",
                pdf_bytes=sample_pdf_content.hex(),  # 실제 파일 대신 픽스처를 사용
            )

        # Assert
        assert result == {
            "conversion_id": "conv-1",
            "state": "pending",
            "progress": mock_job.progress,
            "message": mock_job.message,
            "current_step": mock_job.current_step,
            "result_path": "results/conv-1.epub",
            "job": {
                "conversion_id": "conv-1",
                "filename": mock_job.filename,
                "file_size": mock_job.file_size,
                "ocr_enabled": mock_job.ocr_enabled,
                "owner_user_id": None,
                "translate_to_korean": mock_job.translate_to_korean,
                "state": "pending",
                "progress": mock_job.progress,
                "message": mock_job.message,
                "created_at": mock_job.created_at,
                "updated_at": mock_job.updated_at,
                "current_step": mock_job.current_step,
                "steps": [],
                "result_path": "results/conv-1.epub",
                "error_message": mock_job.error_message,
                "llm_used_model": mock_job.llm_used_model,
                "llm_attempt_count": mock_job.llm_attempt_count,
                "llm_fallback_used": mock_job.llm_fallback_used,
                "attempts": mock_job.attempts,
            },
        }
        mock_orch.run_to_completion.assert_awaited_once_with(
            conversion_id="conv-1",
            filename="test.pdf",
            file_size=len(sample_pdf_content),
            ocr_enabled=True,
            owner_user_id="user-123",
            translate_to_korean=False,
            pdf_bytes=sample_pdf_content,
            status_callback=ANY,
        )

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
