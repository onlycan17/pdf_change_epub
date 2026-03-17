"""변환 파이프라인 통합 관리자(오케스트레이터)

설명: PDF → EPUB 과정을 단계별로 조율하고, 진행 상태를 추적/조회/취소하는 서비스.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException

from app.core.config import Settings, get_settings
from .conversion_epub_renderer import (
    build_epub_image_assets,
    build_scan_math_image_assets,
    extract_content_flow_pages,
    extract_math_image_marker,
    filter_epub_images_by_usage,
    is_page_sized_scan_image,
    normalize_image_for_epub,
    render_content_flow_to_xhtml,
    render_image_figure,
    render_image_figure_group,
    render_markdown_to_xhtml_body,
    render_preserved_lines_block,
    render_text_with_page_images,
    resolve_image_format,
    resolve_page_image_refs,
    split_text_to_paragraphs,
    wrap_text_block,
)
from app.services.conversion_metrics_service import get_conversion_metrics_service
from app.services.pdf_service import (
    PDFAnalyzer,
    PDFExtractor,
    PDFType,
    create_pdf_analyzer,
    create_pdf_extractor,
)
from app.services.epub_service import EpubGenerator, Chapter, EpubImage
from app.services.epub_validator import validate_epub_bytes
from app.services.progress_tracker import ProgressTracker
from app.services.text_context_service import create_text_context_corrector
from app.services.text_cleanup import clean_text_for_epub_body


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
    owner_user_id: Optional[str] = None
    translate_to_korean: bool = False
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
    llm_used_model: Optional[str] = None
    llm_attempt_count: int = 0
    llm_fallback_used: bool = False
    attempts: int = 0
    celery_task_id: Optional[str] = None
    source_pdf_bytes: Optional[bytes] = field(default=None, repr=False)
    _cancel_event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)

    def cancel(self) -> None:
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()


JobStatusCallback = Callable[["ConversionJob"], Awaitable[None]]
PublishStatusCallback = Callable[[], Awaitable[None]]
StepUpdateCallback = Callable[[str, int, str], Awaitable[None]]


@dataclass
class EpubBuildArtifacts:
    chapters: List[Chapter]
    images: List[EpubImage]


@dataclass
class ScanProcessingArtifacts:
    synthesis_markdown: Optional[str] = None
    scan_math_image_refs: Dict[str, Dict[str, str]] = field(default_factory=dict)
    scan_math_images: List[EpubImage] = field(default_factory=list)


def serialize_job_status(job: ConversionJob) -> Dict[str, Any]:
    """Serialize a conversion job into a JSON-safe status payload."""

    payload = {
        "conversion_id": job.conversion_id,
        "filename": job.filename,
        "file_size": job.file_size,
        "ocr_enabled": job.ocr_enabled,
        "owner_user_id": job.owner_user_id,
        "translate_to_korean": job.translate_to_korean,
        "state": getattr(job.state, "value", job.state),
        "progress": job.progress,
        "message": job.message,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "current_step": job.current_step,
        "steps": [
            {
                "name": step.name,
                "progress": step.progress,
                "message": step.message,
            }
            for step in job.steps
        ],
        "result_path": job.result_path,
        "error_message": job.error_message,
        "llm_used_model": job.llm_used_model,
        "llm_attempt_count": job.llm_attempt_count,
        "llm_fallback_used": job.llm_fallback_used,
        "attempts": job.attempts,
    }

    if isinstance(job.celery_task_id, str) and job.celery_task_id:
        payload["celery_task_id"] = job.celery_task_id

    return payload


def apply_serialized_job_status(
    job: ConversionJob, payload: Dict[str, Any]
) -> ConversionJob:
    """Apply a serialized status payload onto an existing job instance."""

    state_value = payload.get("state")
    if isinstance(state_value, str):
        try:
            job.state = JobState(state_value)
        except ValueError:
            pass

    for attr in (
        "filename",
        "file_size",
        "ocr_enabled",
        "owner_user_id",
        "translate_to_korean",
        "progress",
        "message",
        "created_at",
        "updated_at",
        "current_step",
        "result_path",
        "error_message",
        "llm_used_model",
        "llm_attempt_count",
        "llm_fallback_used",
        "attempts",
        "celery_task_id",
    ):
        if attr == "celery_task_id":
            value = payload.get(attr)
            if isinstance(value, str) and value:
                setattr(job, attr, value)
            continue
        if attr in payload:
            setattr(job, attr, payload[attr])

    raw_steps = payload.get("steps")
    if isinstance(raw_steps, list):
        job.steps = [
            JobStep(
                name=str(step.get("name", "")),
                progress=int(step.get("progress", 0)),
                message=str(step.get("message", "")),
            )
            for step in raw_steps
            if isinstance(step, dict)
        ]

    return job


class ConversionJobStore:
    """간단한 인메모리 작업 저장소 (향후 Redis/DB로 대체 가능)"""

    def __init__(self) -> None:
        self._jobs: Dict[str, ConversionJob] = {}
        self._lock = asyncio.Lock()
        settings = get_settings()
        self._metrics_service = get_conversion_metrics_service(settings.database.url)

    async def create(self, job: ConversionJob) -> None:
        async with self._lock:
            self._jobs[job.conversion_id] = job
            self._metrics_service.upsert_job(job)

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
            self._metrics_service.upsert_job(job)
            return job

    async def list_jobs(self) -> list[ConversionJob]:
        async with self._lock:
            return sorted(
                self._jobs.values(),
                key=lambda job: job.created_at,
                reverse=True,
            )

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
        self.text_context_corrector = create_text_context_corrector(self.settings)
        self.epub = EpubGenerator(language="ko")

    def _create_job(
        self,
        *,
        conversion_id: str,
        filename: str,
        file_size: int,
        ocr_enabled: bool,
        owner_user_id: Optional[str] = None,
        translate_to_korean: bool = False,
        pdf_bytes: bytes,
    ) -> ConversionJob:
        return ConversionJob(
            conversion_id=conversion_id,
            filename=filename,
            file_size=file_size,
            ocr_enabled=ocr_enabled,
            owner_user_id=owner_user_id,
            translate_to_korean=translate_to_korean,
            source_pdf_bytes=pdf_bytes,
            state=JobState.PENDING,
            progress=0,
            current_step="queued",
        )

    async def start(
        self,
        *,
        conversion_id: str,
        filename: str,
        file_size: int,
        ocr_enabled: bool,
        owner_user_id: Optional[str] = None,
        translate_to_korean: bool = False,
        pdf_bytes: bytes,
    ) -> ConversionJob:
        job = self._create_job(
            conversion_id=conversion_id,
            filename=filename,
            file_size=file_size,
            ocr_enabled=ocr_enabled,
            owner_user_id=owner_user_id,
            translate_to_korean=translate_to_korean,
            pdf_bytes=pdf_bytes,
        )
        await self.store.create(job)

        # 백그라운드 실행
        asyncio.create_task(self._run_pipeline(job.conversion_id, pdf_bytes))
        return job

    async def run_to_completion(
        self,
        *,
        conversion_id: str,
        filename: str,
        file_size: int,
        ocr_enabled: bool,
        owner_user_id: Optional[str] = None,
        translate_to_korean: bool = False,
        pdf_bytes: bytes,
        status_callback: Optional[JobStatusCallback] = None,
    ) -> ConversionJob:
        job = self._create_job(
            conversion_id=conversion_id,
            filename=filename,
            file_size=file_size,
            ocr_enabled=ocr_enabled,
            owner_user_id=owner_user_id,
            translate_to_korean=translate_to_korean,
            pdf_bytes=pdf_bytes,
        )
        await self.store.create(job)
        await self._run_pipeline(
            conversion_id,
            pdf_bytes,
            status_callback=status_callback,
        )
        return await self.store.get(conversion_id)

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
            self._run_pipeline(conversion_id, getattr(job, "source_pdf_bytes") or b"")
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

    def _build_epub_artifacts(
        self,
        *,
        pdf_bytes: bytes,
        analysis: Any,
        ocr_enabled: bool,
        text_result: Optional[Dict[str, Any]],
        synthesis_markdown: Optional[str],
        scan_math_image_refs: Dict[str, Dict[str, str]],
        scan_math_images: List[EpubImage],
    ) -> EpubBuildArtifacts:
        content_flow = self._extract_content_flow_pages(pdf_bytes)
        scanned_pages_for_images = (
            set(analysis.get_scanned_pages()) if ocr_enabled else None
        )
        (
            base_epub_images,
            image_file_by_xref,
            image_file_by_page,
        ) = self._build_epub_image_assets(pdf_bytes)
        page_image_refs = self._resolve_page_image_refs(
            content_flow,
            image_file_by_xref,
            image_file_by_page,
            scanned_pages=scanned_pages_for_images,
        )
        epub_images = [
            *self._filter_epub_images_by_usage(base_epub_images, page_image_refs),
            *scan_math_images,
        ]

        chapters: List[Chapter] = []
        if synthesis_markdown:
            html_body = self._render_markdown_to_xhtml_body(
                synthesis_markdown,
                page_image_refs,
                math_image_refs=scan_math_image_refs,
            )
            chapters.append(
                Chapter(
                    title="Converted",
                    file_name="chapter1.xhtml",
                    content=html_body,
                )
            )
        elif text_result and text_result.get("total_text"):
            total_text: str = clean_text_for_epub_body(
                str(text_result.get("total_text"))
            )
            html_body = self._render_text_with_page_images(total_text, page_image_refs)
            chapters.append(
                Chapter(
                    title="Converted",
                    file_name="chapter1.xhtml",
                    content=html_body,
                )
            )
        elif content_flow:
            html_body = self._render_content_flow_to_xhtml(
                content_flow,
                image_file_by_xref,
            )
            chapters.append(
                Chapter(
                    title="Converted",
                    file_name="chapter1.xhtml",
                    content=html_body,
                )
            )
        else:
            chapters.append(
                Chapter(
                    title="Converted",
                    file_name="chapter1.xhtml",
                    content="<p>내용을 추출하지 못했습니다.</p>",
                )
            )
            for page in sorted(page_image_refs.keys()):
                chapters[0].content += self._render_image_figure_group(
                    page_image_refs[page]
                )

        return EpubBuildArtifacts(chapters=chapters, images=epub_images)

    async def _complete_job_successfully(
        self,
        *,
        conversion_id: str,
        epub_bytes: bytes,
        publish_status: Callable[[], Awaitable[None]],
    ) -> None:
        await self.store.set_result(conversion_id, epub_bytes)
        out_dir = "./results"

        if out_dir:
            try:
                path = Path(out_dir)
                path.mkdir(parents=True, exist_ok=True)
                out_path = path / f"{conversion_id}.epub"
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
        await publish_status()

    async def _handle_pipeline_failure(
        self,
        *,
        conversion_id: str,
        pdf_bytes: bytes,
        error: Exception,
        publish_status: Callable[[], Awaitable[None]],
    ) -> None:
        logger.error("변환 파이프라인 실패", exc_info=True)
        max_retries = 1

        job = await self.store.get(conversion_id)
        job.error_message = str(error)
        job.updated_at = datetime.now(timezone.utc).isoformat()

        if job.attempts < max_retries:
            backoff = min(5 * job.attempts, 30)
            await self.store.update(
                conversion_id,
                state=JobState.PENDING,
                message=f"에러 발생, 자동 재시도 대기중 (backoff {backoff}s)",
            )
            await publish_status()
            await asyncio.sleep(backoff)
            asyncio.create_task(self._run_pipeline(conversion_id, pdf_bytes))
            return

        await self.store.update(
            conversion_id,
            state=JobState.FAILED,
            message=str(error),
            error_message=str(error),
            current_step="failed",
        )
        await publish_status()

    async def _is_job_cancelled(self, conversion_id: str) -> bool:
        return (await self.store.get(conversion_id)).is_cancelled()

    async def _mark_pipeline_started(
        self,
        conversion_id: str,
        publish_status: PublishStatusCallback,
    ) -> None:
        job = await self.store.get(conversion_id)
        job.attempts += 1
        await self.store.update(
            conversion_id,
            state=JobState.PROCESSING,
            current_step="started",
            message=f"시도 #{job.attempts}",
        )
        await publish_status()

    async def _extract_text_result(
        self,
        *,
        conversion_id: str,
        pdf_bytes: bytes,
        pdf_type: PDFType,
        set_step: StepUpdateCallback,
    ) -> Optional[Dict[str, Any]]:
        try:
            chunks = self.pdf_extractor.extract_text_in_chunks(pdf_bytes)
            if chunks and len(chunks) > 1:
                return await self._extract_text_from_chunks(
                    conversion_id=conversion_id,
                    pdf_type=pdf_type,
                    chunks=chunks,
                    set_step=set_step,
                )
            if pdf_type in (PDFType.TEXT_BASED, PDFType.MIXED):
                return self.pdf_extractor.extract_text_from_pdf(pdf_bytes)
            return None
        except Exception:
            if pdf_type in (PDFType.TEXT_BASED, PDFType.MIXED):
                self.pdf_extractor.extract_text_from_pdf(pdf_bytes)
            return self.pdf_extractor.extract_text_from_pdf(pdf_bytes)

    async def _extract_text_from_chunks(
        self,
        *,
        conversion_id: str,
        pdf_type: PDFType,
        chunks: List[Dict[str, Any]],
        set_step: StepUpdateCallback,
    ) -> Dict[str, Any]:
        assembled_text_parts: List[str] = []
        total_chunks = len(chunks)

        for idx, chunk in enumerate(chunks, start=1):
            if await self._is_job_cancelled(conversion_id):
                return {"total_text": "\n\n".join(assembled_text_parts)}
            chunk_progress = 20 + int(30 * idx / max(1, total_chunks))
            await set_step(
                f"extract_chunk_{idx}",
                chunk_progress,
                f"Extracting pages {chunk['start_page']} - {chunk['end_page']}",
            )
            assembled_text_parts.append(str(chunk.get("total_text", "")))

        if pdf_type not in (PDFType.TEXT_BASED, PDFType.MIXED):
            return {"total_text": "\n\n".join(assembled_text_parts)}

        return await self._apply_context_correction(
            conversion_id=conversion_id,
            chunks=chunks,
            set_step=set_step,
        )

    async def _apply_context_correction(
        self,
        *,
        conversion_id: str,
        chunks: List[Dict[str, Any]],
        set_step: StepUpdateCallback,
    ) -> Dict[str, Any]:
        await set_step("context_correction", 60, "문맥 보정 중")

        async def on_context_progress(processed_chunks: int, total_chunks: int) -> None:
            if total_chunks <= 0:
                return
            progress_delta = int((processed_chunks / total_chunks) * 15)
            context_progress = min(75, 60 + progress_delta)
            await set_step(
                "context_correction",
                context_progress,
                f"문맥 보정 중 ({processed_chunks}/{total_chunks})",
            )

        corrected_text = await self.text_context_corrector.correct_chunk_entries(
            chunks,
            on_chunk_progress=on_context_progress,
        )
        await self._merge_llm_stats(conversion_id)
        return {"total_text": corrected_text}

    async def _apply_document_reflow(
        self,
        *,
        conversion_id: str,
        text: str,
        mode: str,
        set_step: StepUpdateCallback,
    ) -> str:
        if not text.strip() or not hasattr(
            self.text_context_corrector, "reflow_document_text"
        ):
            return text

        await set_step("document_reflow", 76, "문서 구조 정리 중")

        async def on_reflow_progress(
            processed_segments: int, total_segments: int
        ) -> None:
            if total_segments <= 0:
                return
            progress_delta = int((processed_segments / total_segments) * 3)
            reflow_progress = min(79, 76 + progress_delta)
            await set_step(
                "document_reflow",
                reflow_progress,
                f"문서 구조 정리 중 ({processed_segments}/{total_segments})",
            )

        reflowed_text = await self.text_context_corrector.reflow_document_text(
            text,
            mode=mode,
            on_segment_progress=on_reflow_progress,
        )
        await self._merge_llm_stats(conversion_id)
        return reflowed_text

    async def _merge_llm_stats(self, conversion_id: str) -> None:
        llm_stats = getattr(self.text_context_corrector, "last_run_stats", {})
        job = await self.store.get(conversion_id)
        await self.store.update(
            conversion_id,
            llm_used_model=llm_stats.get("last_used_model") or job.llm_used_model,
            llm_attempt_count=job.llm_attempt_count
            + int(llm_stats.get("total_attempts", 0)),
            llm_fallback_used=job.llm_fallback_used
            or bool(llm_stats.get("fallback_used", False)),
        )

    async def _process_scanned_pdf(
        self,
        *,
        conversion_id: str,
        pdf_bytes: bytes,
        pdf_type: PDFType,
        ocr_enabled: bool,
        set_step: StepUpdateCallback,
    ) -> ScanProcessingArtifacts:
        if pdf_type != PDFType.SCANNED or not ocr_enabled:
            return ScanProcessingArtifacts()

        await set_step("ocr_llm", 55, "OCR/LLM 처리 중")

        # 지연 임포트: 무거운 의존성(PaddleOCR) 로딩을 테스트 단계에서 피하기 위함
        from app.services.agent_service import create_scan_pdf_processor

        async def on_scan_progress(processed_tasks: int, total_tasks: int) -> None:
            if total_tasks <= 0:
                return
            progress_delta = int((processed_tasks / total_tasks) * 24)
            scan_progress = min(79, 55 + progress_delta)
            await set_step(
                "ocr_llm",
                scan_progress,
                f"OCR/LLM 처리 중 ({processed_tasks}/{total_tasks})",
            )

        processor = await create_scan_pdf_processor(
            self.settings,
            progress_callback=on_scan_progress,
        )
        synthesis = await processor.process_scanned_pdf(pdf_bytes)
        synthesis_metadata = getattr(synthesis, "metadata", {})
        if not isinstance(synthesis_metadata, dict):
            synthesis_metadata = {}

        artifacts = ScanProcessingArtifacts()
        artifacts.scan_math_image_refs = self._build_scan_math_image_assets(
            synthesis_metadata.get("equation_images", []),
            artifacts.scan_math_images,
        )
        reflowed_markdown = await self._apply_document_reflow(
            conversion_id=conversion_id,
            text=synthesis.markdown_content,
            mode="markdown",
            set_step=set_step,
        )
        artifacts.synthesis_markdown = clean_text_for_epub_body(reflowed_markdown)
        return artifacts

    async def _run_pipeline(
        self,
        conversion_id: str,
        pdf_bytes: bytes,
        status_callback: Optional[JobStatusCallback] = None,
    ) -> None:
        # 공통 업데이트 헬퍼
        async def publish_status() -> None:
            if status_callback is None:
                return
            job_snapshot = await self.store.get(conversion_id)
            await status_callback(job_snapshot)

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
            await publish_status()

        try:
            await self._mark_pipeline_started(conversion_id, publish_status)
            await set_step("analyze", 5, "PDF 유형 분석 중")
            analysis = self.pdf_analyzer.analyze_pdf(pdf_bytes)
            pdf_type = analysis.pdf_type

            if await self._is_job_cancelled(conversion_id):
                return

            text_result = (
                await self._extract_text_result(
                    conversion_id=conversion_id,
                    pdf_bytes=pdf_bytes,
                    pdf_type=pdf_type,
                    set_step=set_step,
                )
                or {}
            )
            total_text = str(text_result.get("total_text", "")).strip()
            if total_text:
                text_result["total_text"] = await self._apply_document_reflow(
                    conversion_id=conversion_id,
                    text=total_text,
                    mode="plain",
                    set_step=set_step,
                )

            if await self._is_job_cancelled(conversion_id):
                return

            current_job = await self.store.get(conversion_id)
            scan_processing = await self._process_scanned_pdf(
                conversion_id=conversion_id,
                pdf_bytes=pdf_bytes,
                pdf_type=pdf_type,
                ocr_enabled=current_job.ocr_enabled,
                set_step=set_step,
            )

            if await self._is_job_cancelled(conversion_id):
                return

            await set_step("epub", 80, "EPUB 생성 중")
            current_job = await self.store.get(conversion_id)
            artifacts = self._build_epub_artifacts(
                pdf_bytes=pdf_bytes,
                analysis=analysis,
                ocr_enabled=current_job.ocr_enabled,
                text_result=text_result,
                synthesis_markdown=scan_processing.synthesis_markdown,
                scan_math_image_refs=scan_processing.scan_math_image_refs,
                scan_math_images=scan_processing.scan_math_images,
            )

            epub_bytes = self.epub.create_epub_bytes(
                title="변환된 문서",
                author="",
                chapters=artifacts.chapters,
                images=artifacts.images,
                uid=conversion_id,
            )

            # 5) 검증
            await set_step("validate", 95, "EPUB 구조 검증 중")
            _validation = validate_epub_bytes(epub_bytes)

            # 결과 저장/완료
            await self._complete_job_successfully(
                conversion_id=conversion_id,
                epub_bytes=epub_bytes,
                publish_status=publish_status,
            )

        except Exception as e:
            await self._handle_pipeline_failure(
                conversion_id=conversion_id,
                pdf_bytes=pdf_bytes,
                error=e,
                publish_status=publish_status,
            )

    def _build_epub_image_assets(
        self,
        pdf_bytes: bytes,
    ) -> tuple[List[EpubImage], Dict[int, str], Dict[int, List[str]]]:
        return build_epub_image_assets(self.pdf_extractor, pdf_bytes)

    def _is_page_sized_scan_image(self, image_info: Dict[str, Any]) -> bool:
        return is_page_sized_scan_image(image_info)

    def _extract_content_flow_pages(self, pdf_bytes: bytes) -> List[Dict[str, Any]]:
        return extract_content_flow_pages(self.pdf_extractor, pdf_bytes)

    def _resolve_page_image_refs(
        self,
        content_flow: List[Dict[str, Any]],
        image_file_by_xref: Dict[int, str],
        image_file_by_page: Dict[int, List[str]],
        *,
        scanned_pages: Optional[set[int]] = None,
    ) -> Dict[int, List[str]]:
        return resolve_page_image_refs(
            content_flow,
            image_file_by_xref,
            image_file_by_page,
            scanned_pages=scanned_pages,
        )

    def _filter_epub_images_by_usage(
        self, epub_images: List[EpubImage], page_image_refs: Dict[int, List[str]]
    ) -> List[EpubImage]:
        return filter_epub_images_by_usage(epub_images, page_image_refs)

    def _render_content_flow_to_xhtml(
        self,
        content_flow: List[Dict[str, Any]],
        image_file_by_xref: Dict[int, str],
    ) -> str:
        return render_content_flow_to_xhtml(content_flow, image_file_by_xref)

    def _render_text_with_page_images(
        self, total_text: str, page_image_refs: Dict[int, List[str]]
    ) -> str:
        return render_text_with_page_images(total_text, page_image_refs)

    def _render_markdown_to_xhtml_body(
        self,
        markdown_text: str,
        page_image_refs: Dict[int, List[str]],
        *,
        math_image_refs: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> str:
        return render_markdown_to_xhtml_body(
            markdown_text,
            page_image_refs,
            math_image_refs=math_image_refs,
        )

    def _split_text_to_paragraphs(self, text: str) -> List[str]:
        return split_text_to_paragraphs(text)

    def _wrap_text_block(self, text: str) -> str:
        return wrap_text_block(text)

    def _render_preserved_lines_block(self, lines: List[tuple[int, str]]) -> str:
        return render_preserved_lines_block(lines)

    def _render_image_figure_group(self, image_refs: List[str]) -> str:
        return render_image_figure_group(image_refs)

    def _render_image_figure(
        self,
        file_name: str,
        *,
        alt_text: str = "문서 이미지",
        caption_text: Optional[str] = None,
        css_class: Optional[str] = None,
    ) -> str:
        return render_image_figure(
            file_name,
            alt_text=alt_text,
            caption_text=caption_text,
            css_class=css_class,
        )

    def _extract_math_image_marker(self, line: str) -> Optional[str]:
        return extract_math_image_marker(line)

    def _build_scan_math_image_assets(
        self,
        raw_images: Any,
        assets: List[EpubImage],
    ) -> Dict[str, Dict[str, str]]:
        return build_scan_math_image_assets(raw_images, assets)

    def _resolve_image_format(self, image_format: str) -> tuple[str, str]:
        return resolve_image_format(image_format)

    def _normalize_image_for_epub(
        self, image_bytes: bytes, image_format: str
    ) -> Optional[tuple[str, str, bytes]]:
        return normalize_image_for_epub(image_bytes, image_format)


# 전역 오케스트레이터 인스턴스 (간단 의존성)
_orchestrator: Optional[ConversionOrchestrator] = None


def get_orchestrator(settings: Optional[Settings] = None) -> ConversionOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ConversionOrchestrator(settings or get_settings())
    return _orchestrator
