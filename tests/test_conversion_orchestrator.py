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


def make_dummy_pdf_bytes() -> bytes:
    # Very small valid PDF-like header (not full PDF) but enough for our code paths
    return b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


@pytest.mark.asyncio
async def test_start_and_status_and_download(monkeypatch):
    settings = None

    # Create orchestrator
    orch = ConversionOrchestrator(settings)

    # Patch PDFAnalyzer.analyze_pdf to return a simple object with pdf_type attribute
    class DummyAnalysis:
        def __init__(self):
            from app.services.pdf_service import PDFType

            self.pdf_type = PDFType.TEXT_BASED

    monkeypatch.setattr(orch, "pdf_analyzer", AsyncMock())
    orch.pdf_analyzer.analyze_pdf = lambda _b: DummyAnalysis()

    # Patch PDFExtractor.extract_text_from_pdf
    monkeypatch.setattr(orch, "pdf_extractor", AsyncMock())
    orch.pdf_extractor.extract_text_from_pdf = lambda _b: {
        "total_text": "Hello World",
        "page_texts": [{"page": "1", "text": "Hello World"}],
    }

    # Patch EpubGenerator to return simple bytes
    orch.epub.create_epub_bytes = lambda **kw: b"EPUBBYTES"

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
