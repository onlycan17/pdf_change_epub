"""ConversionOrchestrator unit tests"""

import asyncio
import uuid
from unittest.mock import AsyncMock

import pytest

from app.services.conversion_orchestrator import (
    ConversionOrchestrator,
    ConversionJob,
    JobState,
    get_orchestrator,
)
from app.services.pdf_service import (
    PDFType,
    PDFAnalysisResult,
    PageAnalysisResult,
)


def make_dummy_pdf_bytes() -> bytes:
    # Very small valid PDF-like header (not full PDF) but enough for our code paths
    return b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


@pytest.mark.asyncio
async def test_start_and_status_and_download(monkeypatch):
    settings = None

    # Create orchestrator
    orch = ConversionOrchestrator(settings)

    # Patch PDFAnalyzer.analyze_pdf to return a properly-typed PDFAnalysisResult
    monkeypatch.setattr(orch, "pdf_analyzer", AsyncMock())
    pdf_analysis = PDFAnalysisResult(
        pdf_type=PDFType.TEXT_BASED,
        total_pages=1,
        pages_analysis=[
            PageAnalysisResult(page_number=1, has_text=True, text_content="Hello")
        ],
        overall_confidence=1.0,
        mixed_ratio=0.0,
    )

    orch.pdf_analyzer.analyze_pdf = lambda pdf_content: pdf_analysis

    # Patch PDFExtractor.extract_text_from_pdf with correct signature
    monkeypatch.setattr(orch, "pdf_extractor", AsyncMock())

    def fake_extract_text_from_pdf(pdf_content, page_numbers=None):
        return {
            "total_text": "Hello World",
            "page_texts": [{"page": "1", "text": "Hello World"}],
        }

    orch.pdf_extractor.extract_text_from_pdf = fake_extract_text_from_pdf

    # Patch EpubGenerator.create_epub_bytes with correct signature
    def fake_create_epub_bytes(title: str, author: str, chapters, uid=None, include_legacy_ncx=True, auto_toc_from_headings=True):
        return b"EPUBBYTES"

    orch.epub.create_epub_bytes = fake_create_epub_bytes

    conversion_id = str(uuid.uuid4())
    pdf_bytes = make_dummy_pdf_bytes()

    await orch.start(
        conversion_id=conversion_id,
        filename="test.pdf",
        file_size=len(pdf_bytes),
        ocr_enabled=False,
        pdf_bytes=pdf_bytes,
    )

    # wait briefly for background task to complete
    await asyncio.sleep(0.5)

    status = await orch.status(conversion_id)
    assert status.conversion_id == conversion_id
    assert status.filename == "test.pdf"

    # If completed, download returns bytes
    if status.state == JobState.COMPLETED:
        data = await orch.download(conversion_id)
        assert data == b"EPUBBYTES"


@pytest.mark.asyncio
async def test_cancel_conversion(monkeypatch):
    orch = get_orchestrator()

    # Prepare a job manually in the store
    conversion_id = "cancel-test-id"
    job = ConversionJob(
        conversion_id=conversion_id,
        filename="a.pdf",
        file_size=10,
        ocr_enabled=False,
    )

    await orch.store.create(job)

    # Cancel and verify state
    await orch.cancel(conversion_id)
    fetched = await orch.status(conversion_id)
    assert fetched.state == JobState.CANCELLED
