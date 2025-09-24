#!/bin/bash
# Start Celery worker
cd /app
export PYTHONPATH=/app
exec celery -A app.celery_config:celery_app worker --loglevel=info --concurrency=4
