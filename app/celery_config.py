"""Celery 설정 및 초기화 모듈"""

import os
from celery import Celery

# 환경 변수에서 설정 가져오기
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Celery 앱 생성
celery_app = Celery(
    "pdf_to_epub",
    broker=REDIS_URL,
    backend=REDIS_URL,
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
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
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
