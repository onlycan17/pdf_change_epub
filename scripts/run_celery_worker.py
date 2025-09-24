#!/usr/bin/env python3
"""Celery Worker 실행 스크립트"""

import os
import sys
import logging

# Python 경로 설정
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Celery Worker 실행"""
    try:
        # Celery 앱 가져오기
        from app.celery_config import celery_app
        
        # Worker 실행
        logger.info("Starting Celery Worker...")
        celery_app.start([
            'worker',
            '--loglevel=info',
            '--concurrency=4',
            '--hostname=worker@%h'
        ])
        
    except Exception as e:
        logger.error(f"Failed to start Celery Worker: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()