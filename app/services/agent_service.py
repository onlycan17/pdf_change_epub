"""에이전트 기반 스캔 PDF 처리 서비스"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

import httpx
from paddleocr import PaddleOCR

from app.core.config import Settings, get_settings
from app.services.pdf_service import PDFAnalyzer, PDFExtractor

logger = logging.getLogger(__name__)


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
        self.api_key = self.settings.llm.api_key
        self.base_url = self.settings.llm.base_url or "https://openrouter.ai/api/v1"
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
            self.logger.error(f"이미지 분석 실패: {str(e)}")
            raise ValueError(f"이미지 분석 중 오류 발생: {str(e)}")

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
        self.language = self.settings.ocr.language
        self.ocr_engine: Optional[PaddleOCR] = None

    async def validate(self) -> bool:
        """OCR 엔진 초기화 및 검증"""
        try:
            self.ocr_engine = PaddleOCR(
                use_angle_cls=True, lang=self.language, show_log=False
            )
            return True
        except Exception as e:
            self.logger.error(f"PaddleOCR 초기화 실패: {str(e)}")
            return False

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
            self.logger.error(f"OCR 처리 실패: {str(e)}")
            raise ValueError(f"OCR 처리 중 오류 발생: {str(e)}")

    async def _run_ocr(self, image_data: bytes) -> Dict[str, Any]:
        """PaddleOCR 실행"""
        import io
        from PIL import Image

        try:
            # 바이트 데이터를 PIL 이미지로 변환
            image = Image.open(io.BytesIO(image_data))

            # OCR 실행 (PaddleOCR은 동기 함수이므로 스레드 풀에서 실행)
            loop = asyncio.get_event_loop()
            ocr_result = await loop.run_in_executor(
                None, lambda: self.ocr_engine.ocr(image) if self.ocr_engine else []
            )

            if not ocr_result or not ocr_result[0]:
                return {"text": "", "confidence": 0.0, "bounding_boxes": []}

            # 결과 처리
            text_parts = []
            bounding_boxes = []

            for line in ocr_result[0]:
                if len(line) >= 2:
                    text_parts.append(line[1][0])  # 텍스트
                    bounding_boxes.append(
                        {
                            "text": line[1][0],
                            "bbox": line[0],
                            "confidence": line[1][1] if len(line[1]) > 1 else 0.0,
                        }
                    )

            full_text = " ".join(text_parts)

            # 전체 신뢰도 계산
            confidences = [
                box["confidence"] for box in bounding_boxes if box["confidence"] > 0
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return {
                "text": full_text,
                "confidence": avg_confidence,
                "bounding_boxes": bounding_boxes,
            }

        except Exception as e:
            self.logger.error(f"OCR 실행 실패: {str(e)}")
            return {"text": "", "confidence": 0.0, "bounding_boxes": []}


class SynthesisAgent(BaseAgent):
    """결과 종합 에이전트"""

    def __init__(self, settings: Optional[Settings] = None):
        super().__init__(AgentType.SYNTHESIS, settings)
        self.multimodal_agent = MultimodalLLMAgent(settings)
        self.chunk_size = self.settings.conversion.chunk_size

    async def validate(self) -> bool:
        """하위 에이전트 유효성 검증"""
        return await self.multimodal_agent.validate()

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
                page_groups[page_num]["descriptions"].append(result.get("content", {}))
            elif agent_type == "ocr":
                page_groups[page_num]["ocr_texts"].append(result.get("content", ""))

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
                    desc_data = desc.get("image_description", "")
                    if desc_data:
                        markdown_parts.append(f"### 이미지 {i+1}")
                        markdown_parts.append(desc_data)
                        markdown_parts.append("")

            # OCR 텍스트들
            ocr_texts = page_data.get("ocr_texts", [])
            if ocr_texts:
                markdown_parts.append("## 추출된 텍스트")
                for i, ocr_text in enumerate(ocr_texts):
                    text = ocr_text.get("text", "")
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
            text = ocr_text.get("text", "")
            if text.strip():
                texts.append(text)

        # OCR 텍스트가 없으면 이미지 분석 결과 사용
        if not texts:
            for desc in page_data.get("descriptions", []):
                text = desc.get("text_content", "")
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


class ScanPDFProcessor:
    """에이전트 기반 스캔 PDF 처리 오케스트레이터"""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.logger = logging.getLogger(__name__)

        # 에이전트 초기화
        self.multimodal_agent = MultimodalLLMAgent(self.settings)
        self.ocr_agent = OCRAgent(self.settings)
        self.synthesis_agent = SynthesisAgent(self.settings)

        # PDF 처리 도구
        self.pdf_analyzer = PDFAnalyzer(self.settings)
        self.pdf_extractor = PDFExtractor(self.settings)

    async def validate_agents(self) -> bool:
        """모든 에이전트 유효성 검증"""
        agents = [self.multimodal_agent, self.ocr_agent, self.synthesis_agent]
        validation_results = await asyncio.gather(
            *[agent.validate() for agent in agents]
        )

        all_valid = all(validation_results)
        if not all_valid:
            self.logger.error("하나 이상의 에이전트 검증 실패")

        return all_valid

    async def process_scanned_pdf(self, pdf_content: bytes) -> SynthesisResult:
        """스캔 PDF 처리 전체 워크플로우"""
        try:
            # PDF 분석
            analysis_result = self.pdf_analyzer.analyze_pdf(pdf_content)

            if analysis_result.pdf_type != analysis_result.pdf_type.SCANNED:
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
            self.logger.error(f"스캔 PDF 처리 실패: {str(e)}")
            raise ValueError(f"스캔 PDF 처리 중 오류 발생: {str(e)}")

    async def _process_images_parallel(
        self, images: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """이미지들을 병렬로 처리"""
        tasks = []

        for image_info in images:
            # OCR 작업
            ocr_task = self._process_image_with_ocr(image_info)
            tasks.append(ocr_task)

            # 이미지 분석 작업 (선택적 - 비용 절약을 위해 일부만)
            if len(tasks) <= 5:  # 처음 5개 이미지만 분석
                analysis_task = self._process_image_with_llm(image_info)
                tasks.append(analysis_task)

        # 병렬 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 예외 처리
        processed_results: List[Dict[str, Any]] = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.warning(f"이미지 처리 실패: {str(result)}")
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

        return {
            "page_number": image_info["page"],
            "agent_type": "ocr",
            "content": result_message.content,
            "metadata": result_message.metadata,
        }

    async def _process_image_with_llm(
        self, image_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """단일 이미지 LLM 분석"""
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

        return {
            "page_number": image_info["page"],
            "agent_type": "multimodal_llm",
            "content": result_message.content,
            "metadata": result_message.metadata,
        }


# 팩토리 함수
async def create_scan_pdf_processor(
    settings: Optional[Settings] = None,
) -> ScanPDFProcessor:
    """스캔 PDF 프로세서 생성 및 검증"""
    processor = ScanPDFProcessor(settings)

    if not await processor.validate_agents():
        raise ValueError("하나 이상의 에이전트 초기화에 실패했습니다.")

    return processor
