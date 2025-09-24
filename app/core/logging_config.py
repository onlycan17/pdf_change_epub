"""로깅 설정 모듈"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime
from typing import Optional

from app.core.config import Settings


def setup_logging(
    settings: Settings,
    log_level: str = "INFO",
    log_format: Optional[str] = None,
    json_logs: bool = False,
) -> logging.Logger:
    """로깅 설정을 초기화하고 로거를 반환합니다.

    Args:
        settings: 애플리케이션 설정
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: 커스텀 로그 포맷 (None인 경우 기본값 사용)
        json_logs: JSON 형식의 로그를 사용할지 여부

    Returns:
        logging.Logger: 설정된 루트 로거
    """

    # 레벨 설정
    level = getattr(logging, log_level.upper(), logging.INFO)

    # 포맷 설정
    if json_logs:
        # JSON 형식의 로그 (프로덕션 환경 권장)
        formatter = logging.Formatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    elif log_format:
        # 커스텀 포맷
        formatter = logging.Formatter(log_format)
    else:
        # 기본 포맷 (개발 환경용 상세 정보)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # 핸들러 설정
    handlers: list[logging.Handler] = []

    # 콘솔 핸들러 (항상 추가)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    # 파일 핸들러 (개발 환경이거나 설정에 따라)
    if False:  # debug 기본값 False
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # 일반 로그 파일
        log_file = logs_dir / "app.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

        # 에러 전용 로그 파일
        error_log_file = logs_dir / "error.log"
        error_handler = logging.FileHandler(error_log_file, encoding="utf-8")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        handlers.append(error_handler)

    # 로거 설정
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.handlers.clear()  # 기존 핸들러 제거

    for handler in handlers:
        logger.addHandler(handler)

    return logger


class StructuredLogger:
    """구조화된 로깅을 위한 커스텀 로거"""

    def __init__(self, name: str):
        """커스텀 로거 초기화

        Args:
            name: 로거 이름
        """
        self.logger = logging.getLogger(name)

    def debug(self, message: str, **kwargs):
        """디버그 로깅"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """정보 로깅"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """경고 로깅"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """오류 로깅"""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """크리티컬 로깅"""
        self._log(logging.CRITICAL, message, **kwargs)

    def _log(self, level: int, message: str, **kwargs):
        """내부 로깅 메서드

        Args:
            level: 로그 레벨
            message: 로그 메시지
            **kwargs: 추가 컨텍스트 정보
        """
        # 기본 컨텍스트 생성
        context: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "logger_name": self.logger.name,
        }

        # 추가 컨텍스트 병합
        if kwargs:
            context.update(kwargs)

        # 개발 환경에서는 상세 정보 출력
        if self.logger.isEnabledFor(logging.DEBUG):
            context["debug_context"] = {
                "thread": getattr(self.logger, "_thread_name", "unknown"),
                "module": getattr(self.logger, "_module", "unknown"),
            }

        # 메시지와 컨텍스트 결합
        if context:
            log_message = (
                f"{message} | Context: {json.dumps(context, ensure_ascii=False)}"
            )
        else:
            log_message = message

        self.logger.log(level, log_message)

    def log_request(self, method: str, url: str, **kwargs):
        """HTTP 요청 로깅

        Args:
            method: HTTP 메서드
            url: URL
            **kwargs: 추가 컨텍스트 정보 (user_agent, ip 등)
        """
        self.info("HTTP Request", method=method, url=url, **kwargs)

    def log_response(self, method: str, url: str, status_code: int, **kwargs):
        """HTTP 응답 로깅

        Args:
            method: HTTP 메서드
            url: URL
            status_code: 상태 코드
            **kwargs: 추가 컨텍스트 정보 (response_time 등)
        """
        self.info(
            "HTTP Response", method=method, url=url, status_code=status_code, **kwargs
        )

    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """에러 로깅

        Args:
            error: 발생한 예외
            context: 추가 컨텍스트 정보
        """
        if context is None:
            context = {}

        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
        }

        error_context.update(context)

        self.error("Application Error Occurred", **error_context)


def get_logger(name: str) -> StructuredLogger:
    """구조화된 로거를 반환합니다.

    Args:
        name: 로거 이름

    Returns:
        StructuredLogger: 구조화된 커스텀 로거
    """
    return StructuredLogger(name)


def configure_debug_logging():
    """디버그 모드를 위한 고급 로깅 설정"""

    # 루트 로거에 디버그 핸들러 추가
    logger = logging.getLogger()

    # 콘솔용 포맷터 (상세 정보)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)8s - [%(filename)s:%(lineno)-3d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.DEBUG)  # 디버그 모드에서는 전체 레벨 출력

    logger.addHandler(console_handler)

    # 특정 모듈의 로그 레벨 조절
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.WARNING)

    return logger


def setup_performance_logging():
    """성능 모니터링을 위한 로깅 설정"""

    # 성능 관련 로거
    perf_logger = logging.getLogger("performance")
    perf_logger.setLevel(logging.INFO)

    # 성능 로그 포맷
    perf_formatter = logging.Formatter(
        "PERF | %(asctime)s | %(message)s", datefmt="%H:%M:%S"
    )

    # 콘솔 핸들러
    perf_handler = logging.StreamHandler(sys.stdout)
    perf_handler.setFormatter(perf_formatter)

    # 중복 핸들러 방지
    if not any(isinstance(h, logging.StreamHandler) for h in perf_logger.handlers):
        perf_logger.addHandler(perf_handler)

    return perf_logger
