"""GLM-OCR 엔진 어댑터.

설명:
- GLM-OCR VLM(0.9B)을 셀프호스팅 추론 서버(vLLM/SGLang)를 통해 사용합니다.
- BaseOCREngine 인터페이스를 구현하여 기존 파이프라인과 호환됩니다.
- 별도의 추론 서버가 실행 중이어야 합니다.
"""

from __future__ import annotations

import logging
import os
import tempfile
from typing import Any, Dict, List, Tuple

from PIL import Image

from app.services.ocr_engines import BaseOCREngine, OCREngineResult

logger = logging.getLogger(__name__)

# GLM-OCR bbox는 0-1000 정규화 좌표를 사용합니다.
_GLM_BBOX_SCALE = 1000


class GlmOCREngine(BaseOCREngine):
    """GLM-OCR 셀프호스팅 엔진 어댑터"""

    engine_name = "glm"

    def __init__(
        self,
        language: str,
        api_host: str = "localhost",
        api_port: int = 8080,
        layout_device: str = "cuda:0",
    ) -> None:
        self.language = language
        self.api_host = api_host
        self.api_port = api_port
        self.layout_device = layout_device
        self._parser: Any = None

    def validate(self) -> None:
        self._ensure_parser()

    def run(self, image: Image.Image) -> OCREngineResult:
        parser = self._ensure_parser()
        temp_path = _save_image_to_temp(image)
        try:
            pipeline_result = parser.parse(temp_path)
            return _build_engine_result(
                pipeline_result, image.width, image.height
            )
        finally:
            _cleanup_temp(temp_path)

    def _ensure_parser(self) -> Any:
        if self._parser is not None:
            return self._parser

        try:
            from glmocr import GlmOcr
        except ImportError as exc:
            raise ValueError(
                "glmocr 패키지가 설치되지 않았습니다. "
                "pip install 'glmocr[selfhosted]' 를 실행하세요."
            ) from exc

        self._parser = GlmOcr(
            mode="selfhosted",
            ocr_api_host=self.api_host,
            ocr_api_port=self.api_port,
            layout_device=self.layout_device,
        )
        return self._parser

    def __del__(self) -> None:
        if self._parser is not None:
            try:
                self._parser.close()
            except Exception:
                pass


def _save_image_to_temp(image: Image.Image) -> str:
    """PIL Image를 임시 PNG 파일로 저장합니다."""
    temp_fd, temp_path = tempfile.mkstemp(suffix=".png")
    os.close(temp_fd)
    image.save(temp_path, format="PNG")
    return temp_path


def _cleanup_temp(temp_path: str) -> None:
    """임시 파일을 안전하게 삭제합니다."""
    try:
        os.unlink(temp_path)
    except OSError:
        logger.debug("임시 파일 삭제 실패: %s", temp_path)


def _build_engine_result(
    pipeline_result: Any,
    image_width: int,
    image_height: int,
) -> OCREngineResult:
    """PipelineResult를 OCREngineResult로 변환합니다."""
    json_result = getattr(pipeline_result, "json_result", None) or []
    regions = _extract_first_page_regions(json_result)
    text, bounding_boxes, line_records = _parse_regions(
        regions, image_width, image_height
    )
    return OCREngineResult(
        text=text,
        confidence=0.95,
        bounding_boxes=bounding_boxes,
        line_records=line_records,
        page_width=image_width,
        engine="glm",
    )


def _extract_first_page_regions(
    json_result: List[List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """json_result에서 첫 페이지의 영역 목록을 추출합니다."""
    if not json_result or not isinstance(json_result, list):
        return []
    first_page = json_result[0]
    if not isinstance(first_page, list):
        return []
    return first_page


def _parse_regions(
    regions: List[Dict[str, Any]],
    image_width: int,
    image_height: int,
) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """영역 목록에서 text, bounding_boxes, line_records를 추출합니다."""
    texts: List[str] = []
    bounding_boxes: List[Dict[str, Any]] = []
    line_records: List[Dict[str, Any]] = []

    for region_index, region in enumerate(regions, start=1):
        content = str(region.get("content", "")).strip()
        if not content:
            continue

        texts.append(content)
        bbox_polygon, left, top, right, bottom = _convert_bbox(
            region.get("bbox_2d"), image_width, image_height
        )
        bounding_boxes.append(
            {"text": content, "bbox": bbox_polygon, "confidence": 0.95}
        )
        line_records.append(
            {
                "block_num": 1,
                "par_num": region_index,
                "line_num": region_index,
                "left": left,
                "top": top,
                "right": right,
                "width": max(right - left, 0),
                "height": max(bottom - top, 0),
                "text": content,
            }
        )

    full_text = "\n".join(texts)
    return full_text, bounding_boxes, line_records


def _convert_bbox(
    bbox_2d: Any,
    image_width: int,
    image_height: int,
) -> Tuple[List[List[int]], int, int, int, int]:
    """GLM 정규화 bbox [x1,y1,x2,y2]를 4-point polygon으로 변환합니다."""
    if not isinstance(bbox_2d, (list, tuple)) or len(bbox_2d) < 4:
        return [[0, 0], [0, 0], [0, 0], [0, 0]], 0, 0, 0, 0

    x1 = int(float(bbox_2d[0]) * image_width / _GLM_BBOX_SCALE)
    y1 = int(float(bbox_2d[1]) * image_height / _GLM_BBOX_SCALE)
    x2 = int(float(bbox_2d[2]) * image_width / _GLM_BBOX_SCALE)
    y2 = int(float(bbox_2d[3]) * image_height / _GLM_BBOX_SCALE)

    polygon = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
    return polygon, x1, y1, x2, y2
