"""GLM-OCR 엔진 어댑터 단위 테스트.

모든 테스트는 glmocr 모듈을 mock하여 GPU 없이 실행 가능합니다.
"""

import os
from dataclasses import dataclass
from typing import Any, List
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from app.services.glm_ocr_engine import (
    GlmOCREngine,
    _build_engine_result,
    _convert_bbox,
    _extract_first_page_regions,
    _parse_regions,
)
from app.services.ocr_engines import OCREngineResult, create_ocr_engine


def test_engine_name_is_glm():
    engine = GlmOCREngine(language="ko")
    assert engine.engine_name == "glm"


def test_validate_import_error_raises():
    engine = GlmOCREngine(language="ko")
    with patch.dict("sys.modules", {"glmocr": None}):
        with pytest.raises(ValueError, match="glmocr 패키지"):
            engine.validate()


def test_validate_success_with_mock():
    mock_glmocr = MagicMock()
    mock_parser_instance = MagicMock()
    mock_glmocr.GlmOcr.return_value = mock_parser_instance

    with patch.dict("sys.modules", {"glmocr": mock_glmocr}):
        engine = GlmOCREngine(language="ko")
        engine.validate()
        assert engine._parser is mock_parser_instance


@dataclass
class FakePipelineResult:
    """테스트용 PipelineResult 모방"""

    json_result: List[List[dict]]
    markdown_result: str = ""


def _make_sample_regions() -> List[List[dict]]:
    return [
        [
            {
                "index": 0,
                "label": "text",
                "content": "안녕하세요",
                "bbox_2d": [100, 200, 500, 300],
            },
            {
                "index": 1,
                "label": "text",
                "content": "GLM-OCR 테스트",
                "bbox_2d": [100, 400, 600, 500],
            },
        ]
    ]


def test_run_returns_ocr_engine_result():
    sample_regions = _make_sample_regions()
    fake_result = FakePipelineResult(json_result=sample_regions)

    mock_parser = MagicMock()
    mock_parser.parse.return_value = fake_result

    engine = GlmOCREngine(language="ko")
    engine._parser = mock_parser

    test_image = Image.new("RGB", (1000, 800), color="white")
    result = engine.run(test_image)

    assert isinstance(result, OCREngineResult)
    assert result.engine == "glm"
    assert "안녕하세요" in result.text
    assert "GLM-OCR 테스트" in result.text
    assert result.confidence == 0.95
    assert result.page_width == 1000
    assert len(result.bounding_boxes) == 2
    assert len(result.line_records) == 2


def test_run_cleans_temp_file():
    """run() 실행 후 임시 파일이 삭제되는지 확인합니다."""
    created_paths: list[str] = []

    original_save = Image.Image.save

    def tracking_save(self: Any, fp: Any, *args: Any, **kwargs: Any) -> None:
        if isinstance(fp, str) and fp.endswith(".png"):
            created_paths.append(fp)
        return original_save(self, fp, *args, **kwargs)

    mock_parser = MagicMock()
    mock_parser.parse.return_value = FakePipelineResult(json_result=[[]])

    engine = GlmOCREngine(language="ko")
    engine._parser = mock_parser

    test_image = Image.new("RGB", (100, 100), color="white")

    with patch.object(Image.Image, "save", tracking_save):
        engine.run(test_image)

    for temp_path in created_paths:
        assert not os.path.exists(temp_path), f"임시 파일이 삭제되지 않음: {temp_path}"


def test_run_cleans_temp_file_on_exception():
    """예외 발생 시에도 임시 파일이 삭제되는지 확인합니다."""
    mock_parser = MagicMock()
    mock_parser.parse.side_effect = RuntimeError("서버 연결 실패")

    engine = GlmOCREngine(language="ko")
    engine._parser = mock_parser

    test_image = Image.new("RGB", (100, 100), color="white")

    with pytest.raises(RuntimeError, match="서버 연결 실패"):
        engine.run(test_image)


def test_convert_bbox_normalized_to_pixels():
    polygon, left, top, right, bottom = _convert_bbox(
        [100, 200, 500, 600], image_width=1000, image_height=800
    )
    assert left == 100
    assert top == 160
    assert right == 500
    assert bottom == 480
    assert polygon == [[100, 160], [500, 160], [500, 480], [100, 480]]


def test_convert_bbox_none_returns_zero():
    polygon, left, top, right, bottom = _convert_bbox(
        None, image_width=1000, image_height=800
    )
    assert polygon == [[0, 0], [0, 0], [0, 0], [0, 0]]
    assert left == 0 and top == 0 and right == 0 and bottom == 0


def test_extract_first_page_regions_empty():
    assert _extract_first_page_regions([]) == []
    assert _extract_first_page_regions(None) == []


def test_extract_first_page_regions_valid():
    regions = _make_sample_regions()
    result = _extract_first_page_regions(regions)
    assert len(result) == 2
    assert result[0]["content"] == "안녕하세요"


def test_parse_regions_builds_line_records():
    regions = [
        {"content": "첫 번째 줄", "bbox_2d": [0, 0, 500, 100]},
        {"content": "두 번째 줄", "bbox_2d": [0, 200, 500, 300]},
    ]
    text, boxes, lines = _parse_regions(regions, 1000, 1000)
    assert text == "첫 번째 줄\n두 번째 줄"
    assert len(boxes) == 2
    assert len(lines) == 2
    assert lines[0]["par_num"] == 1
    assert lines[1]["par_num"] == 2


def test_parse_regions_skips_empty_content():
    regions = [
        {"content": "", "bbox_2d": [0, 0, 100, 100]},
        {"content": "유효한 텍스트", "bbox_2d": [0, 200, 500, 300]},
    ]
    text, boxes, lines = _parse_regions(regions, 1000, 1000)
    assert text == "유효한 텍스트"
    assert len(boxes) == 1


def test_build_engine_result_from_pipeline():
    fake_result = FakePipelineResult(json_result=_make_sample_regions())
    result = _build_engine_result(fake_result, 1000, 800)

    assert isinstance(result, OCREngineResult)
    assert result.engine == "glm"
    assert result.page_width == 1000
    assert result.confidence == 0.95
    assert "안녕하세요" in result.text


def test_factory_creates_glm_engine():
    mock_glmocr = MagicMock()
    with patch.dict("sys.modules", {"glmocr": mock_glmocr}):
        engine = create_ocr_engine("glm", "ko")
        assert isinstance(engine, GlmOCREngine)
        assert engine.engine_name == "glm"


def test_factory_creates_glm_engine_case_insensitive():
    mock_glmocr = MagicMock()
    with patch.dict("sys.modules", {"glmocr": mock_glmocr}):
        engine = create_ocr_engine("GLM", "ko")
        assert isinstance(engine, GlmOCREngine)


def test_glm_engine_default_settings():
    engine = GlmOCREngine(language="ko")
    assert engine.api_host == "localhost"
    assert engine.api_port == 8080
    assert engine.layout_device == "cuda:0"


def test_glm_engine_custom_settings():
    engine = GlmOCREngine(
        language="kor+eng",
        api_host="192.168.1.100",
        api_port=9090,
        layout_device="cuda:1",
    )
    assert engine.api_host == "192.168.1.100"
    assert engine.api_port == 9090
    assert engine.layout_device == "cuda:1"
