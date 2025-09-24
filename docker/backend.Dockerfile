# 다단계 빌드를 위한 Dockerfile
FROM python:3.10-slim as builder

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# 최종 실행 이미지
FROM python:3.10-slim

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH"

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    libpq5 \
    libffi8 \
    libssl3 \
    libxml2 \
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# 빌더 단계에서 패키지 복사
COPY --from=builder /root/.local /root/.local

# 애플리케이션 코드 복사
WORKDIR /app
COPY . .

# 데이터베이스 마이그레이션 (선택 사항)
# RUN alembic upgrade head

# Python 경로 설정
ENV PYTHONPATH=/app

# 실행 스크립트 생성
RUN echo '#!/bin/bash' > /app/start_worker.sh && \
    echo 'cd /app' >> /app/start_worker.sh && \
    echo 'export PYTHONPATH=/app' >> /app/start_worker.sh && \
    echo 'exec celery -A app.celery_config:celery_app worker --loglevel=info --concurrency=4' >> /app/start_worker.sh && \
    chmod +x /app/start_worker.sh

RUN echo '#!/bin/bash' > /app/start_app.sh && \
    echo 'cd /app' >> /app/start_app.sh && \
    echo 'export PYTHONPATH=/app' >> /app/start_app.sh && \
    echo 'exec uvicorn app.main:app --host 0.0.0.0 --port 8000' >> /app/start_app.sh && \
    chmod +x /app/start_app.sh

RUN echo '#!/bin/bash' > /app/start_beat.sh && \
    echo 'cd /app' >> /app/start_beat.sh && \
    echo 'export PYTHONPATH=/app' >> /app/start_beat.sh && \
    echo 'exec celery -A app.celery_config:celery_app beat --loglevel=info --scheduler=django_celery_beat.schedulers:DatabaseScheduler' >> /app/start_beat.sh && \
    chmod +x /app/start_beat.sh

RUN echo '#!/bin/bash' > /app/start_flower.sh && \
    echo 'cd /app' >> /app/start_flower.sh && \
    echo 'export PYTHONPATH=/app' >> /app/start_flower.sh && \
    echo 'exec celery -A app.celery_config:celery_app flower --port=5555' >> /app/start_flower.sh && \
    chmod +x /app/start_flower.sh

# 애플리케이션 실행
EXPOSE 8000 5555

# 기본 실행 명령어
CMD ["bash", "/app/start_app.sh"]