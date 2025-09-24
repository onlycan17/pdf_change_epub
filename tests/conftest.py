"""테스트 설정 파일"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import Generator, Dict, List, Optional

from app.core.config import Settings
from app.services.async_queue_service import AsyncQueueService


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """이벤트 루프 생성"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings() -> Settings:
    """모의 설정 객체"""
    settings = MagicMock()
    settings.redis.url = "redis://localhost:6379/0"
    settings.database.url = "postgresql://user:password@localhost:5432/pdf_to_epub"
    settings.security.api_key = "test-api-key"
    settings.conversion.output_dir = None
    return settings


@pytest.fixture
def mock_store() -> AsyncMock:
    """모의 작업 저장소"""
    store = AsyncMock()
    store.create.return_value = MagicMock()
    store.get.return_value = MagicMock()
    store.update.return_value = MagicMock()
    store.delete.return_value = MagicMock()
    store.list.return_value = []
    store.cancel.return_value = MagicMock()
    store.set_result.return_value = None
    return store


@pytest.fixture
def mock_celery_app() -> MagicMock:
    """모의 Celery 앱"""
    app = MagicMock()
    app.control.inspect.return_value.stats.return_value = {"worker1": {"total": 100}}
    app.send_task.return_value = MagicMock(id="test-task-id")
    app.AsyncResult.return_value = MagicMock(
        state="SUCCESS",
        result=b"test result",
        ready=lambda: True,
        successful=lambda: True,
        failed=lambda: False,
        get=lambda: b"test result",
    )
    return app


@pytest.fixture
def mock_redis_client() -> AsyncMock:
    """모의 Redis 클라이언트"""
    client = AsyncMock()
    client.ping.return_value = True
    client.set.return_value = True
    client.get.return_value = b"test value"
    client.delete.return_value = 1
    client.keys.return_value = [b"test_key"]
    client.flushdb.return_value = True
    return client


@pytest.fixture
def mock_pdf_analyzer() -> MagicMock:
    """모의 PDF 분석기"""
    analyzer = MagicMock()
    analyzer.analyze_pdf.return_value = MagicMock(
        pdf_type="TEXT_BASED",
        pages=10,
        metadata={"title": "Test PDF", "author": "Test Author"},
    )
    return analyzer


@pytest.fixture
def mock_pdf_extractor() -> MagicMock:
    """모의 PDF 추출기"""
    extractor = MagicMock()
    extractor.extract_text_from_pdf.return_value = {
        "total_text": "Test extracted text content",
        "pages": ["Page 1 content", "Page 2 content"],
    }
    extractor.extract_text_in_chunks.return_value = [
        {"start_page": 1, "end_page": 5, "total_text": "Pages 1-5 content"},
        {"start_page": 6, "end_page": 10, "total_text": "Pages 6-10 content"},
    ]
    return extractor


@pytest.fixture
def mock_epub_generator() -> MagicMock:
    """모의 EPUB 생성기"""
    epub = MagicMock()
    epub.create_epub_bytes.return_value = b"test epub content"
    epub.create_epub_file.return_value = "/tmp/test.epub"
    return epub


@pytest.fixture
def mock_epub_validator() -> MagicMock:
    """모의 EPUB 검증기"""
    validator = MagicMock()
    validator.valid = True
    validator.errors = []
    return validator


@pytest.fixture
def mock_agent_service() -> MagicMock:
    """모의 Agent 서비스"""
    service = MagicMock()
    service.process_scanned_pdf.return_value = MagicMock(
        markdown_content="# Test Content\n\nThis is test content.",
        metadata={"language": "ko", "confidence": 0.95},
    )
    return service


@pytest.fixture
def sample_pdf_content() -> bytes:
    """샘플 PDF 콘텐츠"""
    return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
  /Font <<
    /F1 <<
      /Type /Font
      /Subtype /Type1
      /BaseFont /Times-Roman
    >>
  >>
