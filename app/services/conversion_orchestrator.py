"""변환 파이프라인 통합 관리자(오케스트레이터)

설명: PDF → EPUB 과정을 단계별로 조율하고, 진행 상태를 추적/조회/취소하는 서비스.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from html import escape
from io import BytesIO
import re
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
        self.text_context_corrector = create_text_context_corrector(self.settings)
        self.epub = EpubGenerator(language="ko")

    async def start(
        self,
        *,
        conversion_id: str,
        filename: str,
        file_size: int,
        ocr_enabled: bool,
        translate_to_korean: bool = False,
        pdf_bytes: bytes,
    ) -> ConversionJob:
        job = ConversionJob(
            conversion_id=conversion_id,
            filename=filename,
            file_size=file_size,
            ocr_enabled=ocr_enabled,
            translate_to_korean=translate_to_korean,
            source_pdf_bytes=pdf_bytes,
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
                    # 문맥 경계 보정 단계:
                    # 이전/다음 청크 일부를 참고해 현재 청크의 문장 연결을 자연스럽게 보정
                    if pdf_type in (PDFType.TEXT_BASED, PDFType.MIXED):
                        await set_step("context_correction", 60, "문맥 보정 중")

                        async def on_context_progress(
                            processed_chunks: int, total_chunks: int
                        ) -> None:
                            if total_chunks <= 0:
                                return
                            progress_delta = int((processed_chunks / total_chunks) * 15)
                            context_progress = min(75, 60 + progress_delta)
                            await set_step(
                                "context_correction",
                                context_progress,
                                f"문맥 보정 중 ({processed_chunks}/{total_chunks})",
                            )

                        corrected_text = (
                            await self.text_context_corrector.correct_chunk_entries(
                                chunks,
                                on_chunk_progress=on_context_progress,
                            )
                        )
                        llm_stats = getattr(
                            self.text_context_corrector, "last_run_stats", {}
                        )
                        await self.store.update(
                            conversion_id,
                            llm_used_model=llm_stats.get("last_used_model"),
                            llm_attempt_count=int(llm_stats.get("total_attempts", 0)),
                            llm_fallback_used=bool(
                                llm_stats.get("fallback_used", False)
                            ),
                        )
                        text_result = {"total_text": corrected_text}
                    else:
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
                synthesis_markdown = clean_text_for_epub_body(
                    synthesis.markdown_content
                )

            # 취소 확인
            if (await self.store.get(conversion_id)).is_cancelled():
                return

            # 4) EPUB 생성
            await set_step("epub", 80, "EPUB 생성 중")
            content_flow = self._extract_content_flow_pages(pdf_bytes)
            (
                epub_images,
                image_file_by_xref,
                image_file_by_page,
            ) = self._build_epub_image_assets(pdf_bytes)
            page_image_refs = self._resolve_page_image_refs(
                content_flow,
                image_file_by_xref,
                image_file_by_page,
            )

            chapters: List[Chapter] = []
            if synthesis_markdown:
                html_body = self._render_markdown_to_xhtml_body(
                    synthesis_markdown,
                    page_image_refs,
                )
                chapters.append(
                    Chapter(
                        title="Converted", file_name="chapter1.xhtml", content=html_body
                    )
                )
            elif text_result and text_result.get("total_text"):
                # 텍스트를 단순 문단화
                total_text: str = clean_text_for_epub_body(
                    str(text_result.get("total_text"))
                )
                html_body = self._render_text_with_page_images(
                    total_text,
                    page_image_refs,
                )
                chapters.append(
                    Chapter(
                        title="Converted", file_name="chapter1.xhtml", content=html_body
                    )
                )
            elif content_flow:
                html_body = self._render_content_flow_to_xhtml(
                    content_flow,
                    image_file_by_xref,
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
                for page in sorted(page_image_refs.keys()):
                    chapters[0].content += self._render_image_figure_group(
                        page_image_refs[page]
                    )

            epub_bytes = self.epub.create_epub_bytes(
                title="변환된 문서",
                author="",
                chapters=chapters,
                images=epub_images,
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

    def _build_epub_image_assets(
        self, pdf_bytes: bytes
    ) -> tuple[List[EpubImage], Dict[int, str], Dict[int, List[str]]]:
        """PDF에서 추출한 이미지를 EPUB 리소스로 변환합니다."""
        try:
            raw_images = self.pdf_extractor.extract_images_from_pdf(pdf_bytes)
        except Exception:
            logger.exception("PDF 이미지 추출 실패. 텍스트만으로 EPUB을 생성합니다.")
            return [], {}, {}

        if not isinstance(raw_images, list):
            return [], {}, {}

        assets: List[EpubImage] = []
        image_file_by_xref: Dict[int, str] = {}
        image_file_by_page: Dict[int, List[str]] = {}
        for index, image_info in enumerate(raw_images, start=1):
            if not isinstance(image_info, dict):
                continue
            image_bytes = image_info.get("image_bytes")
            image_format = str(image_info.get("format", "png")).lower()
            if not isinstance(image_bytes, bytes) or not image_bytes:
                continue

            normalized = self._normalize_image_for_epub(image_bytes, image_format)
            if normalized is None:
                logger.warning(
                    "이미지 정규화 실패로 해당 이미지를 건너뜁니다",
                    extra={"index": index, "format": image_format},
                )
                continue
            ext, media_type, normalized_bytes = normalized
            file_name = f"images/image-{index}.{ext}"
            assets.append(
                EpubImage(
                    file_name=file_name,
                    media_type=media_type,
                    data=normalized_bytes,
                )
            )
            xref_value = image_info.get("xref")
            if isinstance(xref_value, int):
                image_file_by_xref[xref_value] = file_name
            page_value = image_info.get("page")
            if isinstance(page_value, int):
                image_file_by_page.setdefault(page_value, []).append(file_name)

        return assets, image_file_by_xref, image_file_by_page

    def _extract_content_flow_pages(self, pdf_bytes: bytes) -> List[Dict[str, Any]]:
        try:
            flow = self.pdf_extractor.extract_content_flow_with_images(pdf_bytes)
        except Exception:
            logger.exception("콘텐츠 흐름 추출 실패. 기본 렌더링으로 진행합니다.")
            return []
        pages = flow.get("pages") if isinstance(flow, dict) else None
        if not isinstance(pages, list):
            return []
        return [page for page in pages if isinstance(page, dict)]

    def _resolve_page_image_refs(
        self,
        content_flow: List[Dict[str, Any]],
        image_file_by_xref: Dict[int, str],
        image_file_by_page: Dict[int, List[str]],
    ) -> Dict[int, List[str]]:
        page_refs: Dict[int, List[str]] = {
            page: list(refs) for page, refs in image_file_by_page.items()
        }
        for page_entry in content_flow:
            page_num = page_entry.get("page")
            elements = page_entry.get("elements")
            if not isinstance(page_num, int) or not isinstance(elements, list):
                continue
            refs: List[str] = []
            for element in elements:
                if not isinstance(element, dict) or element.get("type") != "image":
                    continue
                xref = element.get("xref")
                if isinstance(xref, int):
                    file_name = image_file_by_xref.get(xref)
                    if file_name:
                        refs.append(file_name)
            if refs:
                page_refs[page_num] = refs
        return page_refs

    def _render_content_flow_to_xhtml(
        self,
        content_flow: List[Dict[str, Any]],
        image_file_by_xref: Dict[int, str],
    ) -> str:
        html_parts: List[str] = []
        for page_entry in content_flow:
            page_num = page_entry.get("page")
            elements = page_entry.get("elements")
            if not isinstance(page_num, int) or not isinstance(elements, list):
                continue

            html_parts.append("<section>")
            for element in elements:
                if not isinstance(element, dict):
                    continue
                element_type = element.get("type")
                if element_type == "text":
                    text = clean_text_for_epub_body(
                        str(element.get("text", ""))
                    ).strip()
                    if not text:
                        continue
                    for paragraph in self._split_text_to_paragraphs(text):
                        html_parts.append(f"<p>{escape(paragraph)}</p>")
                    continue

                if element_type == "image":
                    xref = element.get("xref")
                    if isinstance(xref, int):
                        file_name = image_file_by_xref.get(xref)
                        if file_name:
                            html_parts.append(self._render_image_figure(file_name))
            html_parts.append("</section>")
        return "".join(html_parts)

    def _render_text_with_page_images(
        self, total_text: str, page_image_refs: Dict[int, List[str]]
    ) -> str:
        """문맥 보정 텍스트를 우선 사용하고, 페이지 경계에 이미지를 배치합니다."""
        page_sections = re.split(r"===\s*페이지\s*(\d+)\s*===", total_text)
        html_parts: List[str] = []
        inserted_pages: set[int] = set()

        if len(page_sections) <= 1:
            for line in total_text.split("\n"):
                if line.strip():
                    html_parts.append(f"<p>{escape(line)}</p>")
            for page in sorted(page_image_refs.keys()):
                html_parts.append(
                    self._render_image_figure_group(page_image_refs[page])
                )
            return "".join(html_parts)

        leading = page_sections[0].strip()
        if leading:
            for line in leading.split("\n"):
                if line.strip():
                    html_parts.append(f"<p>{escape(line)}</p>")

        for idx in range(1, len(page_sections), 2):
            page_str = page_sections[idx].strip()
            body = page_sections[idx + 1] if idx + 1 < len(page_sections) else ""
            if not page_str.isdigit():
                continue
            page_num = int(page_str)
            for line in body.split("\n"):
                if line.strip():
                    html_parts.append(f"<p>{escape(line)}</p>")
            if page_num in page_image_refs:
                html_parts.append(
                    self._render_image_figure_group(page_image_refs[page_num])
                )
                inserted_pages.add(page_num)

        for page in sorted(page_image_refs.keys()):
            if page in inserted_pages:
                continue
            html_parts.append(self._render_image_figure_group(page_image_refs[page]))

        return "".join(html_parts)

    def _render_markdown_to_xhtml_body(
        self, markdown_text: str, page_image_refs: Dict[int, List[str]]
    ) -> str:
        lines = markdown_text.splitlines()
        html_parts: List[str] = []
        paragraph_buf: List[str] = []
        list_items: List[str] = []
        list_type: Optional[str] = None
        in_code_block = False
        code_lines: List[str] = []
        inserted_pages: set[int] = set()

        def flush_paragraph() -> None:
            if paragraph_buf:
                html_parts.append(f"<p>{escape(' '.join(paragraph_buf))}</p>")
                paragraph_buf.clear()

        def flush_list() -> None:
            nonlocal list_items, list_type
            if not list_items or not list_type:
                return
            html_parts.append(f"<{list_type}>")
            for item in list_items:
                html_parts.append(f"<li>{escape(item)}</li>")
            html_parts.append(f"</{list_type}>")
            list_items = []
            list_type = None

        def flush_code() -> None:
            nonlocal code_lines
            if code_lines:
                html_parts.append("<pre><code>")
                html_parts.append(escape("\n".join(code_lines)))
                html_parts.append("</code></pre>")
                code_lines = []

        for raw_line in lines:
            line = raw_line.rstrip()
            stripped = line.strip()

            if stripped.startswith("<!--") and stripped.endswith("-->"):
                continue

            if stripped.startswith("```"):
                flush_paragraph()
                flush_list()
                if in_code_block:
                    flush_code()
                    in_code_block = False
                else:
                    in_code_block = True
                continue

            if in_code_block:
                code_lines.append(line)
                continue

            if not stripped:
                flush_paragraph()
                flush_list()
                continue

            heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
            if heading:
                flush_paragraph()
                flush_list()
                level = len(heading.group(1))
                title = heading.group(2).strip()
                html_parts.append(f"<h{level}>{escape(title)}</h{level}>")
                page_match = re.search(r"페이지\s*(\d+)", title)
                if page_match:
                    page_num = int(page_match.group(1))
                    if page_num in page_image_refs and page_num not in inserted_pages:
                        html_parts.append(
                            self._render_image_figure_group(page_image_refs[page_num])
                        )
                        inserted_pages.add(page_num)
                continue

            ordered = re.match(r"^\d+\.\s+(.+)$", stripped)
            unordered = re.match(r"^[-*]\s+(.+)$", stripped)
            if ordered or unordered:
                flush_paragraph()
                desired_type = "ol" if ordered else "ul"
                match = ordered or unordered
                if not match:
                    continue
                item_text = match.group(1).strip()
                if list_type and list_type != desired_type:
                    flush_list()
                list_type = desired_type
                list_items.append(item_text)
                continue

            if stripped.startswith(">"):
                flush_paragraph()
                flush_list()
                html_parts.append(
                    f"<blockquote>{escape(stripped[1:].strip())}</blockquote>"
                )
                continue

            paragraph_buf.append(stripped)

        flush_paragraph()
        flush_list()
        if in_code_block:
            flush_code()

        for page_num, refs in sorted(page_image_refs.items()):
            if page_num in inserted_pages:
                continue
            html_parts.append(self._render_image_figure_group(refs))

        return "".join(html_parts)

    def _split_text_to_paragraphs(self, text: str) -> List[str]:
        parts = [segment.strip() for segment in text.split("\n") if segment.strip()]
        return parts if parts else [text]

    def _render_image_figure_group(self, image_refs: List[str]) -> str:
        return "".join(self._render_image_figure(file_name) for file_name in image_refs)

    def _render_image_figure(self, file_name: str) -> str:
        safe_name = escape(file_name)
        return "<figure>" f'<img src="{safe_name}" alt="문서 이미지" />' "</figure>"

    def _resolve_image_format(self, image_format: str) -> tuple[str, str]:
        mapping = {
            "jpg": ("jpg", "image/jpeg"),
            "jpeg": ("jpg", "image/jpeg"),
            "png": ("png", "image/png"),
            "webp": ("webp", "image/webp"),
            "gif": ("gif", "image/gif"),
            "bmp": ("bmp", "image/bmp"),
        }
        return mapping.get(image_format, ("png", "image/png"))

    def _normalize_image_for_epub(
        self, image_bytes: bytes, image_format: str
    ) -> Optional[tuple[str, str, bytes]]:
        ext, media_type = self._resolve_image_format(image_format)
        supported_input_formats = {"jpg", "jpeg", "png", "webp", "gif", "bmp"}
        if image_format in supported_input_formats:
            return ext, media_type, image_bytes

        try:
            from PIL import Image

            with Image.open(BytesIO(image_bytes)) as image:
                buffer = BytesIO()
                image.convert("RGB").save(buffer, format="PNG")
                return "png", "image/png", buffer.getvalue()
        except Exception:
            logger.exception(
                "미지원 이미지 포맷 변환 실패",
                extra={"format": image_format},
            )
            return None


# 전역 오케스트레이터 인스턴스 (간단 의존성)
_orchestrator: Optional[ConversionOrchestrator] = None


def get_orchestrator(settings: Optional[Settings] = None) -> ConversionOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ConversionOrchestrator(settings or get_settings())
    return _orchestrator
