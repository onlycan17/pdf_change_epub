import pytest
import logging
from types import MethodType

from app.services.agent_service import (
    AgentMessage,
    AgentType,
    MultimodalLLMAgent,
    OCRAgent,
    OCRResult,
    ScanPDFProcessor,
)
from app.services.pdf_service import PDFType


@pytest.mark.asyncio
async def test_scan_pdf_processor_synthesis_handles_dataclass_ocr_result(
    sample_pdf_content: bytes,
    mock_pdf_analyzer,
    mock_pdf_extractor,
):
    mock_pdf_analyzer.analyze_pdf.return_value.pdf_type = PDFType.SCANNED

    mock_pdf_extractor.extract_images_from_pdf.return_value = [
        {"page": 1, "image_bytes": b"x"},
    ]

    processor = ScanPDFProcessor()
    processor.pdf_analyzer = mock_pdf_analyzer
    processor.pdf_extractor = mock_pdf_extractor
    processor.multimodal_agent = None

    class FakeOCRAgent(OCRAgent):
        async def process(self, message: AgentMessage) -> AgentMessage:
            page_number = 1
            if isinstance(message.content, dict):
                page_number = int(message.content.get("page_number", 1) or 1)

            ocr_result = OCRResult(
                page_number=page_number,
                text="hello",
                confidence=0.5,
                bounding_boxes=[],
            )

            return AgentMessage(
                agent_type=AgentType.OCR,
                content=ocr_result,
                metadata={"language": "kor+eng"},
            )

    processor.ocr_agent = FakeOCRAgent(processor.settings)

    result = await processor.process_scanned_pdf(sample_pdf_content)

    assert isinstance(result.markdown_content, str)
    assert "hello" in result.markdown_content


@pytest.mark.asyncio
async def test_scan_pdf_processor_reports_incremental_progress(
    sample_pdf_content: bytes,
    mock_pdf_analyzer,
    mock_pdf_extractor,
):
    mock_pdf_analyzer.analyze_pdf.return_value.pdf_type = PDFType.SCANNED
    mock_pdf_extractor.extract_images_from_pdf.return_value = [
        {"page": 1, "image_bytes": b"x"},
        {"page": 2, "image_bytes": b"y"},
    ]

    progress_events = []

    async def on_progress(processed_tasks: int, total_tasks: int) -> None:
        progress_events.append((processed_tasks, total_tasks))

    processor = ScanPDFProcessor(progress_callback=on_progress)
    processor.pdf_analyzer = mock_pdf_analyzer
    processor.pdf_extractor = mock_pdf_extractor
    processor.multimodal_agent = None

    class FakeOCRAgent(OCRAgent):
        async def process(self, message: AgentMessage) -> AgentMessage:
            page_number = 1
            if isinstance(message.content, dict):
                page_number = int(message.content.get("page_number", 1) or 1)

            return AgentMessage(
                agent_type=AgentType.OCR,
                content=OCRResult(
                    page_number=page_number,
                    text=f"page-{page_number}",
                    confidence=0.5,
                    bounding_boxes=[],
                ),
                metadata={"language": "kor+eng"},
            )

    processor.ocr_agent = FakeOCRAgent(processor.settings)

    await processor.process_scanned_pdf(sample_pdf_content)

    assert progress_events == [(1, 2), (2, 2)]


@pytest.mark.asyncio
async def test_scan_pdf_processor_scopes_equation_markers_per_image() -> None:
    processor = ScanPDFProcessor()

    class FakeOCRAgent(OCRAgent):
        async def process(self, message: AgentMessage) -> AgentMessage:
            return AgentMessage(
                agent_type=AgentType.OCR,
                content=OCRResult(
                    page_number=1,
                    text="문장\n\n[[MATHIMG:eq-1]]",
                    confidence=0.5,
                    bounding_boxes=[],
                    equation_images=[
                        {
                            "marker": "[[MATHIMG:eq-1]]",
                            "image_bytes": b"img",
                            "format": "png",
                            "page_number": 1,
                            "alt_text": "x=1",
                        }
                    ],
                ),
                metadata={"language": "kor+eng"},
            )

    processor.ocr_agent = FakeOCRAgent(processor.settings)

    result = await processor._process_image_with_ocr(  # type: ignore[attr-defined]
        {
            "page": 1,
            "image_bytes": b"img",
            "_image_scope": "page-1-img-2",
        }
    )

    content = result["content"]
    assert content["text"] == "문장\n\n[[MATHIMG:page-1-img-2-eq-1]]"
    assert content["equation_images"][0]["marker"] == "[[MATHIMG:page-1-img-2-eq-1]]"