>>
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
50 750 Td
(Test PDF content) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000274 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
343
%%EOF"""


@pytest.fixture
def sample_conversion_job() -> MagicMock:
    """샘플 변환 작업"""
    job = MagicMock()
    job.conversion_id = "test-123"
    job.filename = "test.pdf"
    job.file_size = 1024
    job.ocr_enabled = True
    job.state = "PENDING"
    job.progress = 0
    job.message = "작업 대기 중"
    job.created_at = "2023-01-01T00:00:00Z"
    job.updated_at = "2023-01-01T00:00:00Z"
    job.current_step = ""
    job.steps = []
    job.result_bytes = None
    job.result_path = None
    job.error_message = None
    job.attempts = 0
    job.celery_task_id = None
    job.is_cancelled = MagicMock(return_value=False)
    return job


@pytest.fixture
def async_queue_service(
    mock_settings: Settings,
    mock_celery_app: MagicMock,
    mock_store: AsyncMock,
) -> AsyncQueueService:
    """비동기 작업 큐 서비스"""
    service = AsyncQueueService()
    service.settings = mock_settings
    service.celery_app = mock_celery_app
    service.store = mock_store
    service._initialized = True
    return service


@pytest.fixture
def test_client_headers() -> dict:
    """테스트 클라이언트 헤더"""
    return {
        "X-API-Key": "test-api-key",
        "Content-Type": "application/json",
    }


@pytest.fixture
def test_client_files() -> dict:
    """테스트 클라이언트 파일"""
    return {
        "file": ("test.pdf", b"test pdf content", "application/pdf"),
    }


@pytest.fixture
def test_client_data() -> dict:
    """테스트 클라이언트 데이터"""
    return {
        "ocr_enabled": "true",
    }


# 테스트 유틸리티 함수
def create_test_job(
    conversion_id: str = "test-123",
    filename: str = "test.pdf",
    file_size: int = 1024,
    ocr_enabled: bool = True,
    state: str = "PENDING",
    progress: int = 0,
    message: str = "작업 대기 중",
) -> MagicMock:
    """테스트 작업 생성"""
    job = MagicMock()
    job.conversion_id = conversion_id
    job.filename = filename
    job.file_size = file_size
    job.ocr_enabled = ocr_enabled
    job.state = state
    job.progress = progress
    job.message = message
    job.created_at = "2023-01-01T00:00:00Z"
    job.updated_at = "2023-01-01T00:00:00Z"
    job.current_step = ""
    job.steps = []
    job.result_bytes = None
    job.result_path = None
    job.error_message = None
    job.attempts = 0
    job.celery_task_id = None
    job.is_cancelled = MagicMock(return_value=False)
    return job


def create_test_celery_result(
    state: str = "SUCCESS",
    result: bytes = b"test result",
    ready: bool = True,
    successful: bool = True,
    failed: bool = False,
) -> MagicMock:
    """테스트 Celery 결과 생성"""
    mock_result = MagicMock()
    mock_result.state = state
    mock_result.result = result
    mock_result.ready.return_value = ready
    mock_result.successful.return_value = successful
    mock_result.failed.return_value = failed
    mock_result.get.return_value = result
    return mock_result


def create_test_pdf_analysis(
    pdf_type: str = "TEXT_BASED",
    pages: int = 10,
    metadata: Optional[Dict] = None,
) -> MagicMock:
    """테스트 PDF 분석 결과 생성"""
    if metadata is None:
        metadata = {"title": "Test PDF", "author": "Test Author"}

    analysis = MagicMock()
    analysis.pdf_type = pdf_type
    analysis.pages = pages
    analysis.metadata = metadata
    return analysis


def create_test_extracted_text(
    total_text: str = "Test extracted text content",
    pages: Optional[List] = None,
) -> dict:
    """테스트 추출된 텍스트 생성"""
    if pages is None:
        pages = ["Page 1 content", "Page 2 content"]

    return {
        "total_text": total_text,
        "pages": pages,
    }


def create_test_epub_validation(
    valid: bool = True,
    errors: Optional[List] = None,
) -> MagicMock:
    """테스트 EPUB 검증 결과 생성"""
    if errors is None:
        errors = []

    validation = MagicMock()
    validation.valid = valid
    validation.errors = errors
    return validation


# 테스트 마커
pytestmark = pytest.mark.asyncio
