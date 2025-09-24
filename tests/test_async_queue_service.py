import pytest
from unittest.mock import MagicMock, patch

from app.services.async_queue_service import AsyncQueueService
from app.services.conversion_orchestrator import ConversionJob, JobState


class TestAsyncQueueService:
    """현행 Celery + JobStore 기반 비동기 큐 서비스 테스트"""

    @pytest.mark.asyncio
    async def test_initialize_checks_celery_workers(self):
        service = AsyncQueueService()
        with patch.object(service.celery_app.control, "inspect") as inspect:
            inspect.return_value.stats.return_value = {"w1": {}}
            await service.initialize()
            assert service._initialized is True

    @pytest.mark.asyncio
    async def test_start_conversion_enqueues_task_and_stores_job(self):
        service = AsyncQueueService()
        service._initialized = True
        from unittest.mock import AsyncMock

        service.store = AsyncMock()
        service.celery_app = MagicMock()
        service.celery_app.send_task.return_value.id = "celery-task-1"

        job = await service.start_conversion(
            conversion_id="cid-1",
            filename="doc.pdf",
            file_size=123,
            ocr_enabled=True,
            pdf_bytes=b"%PDF-1.4",
        )

        service.store.create.assert_called_once()
        service.store.update.assert_called_once()
        assert job.celery_task_id == "celery-task-1"

    @pytest.mark.asyncio
    async def test_get_status_updates_from_celery(self):
        service = AsyncQueueService()
        service._initialized = True
        job = ConversionJob(
            conversion_id="cid-1",
            filename="f.pdf",
            file_size=1,
            ocr_enabled=False,
            state=JobState.PENDING,
            progress=0,
        )
        from unittest.mock import AsyncMock

        service.store = AsyncMock()
        service.store.get.return_value = job

        # Simulate Celery SUCCESS (job must have celery_task_id)
        async_result = MagicMock()
        async_result.state = "SUCCESS"
        async_result.result = b"epub-bytes"
        service.celery_app = MagicMock()
        service.celery_app.AsyncResult.return_value = async_result
        job.celery_task_id = "task-1"

        result = await service.get_status("cid-1")
        assert result is job
        service.store.update.assert_called()

    @pytest.mark.asyncio
    async def test_cancel_conversion_revokes_celery_and_updates_store(self):
        service = AsyncQueueService()
        service._initialized = True
        job = ConversionJob(
            conversion_id="cid-1",
            filename="f.pdf",
            file_size=1,
            ocr_enabled=False,
            state=JobState.PROCESSING,
            progress=10,
        )
        job.celery_task_id = "celery-task-1"
        from unittest.mock import AsyncMock

        service.store = AsyncMock()
        service.store.get.return_value = job
        service.celery_app = MagicMock()

        ok = await service.cancel_conversion("cid-1")
        assert ok is True
        service.celery_app.control.revoke.assert_called_once()
        service.store.cancel.assert_called_once_with("cid-1")

    @pytest.mark.asyncio
    async def test_get_queue_stats_reads_inspect(self):
        service = AsyncQueueService()
        service._initialized = True
        inspect = MagicMock()
        inspect.active.return_value = {"w": [1]}
        inspect.reserved.return_value = {"w": [1]}
        inspect.scheduled.return_value = {"w": [1]}
        inspect.stats.return_value = {"w": {}}

        service.celery_app = MagicMock()
        service.celery_app.control.inspect.return_value = inspect

        stats = await service.get_queue_stats()
        assert stats["active_tasks"] == 1
        assert stats["reserved_tasks"] == 1
        assert stats["scheduled_tasks"] == 1
        assert stats["worker_count"] == 1
