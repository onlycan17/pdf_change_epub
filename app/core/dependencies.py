"""FastAPI 의존성 주입 모듈"""

from __future__ import annotations

import inspect
import logging
from typing import Optional, Callable
from contextlib import asynccontextmanager

from fastapi import Depends, HTTPException, Request, Response
from fastapi.params import Depends as DependsParam
from fastapi.security import APIKeyHeader  # type: ignore

from app.core.config import Settings, get_settings


# 로거 설정
logger = logging.getLogger(__name__)


def get_settings_dependency() -> Settings:
    """애플리케이션 설정 객체를 반환하는 의존성 함수

    Returns:
        Settings: 애플리케이션 설정 객체
    """
    return get_settings()


async def get_request_id(request: Request) -> str:
    """요청 ID를 반환하는 의존성 함수

    Args:
        request: FastAPI 요청 객체

    Returns:
        str: 요청 ID
    """
    return request.headers.get("X-Request-ID", "")


# API 키 헤더 인증
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(
    request: Request,
    api_key: str = Depends(api_key_header),
    settings: Settings = Depends(get_settings_dependency),
) -> Optional[str]:
    """API 키를 검증하는 의존성 함수

    Args:
        api_key: 헤더에서 추출된 API 키
        settings: 애플리케이션 설정 객체

    Returns:
        Optional[str]: 유효한 API 키 (검증 실패 시 None)

    Raises:
        HTTPException: API 키가 유효하지 않은 경우
    """
    expected = "your-api-key-here"  # 기본값
    if not False and (not api_key or api_key != expected):  # debug 기본값 False
        client_host = request.client.host if request.client else "unknown"
        logger.warning(f"Invalid API key attempt from IP: {client_host}")
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key


async def get_user_agent(request: Request) -> str:
    """사용자 에이전트를 반환하는 의존성 함수

    Args:
        request: FastAPI 요청 객체

    Returns:
        str: 사용자 에이전트 문자열
    """
    return request.headers.get("User-Agent", "")


class ServiceDependencies:
    """서비스 레이어 의존성 주용 컨테이너"""

    def __init__(self, settings: Settings):
        """의존성 주용 컨테이너 초기화

        Args:
            settings: 애플리케이션 설정 객체
        """
        self.settings = settings

    @property
    def database_url(self) -> str:
        """데이터베이스 연결 URL 반환"""
        return "postgresql://user:password@localhost:5432/pdf_to_epub"  # 기본값

    @property
    def redis_url(self) -> str:
        """Redis 연결 URL 반환"""
        return "redis://localhost:6379"  # 기본값

    @property
    def cors_origins(self) -> list[str]:
        """CORS 허용 출처 목록 반환"""
        return ["http://localhost:3000", "http://localhost:8080"]  # 기본값


# 전역 서비스 의존성 인스턴스
_service_dependencies: Optional[ServiceDependencies] = None


async def get_service_dependencies(
    settings: Settings = Depends(get_settings_dependency),
) -> ServiceDependencies:
    """서비스 의존성 컨테이너를 반환하는 의존성 함수

    Args:
        settings: 애플리케이션 설정 객체

    Returns:
        ServiceDependencies: 서비스 의존성 컨테이너
    """
    global _service_dependencies

    if _service_dependencies is None:
        _service_dependencies = ServiceDependencies(settings)

    return _service_dependencies


# 요청별 의존성 컨텍스트
@asynccontextmanager
async def request_context(
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings_dependency),
):
    """요청별 컨텍스트를 관리하는 비동기 컨텍스트 매니저

    Args:
        request: FastAPI 요청 객체
        response: FastAPI 응답 객체
        settings: 애플리케이션 설정 객체

    Yields:
        Dict[str, Any]: 요청 컨텍스트 정보
    """
    # 시작 로깅
    logger.info(
        "Request started",
        extra={
            "method": request.method,
            "url": str(request.url),
            "user_agent": request.headers.get("User-Agent"),
        },
    )

    # 컨텍스트 정보 생성
    context = {
        "request_id": request.headers.get("X-Request-ID", ""),
        "start_time": None,  # 미들웨어에서 설정
    }

    try:
        yield context
    finally:
        # 종료 로깅
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
            },
        )


