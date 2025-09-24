#!/bin/bash

# 테스트 실행 스크립트

set -e

echo "=== PDF to EPUB 변환기 테스트 실행 ==="

# 환경 변수 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export PYTHONUNBUFFERED=1

# 테스트 디렉토리
TEST_DIR="tests"

# 결과 디렉토리 생성
mkdir -p test_results

# 기본 테스트 실행
echo "1. 기본 테스트 실행..."
python -m pytest \
    --verbose \
    --tb=short \
    --cov=app \
    --cov-report=html:test_results/coverage_html \
    --cov-report=xml:test_results/coverage.xml \
    --junitxml=test_results/junit.xml \
    --asyncio-mode=auto \
    $TEST_DIR/

# 특정 테스트 그룹 실행
echo -e "\n2. 비동기 작업 큐 서비스 테스트 실행..."
python -m pytest \
    $TEST_DIR/test_async_queue_service.py \
    -v \
    --cov=app.services.async_queue_service \
    --cov-report=term-missing

echo -e "\n3. Celery 작업 테스트 실행..."
python -m pytest \
    $TEST_DIR/test_celery_tasks.py \
    -v \
    --cov=app.tasks.conversion_tasks \
    --cov-report=term-missing

echo -e "\n4. 통합 테스트 실행..."
python -m pytest \
    $TEST_DIR/test_integration.py \
    -v \
    --cov=app.api.v1.conversion \
    --cov-report=term-missing

# 성능 테스트 (선택 사항)
if [ "$1" == "--performance" ]; then
    echo -e "\n5. 성능 테스트 실행..."
    python -m pytest \
        $TEST_DIR/test_performance.py \
        -v \
        --benchmark-only \
        --benchmark-sort=mean
fi

# 타입 검사
echo -e "\n6. 타입 검사 실행..."
python -m mypy app/ --ignore-missing-imports || true

# 린팅 검사
echo -e "\n7. 린팅 검사 실행..."
flake8 app/ tests/ --statistics --show-source || true

# 보안 검사
echo -e "\n8. 보안 검사 실행..."
bandit -r app/ || true

# 테스트 결과 요약
echo -e "\n=== 테스트 결과 요약 ==="
if [ -f "test_results/junit.xml" ]; then
    echo "JUnit XML 결과: test_results/junit.xml"
fi

if [ -d "test_results/coverage_html" ]; then
    echo "커버리지 보고서: test_results/coverage_html/index.html"
fi

echo -e "\n테스트가 완료되었습니다."