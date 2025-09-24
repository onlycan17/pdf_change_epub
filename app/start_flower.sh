#!/bin/bash
# Start Celery Flower
cd /app
export PYTHONPATH=/app
exec celery -A app.celery_config:celery_app flower --port=5555