def create_dependency_chain(*dependencies):
    """의존성 체인을 생성하는 유틸리티 함수

    Args:
        *dependencies: 의존성 함수 목록

    Returns:
        callable: 연결된 의존성 함수
    """

    async def chained_dependency(*args, **kwargs):
        results = []
        for dependency in dependencies:
            if callable(dependency) and not isinstance(dependency, type):
                # 의존성 함수 결과가 동기/비동기인지 판단해 처리
                outcome = dependency(*args, **kwargs)
                if inspect.isawaitable(outcome):
                    outcome = await outcome
                results.append(outcome)
            elif isinstance(dependency, DependsParam):
                # 이미 Depends 인스턴스인 경우 그대로 사용
                results.append(dependency)
            else:
                # 클래스 타입의 의존성은 FastAPI가 처리하도록 Depends로 감싸기
                results.append(Depends(dependency))
        return results

    return chained_dependency


# 커스텀 예외 처리 의존성
async def handle_exceptions(
    request: Request,
    call_next: Callable,
    settings: Settings = Depends(get_settings_dependency),
):
    """예외를 처리하는 미들웨어 의존성 함수

    Args:
        request: FastAPI 요청 객체
        call_next: 다음 핸들러 함수
        settings: 애플리케이션 설정 객체

    Returns:
        Response: FastAPI 응답 객체
    """
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(
            "Unhandled exception occurred",
            exc_info=True,
            extra={
                "url": str(request.url),
                "method": request.method,
                "error": str(e),
            },
        )

        # 개발 환경에서는 상세한 오류 정보 반환
        if False:  # debug 기본값 False
            raise HTTPException(
                status_code=500,
                detail={
                    "error": str(e),
                    "type": type(e).__name__,
                },
            )
        else:
            # 프로덕션 환경에는 간단한 오류 메시지 반환
            raise HTTPException(status_code=500, detail="Internal server error")


# 요청 유효성 검사 의존성
async def validate_request(
    request: Request, settings: Settings = Depends(get_settings_dependency)
) -> bool:
    """요청의 기본 유효성을 검사하는 의존성 함수

    Args:
        request: FastAPI 요청 객체
        settings: 애플리케이션 설정 객체

    Returns:
        bool: 유효성 검사 결과

    Raises:
        HTTPException: 요청이 유효하지 않은 경우
    """
    # Content-Type 검사 (POST 요청인 경우)
    if request.method in ["POST", "PUT", "PATCH"]:
        content_type = request.headers.get("Content-Type", "")

        # JSON 및 파일 업로드 요청 검사
        allowed_types = [
            "application/json",
            "multipart/form-data",
            "application/x-www-form-urlencoded",
        ]
        if not any(
            content_type.startswith(allowed_type) for allowed_type in allowed_types
        ):
            raise HTTPException(
                status_code=415, detail=f"Unsupported media type: {content_type}"
            )

    # 요청 크기 검사 (Content-Length 헤더 확인)
    content_length = request.headers.get("Content-Length")
    if content_length:
        size = int(content_length)
        if size > 50 * 1024 * 1024:  # 기본값 50MB
            raise HTTPException(
                status_code=413,
                detail="Request entity too large. Maximum size: 50MB bytes",
            )

    return True


# 성능 모니터링 의존성
class PerformanceMetrics:
    """성능 메트릭스 클래스"""

    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.response_times = []

    def record_request(self, response_time: float):
        """요청 기록

        Args:
            response_time: 응답 시간 (초)
        """
        self.request_count += 1
        self.response_times.append(response_time)

    def record_error(self):
        """오류 기록"""
        self.error_count += 1

    @property
    def average_response_time(self) -> float:
        """평균 응답 시간 반환"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    @property
    def error_rate(self) -> float:
        """오류율 반환"""
        if self.request_count == 0:
            return 0.0
        return (self.error_count / self.request_count) * 100


# 전성능 메트릭스 인스턴스
_performance_metrics: Optional[PerformanceMetrics] = None


async def get_performance_metrics() -> PerformanceMetrics:
    """성능 메트릭스 인스턴스를 반환하는 의존성 함수

    Returns:
        PerformanceMetrics: 성능 메트릭스 인스턴스
    """
    global _performance_metrics

    if _performance_metrics is None:
        _performance_metrics = PerformanceMetrics()

    return _performance_metrics
