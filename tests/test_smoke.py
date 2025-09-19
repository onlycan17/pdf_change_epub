"""최소 동작 검증을 위한 스모크 테스트(설명: 시스템이 기본적으로 동작하는지 빠르게 확인하는 검사)."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_app_creation() -> None:
    """FastAPI 애플리케이션 인스턴스가 정상적으로 생성되는지 확인합니다."""
    assert app is not None
    assert app.title == "PDF to EPUB Converter API"
    assert app.version == "1.0.0"


def test_health_endpoint() -> None:
    """헬스체크 엔드포인트가 정상적으로 응답하는지 확인합니다."""
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data


def test_root_endpoint() -> None:
    """루트 엔드포인트가 정상적으로 응답하는지 확인합니다."""
    client = TestClient(app)
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
