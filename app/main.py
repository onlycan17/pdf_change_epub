"""PDF to EPUB 변환기 FastAPI 애플리케이션"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
import socket

from fastapi import FastAPI, Request, Response

from app.core.config import get_settings
from app.core.dependencies import (
    handle_exceptions,
    request_context,
    validate_request,
    get_service_dependencies,
)
from app.core.logging_config import setup_logging, configure_debug_logging
from app.api.v1 import auth, conversion


# 로깅 설정 초기화
def setup_app_logging():
    """애플리케이션 로깅 설정 초기화"""
    settings = get_settings()

    # 커스텀 로깅 설정 적용
    setup_logging(
        settings=settings,
        log_level=getattr(settings, "log_level", "INFO"),
        json_logs=not settings.debug,  # 개발 환경에서는 상세 로그
    )

    # 디버그 모드인 경우 추가 설정 적용
    if settings.debug:
        configure_debug_logging()

    # 애플리케이션 로거 생성
    logger = logging.getLogger(__name__)

    # 성능 모니터링 로거 설정
    from app.core.logging_config import setup_performance_logging

    setup_performance_logging()

    return logger


# 로깅 설정 적용 및 로거 생성
logger = setup_app_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리 미들웨어

    Args:
        app: FastAPI 애플리케이션 인스턴스

    Yields:
        None: 애플리케이션 시작/종료 이벤트
    """
    # 애플리케이션 시작 시 실행될 작업
    settings = get_settings()

    # 시작 로깅 (구조화된 로거 사용)
    from app.core.logging_config import get_logger

    app_logger = get_logger("app.lifespan")

    app_logger.info(
        "Application starting",
        service_name=settings.app_name,
        version=settings.version,
        environment="development" if settings.debug else "production",
    )

    # 서비스 의존성 초기화
    await get_service_dependencies(settings)

    yield

    # 애플리케이션 종료 시 실행될 작업
    app_logger.info(
        "Application shutting down",
        service_name=settings.app_name,
        version=settings.version,
    )


# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title="PDF to EPUB Converter API",
    description="PDF 문서를 EPUB 전자책으로 변환하는 RESTful API 서비스",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# CORS 미들웨어 등록
@app.middleware("http")
async def add_cors_middleware(request: Request, call_next):
    """CORS 미들웨어

    Args:
        request: FastAPI 요청 객체
        call_next: 다음 핸들러 함수

    Returns:
        Response: FastAPI 응답 객체
    """
    settings = get_settings()

    response = await call_next(request)

    # CORS 헤더 추가
    response.headers["Access-Control-Allow-Origin"] = ", ".join(settings.cors_origins)
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = (
        "Content-Type, Authorization, X-API-Key, X-Request-ID"
    )

    return response


# 예외 처리 미들웨어 등록
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 핸들러

    Args:
        request: FastAPI 요청 객체
        exc: 발생한 예외

    Returns:
        Response: 오류 응답 객체
    """
    return await handle_exceptions(request, lambda r: None, get_settings())


# 요청 처리 미들웨어 체인
@app.middleware("http")
async def process_request(request: Request, call_next):
    """요청 처리 파이프라인

    Args:
        request: FastAPI 요청 객체
        call_next: 다음 핸들러 함수

    Returns:
        Response: FastAPI 응답 객체
    """
    # 요청 유효성 검사
    await validate_request(request, get_settings())

    # 요청 컨텍스트 생성
    async with request_context(request, Response(), get_settings()):
        # 다음 핸들러 호출
        response = await call_next(request)

        return response


# 라우트 등록 (v1 API)
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])

app.include_router(conversion.router, prefix="/api/v1/conversion", tags=["Conversion"])


# 헬스체크 엔드포인트
@app.get("/health", tags=["Health"])
async def health_check():
    """애플리케이션 상태 확인 엔드포인트

    Returns:
        dict: 애플리케이션 상태 정보
    """
    settings = get_settings()

    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.version,
        "timestamp": "2024-09-18T11:30:00Z",
    }


# 루트 엔드포인트
@app.get("/", tags=["Root"])
async def root():
    """루트 엔드포인트

    Returns:
        dict: 애플리케이션 정보
    """
    settings = get_settings()

    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.version,
        "docs_url": "/docs",
    }


# 애플리케이션 실행 함수
def run() -> None:
    """개발 서버 실행용 스크립트 함수"""
    import uvicorn

    settings = get_settings()

    # 포트 점유 시 자동으로 사용 가능한 포트로 대체
    def _is_port_in_use(host: str, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, port))
                return False
            except OSError:
                return True

    def _find_free_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    host = settings.host
    port = settings.port
    if _is_port_in_use(host, port):
        logger.info("Port %s is in use. Selecting a free port automatically.", port)
        port = _find_free_port()

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
    )


if __name__ == "__main__":
    run()
