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
from pathlib import Path

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
from app.services.progress_tracker import ProgressTracker


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
    result_path: Optional[str] = None
    error_message: Optional[str] = None
    attempts: int = 0
    celery_task_id: Optional[str] = None
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
        self.tracker = ProgressTracker()
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

    async def retry(self, conversion_id: str, force: bool = False) -> ConversionJob:
        """실패한 작업 재시도(수동 호출).

        force: 실패 여부와 상관없이 재시도 허용
        """
        job = await self.store.get(conversion_id)
        if job.state not in (JobState.FAILED, JobState.CANCELLED) and not force:
            raise KeyError("재시도 가능한 상태가 아닙니다.")

        # 증가된 시도 횟수 반영
        job.attempts += 1
        await self.store.update(
            conversion_id, state=JobState.PENDING, message="재시도 대기중", progress=0
        )

        # 새로운 백그라운드 작업 실행
        # note: 이전 결과는 보존되며, 재시작 시 필요하면 덮어씌워짐
        asyncio.create_task(
            self._run_pipeline(conversion_id, getattr(job, "result_bytes") or b"")
        )
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
            # persist to tracker as well
            await self.tracker.set_step(conversion_id, step, progress, message)
            await self.store.update(
                conversion_id,
                current_step=step,
                progress=progress,
                state=JobState.PROCESSING,
                message=message,
            )

        try:
            # increment attempt counter for monitoring
            job = await self.store.get(conversion_id)
            job.attempts += 1
            await self.store.update(conversion_id, message=f"시도 #{job.attempts}")
            # 1) 분석
            await set_step("analyze", 5, "PDF 유형 분석 중")
            analysis = self.pdf_analyzer.analyze_pdf(pdf_bytes)
            pdf_type = analysis.pdf_type

            # 취소 확인
            if (await self.store.get(conversion_id)).is_cancelled():
                return

            # 대용량 문서일 경우 청크 단위로 텍스트를 추출하여 처리
            try:
                # 추출 시 청크 분할 사용
                chunks = self.pdf_extractor.extract_text_in_chunks(pdf_bytes)
                if chunks and len(chunks) > 1:
                    # 청크별로 진행을 보고하면서 텍스트를 합성하지 않고
                    # 각 청크를 LLM/EPUB 변환 파이프에 독립적으로 전달할 수 있음
                    assembled_text_parts: List[str] = []
                    for idx, ch in enumerate(chunks, start=1):
                        if (await self.store.get(conversion_id)).is_cancelled():
                            return
                        # 청크 처리 중인 상태 업데이트
                        chunk_progress = 20 + int(30 * idx / max(1, len(chunks)))
                        await set_step(
                            f"extract_chunk_{idx}",
                            chunk_progress,
                            f"Extracting pages {ch['start_page']} - {ch['end_page']}",
                        )
                        # 여기서는 간단히 합쳐서 후속 처리에 사용
                        assembled_text_parts.append(ch.get("total_text", ""))

                    text_result = {"total_text": "\n\n".join(assembled_text_parts)}
                else:
                    # 단일 청크 혹은 작은 문서: 기존 방식 유지
                    if pdf_type == PDFType.TEXT_BASED or pdf_type == PDFType.MIXED:
                        text_result = self.pdf_extractor.extract_text_from_pdf(
                            pdf_bytes
                        )
                    else:
                        text_result = None
            except Exception:
                # 추출 실패 시 기존 동작 유지
                if pdf_type == PDFType.TEXT_BASED or pdf_type == PDFType.MIXED:
                    text_result = self.pdf_extractor.extract_text_from_pdf(pdf_bytes)
                else:
                    text_result = None
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
            # 디스크에도 저장해야 하는 경우 설정에 따라 저장
            try:
                out_dir = "./results"  # 기본값
            except Exception:
                out_dir = None

            if out_dir:
                try:
                    p = Path(out_dir)
                    p.mkdir(parents=True, exist_ok=True)
                    file_name = f"{conversion_id}.epub"
                    out_path = p / file_name
                    out_path.write_bytes(epub_bytes)
                    await self.store.update(conversion_id, result_path=str(out_path))
                except Exception:
                    logger.exception("결과 파일을 디스크에 저장하는 중 오류 발생")
            await self.store.update(
                conversion_id,
                state=JobState.COMPLETED,
                progress=100,
                message="변환 완료",
                current_step="completed",
            )

        except Exception as e:
            logger.error("변환 파이프라인 실패", exc_info=True)
            # 기록 후 재시도 여부 판단(설정 기반)
            try:
                max_retries = 1  # 기본값
            except Exception:
                max_retries = 1

            job = await self.store.get(conversion_id)
            job.error_message = str(e)
            job.updated_at = datetime.now(timezone.utc).isoformat()

            if job.attempts < max_retries:
                # 자동 재시도: 간단한 백오프
                backoff = min(5 * job.attempts, 30)
                await self.store.update(
                    conversion_id,
                    state=JobState.PENDING,
                    message=f"에러 발생, 자동 재시도 대기중 (backoff {backoff}s)",
                )
                await asyncio.sleep(backoff)
                asyncio.create_task(self._run_pipeline(conversion_id, pdf_bytes))
                return

            # 재시도 초과 또는 비허용 -> 실패로 마감
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