@pytest.mark.asyncio
async def test_multimodal_agent_uses_qwen_primary_by_default() -> None:
    agent = object.__new__(MultimodalLLMAgent)
    agent.model_name = "qwen/qwen3.5-flash-02-23"
    agent.fallback_model_name = "google/gemini-3.1-flash-lite-preview"
    agent.logger = logging.getLogger("test.multimodal.primary")

    seen_models = []

    async def fake_request_with_model(
        *,
        model_name: str,
        image_base64: str,
        context: str,
        image_mime_type: str,
    ):
        seen_models.append(model_name)
        assert image_mime_type == "image/png"
        return {
            "choices": [
                {"message": {"content": '{"description": "ok", "text_content": "ok"}'}}
            ],
            "usage": {"total_tokens": 10},
        }

    setattr(
        agent,
        "_request_analysis_with_model",
        MethodType(
            lambda self, **kwargs: fake_request_with_model(**kwargs),
            agent,
        ),
    )

    analysis, result, model_used, fallback_used = await agent._request_analysis(
        image_base64="ZmFrZQ==",
        context="",
        image_mime_type="image/png",
    )

    assert analysis == '{"description": "ok", "text_content": "ok"}'
    assert result["usage"]["total_tokens"] == 10
    assert model_used == "qwen/qwen3.5-flash-02-23"
    assert fallback_used is False
    assert seen_models == ["qwen/qwen3.5-flash-02-23"]


@pytest.mark.asyncio
async def test_multimodal_agent_falls_back_to_gemini_when_primary_fails() -> None:
    agent = object.__new__(MultimodalLLMAgent)
    agent.model_name = "qwen/qwen3.5-flash-02-23"
    agent.fallback_model_name = "google/gemini-3.1-flash-lite-preview"
    agent.logger = logging.getLogger("test.multimodal.fallback")

    seen_models = []

    async def fake_request_with_model(
        *,
        model_name: str,
        image_base64: str,
        context: str,
        image_mime_type: str,
    ):
        seen_models.append(model_name)
        assert image_mime_type == "image/webp"
        if model_name == "qwen/qwen3.5-flash-02-23":
            raise RuntimeError("primary failed")
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"description": "fallback", "text_content": "fallback"}'
                    }
                }
            ],
            "usage": {"total_tokens": 12},
        }

    setattr(
        agent,
        "_request_analysis_with_model",
        MethodType(
            lambda self, **kwargs: fake_request_with_model(**kwargs),
            agent,
        ),
    )

    analysis, result, model_used, fallback_used = await agent._request_analysis(
        image_base64="ZmFrZQ==",
        context="",
        image_mime_type="image/webp",
    )

    assert analysis == '{"description": "fallback", "text_content": "fallback"}'
    assert result["usage"]["total_tokens"] == 12
    assert model_used == "google/gemini-3.1-flash-lite-preview"
    assert fallback_used is True
    assert seen_models == [
        "qwen/qwen3.5-flash-02-23",
        "google/gemini-3.1-flash-lite-preview",
    ]


def test_ocr_agent_reconstructs_paragraphs_from_tesseract_layout() -> None:
    agent = OCRAgent()

    tesseract_data = {
        "text": [
            "첫째",
            "문단",
            "첫줄",
            "둘째",
            "줄",
            "둘째",
            "문단",
            "새줄",
        ],
        "block_num": [1, 1, 1, 1, 1, 1, 1, 1],
        "par_num": [1, 1, 1, 1, 1, 2, 2, 2],
        "line_num": [1, 1, 2, 2, 2, 1, 1, 2],
    }

    text = agent._reconstruct_ocr_text(tesseract_data, 8)  # type: ignore[attr-defined]

    assert text == "첫째 문단 첫줄 둘째 줄\n\n둘째 문단 새줄"


def test_ocr_agent_merges_hyphenated_line_breaks() -> None:
    agent = OCRAgent()

    merged = agent._merge_ocr_lines(["para-", "graph continues"])  # type: ignore[attr-defined]

    assert merged == "paragraph continues"


def test_ocr_agent_uses_block_boundaries_when_paragraph_numbers_missing() -> None:
    agent = OCRAgent()

    tesseract_data = {
        "text": ["첫", "문단", "둘째", "문단"],
        "block_num": [1, 1, 2, 2],
        "par_num": [0, 0, 0, 0],
        "line_num": [1, 1, 1, 1],
    }

    text = agent._reconstruct_ocr_text(tesseract_data, 4)  # type: ignore[attr-defined]

    assert text == "첫 문단\n\n둘째 문단"


def test_ocr_agent_collapses_to_single_paragraph_when_layout_is_degenerate() -> None:
    agent = OCRAgent()

    tesseract_data = {
        "text": ["문장", "하나", "문장", "둘"],
        "block_num": [0, 0, 0, 0],
        "par_num": [0, 0, 0, 0],
        "line_num": [0, 0, 0, 0],
    }

    text = agent._reconstruct_ocr_text(tesseract_data, 4)  # type: ignore[attr-defined]

    assert text == "문장 하나 문장 둘"


