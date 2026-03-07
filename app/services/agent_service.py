"""에이전트 기반 스캔 PDF 처리 서비스"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, List, Optional
from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum

import httpx

from app.core.config import Settings, get_settings
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


@dataclass
class OCRResult:
    """OCR 처리 결과"""

    page_number: int
    text: str
    confidence: float
    bounding_boxes: Optional[List[Dict[str, Any]]] = None


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
        self.model_name = self.settings.llm.model_name
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

            if not image_data:
                raise ValueError("이미지 데이터가 없습니다.")

            # 이미지 인코딩
            image_base64 = base64.b64encode(image_data).decode()

            # OpenRouter API 요청 구성
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self._build_prompt(context)},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                },
                            },
                        ],
                    }
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            }

            # API 호출
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

                result = response.json()
                analysis = result["choices"][0]["message"]["content"]

            # 결과 파싱 및 구조화
            structured_result = self._parse_analysis_result(analysis, page_number)

            return AgentMessage(
                agent_type=self.agent_type,
                content=structured_result,
                metadata={
                    "model": self.model_name,
                    "tokens_used": result.get("usage", {}).get("total_tokens", 0),
                    "processing_time": message.timestamp,
                },
            )

        except Exception as e:
            error_detail = _format_exception_message(e)
            self.logger.exception("이미지 분석 실패: %s", error_detail)
            raise ValueError(f"이미지 분석 중 오류 발생: {error_detail}") from e

    def _build_prompt(self, context: str) -> str:
        """분석 프롬프트 생성"""
        base_prompt = """다음 이미지를 분석하여 문서 변환에 필요한 정보를 추출해주세요.

다음 항목들을 JSON 형식으로 반환해주세요:
{
  "description": "이미지의 전체적인 설명 (상황, 인물, 배경 등)",
  "text_content": "이미지에서 인식된 모든 텍스트",
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
2. 레이아웃 구조 파악
3. 표나 다이어그램의 존재 여부
4. 문서의 목적과 맥락 이해
5. 한국어와 영어 모두 지원

"""

        if context:
            base_prompt += f"\n추가 맥락: {context}"

        return base_prompt

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
            )

        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON 파싱 실패, 기본 구조 사용: {str(e)}")
            return ImageAnalysisResult(
                page_number=page_number,
                image_description=raw_result,
                text_content=raw_result,
                confidence=0.5,
                layout_info={},
            )


class OCRAgent(BaseAgent):
    """PaddleOCR 연동 에이전트"""

    def __init__(self, settings: Optional[Settings] = None):
        super().__init__(AgentType.OCR, settings)
        self.language = "kor+eng"  # 기본값
        self.ocr_engine: None = None

    async def validate(self) -> bool:
        """OCR 엔진 초기화 및 검증"""
        import pytesseract

        try:
            _ = pytesseract.get_tesseract_version()
            langs = set(pytesseract.get_languages(config=""))

            required = [p for p in self.language.split("+") if p]
            missing = [p for p in required if p not in langs]
            if missing:
                raise ValueError(
                    f"Tesseract language data missing: {', '.join(missing)} (available: {', '.join(sorted(langs))})"
                )
            return True
        except Exception as e:
            # Raise so the orchestrator can surface a useful message.
            raise ValueError(f"Tesseract OCR init failed: {e}")

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
            )

            return AgentMessage(
                agent_type=self.agent_type,
                content=ocr_result,
                metadata={
                    "language": self.language,
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
        import pytesseract

        try:
            # 바이트 데이터를 PIL 이미지로 변환
            image = Image.open(io.BytesIO(image_data))

            def _run_tesseract() -> Dict[str, Any]:
                data = pytesseract.image_to_data(
                    image,
                    lang=self.language,
                    output_type=pytesseract.Output.DICT,
                )
                n = int(data.get("level") and len(data["level"]) or 0)
                boxes: List[Dict[str, Any]] = []
                tokens: List[str] = []
                confidences: List[float] = []

                for i in range(n):
                    text = str(data.get("text", [""] * n)[i]).strip()
                    if not text:
                        continue

                    conf_raw = str(data.get("conf", ["-1"] * n)[i]).strip()
                    try:
                        conf = float(conf_raw)
                    except ValueError:
                        conf = -1.0

                    left = int(float(data.get("left", [0] * n)[i]))
                    top = int(float(data.get("top", [0] * n)[i]))
                    width = int(float(data.get("width", [0] * n)[i]))
                    height = int(float(data.get("height", [0] * n)[i]))
                    bbox = [[left, top], [left + width, top], [left + width, top + height], [left, top + height]]

                    tokens.append(text)
                    if conf >= 0:
                        confidences.append(conf)

                    boxes.append(
                        {
                            "text": text,
                            "bbox": bbox,
                            "confidence": max(conf, 0.0) / 100.0 if conf >= 0 else 0.0,
                        }
                    )

                avg_conf = (sum(confidences) / len(confidences)) / 100.0 if confidences else 0.0
                return {
                    "text": " ".join(tokens),
                    "confidence": avg_conf,
                    "bounding_boxes": boxes,
                }

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _run_tesseract)

        except Exception as e:
            self.logger.exception("OCR 실행 실패: %s", _format_exception_message(e))
            return {"text": "", "confidence": 0.0, "bounding_boxes": []}


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
                }

            if agent_type == "multimodal_llm":
                page_groups[page_num]["images"].append(result)
                page_groups[page_num]["descriptions"].append(
                    self._normalize_content(result.get("content", {}))
                )
            elif agent_type == "ocr":
                page_groups[page_num]["ocr_texts"].append(
                    self._normalize_content(result.get("content", ""))
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
                    desc_data = desc.get("image_description", "") if isinstance(desc, dict) else ""
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
                    text = ocr_text.get("text", "") if isinstance(ocr_text, dict) else ""
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
                texts.append(text)

        # OCR 텍스트가 없으면 이미지 분석 결과 사용
        if not texts:
            for desc in page_data.get("descriptions", []):
                if not isinstance(desc, dict):
                    desc = self._normalize_content(desc)
                text = desc.get("text_content", "") if isinstance(desc, dict) else ""
                if text.strip():
                    texts.append(text)

        return " ".join(texts)

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
                required_errors.append(f"{agent.agent_type.value}: validate returned {result!r}")

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

        for image_info in images:
            # OCR 작업
            ocr_task = self._process_image_with_ocr(image_info)
            tasks.append(ocr_task)

            # 이미지 분석 작업 (선택적 - 비용 절약을 위해 일부만)
            if self.multimodal_agent is not None and analysis_scheduled < 5:
                analysis_task = self._process_image_with_llm(image_info)
                tasks.append(analysis_task)
                analysis_scheduled += 1

        total_tasks = len(tasks)
        results = []
        completed_tasks = 0

        for done in asyncio.as_completed(tasks):
            try:
                result = await done
            except Exception as exc:
                result = exc
            results.append(result)
            completed_tasks += 1
            if self.progress_callback is not None:
                await self.progress_callback(completed_tasks, max(1, total_tasks))

        # 예외 처리
        processed_results: List[Dict[str, Any]] = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.warning("이미지 처리 실패: %s", _format_exception_message(result))
                continue
            # mypy를 위한 타입 단언
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

        return {
            "page_number": image_info["page"],
            "agent_type": "ocr",
            "content": content,
            "metadata": result_message.metadata,
        }

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
