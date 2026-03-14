"""비동기 작업 큐 서비스

설명: Celery와 상호작용하는 서비스로, 변환 작업을 큐에 등록하고 상태를 추적합니다.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path

from app.core.config import get_settings
from app.celery_config import celery_app
from app.services.conversion_orchestrator import (
    apply_serialized_job_status,
    ConversionJob,
    JobState,
    ConversionJobStore,
    get_orchestrator,
)

logger = logging.getLogger(__name__)


class QueueUnavailableError(RuntimeError):
    """변환 큐가 준비되지 않았을 때 발생하는 예외"""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(
            message or "변환 작업 큐가 준비되지 않았습니다. 잠시 후 다시 시도해주세요."
        )


class AsyncQueueService:
    """비동기 작업 큐 서비스"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.celery_app = celery_app
        self.orchestrator = get_orchestrator(self.settings)
        self._celery_requested = os.getenv(
            "APP_USE_CELERY", "true"
        ).strip().lower() not in (
            "0",
            "false",
        )
        self._allow_direct_fallback = self.settings.ALLOW_DIRECT_CONVERSION_FALLBACK
        self.use_celery = self._celery_requested
        self.store = (
            ConversionJobStore() if self.use_celery else self.orchestrator.store
        )
        self._initialized = False
        self._last_celery_failure_at: Optional[datetime] = None
        self._celery_retry_cooldown_seconds = 30

    def _activate_direct_mode(self) -> None:
        self.use_celery = False
        self.store = self.orchestrator.store

    def _activate_celery_mode(self) -> None:
        self.use_celery = True
        self._last_celery_failure_at = None
        if self.store is self.orchestrator.store:
            self.store = ConversionJobStore()

    def _record_celery_failure(self) -> None:
        self._last_celery_failure_at = datetime.now(timezone.utc)

    def _raise_queue_unavailable(self, *, reason: str) -> None:
        logger.warning("변환 큐 사용 불가", extra={"reason": reason})
        raise QueueUnavailableError(
            f"변환 작업 큐가 준비되지 않았습니다: {reason}. 잠시 후 다시 시도해주세요."
        )

    def _is_celery_retry_cooldown_active(self) -> bool:
        if self._last_celery_failure_at is None:
            return False

        retry_allowed_at = self._last_celery_failure_at + timedelta(
            seconds=self._celery_retry_cooldown_seconds
        )
        return datetime.now(timezone.utc) < retry_allowed_at

    def _create_pending_job(
        self,
        *,
        conversion_id: str,
        filename: str,
        file_size: int,
        ocr_enabled: bool,
        owner_user_id: Optional[str] = None,
        translate_to_korean: bool = False,
    ) -> ConversionJob:
        return ConversionJob(
            conversion_id=conversion_id,
            filename=filename,
            file_size=file_size,
            ocr_enabled=ocr_enabled,
            owner_user_id=owner_user_id,
            translate_to_korean=translate_to_korean,
            source_pdf_bytes=None,
            state=JobState.PENDING,
            progress=0,
            current_step="queued",
        )

    def _build_celery_task_kwargs(
        self,
        *,
        conversion_id: str,
        filename: str,
        file_size: int,
        ocr_enabled: bool,
        translate_to_korean: bool,
        pdf_path: str,
    ) -> Dict[str, Any]:
        return {
            "conversion_id": conversion_id,
            "filename": filename,
            "file_size": file_size,
            "ocr_enabled": ocr_enabled,
            "translate_to_korean": translate_to_korean,
            "pdf_path": pdf_path,
        }

    def _submit_celery_conversion_task(self, **kwargs: Any) -> Any:
        return self.celery_app.send_task(
            "app.tasks.conversion_tasks.start_conversion",
            kwargs=kwargs,
        )

    async def _persist_uploaded_pdf(self, conversion_id: str, pdf_bytes: bytes) -> Path:
        uploads_dir = Path("./uploads")
        uploads_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = uploads_dir / f"{conversion_id}.pdf"
        pdf_path.write_bytes(pdf_bytes)
        return pdf_path

    async def _queue_conversion_job(
        self,
        *,
        conversion_id: str,
        filename: str,
        file_size: int,
        ocr_enabled: bool,
        translate_to_korean: bool,
        pdf_bytes: bytes,
        job: ConversionJob,
    ) -> ConversionJob:
        pdf_path = await self._persist_uploaded_pdf(conversion_id, pdf_bytes)
        task_kwargs = self._build_celery_task_kwargs(
            conversion_id=conversion_id,
            filename=filename,
            file_size=file_size,
            ocr_enabled=ocr_enabled,
            translate_to_korean=translate_to_korean,
            pdf_path=str(pdf_path),
        )
        task = self._submit_celery_conversion_task(**task_kwargs)

        job.celery_task_id = task.id
        await self.store.update(conversion_id, celery_task_id=task.id)

        logger.info(
            "변환 작업이 큐에 등록되었습니다",
            extra={
                "conversion_id": conversion_id,
                "celery_task_id": task.id,
                "queue": "conversion",
            },
        )
        return job

    async def _fallback_to_direct_start(
        self,
        *,
        conversion_id: str,
        filename: str,
        file_size: int,
        ocr_enabled: bool,
        owner_user_id: Optional[str],
        translate_to_korean: bool,
        pdf_bytes: bytes,
        error: Exception,
    ) -> ConversionJob:
        logger.error("Celery 작업 등록 실패", exc_info=True)
        await self.store.update(
            conversion_id,
            state=JobState.FAILED,
            message=f"작업 등록 실패: {str(error)}",
            error_message=str(error),
        )
        if not self._allow_direct_fallback:
            self._record_celery_failure()
            self._raise_queue_unavailable(reason="Celery 작업 등록에 실패했습니다")
        self.use_celery = False
        self.store = self.orchestrator.store
        return await self.orchestrator.start(
            conversion_id=conversion_id,
            filename=filename,
            file_size=file_size,
            ocr_enabled=ocr_enabled,
            owner_user_id=owner_user_id,
            translate_to_korean=translate_to_korean,
            pdf_bytes=pdf_bytes,
        )

    async def initialize(self, force: bool = False) -> None:
        """서비스 초기화"""
        if self._initialized and not force:
            return

        if not self._celery_requested:
            self._activate_direct_mode()
            logger.info("직접 실행 모드로 동작합니다 (Celery 비활성화)")
            self._initialized = True
            return

        # Celery 앱 초기화 확인
        try:
            # Celery 워커 상태 확인
            inspect = self.celery_app.control.inspect()
            stats = inspect.stats()
            ping = inspect.ping()
            if stats and ping:
                self._activate_celery_mode()
                logger.info(
                    "Celery 워커 연결 성공",
                    extra={"worker_count": len(stats)},
                )
            else:
                raise RuntimeError("Celery 워커 응답을 확인할 수 없습니다")
        except Exception:
            logger.warning(
                "Celery 연결 실패로 직접 실행 모드로 전환합니다", exc_info=True
            )
            self._activate_direct_mode()
            self._record_celery_failure()

        self._initialized = True

    async def _ensure_runtime_mode(self) -> None:
        if not self._initialized:
            await self.initialize()
            return

        if self._celery_requested and not self.use_celery:
            if self._is_celery_retry_cooldown_active():
                logger.debug(
                    "Celery 재연결 냉각 시간 중이라 직접 실행 모드를 유지합니다"
                )
                return
            await self.initialize(force=True)

    async def _get_job_from_available_stores(
        self, conversion_id: str
    ) -> Optional[ConversionJob]:
        stores = [self.store]
        if self.store is not self.orchestrator.store:
            stores.append(self.orchestrator.store)

        for store in stores:
            try:
                return await store.get(conversion_id)
            except KeyError:
                continue

        return None

    @staticmethod
    def _extract_celery_job_payload(result: Any) -> Optional[Dict[str, Any]]:
        info = getattr(result, "info", None)
        if isinstance(info, dict):
            job_payload = info.get("job")
            if isinstance(job_payload, dict):
                return job_payload
        result_payload = getattr(result, "result", None)
        if isinstance(result_payload, dict):
            job_payload = result_payload.get("job")
            if isinstance(job_payload, dict):
                return job_payload
        return None

    async def _apply_celery_job_payload(
        self,
        conversion_id: str,
        payload: Dict[str, Any],
        existing_job: Optional[ConversionJob] = None,
    ) -> ConversionJob:
        job = existing_job or await self._get_job_from_available_stores(conversion_id)
        if job is None:
            job = ConversionJob(
                conversion_id=conversion_id,
                filename=str(payload.get("filename", "")),
                file_size=int(payload.get("file_size", 0)),
                ocr_enabled=bool(payload.get("ocr_enabled", False)),
                owner_user_id=(
                    str(payload.get("owner_user_id"))
                    if payload.get("owner_user_id") is not None
                    else None
                ),
                translate_to_korean=bool(payload.get("translate_to_korean", False)),
            )
            await self.store.create(job)

        apply_serialized_job_status(job, payload)
        await self.store.update(
            conversion_id,
            filename=job.filename,
            file_size=job.file_size,
            ocr_enabled=job.ocr_enabled,
            owner_user_id=job.owner_user_id,
            translate_to_korean=job.translate_to_korean,
            state=job.state,
            progress=job.progress,
            message=job.message,
            created_at=job.created_at,
            updated_at=job.updated_at,
            current_step=job.current_step,
            steps=job.steps,
            result_path=job.result_path,
            error_message=job.error_message,
            llm_used_model=job.llm_used_model,
            llm_attempt_count=job.llm_attempt_count,
            llm_fallback_used=job.llm_fallback_used,
            attempts=job.attempts,
            celery_task_id=job.celery_task_id,
        )
        return job

    async def _reload_job(
        self, conversion_id: str, fallback_job: ConversionJob
    ) -> ConversionJob:
        return await self._get_job_from_available_stores(conversion_id) or fallback_job

    async def _update_job_for_result_state(
        self,
        *,
        conversion_id: str,
        result: Any,
        job: ConversionJob,
        payload: Optional[Dict[str, Any]],
    ) -> ConversionJob:
        if payload is not None:
            job = await self._apply_celery_job_payload(
                conversion_id,
                payload,
                existing_job=job,
            )

        if result.state in {"PROGRESS", "STARTED"}:
            return await self._handle_progress_state(
                conversion_id=conversion_id,
                job=job,
                result_state=result.state,
                payload=payload,
            )
        if result.state == "RETRY":
            await self.store.update(
                conversion_id,
                state=JobState.PENDING,
                current_step=job.current_step or "retrying",
                message=job.message or "작업 재시도 대기중",
            )
            return await self._reload_job(conversion_id, job)
        if result.state == "SUCCESS":
            return await self._handle_success_state(
                conversion_id=conversion_id,
                job=job,
                result_payload=result.result,
            )
        if result.state == "FAILURE":
            await self.store.update(
                conversion_id,
                state=JobState.FAILED,
                current_step="failed",
                message=job.message or f"작업 실패: {str(result.result)}",
                error_message=job.error_message or str(result.result),
            )
            return await self._reload_job(conversion_id, job)
        if result.state == "REVOKED":
            await self.store.update(
                conversion_id,
                state=JobState.CANCELLED,
                current_step="cancelled",
                message="작업이 취소되었습니다",
            )
            return await self._reload_job(conversion_id, job)
        return job

    async def _handle_progress_state(
        self,
        *,
        conversion_id: str,
        job: ConversionJob,
        result_state: str,
        payload: Optional[Dict[str, Any]],
    ) -> ConversionJob:
        if payload is None:
            state = JobState.PROCESSING
            if result_state == "PROGRESS":
                await self.store.update(
                    conversion_id,
                    state=state,
                    message="변환 처리 중",
                )
            else:
                await self.store.update(
                    conversion_id,
                    state=state,
                    current_step=job.current_step or "started",
                    message=job.message or "변환 처리 시작",
                )
        return await self._reload_job(conversion_id, job)

    async def _handle_success_state(
        self,
        *,
        conversion_id: str,
        job: ConversionJob,
        result_payload: Any,
    ) -> ConversionJob:
        result_bytes: Optional[bytes] = getattr(job, "result_bytes", None)
        result_path: Optional[str] = getattr(job, "result_path", None)
        if isinstance(result_payload, (bytes, bytearray)):
            result_bytes = bytes(result_payload)
        elif isinstance(result_payload, dict):
            candidate = result_payload.get("result_path")
            if isinstance(candidate, str) and candidate:
                result_path = candidate
                try:
                    result_bytes = Path(result_path).read_bytes()
                except Exception:
                    logger.warning(
                        "결과 파일을 읽지 못해 기존 result_bytes를 유지합니다",
                        extra={
                            "conversion_id": conversion_id,
                            "result_path": result_path,
                        },
                    )

        await self.store.update(
            conversion_id,
            state=JobState.COMPLETED,
            progress=100,
            message=(job.message or "변환 완료"),
            current_step=(job.current_step or "completed"),
            result_bytes=result_bytes,
            result_path=result_path or job.result_path,
        )
        return await self._reload_job(conversion_id, job)

    async def _reset_job_for_retry(
        self, conversion_id: str, job: ConversionJob
    ) -> None:
        previous_task_id = job.celery_task_id
        if previous_task_id:
            self.celery_app.control.revoke(previous_task_id, terminate=True)
        job.celery_task_id = None
        await self.store.update(
            conversion_id,
            celery_task_id=None,
            state=JobState.PENDING,
            progress=0,
            current_step="queued",
            message="재시도 대기중",
            error_message=None,
            result_path=None,
            result_bytes=None,
            steps=[],
        )

    async def _retry_with_saved_file(
        self,
        conversion_id: str,
        job: ConversionJob,
    ) -> ConversionJob:
        pdf_path = Path("./uploads") / f"{conversion_id}.pdf"
        if not pdf_path.exists():
            raise KeyError("PDF file not found")

        task_kwargs = self._build_celery_task_kwargs(
            conversion_id=conversion_id,
            filename=job.filename,
            file_size=job.file_size,
            ocr_enabled=job.ocr_enabled,
            translate_to_korean=job.translate_to_korean,
            pdf_path=str(pdf_path),
        )
        task = self._submit_celery_conversion_task(**task_kwargs)
        job.celery_task_id = task.id
        await self.store.update(conversion_id, celery_task_id=task.id)
        return job

    async def start_conversion(
        self,
        *,
        conversion_id: str,
        filename: str,
        file_size: int,
        ocr_enabled: bool,
        owner_user_id: Optional[str] = None,
        translate_to_korean: bool = False,
        pdf_bytes: bytes,
    ) -> ConversionJob:
        """변환 작업 시작 (비동기 큐에 등록)

        Args:
            conversion_id: 변환 작업 ID
            filename: 파일 이름
            file_size: 파일 크기
            ocr_enabled: OCR 활성화 여부
            pdf_bytes: PDF 파일 바이트 데이터

        Returns:
            ConversionJob: 생성된 작업 정보
        """
        await self._ensure_runtime_mode()

        if not self.use_celery:
            if not self._allow_direct_fallback:
                reason = (
                    "Celery 사용이 비활성화되었습니다"
                    if not self._celery_requested
                    else "Celery 또는 Redis에 연결할 수 없습니다"
                )
                self._raise_queue_unavailable(reason=reason)
            return await self.orchestrator.start(
                conversion_id=conversion_id,
                filename=filename,
                file_size=file_size,
                ocr_enabled=ocr_enabled,
                owner_user_id=owner_user_id,
                translate_to_korean=translate_to_korean,
                pdf_bytes=pdf_bytes,
            )

        job = self._create_pending_job(
            conversion_id=conversion_id,
            filename=filename,
            file_size=file_size,
            ocr_enabled=ocr_enabled,
            owner_user_id=owner_user_id,
            translate_to_korean=translate_to_korean,
        )
        await self.store.create(job)

        try:
            return await self._queue_conversion_job(
                conversion_id=conversion_id,
                filename=filename,
                file_size=file_size,
                ocr_enabled=ocr_enabled,
                translate_to_korean=translate_to_korean,
                pdf_bytes=pdf_bytes,
                job=job,
            )
        except Exception as e:
            return await self._fallback_to_direct_start(
                conversion_id=conversion_id,
                filename=filename,
                file_size=file_size,
                ocr_enabled=ocr_enabled,
                owner_user_id=owner_user_id,
                translate_to_korean=translate_to_korean,
                pdf_bytes=pdf_bytes,
                error=e,
            )

    async def get_status(self, conversion_id: str) -> ConversionJob:
        """변환 작업 상태 조회

        Args:
            conversion_id: 변환 작업 ID

        Returns:
            ConversionJob: 작업 상태 정보
        """
        await self._ensure_runtime_mode()

        if not self.use_celery:
            return await self.orchestrator.status(conversion_id)

        job = await self._get_job_from_available_stores(conversion_id)
        if job is None:
            raise KeyError("Job not found")

        # Celery 작업 상태 확인
        if job.celery_task_id:
            try:
                result = self.celery_app.AsyncResult(job.celery_task_id)
                payload = self._extract_celery_job_payload(result)
                job = await self._update_job_for_result_state(
                    conversion_id=conversion_id,
                    result=result,
                    job=job,
                    payload=payload,
                )
            except Exception as e:
                logger.error(
                    "Celery 작업 상태 확인 실패",
                    extra={"conversion_id": conversion_id, "error": str(e)},
                )

        return job

    async def cancel_conversion(self, conversion_id: str) -> bool:
        """변환 작업 취소

        Args:
            conversion_id: 변환 작업 ID

        Returns:
            bool: 취소 성공 여부
        """
        await self._ensure_runtime_mode()

        if not self.use_celery:
            try:
                await self.orchestrator.cancel(conversion_id)
                return True
            except KeyError:
                return False
            except Exception:
                logger.error("직접 모드 작업 취소 실패", exc_info=True)
                return False

        try:
            job = await self._get_job_from_available_stores(conversion_id)
            if job is None:
                raise KeyError

            # Celery 작업 취소
            if job.celery_task_id:
                self.celery_app.control.revoke(job.celery_task_id, terminate=True)

            # 로컬 상태 업데이트
            target_store = self.store
            if self.store is not self.orchestrator.store and job.celery_task_id is None:
                target_store = self.orchestrator.store
            await target_store.cancel(conversion_id)

            logger.info(
                "변환 작업이 취소되었습니다",
                extra={"conversion_id": conversion_id},
            )

            return True

        except KeyError:
            logger.warning(
                "작업을 찾을 수 없습니다", extra={"conversion_id": conversion_id}
            )
            return False
        except Exception:
            logger.error("작업 취소 실패", exc_info=True)
            return False

    async def list_recent_jobs(self, limit: int = 10) -> list[ConversionJob]:
        await self._ensure_runtime_mode()

        stores = [self.store]
        if self.store is not self.orchestrator.store:
            stores.append(self.orchestrator.store)

        jobs_by_id: dict[str, ConversionJob] = {}
        for store in stores:
            try:
                jobs = await store.list_jobs()
            except AttributeError:
                continue
            for job in jobs:
                jobs_by_id[job.conversion_id] = job

        sorted_jobs = sorted(
            jobs_by_id.values(),
            key=lambda job: job.created_at,
            reverse=True,
        )
        return sorted_jobs[: max(1, limit)]

    async def retry_conversion(self, conversion_id: str) -> ConversionJob:
        """실패한 작업 재시도

        Args:
            conversion_id: 변환 작업 ID

        Returns:
            ConversionJob: 재시도된 작업 정보
        """
        await self._ensure_runtime_mode()

        if not self.use_celery:
            return await self.orchestrator.retry(conversion_id)

        job = await self._get_job_from_available_stores(conversion_id)
        if job is None:
            raise KeyError("Job not found")

        if job.state not in (JobState.FAILED, JobState.CANCELLED):
            raise ValueError("재시도 가능한 상태가 아닙니다")

        await self._reset_job_for_retry(conversion_id, job)

        if job.source_pdf_bytes:
            return await self.start_conversion(
                conversion_id=conversion_id,
                filename=job.filename,
                file_size=job.file_size,
                ocr_enabled=job.ocr_enabled,
                owner_user_id=job.owner_user_id,
                translate_to_korean=job.translate_to_korean,
                pdf_bytes=job.source_pdf_bytes,
            )

        return await self._retry_with_saved_file(conversion_id, job)

    async def get_queue_stats(self) -> Dict[str, Any]:
        """큐 통계 정보 조회

        Returns:
            Dict[str, Any]: 큐 통계 정보
        """
        await self._ensure_runtime_mode()

        if not self.use_celery:
            jobs = getattr(self.orchestrator.store, "_jobs", {})
            active_count = sum(
                1 for job in jobs.values() if job.state == JobState.PROCESSING
            )
            pending_count = sum(
                1 for job in jobs.values() if job.state == JobState.PENDING
            )
            return {
                "active_tasks": active_count,
                "reserved_tasks": pending_count,
                "scheduled_tasks": 0,
                "worker_count": 0,
                "mode": "direct",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        try:
            inspect = self.celery_app.control.inspect()

            # 활성 작업
            active_tasks = inspect.active()
            active_count = sum(len(tasks) for tasks in (active_tasks or {}).values())

            # 대기 중인 작업
            reserved_tasks = inspect.reserved()
            reserved_count = sum(
                len(tasks) for tasks in (reserved_tasks or {}).values()
            )

            # 큐 정보
            scheduled_tasks = inspect.scheduled()
            scheduled_count = sum(
                len(tasks) for tasks in (scheduled_tasks or {}).values()
            )

            # 워커 정보
            stats = inspect.stats()
            worker_count = len(stats) if stats else 0

            return {
                "active_tasks": active_count,
                "reserved_tasks": reserved_count,
                "scheduled_tasks": scheduled_count,
                "worker_count": worker_count,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error("큐 통계 조회 실패", exc_info=True)
            return {
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    async def cleanup_old_jobs(self, days: int = 7) -> int:
        """오래된 작업 정리

        Args:
            days: 정리할 기간 (일)

        Returns:
            int: 정리된 작업 수
        """
        # TODO: 데이터베이스 구현 시 실제 정리 로직 추가
        # 현재는 인메모리 저장소이므로 구현 불가
        logger.info("오래된 작업 정리 (현재 구현되지 않음)")
        return 0


# 전역 서비스 인스턴스
_async_queue_service: Optional[AsyncQueueService] = None


def get_async_queue_service() -> AsyncQueueService:
    """비동기 작업 큐 서비스 인스턴스 반환

    Returns:
        AsyncQueueService: 비동기 작업 큐 서비스
    """
    global _async_queue_service
    if _async_queue_service is None:
        _async_queue_service = AsyncQueueService()
    return _async_queue_service