def test_scan_pdf_synthesis_preserves_paragraph_breaks() -> None:
    synthesis = ScanPDFProcessor().synthesis_agent

    combined = synthesis._combine_page_content(  # type: ignore[attr-defined]
        {
            "ocr_texts": [
                {"text": "첫 문단 첫 줄 둘째 줄\n\n둘째 문단 시작"},
                {"text": "셋째 문단"},
            ],
            "descriptions": [],
        }
    )

    assert combined == "첫 문단 첫 줄 둘째 줄\n\n둘째 문단 시작\n\n셋째 문단"


def test_ocr_agent_orders_two_column_paragraphs_left_to_right() -> None:
    agent = OCRAgent()

    tesseract_data = {
        "text": [
            "왼쪽",
            "첫문단",
            "오른쪽",
            "첫문단",
            "왼쪽",
            "둘째문단",
            "오른쪽",
            "둘째문단",
        ],
        "block_num": [1, 1, 2, 2, 3, 3, 4, 4],
        "par_num": [1, 1, 1, 1, 1, 1, 1, 1],
        "line_num": [1, 1, 1, 1, 1, 1, 1, 1],
        "left": [30, 90, 360, 430, 35, 105, 365, 435],
        "top": [20, 20, 25, 25, 220, 220, 230, 230],
        "width": [40, 90, 50, 95, 40, 100, 50, 100],
        "height": [18, 18, 18, 18, 18, 18, 18, 18],
    }

    text = agent._reconstruct_ocr_text(tesseract_data, 8)  # type: ignore[attr-defined]

    assert text == "왼쪽 첫문단\n\n왼쪽 둘째문단\n\n오른쪽 첫문단\n\n오른쪽 둘째문단"


def test_ocr_agent_marks_poetry_lines_for_preservation() -> None:
    agent = OCRAgent()

    tesseract_data = {
        "text": ["산길", "조용히", "걷는다", "달빛", "비친다", "마음", "머문다"],
        "block_num": [1, 1, 1, 1, 1, 1, 1],
        "par_num": [1, 1, 1, 1, 1, 1, 1],
        "line_num": [1, 1, 2, 2, 3, 4, 4],
        "left": [40, 95, 60, 120, 90, 130, 180],
        "top": [20, 20, 52, 52, 84, 116, 116],
        "width": [40, 70, 55, 70, 65, 50, 70],
        "height": [18, 18, 18, 18, 18, 18, 18],
    }

    text = agent._reconstruct_ocr_text(tesseract_data, 7)  # type: ignore[attr-defined]

    assert text.startswith("[[VERSE]]")
    assert "[[LINE:0]]산길 조용히" in text
    assert "[[/VERSE]]" in text


def test_ocr_agent_orders_sparse_two_column_layouts_without_interleaving() -> None:
    agent = OCRAgent()

    tesseract_data = {
        "text": ["왼쪽", "첫문단", "오른쪽", "문단", "왼쪽", "둘째문단"],
        "block_num": [1, 1, 2, 2, 3, 3],
        "par_num": [1, 1, 1, 1, 1, 1],
        "line_num": [1, 1, 1, 1, 1, 1],
        "left": [30, 90, 360, 430, 35, 105],
        "top": [20, 20, 30, 30, 220, 220],
        "width": [40, 90, 50, 80, 40, 100],
        "height": [18, 18, 18, 18, 18, 18],
    }

    text = agent._reconstruct_ocr_text(tesseract_data, 6)  # type: ignore[attr-defined]

    assert text == "왼쪽 첫문단\n\n왼쪽 둘째문단\n\n오른쪽 문단"


def test_ocr_agent_detects_equation_lines() -> None:
    agent = OCRAgent()

    assert agent._looks_like_equation_line("x^2 + y^2 = z^2") is True  # type: ignore[attr-defined]
    assert agent._looks_like_equation_line("이것은 일반 문장입니다") is False  # type: ignore[attr-defined]


def test_scan_pdf_synthesis_carries_equation_image_metadata() -> None:
    synthesis = ScanPDFProcessor().synthesis_agent

    grouped = synthesis._group_results_by_page(  # type: ignore[attr-defined]
        [
            {
                "page_number": 1,
                "agent_type": "ocr",
                "content": {
                    "text": "문장\n\n[[MATHIMG:page-1-eq-1]]",
                    "equation_images": [
                        {
                            "marker": "[[MATHIMG:page-1-eq-1]]",
                            "image_bytes": b"img",
                            "format": "png",
                            "page_number": 1,
                            "alt_text": "x^2 + y^2 = z^2",
                        }
                    ],
                },
            }
        ]
    )

    assert grouped[1]["equation_images"][0]["marker"] == "[[MATHIMG:page-1-eq-1]]"
