"""비동기 작업 큐 서비스

설명: Celery와 상호작용하는 서비스로, 변환 작업을 큐에 등록하고 상태를 추적합니다.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from datetime import datetime, timezone

from app.core.config import get_settings
from app.celery_config import celery_app
from app.services.conversion_orchestrator import (
    ConversionJob,
    JobState,
    ConversionJobStore,
)

logger = logging.getLogger(__name__)


class AsyncQueueService:
    """비동기 작업 큐 서비스"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.celery_app = celery_app
        self.store = ConversionJobStore()
        self._initialized = False

    async def initialize(self) -> None:
        """서비스 초기화"""
        if self._initialized:
            return

        # Celery 앱 초기화 확인
        try:
            # Celery 워커 상태 확인
            inspect = self.celery_app.control.inspect()
            stats = inspect.stats()
            if stats:
                logger.info("Celery 워커 연결 성공", extra={"worker_count": len(stats)})
            else:
                logger.warning("Celery 워커가 연결되지 않았습니다")
        except Exception:
            logger.error("Celery 연결 확인 실패", exc_info=True)
            raise

        self._initialized = True

    async def start_conversion(
        self,
        *,
        conversion_id: str,
        filename: str,
        file_size: int,
        ocr_enabled: bool,
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
        if not self._initialized:
            await self.initialize()

        # 작업 생성
        job = ConversionJob(
            conversion_id=conversion_id,
            filename=filename,
            file_size=file_size,
            ocr_enabled=ocr_enabled,
            state=JobState.PENDING,
            progress=0,
            current_step="queued",
        )
        await self.store.create(job)

        # Celery 작업 큐에 등록
        try:
            task = self.celery_app.send_task(
                "app.tasks.conversion_tasks.start_conversion",
                kwargs={
                    "conversion_id": conversion_id,
                    "filename": filename,
                    "file_size": file_size,
                    "ocr_enabled": ocr_enabled,
                    "pdf_bytes": pdf_bytes.hex(),  # 바이트 데이터를 16진수 문자열로 변환
                },
                task_id=conversion_id,
                task_queue="conversion",
            )

            # 작업 ID 저장
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

        except Exception as e:
            logger.error("Celery 작업 등록 실패", exc_info=True)
            await self.store.update(
                conversion_id,
                state=JobState.FAILED,
                message=f"작업 등록 실패: {str(e)}",
                error_message=str(e),
            )
            raise

        return job

    async def get_status(self, conversion_id: str) -> ConversionJob:
        """변환 작업 상태 조회

        Args:
            conversion_id: 변환 작업 ID

        Returns:
            ConversionJob: 작업 상태 정보
        """
        if not self._initialized:
            await self.initialize()

        job = await self.store.get(conversion_id)

        # Celery 작업 상태 확인
        if job.celery_task_id:
            try:
                result = self.celery_app.AsyncResult(job.celery_task_id)
                if result.state == "PROGRESS":
                    # 진행률 업데이트
                    if hasattr(result.info, "progress"):
                        await self.store.update(
                            conversion_id,
                            progress=result.info.progress,
                            message=result.info.get("message", ""),
                        )
                elif result.state == "SUCCESS":
                    # 작업 완료
                    await self.store.update(
                        conversion_id,
                        state=JobState.COMPLETED,
                        progress=100,
                        message="변환 완료",
                        result_bytes=result.result,
                    )
                elif result.state == "FAILURE":
                    # 작업 실패
                    await self.store.update(
                        conversion_id,
                        state=JobState.FAILED,
                        message=f"작업 실패: {str(result.result)}",
                        error_message=str(result.result),
                    )
                elif result.state == "REVOKED":
                    # 작업 취소
                    await self.store.update(
                        conversion_id,
                        state=JobState.CANCELLED,
                        message="작업이 취소되었습니다",
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
        if not self._initialized:
            await self.initialize()

        try:
            job = await self.store.get(conversion_id)

            # Celery 작업 취소
            if job.celery_task_id:
                self.celery_app.control.revoke(job.celery_task_id, terminate=True)

            # 로컬 상태 업데이트
            await self.store.cancel(conversion_id)

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

    async def retry_conversion(self, conversion_id: str) -> ConversionJob:
        """실패한 작업 재시도

        Args:
            conversion_id: 변환 작업 ID

        Returns:
            ConversionJob: 재시도된 작업 정보
        """
        if not self._initialized:
            await self.initialize()

        job = await self.store.get(conversion_id)

        if job.state not in (JobState.FAILED, JobState.CANCELLED):
            raise ValueError("재시도 가능한 상태가 아닙니다")

        # 기존 Celery 작업 ID 초기화
        job.celery_task_id = None
        await self.store.update(conversion_id, celery_task_id=None)

        # 새로운 작업 등록
        return await self.start_conversion(
            conversion_id=conversion_id,
            filename=job.filename,
            file_size=job.file_size,
            ocr_enabled=job.ocr_enabled,
            pdf_bytes=b"",  # 기존 데이터는 재사용하지 않음
        )

    async def get_queue_stats(self) -> Dict[str, Any]:
        """큐 통계 정보 조회

        Returns:
            Dict[str, Any]: 큐 통계 정보
        """
        if not self._initialized:
            await self.initialize()

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
