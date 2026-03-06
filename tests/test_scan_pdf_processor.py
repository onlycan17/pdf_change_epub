import pytest

from app.services.agent_service import AgentMessage, AgentType, OCRAgent, OCRResult, ScanPDFProcessor
from app.services.pdf_service import PDFType


@pytest.mark.asyncio
async def test_scan_pdf_processor_synthesis_handles_dataclass_ocr_result(
    sample_pdf_content: bytes,
    mock_pdf_analyzer,
    mock_pdf_extractor,
):
    processor = ScanPDFProcessor()
    processor.pdf_analyzer = mock_pdf_analyzer
    processor.pdf_extractor = mock_pdf_extractor

    processor.pdf_analyzer.analyze_pdf.return_value.pdf_type = PDFType.SCANNED

    processor.pdf_extractor.extract_images_from_pdf.return_value = [
        {"page": 1, "image_bytes": b"x"},
    ]

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
