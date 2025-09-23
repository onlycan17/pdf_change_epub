"""애플리케이션 설정 관리 모듈"""

from __future__ import annotations

import os
from typing import List, Optional
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class DatabaseSettings(BaseSettings):
    """데이터베이스 설정"""

    model_config = SettingsConfigDict(env_prefix="DB_", env_file_encoding="utf-8")

    url: str = Field(
        default="sqlite:///./pdf_to_epub.db", description="데이터베이스 연결 URL"
    )
    pool_size: int = Field(default=20, description="데이터베이스 커넥션 풀 크기")
    max_overflow: int = Field(default=30, description="최대 오버플로 커넥션 수")


class RedisSettings(BaseSettings):
    """Redis 캐시 설정"""

    model_config = SettingsConfigDict(env_prefix="REDIS_", env_file_encoding="utf-8")

    host: str = Field(default="localhost", description="Redis 호스트 주소")
    port: int = Field(default=6379, description="Redis 포트 번호")
    password: Optional[str] = Field(default=None, description="Redis 비밀번호")
    db: int = Field(default=0, description="Redis 데이터베이스 번호")

    @property
    def url(self) -> str:
        """Redis 연결 URL 생성"""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class OCRSettings(BaseSettings):
    """OCR 처리 설정"""

    model_config = SettingsConfigDict(env_prefix="OCR_", env_file_encoding="utf-8")

    enabled: bool = Field(default=True, description="OCR 기능 활성화 여부")
    language: str = Field(default="ko", description="OCR 기본 언어 (ko, en)")
    paddle_ocr_model: str = Field(default="korean", description="Paddle OCR 모델 종류")
    max_workers: int = Field(default=4, description="OCR 처리 최대 워커 수")


class LLMSettings(BaseSettings):
    """LLM (Large Language Model) 설정"""

    model_config = SettingsConfigDict(
        env_prefix="LLM_", env_file_encoding="utf-8", protected_namespaces=()
    )

    provider: str = Field(default="openrouter", description="LLM 제공업체")
    model_name: str = Field(
        default="deepseek/deepseek-chat", description="사용할 LLM 모델"
    )
    api_key: str = Field(default="", description="LLM API 키")
    base_url: Optional[str] = Field(
        default=None, description="API 기본 URL (커스텀 엔드포인트)"
    )
    max_tokens: int = Field(default=4000, description="최대 토큰 수")
    temperature: float = Field(default=0.1, description="생성 온도 (0-1)")
    timeout: int = Field(default=60, description="요청 타임아웃 (초)")


class SecuritySettings(BaseSettings):
    """보안 관련 설정 (JWT/API Key)"""

    model_config = SettingsConfigDict(env_prefix="SECURITY_", env_file_encoding="utf-8")

    jwt_secret: str = Field(
        default="change-me",
        description="JWT 서명용 시크릿 키 (운영환경에서 반드시 환경변수로 설정)",
    )
    api_key: str = Field(
        default="your-api-key-here",
        description="간단한 API 키 인증용 키 (개발 기본값)",
    )


class ConversionSettings(BaseSettings):
    """변환 처리 설정"""

    model_config = SettingsConfigDict(
        env_prefix="CONVERSION_", env_file_encoding="utf-8"
    )

    max_file_size: int = Field(
        default=50 * 1024 * 1024, description="최대 파일 크기 (바이트)"
    )
    supported_formats: List[str] = Field(
        default=["pdf"], description="지원하는 파일 형식 목록"
    )
    output_format: str = Field(default="epub3", description="출력 형식")
    chunk_size: int = Field(default=1000, description="텍스트 처리 청크 크기")
    cleanup_temp_files: bool = Field(
        default=True, description="임시 파일 자동 삭제 여부"
    )


class Settings(BaseSettings):
    """애플리케이션 전체 설정"""

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8", case_sensitive=False  # 환경 변수명 대소문자 무시
    )

    # 기본 설정
    app_name: str = Field(
        default="PDF to EPUB Converter", description="애플리케이션 이름"
    )
    version: str = Field(default="1.0.0", description="애플리케이션 버전")
    debug: bool = Field(default=False, description="디버그 모드 활성화 여부")
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 접두사")

    # 서비스 설정
    host: str = Field(default="0.0.0.0", description="서버 호스트 주소")
    port: int = Field(default=8000, description="서버 포트 번호")

    # 하위 설정 그룹
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    ocr: OCRSettings = Field(default_factory=OCRSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    conversion: ConversionSettings = Field(default_factory=ConversionSettings)

    # DEBUG 환경변수가 문자열로 들어오더라도 안전하게 처리
    @field_validator("debug", mode="before")
    @classmethod
    def coerce_debug(cls, v):  # type: ignore[no-untyped-def]
        """DEBUG 값이 'WARN' 같은 비표준 문자열이어도 예외 없이 False로 처리

        - 허용 true 값: 1, true, yes, on
        - 허용 false 값: 0, false, no, off
        - 그 외 값: False
        """
        if isinstance(v, bool) or v is None:
            return v or False
        if isinstance(v, str):
            s = v.strip().lower()
            if s in {"1", "true", "yes", "on"}:
                return True
            if s in {"0", "false", "no", "off"}:
                return False
            # 비표준 값은 False로 강제
            return False
        try:
            return bool(v)
        except Exception:
            return False

    @property
    def postgresql_url(self) -> str:
        """PostgreSQL 연결 URL 생성"""
        if self.database.url.startswith("postgresql://"):
            return self.database.url
        # 기본이 SQLite이므로 PostgreSQL URL이 아닌 경우 그대로 반환
        return self.database.url

    @property
    def cors_origins(self) -> List[str]:
        """CORS 허용 출처 목록"""
        origins = [
            "http://localhost:3000",  # 로컬 개발 서버
            "http://127.0.0.1:3000",
        ]

        # 환경 변수에서 추가된 출처 포함
        additional_hosts = os.getenv("ALLOWED_HOSTS")
        if additional_hosts:
            additional_origins = additional_hosts.split(",")
            origins.extend([origin.strip() for origin in additional_origins])

        return origins


@lru_cache
def get_settings() -> Settings:
    """캐시된 설정 객체 반환

    Returns:
        Settings: 애플리케이션 설정 객체
    """
    return Settings()
