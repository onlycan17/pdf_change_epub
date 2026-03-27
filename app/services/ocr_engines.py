"""OCR 엔진 어댑터.

설명:
- 서로 다른 OCR 엔진의 출력을 공통 형식으로 맞춥니다.
- 기본 전략은 PaddleOCR 우선, Tesseract 폴백입니다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

from PIL import Image


@dataclass
class OCREngineResult:
    """엔진 공통 OCR 결과"""

    text: str
    confidence: float
    bounding_boxes: List[Dict[str, Any]]
    line_records: List[Dict[str, Any]]
    page_width: int
    engine: str


class BaseOCREngine(ABC):
    """OCR 엔진 인터페이스"""

    engine_name: str

    @abstractmethod
    def validate(self) -> None:
        """엔진 사용 가능 여부를 검증합니다."""

    @abstractmethod
    def run(self, image: Image.Image) -> OCREngineResult:
        """이미지에서 텍스트를 추출합니다."""


class TesseractOCREngine(BaseOCREngine):
    """Tesseract OCR 엔진 어댑터"""

    engine_name = "tesseract"

    def __init__(self, language: str) -> None:
        self.language = language

    def validate(self) -> None:
        import pytesseract

        _ = pytesseract.get_tesseract_version()
        langs = set(pytesseract.get_languages(config=""))
        required = [part for part in self.language.split("+") if part]
        missing = [part for part in required if part not in langs]
        if missing:
            available = ", ".join(sorted(langs))
            raise ValueError(
                "Tesseract language data missing: "
                f"{', '.join(missing)} (available: {available})"
            )

    def run(self, image: Image.Image) -> OCREngineResult:
        import pytesseract

        data = pytesseract.image_to_data(
            image,
            lang=self.language,
            output_type=pytesseract.Output.DICT,
        )
        count = int(data.get("level") and len(data["level"]) or 0)
        bounding_boxes: List[Dict[str, Any]] = []
        confidences: List[float] = []

        for index in range(count):
            text = str(data.get("text", [""] * count)[index]).strip()
            if not text:
                continue

            conf_raw = str(data.get("conf", ["-1"] * count)[index]).strip()
            try:
                conf = float(conf_raw)
            except ValueError:
                conf = -1.0

            left = _parse_index(data, "left", index, count)
            top = _parse_index(data, "top", index, count)
            width = _parse_index(data, "width", index, count)
            height = _parse_index(data, "height", index, count)
            bbox = [
                [left, top],
                [left + width, top],
                [left + width, top + height],
                [left, top + height],
            ]

            if conf >= 0:
                confidences.append(conf)

            bounding_boxes.append(
                {
                    "text": text,
                    "bbox": bbox,
                    "confidence": max(conf, 0.0) / 100.0 if conf >= 0 else 0.0,
                }
            )

        line_records = _build_tesseract_line_records(data, count)
        page_width = max((record.get("right", 0) for record in line_records), default=0)
        avg_confidence = (
            (sum(confidences) / len(confidences)) / 100.0 if confidences else 0.0
        )
        text = "\n".join(
            str(record.get("text", "")).strip()
            for record in line_records
            if str(record.get("text", "")).strip()
        )

        return OCREngineResult(
            text=text,
            confidence=avg_confidence,
            bounding_boxes=bounding_boxes,
            line_records=line_records,
            page_width=page_width,
            engine=self.engine_name,
        )


class PaddleOCREngine(BaseOCREngine):
    """PaddleOCR 엔진 어댑터"""

    engine_name = "paddle"

    def __init__(self, language: str) -> None:
        self.language = language
        self._ocr_instance: Any | None = None

    def validate(self) -> None:
        self._ensure_instance()

    def run(self, image: Image.Image) -> OCREngineResult:
        ocr = self._ensure_instance()
        result = ocr.ocr(image, cls=True)
        entries = _flatten_paddle_result(result)

        line_records: List[Dict[str, Any]] = []
        bounding_boxes: List[Dict[str, Any]] = []
        confidences: List[float] = []

        for index, entry in enumerate(entries, start=1):
            bbox = entry.get("bbox")
            text = str(entry.get("text", "")).strip()
            confidence = float(entry.get("confidence", 0.0) or 0.0)
            if not bbox or not text:
                continue

            left = min(int(point[0]) for point in bbox)
            top = min(int(point[1]) for point in bbox)
            right = max(int(point[0]) for point in bbox)
            bottom = max(int(point[1]) for point in bbox)
            width = max(right - left, 0)
            height = max(bottom - top, 0)

            confidences.append(confidence)
            bounding_boxes.append(
                {
                    "text": text,
                    "bbox": bbox,
                    "confidence": max(min(confidence, 1.0), 0.0),
                }
            )
            line_records.append(
                {
                    "block_num": 1,
                    "par_num": 0,
                    "line_num": index,
                    "left": left,
                    "top": top,
                    "right": right,
                    "width": width,
                    "height": height,
                    "text": text,
                }
            )

        line_records.sort(key=lambda item: (int(item["top"]), int(item["left"])))
        _assign_paddle_paragraph_numbers(line_records)
        page_width = max((record.get("right", 0) for record in line_records), default=0)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        text = "\n".join(
            str(record.get("text", "")).strip()
            for record in line_records
            if str(record.get("text", "")).strip()
        )

        return OCREngineResult(
            text=text,
            confidence=avg_confidence,
            bounding_boxes=bounding_boxes,
            line_records=line_records,
            page_width=page_width,
            engine=self.engine_name,
        )

    def _ensure_instance(self) -> Any:
        if self._ocr_instance is not None:
            return self._ocr_instance

        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise ValueError("PaddleOCR import failed") from exc

        language_map = {
            "kor+eng": "korean",
            "kor": "korean",
            "ko": "korean",
            "eng": "en",
            "en": "en",
        }
        lang = language_map.get(self.language.lower(), "korean")
        self._ocr_instance = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
        return self._ocr_instance


def create_ocr_engine(engine_name: str, language: str) -> BaseOCREngine:
    normalized = engine_name.strip().lower()
    if normalized == "paddle":
        return PaddleOCREngine(language)
    if normalized == "tesseract":
        return TesseractOCREngine(language)
    if normalized == "glm":
        from app.services.glm_ocr_engine import GlmOCREngine

        return GlmOCREngine(language)
    raise ValueError(f"Unsupported OCR engine: {engine_name}")


def _parse_index(
    data: Dict[str, Sequence[Any]],
    field: str,
    index: int,
    count: int,
) -> int:
    values = data.get(field, [0] * count)
    try:
        return int(float(values[index]))
    except (TypeError, ValueError, IndexError):
        return 0


def _build_tesseract_line_records(
    data: Dict[str, Sequence[Any]],
    count: int,
) -> List[Dict[str, Any]]:
    tokens: List[Dict[str, Any]] = []
    for index in range(count):
        text_values = data.get("text", [""] * count)
        try:
            text = str(text_values[index]).strip()
        except IndexError:
            text = ""
        if not text:
            continue

        left = _parse_index(data, "left", index, count)
        top = _parse_index(data, "top", index, count)
        width = _parse_index(data, "width", index, count)
        height = _parse_index(data, "height", index, count)
        tokens.append(
            {
                "text": text,
                "block_num": _parse_index(data, "block_num", index, count),
                "par_num": _parse_index(data, "par_num", index, count),
                "line_num": _parse_index(data, "line_num", index, count),
                "left": left,
                "top": top,
                "width": width,
                "height": height,
                "right": left + width,
            }
        )

    grouped: Dict[tuple[int, int, int], List[Dict[str, Any]]] = {}
    for token in tokens:
        key = (
            int(token.get("block_num", 0)),
            int(token.get("par_num", 0)),
            int(token.get("line_num", 0)),
        )
        grouped.setdefault(key, []).append(token)

    lines: List[Dict[str, Any]] = []
    for key, members in grouped.items():
        members.sort(key=lambda item: (int(item["left"]), int(item["top"])))
        left = min(int(item["left"]) for item in members)
        top = min(int(item["top"]) for item in members)
        right = max(int(item["right"]) for item in members)
        height = max(int(item["height"]) for item in members)
        lines.append(
            {
                "block_num": key[0],
                "par_num": key[1],
                "line_num": key[2],
                "left": left,
                "top": top,
                "right": right,
                "width": max(right - left, 0),
                "height": height,
                "text": " ".join(
                    str(item.get("text", "")).strip()
                    for item in members
                    if str(item.get("text", "")).strip()
                ).strip(),
            }
        )

    lines.sort(key=lambda item: (int(item["top"]), int(item["left"])))
    return lines


def _flatten_paddle_result(result: Any) -> List[Dict[str, Any]]:
    flattened: List[Dict[str, Any]] = []
    if not isinstance(result, list):
        return flattened

    for page in result:
        if not isinstance(page, list):
            continue
        for entry in page:
            if not isinstance(entry, (list, tuple)) or len(entry) < 2:
                continue
            bbox_raw, text_info = entry[0], entry[1]
            if not isinstance(bbox_raw, (list, tuple)) or not isinstance(
                text_info, (list, tuple)
            ):
                continue
            if len(text_info) < 2:
                continue
            text = str(text_info[0]).strip()
            confidence = float(text_info[1] or 0.0)
            bbox = [
                [int(float(point[0])), int(float(point[1]))]
                for point in bbox_raw
                if isinstance(point, (list, tuple)) and len(point) >= 2
            ]
            if len(bbox) != 4 or not text:
                continue
            flattened.append(
                {
                    "bbox": bbox,
                    "text": text,
                    "confidence": confidence,
                }
            )

    return flattened


def _assign_paddle_paragraph_numbers(line_records: List[Dict[str, Any]]) -> None:
    if not line_records:
        return

    average_height = sum(
        max(int(record.get("height", 0)), 1) for record in line_records
    ) / len(line_records)
    paragraph_index = 1
    previous_bottom: int | None = None

    for line_index, record in enumerate(line_records, start=1):
        top = int(record.get("top", 0))
        height = max(int(record.get("height", 0)), 1)
        bottom = top + height
        if previous_bottom is not None:
            gap = top - previous_bottom
            if gap > average_height * 1.2:
                paragraph_index += 1
        record["par_num"] = paragraph_index
        record["line_num"] = line_index
        previous_bottom = bottom
