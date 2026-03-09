"""ConversionOrchestrator unit tests"""

import asyncio
import uuid
from unittest.mock import MagicMock
from io import BytesIO

import pytest

from app.services.conversion_orchestrator import (
    ConversionOrchestrator,
    ConversionJob,
    JobState,
    get_orchestrator,
)
from app.services.agent_service import SynthesisAgent
from app.services.pdf_service import (
    PDFType,
    PDFAnalysisResult,
    PageAnalysisResult,
)


def make_dummy_pdf_bytes() -> bytes:
    # Very small valid PDF-like header (not full PDF) but enough for our code paths
    return b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


def make_tiny_png_bytes() -> bytes:
    try:
        from PIL import Image

        image = Image.new("RGB", (1, 1), color=(255, 255, 255))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
    except Exception:
        # 최소 PNG 헤더 + IHDR/IEND 구조(테스트 대체용)
        return (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde"
            b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\xe2 \x00"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )


@pytest.mark.asyncio
async def test_start_and_status_and_download(monkeypatch):
    settings = None

    # Create orchestrator
    orch = ConversionOrchestrator(settings)

    # Patch PDFAnalyzer.analyze_pdf to return a properly-typed PDFAnalysisResult
    monkeypatch.setattr(orch, "pdf_analyzer", MagicMock())
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
    monkeypatch.setattr(orch, "pdf_extractor", MagicMock())

    def fake_extract_text_from_pdf(pdf_content, page_numbers=None):
        return {
            "total_text": "Hello World",
            "page_texts": [{"page": "1", "text": "Hello World"}],
        }

    orch.pdf_extractor.extract_text_from_pdf = fake_extract_text_from_pdf

    def fake_extract_text_in_chunks(pdf_content, chunk_chars=None):
        return []

    orch.pdf_extractor.extract_text_in_chunks = fake_extract_text_in_chunks

    # Patch EpubGenerator.create_epub_bytes with correct signature
    def fake_create_epub_bytes(
        title: str,
        author: str,
        chapters,
        images=None,
        uid=None,
        include_legacy_ncx=True,
        auto_toc_from_headings=True,
    ):
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


@pytest.mark.asyncio
async def test_text_pdf_chunks_apply_context_correction(monkeypatch):
    orch = ConversionOrchestrator(None)

    monkeypatch.setattr(orch, "pdf_analyzer", MagicMock())
    pdf_analysis = PDFAnalysisResult(
        pdf_type=PDFType.TEXT_BASED,
        total_pages=2,
        pages_analysis=[
            PageAnalysisResult(page_number=1, has_text=True, text_content="A"),
            PageAnalysisResult(page_number=2, has_text=True, text_content="B"),
        ],
        overall_confidence=1.0,
        mixed_ratio=0.0,
    )
    orch.pdf_analyzer.analyze_pdf = lambda pdf_content: pdf_analysis

    monkeypatch.setattr(orch, "pdf_extractor", MagicMock())
    orch.pdf_extractor.extract_text_in_chunks = lambda pdf_content, chunk_chars=None: [
        {"start_page": 1, "end_page": 1, "total_text": "첫청크"},
        {"start_page": 2, "end_page": 2, "total_text": "둘청크"},
    ]
    orch.pdf_extractor.extract_text_from_pdf = lambda pdf_content, page_numbers=None: {
        "total_text": "fallback"
    }

    class DummyCorrector:
        last_run_stats = {
            "total_chunks": 2,
            "total_attempts": 3,
            "last_used_model": "nvidia/nemotron-3-nano-30b-a3b",
            "fallback_used": True,
        }

        async def correct_chunk_entries(self, chunks, on_chunk_progress=None):
            if on_chunk_progress:
                await on_chunk_progress(1, 2)
                await on_chunk_progress(2, 2)
            return "보정된 전체 텍스트"

    monkeypatch.setattr(orch, "text_context_corrector", DummyCorrector())

    def fake_create_epub_bytes(
        title: str,
        author: str,
        chapters,
        images=None,
        uid=None,
        include_legacy_ncx=True,
        auto_toc_from_headings=True,
    ):
        assert "보정된 전체 텍스트" in chapters[0].content
        return b"EPUBBYTES"

    orch.epub.create_epub_bytes = fake_create_epub_bytes

    conversion_id = "ctx-test-id"
    pdf_bytes = make_dummy_pdf_bytes()
    await orch.start(
        conversion_id=conversion_id,
        filename="ctx.pdf",
        file_size=len(pdf_bytes),
        ocr_enabled=False,
        pdf_bytes=pdf_bytes,
    )

    await asyncio.sleep(0.5)
    status = await orch.status(conversion_id)
    assert status.state == JobState.COMPLETED
    assert status.llm_used_model == "nvidia/nemotron-3-nano-30b-a3b"
    assert status.llm_attempt_count == 3
    assert status.llm_fallback_used is True


@pytest.mark.asyncio
async def test_text_result_is_preferred_over_content_flow(monkeypatch):
    orch = ConversionOrchestrator(None)

    monkeypatch.setattr(orch, "pdf_analyzer", MagicMock())
    pdf_analysis = PDFAnalysisResult(
        pdf_type=PDFType.TEXT_BASED,
        total_pages=1,
        pages_analysis=[
            PageAnalysisResult(page_number=1, has_text=True, text_content="A"),
        ],
        overall_confidence=1.0,
        mixed_ratio=0.0,
    )
    orch.pdf_analyzer.analyze_pdf = lambda pdf_content: pdf_analysis

    monkeypatch.setattr(orch, "pdf_extractor", MagicMock())
    orch.pdf_extractor.extract_text_in_chunks = lambda pdf_content, chunk_chars=None: []
    orch.pdf_extractor.extract_text_from_pdf = lambda pdf_content, page_numbers=None: {
        "total_text": "=== 페이지 1 ===\n보정된 문장"
    }
    orch.pdf_extractor.extract_content_flow_with_images = lambda pdf_content: {
        "pages": [
            {
                "page": 1,
                "elements": [{"type": "text", "text": "블록텍스트"}],
            }
        ]
    }
    orch.pdf_extractor.extract_images_from_pdf = lambda pdf_content: []

    def fake_create_epub_bytes(
        title: str,
        author: str,
        chapters,
        images=None,
        uid=None,
        include_legacy_ncx=True,
        auto_toc_from_headings=True,
    ):
        content = chapters[0].content
        assert "보정된 문장" in content
        assert "블록텍스트" not in content
        return b"EPUBBYTES"

    orch.epub.create_epub_bytes = fake_create_epub_bytes

    conversion_id = "prefer-text-result-id"
    pdf_bytes = make_dummy_pdf_bytes()
    await orch.start(
        conversion_id=conversion_id,
        filename="prefer.pdf",
        file_size=len(pdf_bytes),
        ocr_enabled=False,
        pdf_bytes=pdf_bytes,
    )

    await asyncio.sleep(0.5)
    status = await orch.status(conversion_id)
    assert status.state == JobState.COMPLETED


@pytest.mark.asyncio
async def test_epub_includes_extracted_images(monkeypatch):
    orch = ConversionOrchestrator(None)

    monkeypatch.setattr(orch, "pdf_analyzer", MagicMock())
    pdf_analysis = PDFAnalysisResult(
        pdf_type=PDFType.TEXT_BASED,
        total_pages=1,
        pages_analysis=[
            PageAnalysisResult(page_number=1, has_text=True, text_content="본문")
        ],
        overall_confidence=1.0,
        mixed_ratio=0.0,
    )
    orch.pdf_analyzer.analyze_pdf = lambda pdf_content: pdf_analysis

    monkeypatch.setattr(orch, "pdf_extractor", MagicMock())
    orch.pdf_extractor.extract_text_in_chunks = lambda pdf_content, chunk_chars=None: []
    orch.pdf_extractor.extract_text_from_pdf = lambda pdf_content, page_numbers=None: {
        "total_text": "이미지 포함 테스트"
    }
    orch.pdf_extractor.extract_images_from_pdf = lambda pdf_content: [
        {"page": 1, "xref": 1, "image_bytes": b"img-bytes", "format": "png"}
    ]

    def fake_create_epub_bytes(
        title: str,
        author: str,
        chapters,
        images=None,
        uid=None,
        include_legacy_ncx=True,
        auto_toc_from_headings=True,
    ):
        assert images is not None
        assert len(images) == 1
        assert images[0].file_name.endswith(".png")
        assert 'src="images/image-1.png"' in chapters[0].content
        return b"EPUBBYTES"

    orch.epub.create_epub_bytes = fake_create_epub_bytes

    conversion_id = "image-test-id"
    pdf_bytes = make_dummy_pdf_bytes()
    await orch.start(
        conversion_id=conversion_id,
        filename="img.pdf",
        file_size=len(pdf_bytes),
        ocr_enabled=False,
        pdf_bytes=pdf_bytes,
    )

    await asyncio.sleep(0.5)
    status = await orch.status(conversion_id)
    assert status.state == JobState.COMPLETED


@pytest.mark.asyncio
async def test_unknown_image_format_is_normalized_to_png(monkeypatch):
    orch = ConversionOrchestrator(None)

    monkeypatch.setattr(orch, "pdf_analyzer", MagicMock())
    pdf_analysis = PDFAnalysisResult(
        pdf_type=PDFType.TEXT_BASED,
        total_pages=1,
        pages_analysis=[
            PageAnalysisResult(page_number=1, has_text=True, text_content="본문")
        ],
        overall_confidence=1.0,
        mixed_ratio=0.0,
    )
    orch.pdf_analyzer.analyze_pdf = lambda pdf_content: pdf_analysis

    monkeypatch.setattr(orch, "pdf_extractor", MagicMock())
    orch.pdf_extractor.extract_text_in_chunks = lambda pdf_content, chunk_chars=None: []
    orch.pdf_extractor.extract_text_from_pdf = lambda pdf_content, page_numbers=None: {
        "total_text": "이미지 정규화 테스트"
    }
    orch.pdf_extractor.extract_images_from_pdf = lambda pdf_content: [
        {
            "page": 1,
            "xref": 1,
            "image_bytes": make_tiny_png_bytes(),
            "format": "jpx",
        }
    ]

    def fake_create_epub_bytes(
        title: str,
        author: str,
        chapters,
        images=None,
        uid=None,
        include_legacy_ncx=True,
        auto_toc_from_headings=True,
    ):
        assert images is not None
        assert len(images) == 1
        assert images[0].file_name.endswith(".png")
        assert images[0].media_type == "image/png"
        assert len(images[0].data) > 0
        return b"EPUBBYTES"

    orch.epub.create_epub_bytes = fake_create_epub_bytes

    conversion_id = "image-normalize-test-id"
    pdf_bytes = make_dummy_pdf_bytes()
    await orch.start(
        conversion_id=conversion_id,
        filename="normalize.pdf",
        file_size=len(pdf_bytes),
        ocr_enabled=False,
        pdf_bytes=pdf_bytes,
    )

    await asyncio.sleep(0.5)
    status = await orch.status(conversion_id)
    assert status.state == JobState.COMPLETED


@pytest.mark.asyncio
async def test_scanned_pdf_skips_full_page_scan_images_in_epub(monkeypatch):
    orch = ConversionOrchestrator(None)

    monkeypatch.setattr(orch, "pdf_analyzer", MagicMock())
    pdf_analysis = PDFAnalysisResult(
        pdf_type=PDFType.SCANNED,
        total_pages=1,
        pages_analysis=[
            PageAnalysisResult(page_number=1, has_text=False, is_scanned_page=True)
        ],
        overall_confidence=1.0,
        mixed_ratio=0.0,
    )
    orch.pdf_analyzer.analyze_pdf = lambda pdf_content: pdf_analysis

    monkeypatch.setattr(orch, "pdf_extractor", MagicMock())
    orch.pdf_extractor.extract_text_in_chunks = lambda pdf_content, chunk_chars=None: []
    orch.pdf_extractor.extract_images_from_pdf = lambda pdf_content: [
        {
            "page": 1,
            "xref": 1,
            "image_bytes": make_tiny_png_bytes(),
            "format": "png",
            "coverage_ratio": 0.99,
            "is_full_page_scan": "true",
        }
    ]
    orch.pdf_extractor.extract_content_flow_with_images = lambda pdf_content: {
        "pages": [
            {
                "page": 1,
                "elements": [
                    {
                        "type": "image",
                        "xref": 1,
                        "coverage_ratio": 0.99,
                        "is_full_page_scan": True,
                    }
                ],
            }
        ]
    }

    class DummyProcessor:
        async def process_scanned_pdf(self, _pdf_bytes: bytes):
            return type("Synthesis", (), {"markdown_content": "# 페이지 1\nOCR 본문"})()

    async def fake_create_scan_pdf_processor(settings, progress_callback=None):
        return DummyProcessor()

    import app.services.agent_service as agent_service

    monkeypatch.setattr(
        agent_service,
        "create_scan_pdf_processor",
        fake_create_scan_pdf_processor,
    )

    def fake_create_epub_bytes(
        title: str,
        author: str,
        chapters,
        images=None,
        uid=None,
        include_legacy_ncx=True,
        auto_toc_from_headings=True,
    ):
        assert images == []
        assert 'src="images/image-1.png"' not in chapters[0].content
        assert "OCR 본문" in chapters[0].content
        return b"EPUBBYTES"

    orch.epub.create_epub_bytes = fake_create_epub_bytes

    conversion_id = "scanned-image-skip-id"
    pdf_bytes = make_dummy_pdf_bytes()
    await orch.start(
        conversion_id=conversion_id,
        filename="scan.pdf",
        file_size=len(pdf_bytes),
        ocr_enabled=True,
        pdf_bytes=pdf_bytes,
    )

    await asyncio.sleep(0.5)
    status = await orch.status(conversion_id)
    assert status.state == JobState.COMPLETED


@pytest.mark.asyncio
async def test_scanned_pdf_without_ocr_keeps_full_page_images(monkeypatch):
    orch = ConversionOrchestrator(None)

    monkeypatch.setattr(orch, "pdf_analyzer", MagicMock())
    pdf_analysis = PDFAnalysisResult(
        pdf_type=PDFType.SCANNED,
        total_pages=1,
        pages_analysis=[
            PageAnalysisResult(page_number=1, has_text=False, is_scanned_page=True)
        ],
        overall_confidence=1.0,
        mixed_ratio=0.0,
    )
    orch.pdf_analyzer.analyze_pdf = lambda pdf_content: pdf_analysis

    monkeypatch.setattr(orch, "pdf_extractor", MagicMock())
    orch.pdf_extractor.extract_text_in_chunks = lambda pdf_content, chunk_chars=None: []
    orch.pdf_extractor.extract_images_from_pdf = lambda pdf_content: [
        {
            "page": 1,
            "xref": 1,
            "image_bytes": make_tiny_png_bytes(),
            "format": "png",
            "coverage_ratio": 0.99,
            "is_full_page_scan": "true",
        }
    ]
    orch.pdf_extractor.extract_content_flow_with_images = lambda pdf_content: {
        "pages": [
            {
                "page": 1,
                "elements": [
                    {
                        "type": "image",
                        "xref": 1,
                        "coverage_ratio": 0.99,
                        "is_full_page_scan": True,
                    }
                ],
            }
        ]
    }

    def fake_create_epub_bytes(
        title: str,
        author: str,
        chapters,
        images=None,
        uid=None,
        include_legacy_ncx=True,
        auto_toc_from_headings=True,
    ):
        assert images is not None
        assert len(images) == 1
        assert 'src="images/image-1.png"' in chapters[0].content
        return b"EPUBBYTES"

    orch.epub.create_epub_bytes = fake_create_epub_bytes

    conversion_id = "scanned-image-keep-id"
    pdf_bytes = make_dummy_pdf_bytes()
    await orch.start(
        conversion_id=conversion_id,
        filename="scan-no-ocr.pdf",
        file_size=len(pdf_bytes),
        ocr_enabled=False,
        pdf_bytes=pdf_bytes,
    )

    await asyncio.sleep(0.5)
    status = await orch.status(conversion_id)
    assert status.state == JobState.COMPLETED


@pytest.mark.asyncio
async def test_mixed_pdf_with_ocr_skips_scanned_page_images(monkeypatch):
    orch = ConversionOrchestrator(None)

    monkeypatch.setattr(orch, "pdf_analyzer", MagicMock())
    pdf_analysis = PDFAnalysisResult(
        pdf_type=PDFType.MIXED,
        total_pages=1,
        pages_analysis=[
            PageAnalysisResult(
                page_number=1,
                has_text=True,
                text_content="숨겨진 OCR 레이어",
                is_scanned_page=True,
            )
        ],
        overall_confidence=1.0,
        mixed_ratio=1.0,
    )
    orch.pdf_analyzer.analyze_pdf = lambda pdf_content: pdf_analysis

    monkeypatch.setattr(orch, "pdf_extractor", MagicMock())
    orch.pdf_extractor.extract_text_in_chunks = lambda pdf_content, chunk_chars=None: []
    orch.pdf_extractor.extract_text_from_pdf = lambda pdf_content, page_numbers=None: {
        "total_text": "=== 페이지 1 ===\n숨겨진 OCR 레이어"
    }
    orch.pdf_extractor.extract_images_from_pdf = lambda pdf_content: [
        {
            "page": 1,
            "xref": 1,
            "image_bytes": make_tiny_png_bytes(),
            "format": "png",
            "coverage_ratio": 0.99,
            "is_full_page_scan": "true",
        }
    ]
    orch.pdf_extractor.extract_content_flow_with_images = lambda pdf_content: {
        "pages": [
            {
                "page": 1,
                "elements": [
                    {
                        "type": "image",
                        "xref": 1,
                        "coverage_ratio": 0.99,
                        "is_full_page_scan": True,
                    }
                ],
            }
        ]
    }

    def fake_create_epub_bytes(
        title: str,
        author: str,
        chapters,
        images=None,
        uid=None,
        include_legacy_ncx=True,
        auto_toc_from_headings=True,
    ):
        assert images == []
        assert 'src="images/image-1.png"' not in chapters[0].content
        assert "숨겨진 OCR 레이어" in chapters[0].content
        return b"EPUBBYTES"

    orch.epub.create_epub_bytes = fake_create_epub_bytes

    conversion_id = "mixed-hidden-ocr-id"
    pdf_bytes = make_dummy_pdf_bytes()
    await orch.start(
        conversion_id=conversion_id,
        filename="mixed-hidden-ocr.pdf",
        file_size=len(pdf_bytes),
        ocr_enabled=True,
        pdf_bytes=pdf_bytes,
    )

    await asyncio.sleep(0.5)
    status = await orch.status(conversion_id)
    assert status.state == JobState.COMPLETED


@pytest.mark.asyncio
async def test_scanned_pdf_preserves_verse_blocks_in_rendered_epub(monkeypatch):
    orch = ConversionOrchestrator(None)

    monkeypatch.setattr(orch, "pdf_analyzer", MagicMock())
    pdf_analysis = PDFAnalysisResult(
        pdf_type=PDFType.SCANNED,
        total_pages=1,
        pages_analysis=[
            PageAnalysisResult(page_number=1, has_text=False, is_scanned_page=True)
        ],
        overall_confidence=1.0,
        mixed_ratio=0.0,
    )
    orch.pdf_analyzer.analyze_pdf = lambda pdf_content: pdf_analysis

    monkeypatch.setattr(orch, "pdf_extractor", MagicMock())
    orch.pdf_extractor.extract_text_in_chunks = lambda pdf_content, chunk_chars=None: []
    orch.pdf_extractor.extract_images_from_pdf = lambda pdf_content: []
    orch.pdf_extractor.extract_content_flow_with_images = lambda pdf_content: {"pages": []}

    class DummyProcessor:
        async def process_scanned_pdf(self, _pdf_bytes: bytes):
            return type(
                "Synthesis",
                (),
                {
                    "markdown_content": "# 페이지 1\n[[VERSE]]\n[[LINE:0]]산길 조용히\n[[LINE:2]]달빛 비친다\n[[/VERSE]]"
                },
            )()

    async def fake_create_scan_pdf_processor(settings, progress_callback=None):
        return DummyProcessor()

    import app.services.agent_service as agent_service

    monkeypatch.setattr(
        agent_service,
        "create_scan_pdf_processor",
        fake_create_scan_pdf_processor,
    )

    def fake_create_epub_bytes(
        title: str,
        author: str,
        chapters,
        images=None,
        uid=None,
        include_legacy_ncx=True,
        auto_toc_from_headings=True,
    ):
        assert '<p class="verse">' in chapters[0].content
        assert "산길 조용히<br/>" in chapters[0].content
        assert "&nbsp;&nbsp;&nbsp;&nbsp;달빛 비친다" in chapters[0].content
        return b"EPUBBYTES"

    orch.epub.create_epub_bytes = fake_create_epub_bytes

    conversion_id = "scanned-verse-render-id"
    pdf_bytes = make_dummy_pdf_bytes()
    await orch.start(
        conversion_id=conversion_id,
        filename="verse-scan.pdf",
        file_size=len(pdf_bytes),
        ocr_enabled=True,
        pdf_bytes=pdf_bytes,
    )

    await asyncio.sleep(0.5)
    status = await orch.status(conversion_id)
    assert status.state == JobState.COMPLETED


def test_render_markdown_to_xhtml_body_removes_raw_markdown():
    orch = ConversionOrchestrator(None)

    markdown_text = """# 제목

- 항목1
- 항목2

본문 문장입니다.
"""

    html_body = orch._render_markdown_to_xhtml_body(  # type: ignore[attr-defined]
        markdown_text,
        {},
    )

    assert "<h1>제목</h1>" in html_body
    assert "<ul>" in html_body
    assert "<li>항목1</li>" in html_body
    assert "<p>본문 문장입니다.</p>" in html_body
    assert "# 제목" not in html_body


def test_render_markdown_to_xhtml_body_converts_latex_math_to_mathml():
    orch = ConversionOrchestrator(None)

    markdown_text = """# 수식

이차식은 $x^2 + y^2 = z^2$ 입니다.

$$\\frac{a}{b}$$
"""

    html_body = orch._render_markdown_to_xhtml_body(  # type: ignore[attr-defined]
        markdown_text,
        {},
    )

    assert "<math" in html_body
    assert "<msup>" in html_body
    assert "<mfrac>" in html_body
    assert "$x^2 + y^2 = z^2$" not in html_body


def test_render_text_with_page_images_auto_converts_formula_lines_to_mathml():
    orch = ConversionOrchestrator(None)

    html_body = orch._render_text_with_page_images(  # type: ignore[attr-defined]
        "=== 페이지 1 ===\nx² + y² = z²\n설명 문장",
        {},
    )

    assert '<div class="math-display">' in html_body
    assert "<math" in html_body
    assert "설명 문장" in html_body


def test_combine_page_content_appends_detected_equations_as_latex_blocks():
    synthesis = SynthesisAgent()

    combined = synthesis._combine_page_content(  # type: ignore[attr-defined]
        {
            "ocr_texts": [{"text": "본문 설명"}],
            "descriptions": [
                {
                    "text_content": "",
                    "equations_latex": ["\\frac{a}{b}", "x^2+y^2=z^2"],
                }
            ],
        }
    )

    assert "본문 설명" in combined
    assert "$$ \\frac{a}{b} $$" in combined
    assert "$$ x^2+y^2=z^2 $$" in combined


def test_render_content_flow_places_image_in_order():
    orch = ConversionOrchestrator(None)

    content_flow = [
        {
            "page": 1,
            "elements": [
                {"type": "text", "text": "첫 문단"},
                {"type": "image", "xref": 10},
                {"type": "text", "text": "둘 문단"},
            ],
        }
    ]
    image_map = {10: "images/image-1.png"}

    html_body = orch._render_content_flow_to_xhtml(  # type: ignore[attr-defined]
        content_flow,
        image_map,
    )

    first_text_idx = html_body.find("첫 문단")
    image_idx = html_body.find('src="images/image-1.png"')
    second_text_idx = html_body.find("둘 문단")

    assert first_text_idx != -1
    assert image_idx != -1
    assert second_text_idx != -1
    assert first_text_idx < image_idx < second_text_idx


def test_render_markdown_to_xhtml_body_preserves_verse_line_breaks():
    orch = ConversionOrchestrator(None)

    markdown_text = """# 페이지 1
[[VERSE]]
[[LINE:0]]산길 조용히
[[LINE:2]]달빛 비친다
[[/VERSE]]
"""

    html_body = orch._render_markdown_to_xhtml_body(  # type: ignore[attr-defined]
        markdown_text,
        {},
    )

    assert '<p class="verse">' in html_body
    assert "산길 조용히<br/>" in html_body
    assert "&nbsp;&nbsp;&nbsp;&nbsp;달빛 비친다" in html_body


def test_render_markdown_to_xhtml_body_renders_scanned_math_image_markers():
    orch = ConversionOrchestrator(None)

    html_body = orch._render_markdown_to_xhtml_body(  # type: ignore[attr-defined]
        "# 페이지 1\n문장\n\n[[MATHIMG:page-1-eq-1]]\n",
        {},
        math_image_refs={
            "[[MATHIMG:page-1-eq-1]]": {
                "file_name": "images/scan-math-1.png",
                "alt_text": "x^2 + y^2 = z^2",
            }
        },
    )

    assert 'class="math-figure"' in html_body
    assert 'src="images/scan-math-1.png"' in html_body
    assert "x^2 + y^2 = z^2" in html_body


@pytest.mark.asyncio
async def test_scanned_pdf_renders_equation_crops_as_epub_images(monkeypatch):
    orch = ConversionOrchestrator(None)

    monkeypatch.setattr(orch, "pdf_analyzer", MagicMock())
    pdf_analysis = PDFAnalysisResult(
        pdf_type=PDFType.SCANNED,
        total_pages=1,
        pages_analysis=[
            PageAnalysisResult(page_number=1, has_text=False, is_scanned_page=True)
        ],
        overall_confidence=1.0,
        mixed_ratio=0.0,
    )
    orch.pdf_analyzer.analyze_pdf = lambda pdf_content: pdf_analysis

    monkeypatch.setattr(orch, "pdf_extractor", MagicMock())
    orch.pdf_extractor.extract_text_in_chunks = lambda pdf_content, chunk_chars=None: []
    orch.pdf_extractor.extract_images_from_pdf = lambda pdf_content: []
    orch.pdf_extractor.extract_content_flow_with_images = lambda pdf_content: {"pages": []}

    class DummyProcessor:
        async def process_scanned_pdf(self, _pdf_bytes: bytes):
            return type(
                "Synthesis",
                (),
                {
                    "markdown_content": "# 페이지 1\n설명 문장\n\n[[MATHIMG:page-1-eq-1]]\n\n다음 문장",
                    "metadata": {
                        "equation_images": [
                            {
                                "marker": "[[MATHIMG:page-1-eq-1]]",
                                "image_bytes": make_tiny_png_bytes(),
                                "format": "png",
                                "page_number": 1,
                                "alt_text": "x^2 + y^2 = z^2",
                            }
                        ]
                    },
                },
            )()

    async def fake_create_scan_pdf_processor(settings, progress_callback=None):
        return DummyProcessor()

    import app.services.agent_service as agent_service

    monkeypatch.setattr(
        agent_service,
        "create_scan_pdf_processor",
        fake_create_scan_pdf_processor,
    )

    def fake_create_epub_bytes(
        title: str,
        author: str,
        chapters,
        images=None,
        uid=None,
        include_legacy_ncx=True,
        auto_toc_from_headings=True,
    ):
        assert images is not None
        assert any(image.file_name.startswith("images/scan-math-") for image in images)
        assert 'class="math-figure"' in chapters[0].content
        assert 'src="images/scan-math-1.png"' in chapters[0].content
        assert "x^2 + y^2 = z^2" in chapters[0].content
        return b"EPUBBYTES"

    orch.epub.create_epub_bytes = fake_create_epub_bytes

    conversion_id = "scanned-math-image-id"
    pdf_bytes = make_dummy_pdf_bytes()
    await orch.start(
        conversion_id=conversion_id,
        filename="math-scan.pdf",
        file_size=len(pdf_bytes),
        ocr_enabled=True,
        pdf_bytes=pdf_bytes,
    )

    await asyncio.sleep(0.5)
    status = await orch.status(conversion_id)
    assert status.state == JobState.COMPLETED
