"""에이전트 기반 스캔 PDF 처리 서비스"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import os
import re
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional
from enum import Enum

import httpx
from PIL import Image

from app.core.config import Settings, get_settings
from app.services.ocr_engines import BaseOCREngine, create_ocr_engine
from app.services.pdf_service import PDFAnalyzer, PDFExtractor, PDFType

logger = logging.getLogger(__name__)


def _format_exception_message(exc: Exception) -> str:
    detail = str(exc).strip()
    if detail:
        return f"{type(exc).__name__}: {detail}"
    return repr(exc)


class AgentType(Enum):
    """에이전트 유형 정의"""

    MULTIMODAL_LLM = "multimodal_llm"
    OCR = "ocr"
    SYNTHESIS = "synthesis"


@dataclass
class AgentMessage:
    """에이전트 간 메시지"""

    agent_type: AgentType
    content: Any
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None


@dataclass
class ImageAnalysisResult:
    """이미지 분석 결과"""

    page_number: int
    image_description: str
    text_content: str
    confidence: float
    layout_info: Optional[Dict[str, Any]] = None
    equations_latex: Optional[List[str]] = None


@dataclass
class OCRResult:
    """OCR 처리 결과"""

    page_number: int
    text: str
    confidence: float
    bounding_boxes: Optional[List[Dict[str, Any]]] = None
    equation_images: Optional[List[Dict[str, Any]]] = None
    engine: Optional[str] = None
    llm_corrected: bool = False


@dataclass
class SynthesisResult:
    """결과 종합 결과"""

    markdown_content: str
    metadata: Dict[str, Any]
    processing_stats: Dict[str, Any]


class BaseAgent(ABC):
    """기본 에이전트 추상 클래스"""

    def __init__(self, agent_type: AgentType, settings: Optional[Settings] = None):
        self.agent_type = agent_type
        self.settings = settings or get_settings()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def process(self, message: AgentMessage) -> AgentMessage:
        """메시지 처리"""
        pass

    @abstractmethod
    async def validate(self) -> bool:
        """에이전트 유효성 검증"""
        pass


class MultimodalLLMAgent(BaseAgent):
    """OpenRouter 연동 멀티모달 LLM 에이전트"""

    def __init__(self, settings: Optional[Settings] = None):
        super().__init__(AgentType.MULTIMODAL_LLM, settings)
        self.api_key = (
            self.settings.llm.api_key
            or self.settings.openrouter_api_key
            or os.getenv("OPENROUTER_API_KEY")
            or self.settings.deepseek_api_key
            or self.settings.openai_api_key
        )
        self.base_url = self.settings.llm.base_url
        self.model_name = self.settings.llm.multimodal_primary_model
        self.fallback_model_name = self.settings.llm.multimodal_fallback_model
        self.max_tokens = self.settings.llm.max_tokens
        self.temperature = self.settings.llm.temperature
        self.timeout = self.settings.llm.timeout

        if not self.api_key:
            raise ValueError("OpenRouter API 키가 설정되지 않았습니다.")

    async def validate(self) -> bool:
        """API 연결 및 모델 유효성 검증"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/auth/key",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return response.status_code == 200
        except Exception as e:
            self.logger.error(f"OpenRouter API 검증 실패: {str(e)}")
            return False

    async def process(self, message: AgentMessage) -> AgentMessage:
        """이미지 분석 및 설명 생성"""
        try:
            if not isinstance(message.content, dict):
                raise ValueError("이미지 데이터가 필요합니다.")

            image_data = message.content.get("image_bytes")
            page_number = message.content.get("page_number", 1)
            context = message.content.get("context", "")
            image_format = str(message.content.get("image_format", "jpeg")).lower()

            if not image_data:
                raise ValueError("이미지 데이터가 없습니다.")

            # 이미지 인코딩
            image_base64 = base64.b64encode(image_data).decode()
            image_mime_type = self._resolve_image_mime_type(image_format)

            analysis, result, model_used, fallback_used = await self._request_analysis(
                image_base64=image_base64,
                context=context,
                image_mime_type=image_mime_type,
            )

            # 결과 파싱 및 구조화
            structured_result = self._parse_analysis_result(analysis, page_number)

            return AgentMessage(
                agent_type=self.agent_type,
                content=structured_result,
                metadata={
                    "model": model_used,
                    "fallback_used": fallback_used,
                    "tokens_used": result.get("usage", {}).get("total_tokens", 0),
                    "processing_time": message.timestamp,
                },
            )

        except Exception as e:
            error_detail = _format_exception_message(e)
            self.logger.exception("이미지 분석 실패: %s", error_detail)
            raise ValueError(f"이미지 분석 중 오류 발생: {error_detail}") from e

    async def correct_ocr_text(
        self,
        *,
        image_bytes: bytes,
        ocr_text: str,
        image_format: str = "jpeg",
    ) -> tuple[str, str, bool]:
        """저신뢰 OCR 결과를 이미지와 함께 다시 보정합니다."""
        if not ocr_text.strip():
            return "", "", False

        image_base64 = base64.b64encode(image_bytes).decode()
        image_mime_type = self._resolve_image_mime_type(image_format)
        corrected, _result, model_used, fallback_used = (
            await self._request_ocr_correction(
                image_base64=image_base64,
                image_mime_type=image_mime_type,
                ocr_text=ocr_text,
            )
        )
        return corrected, model_used, fallback_used

    async def _request_analysis(
        self, *, image_base64: str, context: str, image_mime_type: str
    ) -> tuple[str, Dict[str, Any], str, bool]:
        errors: List[str] = []
        tried_models: List[str] = []

        for model_name in [self.model_name, self.fallback_model_name]:
            if not model_name:
                continue

            tried_models.append(model_name)
            try:
                self.logger.info(
                    "이미지 분석 모델 호출 시도", extra={"model": model_name}
                )
                result = await self._request_analysis_with_model(
                    model_name=model_name,
                    image_base64=image_base64,
                    context=context,
                    image_mime_type=image_mime_type,
                )
                analysis = str(result["choices"][0]["message"]["content"])
                if not analysis.strip():
                    raise ValueError("empty response")
                fallback_used = (
                    model_name == self.fallback_model_name
                    and len(tried_models) > 1
                    and bool(self.fallback_model_name)
                )
                return analysis, result, model_name, fallback_used
            except Exception as exc:
                self.logger.warning(
                    "이미지 분석 모델 호출 실패",
                    extra={"model": model_name, "error": str(exc)},
                )
                errors.append(f"{model_name}: {_format_exception_message(exc)}")

        raise RuntimeError(" / ".join(errors) or "all multimodal models failed")

    async def _request_ocr_correction(
        self,
        *,
        image_base64: str,
        image_mime_type: str,
        ocr_text: str,
    ) -> tuple[str, Dict[str, Any], str, bool]:
        errors: List[str] = []
        tried_models: List[str] = []

        for model_name in [self.model_name, self.fallback_model_name]:
            if not model_name:
                continue

            tried_models.append(model_name)
            try:
                result = await self._request_multimodal_prompt_with_model(
                    model_name=model_name,
                    prompt=self._build_ocr_correction_prompt(ocr_text),
                    image_base64=image_base64,
                    image_mime_type=image_mime_type,
                )
                corrected = self._strip_markdown_fence(
                    str(result["choices"][0]["message"]["content"])
                )
                if not corrected.strip():
                    raise ValueError("empty response")
                fallback_used = (
                    model_name == self.fallback_model_name
                    and len(tried_models) > 1
                    and bool(self.fallback_model_name)
                )
                return corrected, result, model_name, fallback_used
            except Exception as exc:
                errors.append(f"{model_name}: {_format_exception_message(exc)}")

        raise RuntimeError(" / ".join(errors) or "all multimodal models failed")

    async def _request_analysis_with_model(
        self,
        *,
        model_name: str,
        image_base64: str,
        context: str,
        image_mime_type: str,
    ) -> Dict[str, Any]:
        return await self._request_multimodal_prompt_with_model(
            model_name=model_name,
            prompt=self._build_prompt(context),
            image_base64=image_base64,
            image_mime_type=image_mime_type,
        )

    async def _request_multimodal_prompt_with_model(
        self,
        *,
        model_name: str,
        prompt: str,
        image_base64: str,
        image_mime_type: str,
    ) -> Dict[str, Any]:
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_mime_type};base64,{image_base64}"
                            },
                        },
                    ],
                }
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://pdf-to-epub-converter.com",
                    "X-Title": "PDF to EPUB Converter",
                },
                json=payload,
            )

        if response.status_code != 200:
            raise ValueError(f"OpenRouter API 오류: {response.status_code}")

        return response.json()

    def _resolve_image_mime_type(self, image_format: str) -> str:
        mapping = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
            "gif": "image/gif",
            "bmp": "image/bmp",
        }
        return mapping.get(image_format.lower(), "image/jpeg")

    def _build_prompt(self, context: str) -> str:
        """분석 프롬프트 생성"""
        base_prompt = """다음 이미지를 분석하여 문서 변환에 필요한 정보를 추출해주세요.

다음 항목들을 JSON 형식으로 반환해주세요:
{
  "description": "이미지의 전체적인 설명 (상황, 인물, 배경 등)",
  "text_content": "이미지에서 인식된 모든 텍스트",
  "equations_latex": ["이미지에서 감지된 수식을 LaTeX로 보존한 목록. 없으면 []"],
  "layout_analysis": {
    "has_title": true/false,
    "has_header": true/false,
    "has_footer": true/false,
    "columns": 1,
    "reading_order": "left_to_right" 또는 "right_to_left"
  },
  "content_type": "text" 또는 "table" 또는 "image" 또는 "mixed",
  "confidence": 0.0-1.0
}

이미지를 분석할 때 다음 사항을 고려해주세요:
1. 텍스트는 정확하게 추출
2. 수식이 있으면 가능한 한 LaTeX 형태로 정확히 보존하고 equations_latex 배열에 각 수식을 개별 항목으로 넣기
3. 레이아웃 구조 파악
4. 표나 다이어그램의 존재 여부
5. 문서의 목적과 맥락 이해
6. 한국어와 영어 모두 지원

"""

        if context:
            base_prompt += f"\n추가 맥락: {context}"

        return base_prompt

    def _build_ocr_correction_prompt(self, ocr_text: str) -> str:
        return f"""아래 이미지를 보고 OCR 원문에서 잘못 읽힌 부분만 바로잡아 주세요.

[원칙]
- 의미를 새로 추측해 덧붙이지 마세요.
- 이미지에서 확인되는 텍스트만 반영하세요.
- 제목, 문단, 줄바꿈은 가능한 한 유지하세요.
- 확실하지 않은 부분은 원문을 유지하세요.
- 출력은 보정된 본문만 반환하세요.

[OCR 원문]
{ocr_text}
"""

    def _strip_markdown_fence(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if "\n" in cleaned:
                cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    def _parse_analysis_result(
        self, raw_result: str, page_number: int
    ) -> ImageAnalysisResult:
        """API 결과 파싱"""
        try:
            # JSON 추출 시도
            start_idx = raw_result.find("{")
            end_idx = raw_result.rfind("}") + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = raw_result[start_idx:end_idx]
                parsed = json.loads(json_str)
            else:
                # JSON 형식이 아닌 경우 기본 구조 생성
                parsed = {
                    "description": raw_result,
                    "text_content": raw_result,
                    "layout_analysis": {"has_title": False, "columns": 1},
                    "content_type": "text",
                    "confidence": 0.7,
                }

            return ImageAnalysisResult(
                page_number=page_number,
                image_description=parsed.get("description", raw_result),
                text_content=parsed.get("text_content", raw_result),
                confidence=parsed.get("confidence", 0.7),
                layout_info=parsed.get("layout_analysis", {}),
                equations_latex=[
                    str(item).strip()
                    for item in parsed.get("equations_latex", [])
                    if str(item).strip()
                ],
            )

        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON 파싱 실패, 기본 구조 사용: {str(e)}")
            return ImageAnalysisResult(
                page_number=page_number,
                image_description=raw_result,
                text_content=raw_result,
                confidence=0.5,
                layout_info={},
                equations_latex=[],
            )


class OCRAgent(BaseAgent):
    """OCR 엔진 선택 및 실행 에이전트"""

    def __init__(self, settings: Optional[Settings] = None):
        super().__init__(AgentType.OCR, settings)
        self.language = self.settings.ocr_language
        self.primary_engine_name = self.settings.ocr.engine
        self.fallback_engine_name = self.settings.ocr.fallback_engine
        self.ocr_engine: BaseOCREngine | None = None

    async def validate(self) -> bool:
        """OCR 엔진 초기화 및 검증"""
        self.ocr_engine = self._resolve_engine()
        return True

    async def process(self, message: AgentMessage) -> AgentMessage:
        """이미지에서 텍스트 추출"""
        try:
            if not isinstance(message.content, dict):
                raise ValueError("이미지 데이터가 필요합니다.")

            image_data = message.content.get("image_bytes")
            page_number = message.content.get("page_number", 1)

            if not image_data:
                raise ValueError("이미지 데이터가 없습니다.")

            if not self.ocr_engine:
                await self.validate()

            # OCR 처리
            result = await self._run_ocr(image_data)

            # 결과 구조화
            ocr_result = OCRResult(
                page_number=page_number,
                text=result.get("text", ""),
                confidence=result.get("confidence", 0.0),
                bounding_boxes=result.get("bounding_boxes", []),
                equation_images=result.get("equation_images", []),
                engine=result.get("engine"),
            )

            return AgentMessage(
                agent_type=self.agent_type,
                content=ocr_result,
                metadata={
                    "language": self.language,
                    "engine": result.get("engine"),
                    "processing_time": message.timestamp,
                },
            )

        except Exception as e:
            error_detail = _format_exception_message(e)
            self.logger.exception("OCR 처리 실패: %s", error_detail)
            raise ValueError(f"OCR 처리 중 오류 발생: {error_detail}") from e

    async def _run_ocr(self, image_data: bytes) -> Dict[str, Any]:
        """OCR 실행"""
        import io
        from PIL import Image

        try:
            image = Image.open(io.BytesIO(image_data))
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._run_ocr_sync, image)

        except Exception as e:
            self.logger.exception("OCR 실행 실패: %s", _format_exception_message(e))
            return {
                "text": "",
                "confidence": 0.0,
                "bounding_boxes": [],
                "equation_images": [],
                "engine": self.ocr_engine.engine_name if self.ocr_engine else None,
            }

    def _run_ocr_sync(self, image: Image.Image) -> Dict[str, Any]:
        engine = self.ocr_engine or self._resolve_engine()
        self.ocr_engine = engine
        engine_result = engine.run(image)
        paragraph_records = self._build_ocr_paragraph_records(
            engine_result.line_records
        )
        equation_images = self._extract_equation_images(
            image, engine_result.line_records
        )
        marker_by_line = {
            image_info["line_key"]: image_info["marker"]
            for image_info in equation_images
            if isinstance(image_info.get("line_key"), tuple)
            and isinstance(image_info.get("marker"), str)
        }
        rendered_text = self._render_ocr_document(
            paragraph_records,
            engine_result.page_width,
            marker_by_line=marker_by_line,
        )
        return {
            "text": rendered_text or engine_result.text,
            "confidence": engine_result.confidence,
            "bounding_boxes": engine_result.bounding_boxes,
            "equation_images": [
                {
                    "marker": image_info["marker"],
                    "image_bytes": image_info["image_bytes"],
                    "format": image_info["format"],
                    "page_number": image_info["page_number"],
                    "alt_text": image_info["alt_text"],
                }
                for image_info in equation_images
            ],
            "engine": engine_result.engine,
        }

    def _resolve_engine(self) -> BaseOCREngine:
        errors: List[str] = []
        for engine_name in [self.primary_engine_name, self.fallback_engine_name]:
            if not engine_name:
                continue
            try:
                engine = create_ocr_engine(engine_name, self.language)
                engine.validate()
                if engine_name != self.primary_engine_name:
                    self.logger.warning(
                        "기본 OCR 엔진을 사용할 수 없어 폴백 엔진으로 전환합니다.",
                        extra={
                            "primary_engine": self.primary_engine_name,
                            "fallback_engine": engine_name,
                        },
                    )
                return engine
            except Exception as exc:
                errors.append(f"{engine_name}: {_format_exception_message(exc)}")

        raise ValueError(" / ".join(errors) or "No OCR engine available")

    def _reconstruct_ocr_text(self, data: Dict[str, Any], count: int) -> str:
        document = self._build_ocr_document(data, count)
        return self._render_ocr_document(
            document["paragraph_records"],
            document["page_width"],
        )

    def _build_ocr_document(self, data: Dict[str, Any], count: int) -> Dict[str, Any]:
        tokens = self._build_ocr_tokens(data, count)
        if not tokens:
            return {"page_width": 0, "line_records": [], "paragraph_records": []}

        page_width = max((token["right"] for token in tokens), default=0)
        line_records = self._build_ocr_line_records(tokens)
        paragraph_records = self._build_ocr_paragraph_records(line_records)
        return {
            "page_width": page_width,
            "line_records": line_records,
            "paragraph_records": paragraph_records,
        }

    def _build_ocr_tokens(
        self, data: Dict[str, Any], count: int
    ) -> List[Dict[str, Any]]:
        tokens: List[Dict[str, Any]] = []

        def parse_index(field: str, index: int) -> int:
            values = data.get(field, [0] * count)
            try:
                return int(float(values[index]))
            except (TypeError, ValueError, IndexError):
                return 0

        for index in range(count):
            text_values = data.get("text", [""] * count)
            try:
                text = str(text_values[index]).strip()
            except IndexError:
                text = ""
            if not text:
                continue

            left = parse_index("left", index)
            top = parse_index("top", index)
            width = parse_index("width", index)
            height = parse_index("height", index)
            tokens.append(
                {
                    "text": text,
                    "block_num": parse_index("block_num", index),
                    "par_num": parse_index("par_num", index),
                    "line_num": parse_index("line_num", index),
                    "left": left,
                    "top": top,
                    "width": width,
                    "height": height,
                    "right": left + width,
                }
            )

        return tokens

    def _build_ocr_line_records(
        self, tokens: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
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
            members.sort(
                key=lambda item: (int(item.get("left", 0)), int(item.get("top", 0)))
            )
            left = min(int(item.get("left", 0)) for item in members)
            top = min(int(item.get("top", 0)) for item in members)
            right = max(int(item.get("right", 0)) for item in members)
            height = max(int(item.get("height", 0)) for item in members)
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

        lines.sort(key=lambda item: (int(item.get("top", 0)), int(item.get("left", 0))))
        return lines

    def _render_ocr_document(
        self,
        paragraph_records: List[Dict[str, Any]],
        page_width: int,
        *,
        marker_by_line: Optional[Dict[tuple[int, int, int], str]] = None,
    ) -> str:
        ordered_paragraphs = self._order_paragraph_records(
            paragraph_records, page_width
        )
        rendered_paragraphs = [
            self._render_ocr_paragraph(
                paragraph,
                page_width,
                marker_by_line=marker_by_line or {},
            )
            for paragraph in ordered_paragraphs
        ]
        return "\n\n".join(
            paragraph for paragraph in rendered_paragraphs if paragraph.strip()
        )

    def _build_ocr_paragraph_records(
        self, lines: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        grouped: Dict[tuple[int, int], List[Dict[str, Any]]] = {}
        for line in lines:
            block_num = int(line.get("block_num", 0))
            par_num = int(line.get("par_num", 0))
            paragraph_key = (block_num, par_num if par_num > 0 else 0)
            grouped.setdefault(paragraph_key, []).append(line)

        paragraphs: List[Dict[str, Any]] = []
        for key, paragraph_lines in grouped.items():
            paragraph_lines.sort(
                key=lambda item: (int(item.get("top", 0)), int(item.get("left", 0)))
            )
            left = min(int(line.get("left", 0)) for line in paragraph_lines)
            top = min(int(line.get("top", 0)) for line in paragraph_lines)
            right = max(int(line.get("right", 0)) for line in paragraph_lines)
            bottom = max(
                int(line.get("top", 0)) + max(int(line.get("height", 0)), 0)
                for line in paragraph_lines
            )
            paragraphs.append(
                {
                    "block_num": key[0],
                    "par_num": key[1],
                    "left": left,
                    "top": top,
                    "right": right,
                    "bottom": bottom,
                    "width": max(right - left, 0),
                    "lines": paragraph_lines,
                }
            )

        return paragraphs

    def _order_paragraph_records(
        self, paragraphs: List[Dict[str, Any]], page_width: int
    ) -> List[Dict[str, Any]]:
        if len(paragraphs) < 2 or page_width <= 0:
            return sorted(
                paragraphs,
                key=lambda item: (int(item.get("top", 0)), int(item.get("left", 0))),
            )

        left_positions = sorted(
            int(paragraph.get("left", 0)) for paragraph in paragraphs
        )
        gaps = [
            (left_positions[idx + 1] - left_positions[idx], idx)
            for idx in range(len(left_positions) - 1)
        ]
        max_gap, gap_index = max(gaps, default=(0, -1))
        if max_gap < max(int(page_width * 0.18), 80):
            return sorted(
                paragraphs,
                key=lambda item: (int(item.get("top", 0)), int(item.get("left", 0))),
            )

        threshold = (left_positions[gap_index] + left_positions[gap_index + 1]) / 2
        left_column = [p for p in paragraphs if int(p.get("left", 0)) <= threshold]
        right_column = [p for p in paragraphs if int(p.get("left", 0)) > threshold]
        if not left_column or not right_column:
            return sorted(
                paragraphs,
                key=lambda item: (int(item.get("top", 0)), int(item.get("left", 0))),
            )

        if len(paragraphs) < 4 and not self._columns_overlap_vertically(
            left_column, right_column
        ):
            return sorted(
                paragraphs,
                key=lambda item: (int(item.get("top", 0)), int(item.get("left", 0))),
            )

        return sorted(
            paragraphs,
            key=lambda item: (
                0 if int(item.get("left", 0)) <= threshold else 1,
                int(item.get("top", 0)),
                int(item.get("left", 0)),
            ),
        )

    def _columns_overlap_vertically(
        self, left_column: List[Dict[str, Any]], right_column: List[Dict[str, Any]]
    ) -> bool:
        left_top = min(int(paragraph.get("top", 0)) for paragraph in left_column)
        left_bottom = max(int(paragraph.get("bottom", 0)) for paragraph in left_column)
        right_top = min(int(paragraph.get("top", 0)) for paragraph in right_column)
        right_bottom = max(
            int(paragraph.get("bottom", 0)) for paragraph in right_column
        )
        return min(left_bottom, right_bottom) > max(left_top, right_top)

    def _render_ocr_paragraph(
        self,
        paragraph: Dict[str, Any],
        page_width: int,
        *,
        marker_by_line: Dict[tuple[int, int, int], str],
    ) -> str:
        lines = paragraph.get("lines", [])
        if not isinstance(lines, list) or not lines:
            return ""

        if self._should_preserve_line_breaks(lines, page_width):
            return self._render_preserved_line_block(lines, marker_by_line)

        return self._render_standard_paragraph(lines, marker_by_line)

    def _render_standard_paragraph(
        self,
        lines: List[Dict[str, Any]],
        marker_by_line: Dict[tuple[int, int, int], str],
    ) -> str:
        segments: List[str] = []
        text_buffer: List[str] = []

        def flush_text_buffer() -> None:
            nonlocal text_buffer
            if not text_buffer:
                return
            merged = self._merge_ocr_lines(text_buffer)
            if merged:
                segments.append(merged)
            text_buffer = []

        for line in lines:
            marker = marker_by_line.get(self._line_record_key(line))
            if marker:
                flush_text_buffer()
                segments.append(marker)
                continue
            text = str(line.get("text", "")).strip()
            if text:
                text_buffer.append(text)

        flush_text_buffer()
        return "\n\n".join(segment for segment in segments if segment.strip())

    def _should_preserve_line_breaks(
        self, lines: List[Dict[str, Any]], page_width: int
    ) -> bool:
        if len(lines) < 2:
            return False

        if any(self._looks_like_list_item(str(line.get("text", ""))) for line in lines):
            return False

        line_widths = [max(int(line.get("width", 0)), 0) for line in lines]
        max_width = max(line_widths, default=0)
        if max_width <= 0:
            return False

        nonfinal_lines = lines[:-1] if len(lines) > 2 else lines
        short_nonfinal_lines = sum(
            1
            for line in nonfinal_lines
            if max(int(line.get("width", 0)), 0) < max_width * 0.75
        )
        short_text_lines = sum(
            1
            for line in lines
            if len(str(line.get("text", "")).split()) <= 6
            or len(str(line.get("text", "")).strip()) <= 18
        )
        punctuation_endings = sum(
            1
            for line in lines
            if str(line.get("text", "")).rstrip().endswith((".", "!", "?", ";", ":"))
        )

        left_positions = [int(line.get("left", 0)) for line in lines]
        indent_variation = max(left_positions) - min(left_positions)
        avg_line_height = max(
            sum(max(int(line.get("height", 0)), 0) for line in lines)
            / max(len(lines), 1),
            1.0,
        )
        narrow_block = max_width < max(page_width * 0.45, avg_line_height * 12)

        if short_nonfinal_lines >= max(
            1, len(nonfinal_lines) // 2
        ) and short_text_lines >= max(2, len(lines) // 2):
            return True
        if (
            narrow_block
            and punctuation_endings <= 1
            and short_text_lines >= max(2, len(lines) - 1)
        ):
            return True
        if indent_variation >= avg_line_height * 1.5 and short_text_lines >= max(
            2, len(lines) // 2
        ):
            return True

        return False

    def _render_preserved_line_block(
        self,
        lines: List[Dict[str, Any]],
        marker_by_line: Dict[tuple[int, int, int], str],
    ) -> str:
        min_left = min(int(line.get("left", 0)) for line in lines)
        avg_line_height = max(
            sum(max(int(line.get("height", 0)), 0) for line in lines)
            / max(len(lines), 1),
            1.0,
        )
        indent_unit = max(avg_line_height * 1.25, 12.0)
        segments: List[str] = []
        verse_lines: List[str] = []

        def flush_verse() -> None:
            nonlocal verse_lines
            if len(verse_lines) <= 1:
                verse_lines = []
                return
            verse_lines.append("[[/VERSE]]")
            segments.append("\n".join(verse_lines))
            verse_lines = []

        for line in lines:
            marker = marker_by_line.get(self._line_record_key(line))
            if marker:
                flush_verse()
                segments.append(marker)
                continue
            text = str(line.get("text", "")).strip()
            if not text:
                continue
            indent_px = max(int(line.get("left", 0)) - min_left, 0)
            indent_level = max(int(round(indent_px / indent_unit)), 0)
            if not verse_lines:
                verse_lines.append("[[VERSE]]")
            verse_lines.append(f"[[LINE:{indent_level}]]{text}")

        flush_verse()
        return "\n\n".join(segment for segment in segments if segment.strip())

    def _line_record_key(self, line: Dict[str, Any]) -> tuple[int, int, int]:
        return (
            int(line.get("block_num", 0)),
            int(line.get("par_num", 0)),
            int(line.get("line_num", 0)),
        )

    def _looks_like_list_item(self, text: str) -> bool:
        stripped = text.strip()
        if not stripped:
            return False
        return bool(re.match(r"^(?:\d+\.|[A-Za-z]\.|\(\d+\)|[-*•◦●])\s+", stripped))

    def _looks_like_equation_line(self, text: str) -> bool:
        stripped = text.strip()
        if not stripped or len(stripped) < 3 or self._looks_like_list_item(stripped):
            return False

        math_symbol_count = len(re.findall(r"[=+\-*/×÷±≈≠≤≥∑∫√^(){}\[\]]", stripped))
        alpha_digit_mix = bool(re.search(r"[A-Za-z]\s*\d|\d\s*[A-Za-z]", stripped))
        variable_pattern = bool(re.search(r"\b[a-zA-Z]\b", stripped))

        if math_symbol_count >= 2 and (alpha_digit_mix or variable_pattern):
            return True
        if re.search(r"\b\d+\s*[=<>]\s*\d+", stripped):
            return True
        if re.search(r"[A-Za-z0-9]\s*[=<>±≈≠≤≥]\s*[A-Za-z0-9]", stripped):
            return True
        return False

    def _extract_equation_images(
        self,
        image: Any,
        line_records: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        equation_images: List[Dict[str, Any]] = []
        for index, line in enumerate(line_records, start=1):
            text = str(line.get("text", "")).strip()
            if not self._looks_like_equation_line(text):
                continue
            image_bytes = self._crop_line_image(image, line)
            if not image_bytes:
                continue
            equation_images.append(
                {
                    "marker": f"[[MATHIMG:eq-{index}]]",
                    "line_key": self._line_record_key(line),
                    "image_bytes": image_bytes,
                    "format": "png",
                    "page_number": 1,
                    "alt_text": text,
                }
            )
        return equation_images

    def _crop_line_image(self, image: Any, line: Dict[str, Any]) -> bytes:
        from PIL import Image

        left = max(int(line.get("left", 0)) - 12, 0)
        top = max(int(line.get("top", 0)) - 10, 0)
        right = min(int(line.get("right", 0)) + 12, image.width)
        bottom = min(
            int(line.get("top", 0)) + max(int(line.get("height", 0)), 0) + 10,
            image.height,
        )
        if right <= left or bottom <= top:
            return b""
        cropped = image.crop((left, top, right, bottom))
        if not isinstance(cropped, Image.Image):
            return b""
        buffer = io.BytesIO()
        cropped.save(buffer, format="PNG")
        return buffer.getvalue()

    def _merge_ocr_lines(self, lines: List[str]) -> str:
        merged = ""
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            if not merged:
                merged = line
                continue
            if merged.endswith("-") and line[:1].isalnum():
                merged = f"{merged[:-1]}{line}"
                continue
            merged = f"{merged} {line}"
        return merged.strip()


class SynthesisAgent(BaseAgent):
    """결과 종합 에이전트"""

    def __init__(self, settings: Optional[Settings] = None):
        super().__init__(AgentType.SYNTHESIS, settings)

    async def validate(self) -> bool:
        """하위 에이전트 유효성 검증"""
        return True

    async def process(self, message: AgentMessage) -> AgentMessage:
        """OCR 결과와 이미지 분석 결과를 종합하여 마크다운 생성"""
        try:
            if not isinstance(message.content, list):
                raise ValueError("결과 리스트가 필요합니다.")

            # 결과들을 페이지별로 그룹화
            page_results = self._group_results_by_page(message.content)

            # 마크다운 생성
            markdown_content = await self._generate_markdown(page_results)

            # 통계 생성
            stats = self._generate_processing_stats(page_results)

            synthesis_result = SynthesisResult(
                markdown_content=markdown_content,
                metadata={
                    "total_pages": len(page_results),
                    "total_images": sum(
                        len(page.get("images", [])) for page in page_results.values()
                    ),
                    "equation_images": [
                        equation_image
                        for page in page_results.values()
                        for equation_image in page.get("equation_images", [])
                        if isinstance(equation_image, dict)
                    ],
                    "total_text_length": len(markdown_content),
                },
                processing_stats=stats,
            )

            return AgentMessage(
                agent_type=self.agent_type,
                content=synthesis_result,
                metadata={"processing_time": message.timestamp},
            )

        except Exception as e:
            self.logger.error(f"결과 종합 실패: {str(e)}")
            raise ValueError(f"결과 종합 중 오류 발생: {str(e)}")

    def _group_results_by_page(
        self, results: List[Dict[str, Any]]
    ) -> Dict[int, Dict[str, Any]]:
        """결과를 페이지별로 그룹화"""
        page_groups = {}

        for result in results:
            page_num = result.get("page_number", 1)
            agent_type = result.get("agent_type", "")

            if page_num not in page_groups:
                page_groups[page_num] = {
                    "page_number": page_num,
                    "images": [],
                    "ocr_texts": [],
                    "descriptions": [],
                    "equation_images": [],
                }

            if agent_type == "multimodal_llm":
                page_groups[page_num]["images"].append(result)
                page_groups[page_num]["descriptions"].append(
                    self._normalize_content(result.get("content", {}))
                )
            elif agent_type == "ocr":
                normalized_content = self._normalize_content(result.get("content", ""))
                page_groups[page_num]["ocr_texts"].append(normalized_content)
                if isinstance(normalized_content, dict):
                    raw_equation_images = (
                        normalized_content.get("equation_images") or []
                    )
                    page_groups[page_num]["equation_images"].extend(
                        [
                            equation_image
                            for equation_image in raw_equation_images
                            if isinstance(equation_image, dict)
                        ]
                    )

        return page_groups

    async def _generate_markdown(self, page_results: Dict[int, Dict[str, Any]]) -> str:
        """페이지 결과를 마크다운으로 변환"""
        markdown_parts = []

        for page_num in sorted(page_results.keys()):
            page_data = page_results[page_num]

            # 페이지 헤더
            markdown_parts.append(f"\n\n# 페이지 {page_num}")
            markdown_parts.append(f"<!-- 페이지 {page_num} 시작 -->")

            # 이미지 설명들
            descriptions = page_data.get("descriptions", [])
            if descriptions:
                markdown_parts.append("## 이미지 분석")
                for i, desc in enumerate(descriptions):
                    if not isinstance(desc, dict):
                        desc = self._normalize_content(desc)
                    desc_data = (
                        desc.get("image_description", "")
                        if isinstance(desc, dict)
                        else ""
                    )
                    if desc_data:
                        markdown_parts.append(f"### 이미지 {i+1}")
                        markdown_parts.append(desc_data)
                        markdown_parts.append("")

            # OCR 텍스트들
            ocr_texts = page_data.get("ocr_texts", [])
            if ocr_texts:
                markdown_parts.append("## 추출된 텍스트")
                for i, ocr_text in enumerate(ocr_texts):
                    if not isinstance(ocr_text, dict):
                        ocr_text = self._normalize_content(ocr_text)
                    text = (
                        ocr_text.get("text", "") if isinstance(ocr_text, dict) else ""
                    )
                    if text.strip():
                        markdown_parts.append(f"### 텍스트 블록 {i+1}")
                        markdown_parts.append(text)
                        markdown_parts.append("")

            # 종합된 내용
            combined_text = self._combine_page_content(page_data)
            if combined_text.strip():
                markdown_parts.append("## 종합 내용")
                markdown_parts.append(combined_text)

            markdown_parts.append(f"<!-- 페이지 {page_num} 종료 -->\n")

        return "\n".join(markdown_parts)

    def _combine_page_content(self, page_data: Dict[str, Any]) -> str:
        """페이지 내용을 종합"""
        texts = []

        # OCR 텍스트 우선 사용
        for ocr_text in page_data.get("ocr_texts", []):
            if not isinstance(ocr_text, dict):
                ocr_text = self._normalize_content(ocr_text)
            text = ocr_text.get("text", "") if isinstance(ocr_text, dict) else ""
            if text.strip():
                texts.append(text.strip())

        # OCR 텍스트가 없으면 이미지 분석 결과 사용
        if not texts:
            for desc in page_data.get("descriptions", []):
                if not isinstance(desc, dict):
                    desc = self._normalize_content(desc)
                text = desc.get("text_content", "") if isinstance(desc, dict) else ""
                if text.strip():
                    texts.append(text.strip())

        equations: List[str] = []
        for desc in page_data.get("descriptions", []):
            if not isinstance(desc, dict):
                desc = self._normalize_content(desc)
            if not isinstance(desc, dict):
                continue
            for item in desc.get("equations_latex", []) or []:
                equation = str(item).strip()
                if equation and equation not in equations:
                    equations.append(equation)

        for equation in equations:
            texts.append(f"\n$$ {equation} $$\n")

        return "\n\n".join(texts)

    def _generate_processing_stats(
        self, page_results: Dict[int, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """처리 통계 생성"""
        total_pages = len(page_results)
        total_ocr_blocks = sum(
            len(page.get("ocr_texts", [])) for page in page_results.values()
        )
        total_descriptions = sum(
            len(page.get("descriptions", [])) for page in page_results.values()
        )

        # 신뢰도 통계
        confidences = []
        for page in page_results.values():
            for ocr_text in page.get("ocr_texts", []):
                if not isinstance(ocr_text, dict):
                    ocr_text = self._normalize_content(ocr_text)
                if isinstance(ocr_text, dict) and "confidence" in ocr_text:
                    confidences.append(ocr_text["confidence"])

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            "total_pages": total_pages,
            "total_ocr_blocks": total_ocr_blocks,
            "total_descriptions": total_descriptions,
            "average_confidence": round(avg_confidence, 3),
            "processing_timestamp": asyncio.get_event_loop().time(),
        }

    def _normalize_content(self, content: Any) -> Any:
        if isinstance(content, dict):
            return content
        if is_dataclass(content):
            if not isinstance(content, type):
                return asdict(content)
        model_dump = getattr(content, "model_dump", None)
        if callable(model_dump):
            return model_dump()
        to_dict = getattr(content, "dict", None)
        if callable(to_dict):
            return to_dict()
        return content


class ScanPDFProcessor:
    """에이전트 기반 스캔 PDF 처리 오케스트레이터"""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        progress_callback: Optional[Callable[[int, int], Awaitable[None]]] = None,
    ):
        self.settings = settings or get_settings()
        self.logger = logging.getLogger(__name__)
        self.progress_callback = progress_callback
        self._low_confidence_correction_lock = asyncio.Lock()
        self._low_confidence_corrections_used = 0

        # 에이전트 초기화
        self.multimodal_agent: Optional[MultimodalLLMAgent]
        try:
            self.multimodal_agent = MultimodalLLMAgent(self.settings)
        except ValueError:
            self.multimodal_agent = None
        self.ocr_agent = OCRAgent(self.settings)
        self.synthesis_agent = SynthesisAgent(self.settings)

        # PDF 처리 도구
        self.pdf_analyzer = PDFAnalyzer(self.settings)
        self.pdf_extractor = PDFExtractor(self.settings)

    async def validate_agents(self) -> bool:
        """모든 에이전트 유효성 검증"""
        # OCR + synthesis must be available. Multimodal LLM is optional.
        required_agents: List[BaseAgent] = [self.ocr_agent, self.synthesis_agent]
        optional_agents: List[BaseAgent] = []
        if self.multimodal_agent is not None:
            optional_agents.append(self.multimodal_agent)

        required_results = await asyncio.gather(
            *[agent.validate() for agent in required_agents],
            return_exceptions=True,
        )

        required_errors: List[str] = []
        for agent, result in zip(required_agents, required_results):
            if isinstance(result, Exception):
                required_errors.append(f"{agent.agent_type.value}: {result}")
            elif result is not True:
                required_errors.append(
                    f"{agent.agent_type.value}: validate returned {result!r}"
                )

        if required_errors:
            raise ValueError("; ".join(required_errors))

        if optional_agents:
            optional_results = await asyncio.gather(
                *[agent.validate() for agent in optional_agents],
                return_exceptions=True,
            )
            for agent, result in zip(optional_agents, optional_results):
                if isinstance(result, Exception) or result is not True:
                    self.logger.warning(
                        "Optional agent validation failed; disabling",
                        extra={"agent": agent.agent_type.value, "error": str(result)},
                    )
                    self.multimodal_agent = None

        return True

    async def process_scanned_pdf(self, pdf_content: bytes) -> SynthesisResult:
        """스캔 PDF 처리 전체 워크플로우"""
        try:
            self._low_confidence_corrections_used = 0
            # PDF 분석
            analysis_result = self.pdf_analyzer.analyze_pdf(pdf_content)

            pdf_type_raw = getattr(analysis_result, "pdf_type", None)
            pdf_type_value = getattr(pdf_type_raw, "value", pdf_type_raw)
            if isinstance(pdf_type_value, str):
                pdf_type_normalized = pdf_type_value.strip().lower()
            else:
                pdf_type_normalized = str(pdf_type_value).strip().lower()

            if pdf_type_normalized != PDFType.SCANNED.value:
                raise ValueError(
                    "텍스트 기반 PDF는 스캔 PDF 워크플로우를 사용하지 않습니다."
                )

            # 이미지 추출
            images = self.pdf_extractor.extract_images_from_pdf(pdf_content)

            if not images:
                raise ValueError("PDF에서 이미지를 추출할 수 없습니다.")

            self.logger.info(f"이미지 {len(images)}개 추출 완료, 처리 시작...")

            # 병렬 처리 결과 수집
            processing_results = await self._process_images_parallel(images)

            # 결과 종합
            synthesis_message = AgentMessage(
                agent_type=AgentType.SYNTHESIS,
                content=processing_results,
                timestamp=asyncio.get_event_loop().time(),
            )

            synthesis_result_message = await self.synthesis_agent.process(
                synthesis_message
            )
            synthesis_result = synthesis_result_message.content

            self.logger.info("스캔 PDF 처리 완료")
            return synthesis_result

        except Exception as e:
            error_detail = _format_exception_message(e)
            self.logger.exception("스캔 PDF 처리 실패: %s", error_detail)
            raise ValueError(f"스캔 PDF 처리 중 오류 발생: {error_detail}") from e

    async def _process_images_parallel(
        self, images: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """이미지들을 병렬로 처리"""
        tasks = []
        analysis_scheduled = 0

        for image_index, image_info in enumerate(images, start=1):
            scoped_image_info = {
                **image_info,
                "_image_scope": f"page-{image_info.get('page', 1)}-img-{image_index}",
            }
            # OCR 작업
            ocr_task = self._process_image_with_ocr(scoped_image_info)
            tasks.append(ocr_task)

            # 이미지 분석 작업 (선택적 - 비용 절약을 위해 일부만)
            if self.multimodal_agent is not None and analysis_scheduled < 5:
                analysis_task = self._process_image_with_llm(scoped_image_info)
                tasks.append(analysis_task)
                analysis_scheduled += 1

        total_tasks = len(tasks)
        results: List[object] = []
        completed_tasks = 0

        for done in asyncio.as_completed(tasks):
            task_result: object
            try:
                task_result = await done
            except Exception as exc:
                task_result = exc
            results.append(task_result)
            completed_tasks += 1
            if self.progress_callback is not None:
                await self.progress_callback(completed_tasks, max(1, total_tasks))

        # 예외 처리
        processed_results: List[Dict[str, Any]] = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.warning(
                    "이미지 처리 실패: %s", _format_exception_message(result)
                )
                continue
            if isinstance(result, dict):
                processed_results.append(result)

        return processed_results

    async def _process_image_with_ocr(
        self, image_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """단일 이미지 OCR 처리"""
        message = AgentMessage(
            agent_type=AgentType.OCR,
            content={
                "image_bytes": image_info["image_bytes"],
                "page_number": image_info["page"],
            },
            timestamp=asyncio.get_event_loop().time(),
        )

        result_message = await self.ocr_agent.process(message)

        content = result_message.content
        if is_dataclass(content):
            if not isinstance(content, type):
                content = asdict(content)

        if isinstance(content, dict):
            content = await self._apply_low_confidence_llm_correction(
                image_info=image_info,
                content=content,
            )
            equation_images = content.get("equation_images", [])
            if isinstance(equation_images, list):
                for equation_image in equation_images:
                    if not isinstance(equation_image, dict):
                        continue
                    marker = equation_image.get("marker")
                    if isinstance(marker, str):
                        image_scope = str(
                            image_info.get(
                                "_image_scope",
                                f"page-{image_info['page']}",
                            )
                        )
                        scoped_marker = marker.replace(
                            "[[MATHIMG:",
                            f"[[MATHIMG:{image_scope}-",
                            1,
                        )
                        equation_image["marker"] = scoped_marker
                        if isinstance(content.get("text"), str):
                            content["text"] = str(content["text"]).replace(
                                marker,
                                scoped_marker,
                            )
                    equation_image["page_number"] = image_info["page"]

        return {
            "page_number": image_info["page"],
            "agent_type": "ocr",
            "content": content,
            "metadata": result_message.metadata,
        }

    async def _apply_low_confidence_llm_correction(
        self,
        *,
        image_info: Dict[str, Any],
        content: Dict[str, Any],
    ) -> Dict[str, Any]:
        if self.multimodal_agent is None:
            return content

        original_text = str(content.get("text", "")).strip()
        confidence = float(content.get("confidence", 0.0) or 0.0)
        threshold = float(self.settings.ocr.llm_correction_threshold)
        if not original_text or confidence >= threshold:
            return content

        if not await self._reserve_low_confidence_correction_slot():
            return content

        try:
            corrected_text, model_used, fallback_used = (
                await self.multimodal_agent.correct_ocr_text(
                    image_bytes=image_info["image_bytes"],
                    ocr_text=original_text,
                    image_format=str(image_info.get("format", "jpeg")),
                )
            )
        except Exception as exc:
            self.logger.warning(
                "저신뢰 OCR LLM 보정 실패",
                extra={"page": image_info.get("page"), "error": str(exc)},
            )
            return content

        if not corrected_text.strip():
            return content

        updated_content = dict(content)
        updated_content["text"] = corrected_text.strip()
        updated_content["llm_corrected"] = True
        updated_content["llm_correction_model"] = model_used
        updated_content["llm_correction_fallback_used"] = fallback_used
        return updated_content

    async def _reserve_low_confidence_correction_slot(self) -> bool:
        max_pages = int(self.settings.ocr.llm_max_pages_per_document)
        if max_pages <= 0:
            return False

        async with self._low_confidence_correction_lock:
            if self._low_confidence_corrections_used >= max_pages:
                return False
            self._low_confidence_corrections_used += 1
            return True

    async def _process_image_with_llm(
        self, image_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """단일 이미지 LLM 분석"""
        if self.multimodal_agent is None:
            raise ValueError("LLM 에이전트가 설정되지 않았습니다.")

        message = AgentMessage(
            agent_type=AgentType.MULTIMODAL_LLM,
            content={
                "image_bytes": image_info["image_bytes"],
                "page_number": image_info["page"],
                "image_format": image_info.get("format", "jpeg"),
                "context": "PDF 문서에서 추출된 이미지입니다. 문서 내용을 파악하여 정확한 설명을 제공해주세요.",
            },
            timestamp=asyncio.get_event_loop().time(),
        )

        result_message = await self.multimodal_agent.process(message)

        content = result_message.content
        if is_dataclass(content):
            if not isinstance(content, type):
                content = asdict(content)

        return {
            "page_number": image_info["page"],
            "agent_type": "multimodal_llm",
            "content": content,
            "metadata": result_message.metadata,
        }


# 팩토리 함수
async def create_scan_pdf_processor(
    settings: Optional[Settings] = None,
    progress_callback: Optional[Callable[[int, int], Awaitable[None]]] = None,
) -> ScanPDFProcessor:
    """스캔 PDF 프로세서 생성 및 검증"""
    processor = ScanPDFProcessor(settings, progress_callback=progress_callback)

    await processor.validate_agents()

    return processor
