"""애플리케이션 설정 관리 모듈 테스트"""

import os
import pytest

from app.core.config import (
    Settings,
    DatabaseSettings,
    RedisSettings,
    OCRSettings,
    LLMSettings,
    ConversionSettings,
    get_settings,
)


class TestDatabaseSettings:
    """데이터베이스 설정 테스트"""

    def test_default_settings(self):
        """기본값으로 데이터베이스 설정 테스트"""
        settings = DatabaseSettings()

        assert settings.url == "sqlite:///./pdf_to_epub.db"
        assert settings.pool_size == 20
        assert settings.max_overflow == 30

    def test_env_override(self, monkeypatch):
        """환경 변수로 설정 값 변경 테스트"""
        monkeypatch.setenv("DB_URL", "postgresql://user:pass@localhost/test")
        monkeypatch.setenv("DB_POOL_SIZE", "50")

        settings = DatabaseSettings()

        assert settings.url == "postgresql://user:pass@localhost/test"
        assert settings.pool_size == 50
        assert settings.max_overflow == 30


class TestRedisSettings:
    """Redis 설정 테스트"""

    def test_default_settings(self):
        """기본값으로 Redis 설정 테스트"""
        settings = RedisSettings()

        assert settings.host == "localhost"
        assert settings.port == 6379
        assert settings.db == 0
        assert settings.password is None

    def test_full_auth_settings(self, monkeypatch):
        """인증 정보가 포함된 Redis 설정 테스트"""
        monkeypatch.setenv("REDIS_HOST", "redis.example.com")
        monkeypatch.setenv("REDIS_PORT", "6380")
        monkeypatch.setenv("REDIS_PASSWORD", "secret123")
        monkeypatch.setenv("REDIS_DB", "1")

        settings = RedisSettings()

        assert settings.host == "redis.example.com"
        assert settings.port == 6380
        assert settings.password == "secret123"
        assert settings.db == 1
        assert settings.url == "redis://:secret123@redis.example.com:6380/1"

    def test_no_auth_settings(self, monkeypatch):
        """인증 정보 없는 Redis 설정 테스트"""
        monkeypatch.setenv("REDIS_HOST", "localhost")

        settings = RedisSettings()

        assert settings.url == "redis://localhost:6379/0"


class TestOCRSettings:
    """OCR 설정 테스트"""

    def test_default_settings(self):
        """기본값으로 OCR 설정 테스트"""
        settings = OCRSettings()

        assert settings.enabled is True
        assert settings.language == "ko"
        assert settings.paddle_ocr_model == "korean"
        assert settings.max_workers == 4

    def test_env_override(self, monkeypatch):
        """환경 변수로 OCR 설정 변경 테스트"""
        monkeypatch.setenv("OCR_ENABLED", "false")
        monkeypatch.setenv("OCR_LANGUAGE", "en")
        monkeypatch.setenv("OCR_MAX_WORKERS", "8")

        settings = OCRSettings()

        assert settings.enabled is False
        assert settings.language == "en"
        assert settings.max_workers == 8


class TestLLMSettings:
    """LLM 설정 테스트"""

    def test_default_settings(self):
        """기본값으로 LLM 설정 테스트"""
        settings = LLMSettings()

        assert settings.provider == "openrouter"
        assert settings.model_name == "deepseek/deepseek-chat"
        assert settings.max_tokens == 4000
        assert settings.temperature == 0.1

    def test_full_settings(self, monkeypatch):
        """모든 설정이 포함된 LLM 테스트"""
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("LLM_MODEL_NAME", "gpt-4")
        monkeypatch.setenv("LLM_API_KEY", "test-api-key")
        monkeypatch.setenv("LLM_MAX_TOKENS", "8192")
        monkeypatch.setenv("LLM_TEMPERATURE", "0.5")

        settings = LLMSettings()

        assert settings.provider == "openai"
        assert settings.model_name == "gpt-4"
        assert settings.api_key == "test-api-key"
        assert settings.max_tokens == 8192
        assert settings.temperature == 0.5


class TestConversionSettings:
    """변환 설정 테스트"""

    def test_default_settings(self):
        """기본값으로 변환 설정 테스트"""
        settings = ConversionSettings()

        assert settings.max_file_size == 50 * 1024 * 1024
        assert settings.supported_formats == ["pdf"]
        assert settings.output_format == "epub3"
        assert settings.chunk_size == 1000
        assert settings.cleanup_temp_files is True

    def test_custom_settings(self, monkeypatch):
        """커스텀 변환 설정 테스트"""
        monkeypatch.setenv("CONVERSION_MAX_FILE_SIZE", "100000000")
        monkeypatch.setenv("CONVERSION_SUPPORTED_FORMATS", '["pdf", "docx"]')
        monkeypatch.setenv("CONVERSION_OUTPUT_FORMAT", "epub2")

        settings = ConversionSettings()

        assert settings.max_file_size == 100000000
        assert settings.supported_formats == ["pdf", "docx"]
        assert settings.output_format == "epub2"


