"""Celery task wrappers for the conversion pipeline.

This file exposes minimal, sync Celery tasks that call async
services via asgiref.sync.async_to_sync so workers don't import the
async stack at module import time.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from app.celery_config import (
    celery_app,
)
from app.services.async_queue_service import (
    get_async_queue_service,
)
from app.services.conversion_orchestrator import (
    get_orchestrator,
)

# Use concurrent.futures instead of asgiref.sync for better compatibility
# This avoids the asgiref dependency issue while still allowing async function calls
import concurrent.futures
from functools import wraps


def async_to_sync(func):
    """
    Convert an async function to a sync function.

    This is a replacement for asgiref.sync.async_to_sync that works
    in any environment without requiring asgiref.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create a new event loop in a separate thread
        def run_async():
            import asyncio

            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(func(*args, **kwargs))
            finally:
                loop.close()

        # Run the async function in a thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_async)
            return future.result()

    return wrapper


logger = logging.getLogger(__name__)


def _decode_pdf_bytes(pdf_bytes: Any) -> bytes:
    """Decode PDF bytes from hex string or return as-is if already bytes."""
    if isinstance(pdf_bytes, str):
        try:
            return bytes.fromhex(pdf_bytes)
        except ValueError as e:
            raise ValueError(f"Invalid hex string for PDF bytes: {e}")
    return pdf_bytes


TASK_START = "app.tasks.conversion_tasks.start_conversion"
TASK_CLEANUP_OLD = "app.tasks.conversion_tasks.cleanup_old_jobs"
TASK_GET_STATS = "app.tasks.conversion_tasks.get_queue_stats"
TASK_HEALTH = "app.tasks.conversion_tasks.health_check"


@celery_app.task(bind=True, name=TASK_START)
def start_conversion(
    self,
    conversion_id: str,
    filename: str,
    file_size: int,
    ocr_enabled: bool,
    pdf_bytes: str,
) -> Dict[str, Any]:
    """Start PDF to EPUB conversion task.

    Args:
        self: Celery task instance
        conversion_id: Unique identifier for the conversion
        filename: Original PDF filename
        file_size: Size of the PDF file in bytes
        ocr_enabled: Whether OCR processing should be enabled
        pdf_bytes: PDF file content as hex string or bytes

    Returns:
        Dictionary containing conversion_id and state

    Raises:
        Celery Retry: On failure with exponential backoff
    """
    orch = get_orchestrator()
    try:
        raw = _decode_pdf_bytes(pdf_bytes)
        logger.info(
            "Starting conversion task",
            extra={
                "conversion_id": conversion_id,
                "filename": filename,
                "file_size": file_size,
                "ocr_enabled": ocr_enabled,
            },
        )

        job = async_to_sync(orch.start)(
            conversion_id=conversion_id,
            filename=filename,
            file_size=file_size,
            ocr_enabled=ocr_enabled,
            pdf_bytes=raw,
        )

        logger.info(
            "Conversion task started successfully",
            extra={"conversion_id": conversion_id, "state": job.state},
        )

        return {"conversion_id": job.conversion_id, "state": job.state}

    except ValueError as exc:
        # Handle specific validation errors without retry
        logger.error(
            "Invalid input for conversion task",
            extra={"conversion_id": conversion_id, "error": str(exc)},
        )
        raise

    except Exception as exc:
        logger.exception(
            "start_conversion failed: %s",
            str(exc),
            extra={"conversion_id": conversion_id},
        )
        # Use countdown with exponential backoff
        countdown = min(60 * (2**self.request.retries), 300)  # Max 5 minutes
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(bind=True, name=TASK_CLEANUP_OLD)
def cleanup_old_jobs(self, days: int = 7) -> int:
    """Clean up old conversion jobs from the queue.

    Args:
        self: Celery task instance
        days: Number of days to keep jobs (default: 7)

    Returns:
        Number of jobs cleaned up

    Raises:
        Celery Retry: On failure with exponential backoff
    """
    if days < 1:
        raise ValueError("Days must be at least 1")

    svc = get_async_queue_service()
    try:
        logger.info("Starting cleanup of old jobs", extra={"days": days})
        result = async_to_sync(svc.cleanup_old_jobs)(days)
        logger.info("Cleanup completed", extra={"days": days, "result": result})
        return result
    except ValueError as exc:
        # Handle specific validation errors without retry
        logger.error(
            "Invalid cleanup parameter", extra={"days": days, "error": str(exc)}
        )
        raise
    except Exception as exc:
        logger.exception("cleanup_old_jobs failed: %s", str(exc), extra={"days": days})
        # Use countdown with exponential backoff
        countdown = min(300 * (2**self.request.retries), 3600)  # Max 1 hour
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(bind=True, name=TASK_GET_STATS)
def get_queue_stats(self) -> Dict[str, Any]:
    """Get queue statistics for monitoring.

    Returns:
        Dictionary containing queue statistics

    Raises:
        Celery Retry: On failure with exponential backoff
    """
    svc = get_async_queue_service()
    try:
        logger.debug("Fetching queue statistics")
        stats = async_to_sync(svc.get_queue_stats)()
        logger.debug("Queue statistics retrieved", extra={"stats": stats})
        return stats
    except Exception as exc:
        logger.exception("get_queue_stats failed: %s", str(exc))
        # Use countdown with exponential backoff
        countdown = min(60 * (2**self.request.retries), 300)  # Max 5 minutes
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(bind=True, name=TASK_HEALTH)
def health_check(self) -> Dict[str, Any]:
    """Perform health check of the conversion service.

    Returns:
        Dictionary containing health status and statistics
    """
    svc = get_async_queue_service()
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        logger.debug("Performing health check")
        stats = async_to_sync(svc.get_queue_stats)()

        logger.info("Health check passed", extra={"stats": stats})
        return {
            "queue_stats": stats,
            "timestamp": timestamp,
            "status": "healthy",
        }

    except Exception as exc:
        logger.exception("health_check failed: %s", str(exc))

        # Return unhealthy status but don't retry for health checks
        return {
            "timestamp": timestamp,
            "status": "unhealthy",
            "error": str(exc),
        }


# Minimal beat schedule
celery_app.conf.beat_schedule = {
    "cleanup-old-jobs": {
        "task": "app.tasks.conversion_tasks.cleanup_old_jobs",
        "schedule": 3600.0,
        "args": (7,),
    },
    "get-queue-stats": {
        "task": "app.tasks.conversion_tasks.get_queue_stats",
        "schedule": 600.0,
    },
    "health-check": {
        "task": "app.tasks.conversion_tasks.health_check",
        "schedule": 300.0,
    },
}
