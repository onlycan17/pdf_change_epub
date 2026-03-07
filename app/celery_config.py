"""Celery 설정 및 초기화 모듈"""

import os

from celery import Celery


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _get_broker_url() -> str:
    return (
        os.getenv("CELERY_BROKER_URL")
        or os.getenv("APP_CELERY_BROKER_URL")
        or os.getenv("REDIS_URL")
        or "redis://localhost:6379/0"
    )


def _get_result_backend() -> str:
    return (
        os.getenv("CELERY_RESULT_BACKEND")
        or os.getenv("CELERY_BACKEND_URL")
        or os.getenv("APP_CELERY_RESULT_BACKEND")
        or os.getenv("REDIS_URL")
        or "redis://localhost:6379/0"
    )


def _get_visibility_timeout_seconds() -> int:
    return _env_int("APP_CELERY_VISIBILITY_TIMEOUT_SECONDS", 7 * 24 * 60 * 60)


def _get_visibility_transport_options() -> dict[str, int]:
    return {"visibility_timeout": _get_visibility_timeout_seconds()}


# Celery 앱 생성
celery_app = Celery(
    "pdf_to_epub",
    broker=_get_broker_url(),
    backend=_get_result_backend(),
    include=["app.tasks.conversion_tasks"],
)

# Celery 설정
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_track_started=True,
    broker_transport_options=_get_visibility_transport_options(),
    result_backend_transport_options=_get_visibility_transport_options(),
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=3600,
    beat_schedule={
        "cleanup-old-tasks": {
            "task": "app.tasks.conversion_tasks.cleanup_old_tasks",
            "schedule": 300.0,
        },
    },
)
