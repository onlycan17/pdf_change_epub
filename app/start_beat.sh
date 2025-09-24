#!/bin/bash
# Start Celery beat
cd /app
export PYTHONPATH=/app
exec celery -A app.celery_config:celery_app beat --loglevel=info
