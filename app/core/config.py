import os
from typing import Optional, List
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """데이터베이스 설정"""

    url: str = "sqlite:///./pdf_to_epub.db"
    pool_size: int = 20
    max_overflow: int = 30

    class Config:
        env_prefix = "DB_"


class RedisSettings(BaseSettings):
    """Redis 설정"""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None

    @property
    def url(self) -> str:
        """Redis URL 생성"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"

    class Config:
        env_prefix = "REDIS_"


class OCRSettings(BaseSettings):
    """OCR 설정"""

    enabled: bool = True
    language: str = "ko"
    paddle_ocr_model: str = "korean"
    max_workers: int = 4

    class Config:
        env_prefix = "OCR_"


class LLMSettings(BaseSettings):
    """LLM 설정"""

    provider: str = "openrouter"
    model_name: str = "deepseek/deepseek-chat"
    api_key: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.1

    class Config:
        env_prefix = "LLM_"
        protected_namespaces = ()


class ConversionSettings(BaseSettings):
    """변환 설정"""

    max_file_size: int = 50 * 1024 * 1024
    supported_formats: List[str] = ["pdf"]
    output_format: str = "epub3"
    chunk_size: int = 1000
    cleanup_temp_files: bool = True

    class Config:
        env_prefix = "CONVERSION_"


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 기본 설정
    app_name: str = "PDF to EPUB Converter"
    version: str = "1.0.0"
    api_v1_str: str = "/api/v1"

    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8000

    # 중첩된 설정
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    ocr: OCRSettings = OCRSettings()
    llm: LLMSettings = LLMSettings()
    conversion: ConversionSettings = ConversionSettings()

    # 파일 저장소 설정
    upload_dir: str = "./uploads"
    temp_dir: str = "./temp"
    result_dir: str = "./results"

    # Celery 설정
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # 보안 설정
    secret_key: str = "your-secret-key-here"
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"

    # 파일 처리 설정
    max_file_size_mb: int = 100
    allowed_file_types: list = ["pdf"]

    # OCR 설정
    ocr_enabled: bool = True
    ocr_language: str = "kor+eng"
    ocr_confidence_threshold: float = 0.8

    # 변환 설정
    conversion_timeout_seconds: int = 3600
    conversion_max_retries: int = 3
    conversion_retry_delay: int = 60

    # 로깅 설정
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"

    # 모니터링 설정
    enable_metrics: bool = True
    metrics_port: int = 8090

    # Supabase 설정
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None

    # AI 서비스 설정
    openai_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None

    # 외부 서비스 설정
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None

    # 캐시 설정
    cache_ttl: int = 3600
    cache_prefix: str = "pdf_epub_"

    # 보안 설정
    cors_origins: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
    ]
    csrf_protection: bool = True

    # 배치 처리 설정
    batch_size: int = 10
    worker_concurrency: int = 4

    # 클린업 설정
    cleanup_interval_hours: int = 24
    temp_file_retention_hours: int = 12
    result_file_retention_days: int = 7

    # debug 속성은 __init__에서만 처리
    debug: bool = False

    class Config:
        case_sensitive = True
        env_prefix = "APP_"
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 환경 변수에서 값 읽기
        self.app_name = os.getenv("APP_NAME", self.app_name)
        self.debug = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")
        self.host = os.getenv("APP_HOST", self.host)
        self.port = int(os.getenv("APP_PORT", str(self.port)))

        # 중첩된 설정 업데이트
        self.database = DatabaseSettings()
        self.redis = RedisSettings()
        self.ocr = OCRSettings()
        self.llm = LLMSettings()
        self.conversion = ConversionSettings()

        # CORS 출처 업데이트
        allowed_hosts = os.getenv("ALLOWED_HOSTS")
        if allowed_hosts:
            additional_origins = [host.strip() for host in allowed_hosts.split(",")]
            self.cors_origins = [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:8080",
            ] + additional_origins

    # 대문자 속성 접근을 위한 프로퍼티
    @property
    def APP_NAME(self) -> str:
        return self.app_name

    @property
    def APP_VERSION(self) -> str:
        return self.version

    @property
    def DEBUG(self) -> bool:
        return self.debug

    @property
    def API_V1_STR(self) -> str:
        return self.api_v1_str

    @property
    def HOST(self) -> str:
        return self.host

    @property
    def PORT(self) -> int:
        return self.port

    @property
    def UPLOAD_DIR(self) -> str:
        return self.upload_dir

    @property
    def TEMP_DIR(self) -> str:
        return self.temp_dir

    @property
    def RESULT_DIR(self) -> str:
        return self.result_dir

    @property
    def CELERY_BROKER_URL(self) -> str:
        return self.celery_broker_url

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return self.celery_result_backend

    @property
    def SECRET_KEY(self) -> str:
        return self.secret_key

    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return self.access_token_expire_minutes

    @property
    def ALGORITHM(self) -> str:
        return self.algorithm

    @property
    def MAX_FILE_SIZE_MB(self) -> int:
        return self.max_file_size_mb

    @property
    def ALLOWED_FILE_TYPES(self) -> list:
        return self.allowed_file_types

    @property
    def OCR_ENABLED(self) -> bool:
        return self.ocr_enabled

    @property
    def OCR_LANGUAGE(self) -> str:
        return self.ocr_language

    @property
    def OCR_CONFIDENCE_THRESHOLD(self) -> float:
        return self.ocr_confidence_threshold

    @property
    def CONVERSION_TIMEOUT_SECONDS(self) -> int:
        return self.conversion_timeout_seconds

    @property
    def CONVERSION_MAX_RETRIES(self) -> int:
        return self.conversion_max_retries

    @property
    def CONVERSION_RETRY_DELAY(self) -> int:
        return self.conversion_retry_delay

    @property
    def LOG_LEVEL(self) -> str:
        return self.log_level

    @property
    def LOG_FILE(self) -> str:
        return self.log_file

    @property
    def ENABLE_METRICS(self) -> bool:
        return self.enable_metrics

    @property
    def METRICS_PORT(self) -> int:
        return self.metrics_port

    @property
    def SUPABASE_URL(self) -> Optional[str]:
        return self.supabase_url

    @property
    def SUPABASE_KEY(self) -> Optional[str]:
        return self.supabase_key

    @property
    def OPENAI_API_KEY(self) -> Optional[str]:
        return self.openai_api_key

    @property
    def DEEPSEEK_API_KEY(self) -> Optional[str]:
        return self.deepseek_api_key

    @property
    def SMTP_HOST(self) -> Optional[str]:
        return self.smtp_host

    @property
    def SMTP_PORT(self) -> int:
        return self.smtp_port

    @property
    def SMTP_USERNAME(self) -> Optional[str]:
        return self.smtp_username

    @property
    def SMTP_PASSWORD(self) -> Optional[str]:
        return self.smtp_password

    @property
    def CACHE_TTL(self) -> int:
        return self.cache_ttl

    @property
    def CACHE_PREFIX(self) -> str:
        return self.cache_prefix

    @property
    def CORS_ORIGINS(self) -> list:
        return self.cors_origins

    @property
    def CSRF_PROTECTION(self) -> bool:
        return self.csrf_protection

    @property
    def BATCH_SIZE(self) -> int:
        return self.batch_size

    @property
    def WORKER_CONCURRENCY(self) -> int:
        return self.worker_concurrency

    @property
    def CLEANUP_INTERVAL_HOURS(self) -> int:
        return self.cleanup_interval_hours

    @property
    def TEMP_FILE_RETENTION_HOURS(self) -> int:
        return self.temp_file_retention_hours

    @property
    def RESULT_FILE_RETENTION_DAYS(self) -> int:
        return self.result_file_retention_days

    @property
    def is_production(self) -> bool:
        """프로덕션 환경 여부"""
        return not self.DEBUG and os.getenv("ENVIRONMENT") == "production"

    @property
    def is_development(self) -> bool:
        """개발 환경 여부"""
        return self.DEBUG or os.getenv("ENVIRONMENT") == "development"

    @property
    def is_testing(self) -> bool:
        """테스트 환경 여부"""
        return os.getenv("ENVIRONMENT") == "testing"


# 설정 인스턴스 생성
settings = Settings()


# 환경별 설정
class DevelopmentSettings(Settings):
    """개발 환경 설정"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.debug = True
        self.log_level = "DEBUG"


class ProductionSettings(Settings):
    """프로덕션 환경 설정"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.debug = False
        self.log_level = "INFO"


class TestingSettings(Settings):
    """테스트 환경 설정"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.debug = True
        self.log_level = "DEBUG"

        # 중첩된 설정 재정의
        self.database = DatabaseSettings(url="sqlite:///./test.db")
        self.redis = RedisSettings(db=3)
        self.conversion = ConversionSettings(
            max_file_size=10 * 1024 * 1024
        )  # 테스트용으로 작은 파일 크기


# 환경에 따른 설정 선택
_settings_cache = None


def get_settings() -> Settings:
    """환경에 따른 설정을 반환합니다."""
    global _settings_cache

    if _settings_cache is None:
        env = os.getenv("ENVIRONMENT", "development")

        if env == "production":
            _settings_cache = ProductionSettings()
        elif env == "testing":
            _settings_cache = TestingSettings()
        else:
            _settings_cache = DevelopmentSettings()

    return _settings_cache


# 현재 환경의 설정
current_settings = get_settings()
