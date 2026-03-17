import pytest
from unittest.mock import MagicMock, patch
from unittest.mock import AsyncMock
from datetime import datetime, timedelta, timezone

from app.services.async_queue_service import AsyncQueueService, QueueUnavailableError
from app.services.conversion_orchestrator import ConversionJob, JobState


class TestAsyncQueueService:
    """현행 Celery + JobStore 기반 비동기 큐 서비스 테스트"""

    @pytest.mark.asyncio
    async def test_initialize_checks_celery_workers(self):
        service = AsyncQueueService()
        with patch.object(service.celery_app.control, "inspect") as inspect:
            inspect.return_value.stats.return_value = {"w1": {}}
            inspect.return_value.ping.return_value = {"w1": {"ok": "pong"}}
            await service.initialize()
            assert service._initialized is True

    @pytest.mark.asyncio
    async def test_start_conversion_enqueues_task_and_stores_job(self):
        service = AsyncQueueService()
        service._initialized = True

        service.store = AsyncMock()
        service.celery_app = MagicMock()
        service.celery_app.send_task.return_value.id = "celery-task-1"

        job = await service.start_conversion(
            conversion_id="cid-1",
            filename="doc.pdf",
            file_size=123,
            ocr_enabled=True,
            owner_user_id="user-1",
            pdf_bytes=b"%PDF-1.4",
        )

        service.store.create.assert_called_once()
        service.store.update.assert_called_once()
        assert job.celery_task_id == "celery-task-1"
        send_task_kwargs = service.celery_app.send_task.call_args.kwargs["kwargs"]
        assert send_task_kwargs["owner_user_id"] == "user-1"

    @pytest.mark.asyncio
    async def test_start_conversion_raises_when_queue_required_but_unavailable(self):
        service = AsyncQueueService()
        service._initialized = True
        service.use_celery = False
        service._allow_direct_fallback = False

        with pytest.raises(QueueUnavailableError):
            await service.start_conversion(
                conversion_id="cid-required",
                filename="doc.pdf",
                file_size=123,
                ocr_enabled=True,
                pdf_bytes=b"%PDF-1.4",
            )

    @pytest.mark.asyncio
    async def test_start_conversion_uses_direct_mode_when_fallback_allowed(self):
        service = AsyncQueueService()
        service._initialized = True
        service.use_celery = False
        service._allow_direct_fallback = True

        expected_job = ConversionJob(
            conversion_id="cid-direct",
            filename="doc.pdf",
            file_size=123,
            ocr_enabled=True,
            state=JobState.PENDING,
            progress=0,
        )

        with patch.object(
            service.orchestrator, "start", AsyncMock(return_value=expected_job)
        ) as mock_start:
            job = await service.start_conversion(
                conversion_id="cid-direct",
                filename="doc.pdf",
                file_size=123,
                ocr_enabled=True,
                pdf_bytes=b"%PDF-1.4",
            )

        assert job is expected_job
        mock_start.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_start_conversion_preserves_owner_when_queue_falls_back_to_direct(
        self,
    ):
        service = AsyncQueueService()
        service._initialized = True
        service.use_celery = True
        service._allow_direct_fallback = True
        service.store = AsyncMock()

        expected_job = ConversionJob(
            conversion_id="cid-fallback-owner",
            filename="doc.pdf",
            file_size=123,
            ocr_enabled=True,
            owner_user_id="user-123",
            state=JobState.PENDING,
            progress=0,
        )

        with patch.object(
            service,
            "_queue_conversion_job",
            AsyncMock(side_effect=RuntimeError("queue down")),
        ), patch.object(
            service.orchestrator,
            "start",
            AsyncMock(return_value=expected_job),
        ) as mock_start:
            job = await service.start_conversion(
                conversion_id="cid-fallback-owner",
                filename="doc.pdf",
                file_size=123,
                ocr_enabled=True,
                owner_user_id="user-123",
                pdf_bytes=b"%PDF-1.4",
            )

        assert job is expected_job
        mock_start.assert_awaited_once_with(
            conversion_id="cid-fallback-owner",
            filename="doc.pdf",
            file_size=123,
            ocr_enabled=True,
            owner_user_id="user-123",
            translate_to_korean=False,
            pdf_bytes=b"%PDF-1.4",
        )

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
    async def test_get_status_applies_progress_payload_from_celery(self):
        service = AsyncQueueService()
        service._initialized = True
        job = ConversionJob(
            conversion_id="cid-progress",
            filename="progress.pdf",
            file_size=10,
            ocr_enabled=True,
            state=JobState.PENDING,
            progress=0,
            current_step="queued",
        )
        await service.store.create(job)

        async_result = MagicMock()
        async_result.state = "PROGRESS"
        async_result.info = {
            "job": {
                "conversion_id": "cid-progress",
                "filename": "progress.pdf",
                "file_size": 10,
                "ocr_enabled": True,
                "translate_to_korean": False,
                "state": "processing",
                "progress": 72,
                "message": "OCR/LLM 처리 중 (8/11)",
                "created_at": job.created_at,
                "updated_at": job.updated_at,
                "current_step": "ocr_llm",
                "steps": [
                    {
                        "name": "analyze",
                        "progress": 5,
                        "message": "PDF 유형 분석 중",
                    },
                    {
                        "name": "ocr_llm",
                        "progress": 72,
                        "message": "OCR/LLM 처리 중 (8/11)",
                    },
                ],
                "result_path": None,
                "error_message": None,
                "llm_used_model": None,
                "llm_attempt_count": 0,
                "llm_fallback_used": False,
                "attempts": 1,
                "celery_task_id": "task-progress",
            }
        }

        service.celery_app = MagicMock()
        service.celery_app.AsyncResult.return_value = async_result
        job.celery_task_id = "task-progress"

        result = await service.get_status("cid-progress")

        assert result.progress == 72
        assert result.current_step == "ocr_llm"
        assert result.state == JobState.PROCESSING
        assert len(result.steps) == 2
        assert result.celery_task_id == "task-progress"

    @pytest.mark.asyncio
    async def test_get_status_progress_payload_does_not_clear_existing_celery_task_id(
        self,
    ):
        service = AsyncQueueService()
        service._initialized = True
        job = ConversionJob(
            conversion_id="cid-keep-task",
            filename="progress.pdf",
            file_size=10,
            ocr_enabled=True,
            state=JobState.PENDING,
            progress=0,
            current_step="queued",
        )
        job.celery_task_id = "task-keep"
        await service.store.create(job)

        async_result = MagicMock()
        async_result.state = "PROGRESS"
        async_result.info = {
            "job": {
                "conversion_id": "cid-keep-task",
                "filename": "progress.pdf",
                "file_size": 10,
                "ocr_enabled": True,
                "translate_to_korean": False,
                "state": "processing",
                "progress": 15,
                "message": "분석 중",
                "created_at": job.created_at,
                "updated_at": job.updated_at,
                "current_step": "analyze",
                "steps": [],
                "result_path": None,
                "error_message": None,
                "llm_used_model": None,
                "llm_attempt_count": 0,
                "llm_fallback_used": False,
                "attempts": 1,
            }
        }
        service.celery_app = MagicMock()
        service.celery_app.AsyncResult.return_value = async_result

        result = await service.get_status("cid-keep-task")

        assert result.celery_task_id == "task-keep"

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

    @pytest.mark.asyncio
    async def test_retry_conversion_reuses_original_pdf_bytes(self):
        service = AsyncQueueService()
        service._initialized = True
        source_pdf = b"%PDF-1.4 retry source"
        job = ConversionJob(
            conversion_id="cid-retry",
            filename="retry.pdf",
            file_size=len(source_pdf),
            ocr_enabled=True,
            owner_user_id="owner-1",
            state=JobState.FAILED,
            progress=0,
            source_pdf_bytes=source_pdf,
        )

        with patch.object(service, "start_conversion") as mock_start:
            from unittest.mock import AsyncMock

            service.store = AsyncMock()
            service.store.get.return_value = job
            service.store.update.return_value = job
            mock_start.return_value = job

            await service.retry_conversion("cid-retry")

            mock_start.assert_called_once_with(
                conversion_id="cid-retry",
                filename="retry.pdf",
                file_size=len(source_pdf),
                ocr_enabled=True,
                owner_user_id="owner-1",
                translate_to_korean=False,
                pdf_bytes=source_pdf,
            )

    @pytest.mark.asyncio
    async def test_retry_conversion_resets_status_before_requeue(self):
        service = AsyncQueueService()
        service._initialized = True
        service.use_celery = True
        job = ConversionJob(
            conversion_id="cid-reset",
            filename="retry.pdf",
            file_size=12,
            ocr_enabled=True,
            state=JobState.CANCELLED,
            progress=44,
            current_step="failed",
        )
        job.celery_task_id = "old-task"

        await service.store.create(job)
        service.celery_app = MagicMock()
        service.celery_app.send_task.return_value.id = "new-task"

        with patch(
            "app.services.async_queue_service.Path.exists", return_value=True
        ), patch("app.services.async_queue_service.Path.write_bytes"), patch(
            "app.services.async_queue_service.Path.read_bytes", return_value=b"%PDF-1.4"
        ):
            result = await service.retry_conversion("cid-reset")

        refreshed = await service.get_status("cid-reset")
        assert result.celery_task_id == "new-task"
        assert refreshed.celery_task_id == "new-task"
        assert refreshed.state == JobState.PENDING
        assert refreshed.progress == 0
        assert refreshed.current_step == "queued"
        assert refreshed.error_message is None
        service.celery_app.control.revoke.assert_called_once_with(
            "old-task", terminate=True
        )

    @pytest.mark.asyncio
    async def test_initialize_force_recovers_to_celery_after_transient_fallback(self):
        service = AsyncQueueService()
        service._initialized = True
        service.use_celery = False
        service.store = service.orchestrator.store

        with patch.object(service.celery_app.control, "inspect") as inspect:
            inspect.return_value.stats.return_value = {"w1": {}}
            inspect.return_value.ping.return_value = {"w1": {"ok": "pong"}}
            await service.initialize(force=True)

        assert service.use_celery is True
        assert service.store is not service.orchestrator.store

    @pytest.mark.asyncio
    async def test_ensure_runtime_mode_skips_forced_reinitialize_during_cooldown(self):
        service = AsyncQueueService()
        service._initialized = True
        service.use_celery = False
        service.store = service.orchestrator.store
        service._celery_requested = True
        service._celery_retry_cooldown_seconds = 30
        service._last_celery_failure_at = datetime.now(timezone.utc)

        with patch.object(service, "initialize", new_callable=AsyncMock) as initialize:
            await service._ensure_runtime_mode()

        initialize.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_ensure_runtime_mode_retries_after_cooldown_expires(self):
        service = AsyncQueueService()
        service._initialized = True
        service.use_celery = False
        service.store = service.orchestrator.store
        service._celery_requested = True
        service._celery_retry_cooldown_seconds = 30
        service._last_celery_failure_at = datetime.now(timezone.utc) - timedelta(
            seconds=31
        )

        with patch.object(service, "initialize", new_callable=AsyncMock) as initialize:
            await service._ensure_runtime_mode()

        initialize.assert_awaited_once_with(force=True)

    @pytest.mark.asyncio
    async def test_get_status_falls_back_to_orchestrator_store_for_direct_mode_job(
        self,
    ):
        service = AsyncQueueService()
        service._initialized = True
        service.use_celery = True
        service.store = AsyncMock()
        service.store.get.side_effect = KeyError("Job not found")

        direct_job = ConversionJob(
            conversion_id="cid-direct",
            filename="direct.pdf",
            file_size=10,
            ocr_enabled=True,
            state=JobState.PROCESSING,
            progress=55,
            current_step="ocr_llm",
        )
        await service.orchestrator.store.create(direct_job)

        result = await service.get_status("cid-direct")

        assert result is direct_job
