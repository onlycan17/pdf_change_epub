"""변환 파이프라인 통합 관리자(오케스트레이터)

설명: PDF → EPUB 과정을 단계별로 조율하고, 진행 상태를 추적/조회/취소하는 서비스.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from fastapi import HTTPException

from app.core.config import Settings, get_settings
from app.services.pdf_service import (
    PDFAnalyzer,
    PDFExtractor,
    PDFType,
    create_pdf_analyzer,
    create_pdf_extractor,
)
from app.services.epub_service import EpubGenerator, Chapter
from app.services.epub_validator import validate_epub_bytes


logger = logging.getLogger(__name__)


class JobState(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobStep:
    name: str
    progress: int = 0  # 0~100
    message: str = ""


@dataclass
class ConversionJob:
    conversion_id: str
    filename: str
    file_size: int
    ocr_enabled: bool
    state: JobState = JobState.PENDING
    progress: int = 0
    message: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    current_step: str = ""
    steps: List[JobStep] = field(default_factory=list)
    result_bytes: Optional[bytes] = None
    error_message: Optional[str] = None
    _cancel_event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)

    def cancel(self) -> None:
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()


class ConversionJobStore:
    """간단한 인메모리 작업 저장소 (향후 Redis/DB로 대체 가능)"""

    def __init__(self) -> None:
        self._jobs: Dict[str, ConversionJob] = {}
        self._lock = asyncio.Lock()

    async def create(self, job: ConversionJob) -> None:
        async with self._lock:
            self._jobs[job.conversion_id] = job

    async def get(self, conversion_id: str) -> ConversionJob:
        async with self._lock:
            job = self._jobs.get(conversion_id)
            if not job:
                raise KeyError("Job not found")
            return job

    async def update(self, conversion_id: str, **kwargs: Any) -> ConversionJob:
        async with self._lock:
            job = self._jobs.get(conversion_id)
            if not job:
                raise KeyError("Job not found")
            for k, v in kwargs.items():
                setattr(job, k, v)
            job.updated_at = datetime.now(timezone.utc).isoformat()
            return job

    async def set_result(self, conversion_id: str, data: bytes) -> None:
        await self.update(conversion_id, result_bytes=data)

    async def cancel(self, conversion_id: str) -> None:
        job = await self.get(conversion_id)
        job.cancel()
        await self.update(
            conversion_id, state=JobState.CANCELLED, message="작업이 취소되었습니다."
        )


class ConversionOrchestrator:
    """변환 파이프라인 통합 관리자"""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.store = ConversionJobStore()
        self.pdf_analyzer: PDFAnalyzer = create_pdf_analyzer(self.settings)
        self.pdf_extractor: PDFExtractor = create_pdf_extractor(self.settings)
        self.epub = EpubGenerator(language="ko")

    async def start(
        self,
        *,
        conversion_id: str,
        filename: str,
        file_size: int,
        ocr_enabled: bool,
        pdf_bytes: bytes,
    ) -> ConversionJob:
        job = ConversionJob(
            conversion_id=conversion_id,
            filename=filename,
            file_size=file_size,
            ocr_enabled=ocr_enabled,
            state=JobState.PENDING,
            progress=0,
            current_step="queued",
        )
        await self.store.create(job)

        # 백그라운드 실행
        asyncio.create_task(self._run_pipeline(job.conversion_id, pdf_bytes))
        return job

    async def status(self, conversion_id: str) -> ConversionJob:
        return await self.store.get(conversion_id)

    async def download(self, conversion_id: str) -> bytes:
        job = await self.store.get(conversion_id)
        if job.state != JobState.COMPLETED or not job.result_bytes:
            raise HTTPException(status_code=404, detail="결과가 준비되지 않았습니다.")
        return job.result_bytes

    async def cancel(self, conversion_id: str) -> None:
        await self.store.cancel(conversion_id)

    async def _run_pipeline(self, conversion_id: str, pdf_bytes: bytes) -> None:
        # 공통 업데이트 헬퍼
        async def set_step(step: str, progress: int, message: str = "") -> None:
            job = await self.store.get(conversion_id)
            job.steps.append(JobStep(name=step, progress=progress, message=message))
            await self.store.update(
                conversion_id,
                current_step=step,
                progress=progress,
                state=JobState.PROCESSING,
                message=message,
            )

        try:
            # 1) 분석
            await set_step("analyze", 5, "PDF 유형 분석 중")
            analysis = self.pdf_analyzer.analyze_pdf(pdf_bytes)
            pdf_type = analysis.pdf_type

            # 취소 확인
            if (await self.store.get(conversion_id)).is_cancelled():
                return

            # 2) 추출
            await set_step("extract", 20, "텍스트/이미지 추출 중")
            text_result: Optional[Dict[str, Any]] = None

            if pdf_type == PDFType.TEXT_BASED:
                text_result = self.pdf_extractor.extract_text_from_pdf(pdf_bytes)
            elif pdf_type == PDFType.MIXED:
                # 기본: 텍스트 우선 추출 후 부족 시 OCR는 스킵(최초 버전)
                text_result = self.pdf_extractor.extract_text_from_pdf(pdf_bytes)
            else:
                # SCANNED: 이미지는 이후 에이전트 경로에서 처리
                pass

            # 취소 확인
            if (await self.store.get(conversion_id)).is_cancelled():
                return

            # 3) OCR/LLM (스캔 + 옵션)
            synthesis_markdown: Optional[str] = None
            if (
                pdf_type == PDFType.SCANNED
                and (await self.store.get(conversion_id)).ocr_enabled
            ):
                await set_step("ocr_llm", 55, "OCR/LLM 처리 중")
                # 지연 임포트: 무거운 의존성(PaddleOCR) 로딩을 테스트 단계에서 피하기 위함
                from app.services.agent_service import (
                    create_scan_pdf_processor,
                )

                processor = await create_scan_pdf_processor(self.settings)
                synthesis = await processor.process_scanned_pdf(pdf_bytes)
                synthesis_markdown = synthesis.markdown_content

            # 취소 확인
            if (await self.store.get(conversion_id)).is_cancelled():
                return

            # 4) EPUB 생성
            await set_step("epub", 80, "EPUB 생성 중")

            chapters: List[Chapter] = []
            if synthesis_markdown:
                # 마크다운을 간단 변환: 줄바꿈을 <p>로 감싸는 경량 변환
                html_body = "".join(
                    f"<p>{line}</p>"
                    for line in synthesis_markdown.split("\n")
                    if line.strip()
                )
                chapters.append(
                    Chapter(
                        title="Converted", file_name="chapter1.xhtml", content=html_body
                    )
                )
            elif text_result and text_result.get("total_text"):
                # 텍스트를 단순 문단화
                total_text: str = str(text_result.get("total_text"))
                html_body = "".join(
                    f"<p>{line}</p>" for line in total_text.split("\n") if line.strip()
                )
                chapters.append(
                    Chapter(
                        title="Converted", file_name="chapter1.xhtml", content=html_body
                    )
                )
            else:
                # 비어있는 경우라도 최소 챕터 제공
                chapters.append(
                    Chapter(
                        title="Converted",
                        file_name="chapter1.xhtml",
                        content="<p>내용을 추출하지 못했습니다.</p>",
                    )
                )

            epub_bytes = self.epub.create_epub_bytes(
                title="변환된 문서",
                author="PdfToEpub Converter",
                chapters=chapters,
                uid=conversion_id,
            )

            # 5) 검증
            await set_step("validate", 95, "EPUB 구조 검증 중")
            _validation = validate_epub_bytes(epub_bytes)

            # 결과 저장/완료
            await self.store.set_result(conversion_id, epub_bytes)
            await self.store.update(
                conversion_id,
                state=JobState.COMPLETED,
                progress=100,
                message="변환 완료",
                current_step="completed",
            )

        except Exception as e:
            logger.error("변환 파이프라인 실패", exc_info=True)
            await self.store.update(
                conversion_id,
                state=JobState.FAILED,
                message=str(e),
                error_message=str(e),
                current_step="failed",
            )


# 전역 오케스트레이터 인스턴스 (간단 의존성)
_orchestrator: Optional[ConversionOrchestrator] = None


def get_orchestrator(settings: Optional[Settings] = None) -> ConversionOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ConversionOrchestrator(settings or get_settings())
    return _orchestrator