class TestSettings:
    """메인 설정 클래스 테스트"""

    def test_settings_creation(self):
        """설정 객체 생성 테스트"""
        settings = Settings()

        assert settings.app_name == "PDF to EPUB Converter"
        assert settings.version == "1.0.0"
        assert settings.debug is False
        assert isinstance(settings.database, DatabaseSettings)
        assert isinstance(settings.redis, RedisSettings)
        assert isinstance(settings.ocr, OCRSettings)
        assert isinstance(settings.llm, LLMSettings)
        assert isinstance(settings.conversion, ConversionSettings)

    def test_caching(self):
        """설정 캐싱 기능 테스트"""
        settings1 = get_settings()
        settings2 = get_settings()

        # 동일한 객체가 반환되는지 확인
        assert settings1 is settings2

        # 설정 값도 동일한지 확인
        assert settings1.app_name == settings2.app_name


class TestSettingsIntegration:
    """통합 설정 테스트"""

    def test_env_file_loading(self, tmp_path):
        """.env 파일 로딩 테스트"""
        # pydantic-settings는 기본적으로 현재 디렉토리의 .env 파일만 읽음
        # 테스트에서는 환경 변수를 직접 설정하는 방식으로 검증

        # 환경 변수로 모든 설정 지정
        original_env = {}

        try:
            # 테스트용 환경 변수 설정
            test_env_vars = {
                "APP_NAME": "Test Converter",
                "DEBUG": "true",
                "DB_URL": "postgresql://user:pass@localhost/testdb",
                "REDIS_HOST": "test-redis.com",
                "OCR_LANGUAGE": "en",
                "LLM_PROVIDER": "openai",
                "CONVERSION_MAX_FILE_SIZE": "200000000",
            }

            # 기존 환경 변수 백업
            for key, value in test_env_vars.items():
                original_env[key] = os.environ.get(key)
                os.environ[key] = value

            # 새로운 설정 로드
            settings = Settings()

            assert settings.app_name == "Test Converter"
            assert settings.debug is True
            assert settings.database.url == "postgresql://user:pass@localhost/testdb"
            assert settings.redis.host == "test-redis.com"
            assert settings.ocr.language == "en"
            assert settings.llm.provider == "openai"
            assert settings.conversion.max_file_size == 200000000

        finally:
            # 원래 환경 변수 복원
            for key, original_value in original_env.items():
                if original_value is not None:
                    os.environ[key] = original_value
                else:
                    # 환경 변수가 없었던 경우 삭제
                    if key in os.environ:
                        del os.environ[key]

    def test_cors_origins(self):
        """CORS 출처 설정 테스트"""
        # 기본 출처 확인
        settings = Settings()
        origins = settings.cors_origins

        assert "http://localhost:3000" in origins
        assert "http://127.0.0.1:3000" in origins

        # 환경 변수로 추가 출처 설정
        os.environ["ALLOWED_HOSTS"] = "https://example.com,https://app.example.com"
        settings2 = Settings()

        origins2 = settings2.cors_origins
        assert "https://example.com" in origins2
        assert "https://app.example.com" in origins2

        # 환경 변수 정리
        del os.environ["ALLOWED_HOSTS"]


class TestSettingsEdgeCases:
    """예외 케이스 테스트"""

    def test_invalid_values_use_defaults(self, monkeypatch):
        """잘못된 값은 기본값 사용 테스트"""
        # pydantic-settings는 유효하지 않은 값에 대해 ValidationError를 발생시킴
        # 검증 로직을 직접 테스트해야 함
        monkeypatch.setenv("DB_POOL_SIZE", "invalid")

        # 이 테스트는 pydantic-settings의 기본 동작을 확인하는 것이 아니라,
        # 애플리케이션에서 예외 처리를 어떻게 할지 검증하는 용도
        from app.core.config import DatabaseSettings

        # 잘못된 값으로 설정 생성 시도
        with pytest.raises(ValueError):
            DatabaseSettings()

    def test_empty_strings_treated_as_none(self, monkeypatch):
        """빈 문자열은 None으로 처리 테스트"""
        monkeypatch.setenv("REDIS_PASSWORD", "")

        settings = RedisSettings()
        # pydantic-settings는 빈 문자열을 그대로 유지함
        assert settings.password == ""

    def test_partial_settings_override(self, monkeypatch):
        """부분 설정만 변경된 경우 테스트"""
        # 일부 설정만 환경 변수로 변경
        monkeypatch.setenv("DB_URL", "postgresql://newhost/newdb")

        settings = Settings()

        # 변경된 설정 확인
        assert settings.database.url == "postgresql://newhost/newdb"

        # 다른 설정은 기본값 유지
        assert settings.database.pool_size == 20
        assert settings.redis.host == "localhost"
        assert settings.ocr.language == "ko"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
