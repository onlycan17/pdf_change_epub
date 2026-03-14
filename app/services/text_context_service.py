"""텍스트 청크 문맥 보정 서비스.

설명:
- 대용량 PDF에서 분할된 텍스트 청크 경계의 문맥 끊김을 줄이기 위해
  이전/다음 청크 일부를 함께 참고하여 현재 청크를 보정합니다.
- API 키가 없거나 호출 실패 시 원문을 그대로 반환하여 안전하게 동작합니다.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx

from app.core.config import Settings, get_settings


logger = logging.getLogger(__name__)


class TextContextCorrector:
    """텍스트 청크 경계 문맥 보정기."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.api_key = (
            self.settings.llm.api_key
            or self.settings.openrouter_api_key
            or os.getenv("OPENROUTER_API_KEY")
            or self.settings.deepseek_api_key
            or self.settings.openai_api_key
        )
        self.base_url = self.settings.llm.base_url.rstrip("/")
        self.model_name = self.settings.llm.context_primary_model
        self.fallback_model_name = self.settings.llm.context_fallback_model
        self.max_tokens = self.settings.llm.max_tokens
        self.temperature = self.settings.llm.temperature
        self.timeout = self.settings.llm.timeout
        self.enabled = bool(self.api_key)
        self.max_context_chars = 1200
        self.document_segment_chars = 3500
        self.last_run_stats: Dict[str, Any] = {
            "total_chunks": 0,
            "total_attempts": 0,
            "last_used_model": None,
            "fallback_used": False,
        }
        self._last_model_used: Optional[str] = None
        self._last_attempt_count: int = 0
        self._last_fallback_used: bool = False

    async def correct_chunk_entries(
        self,
        chunks: List[Dict[str, Any]],
        on_chunk_progress: Optional[Callable[[int, int], Awaitable[None]]] = None,
    ) -> str:
        """청크 목록을 문맥 보정 후 하나의 텍스트로 합칩니다."""
        texts = [str(chunk.get("total_text", "")) for chunk in chunks if chunk]
        if not texts:
            self._set_last_run_stats(total_chunks=0)
            return ""

        if not self.enabled:
            logger.info("LLM API 키가 없어 문맥 보정을 건너뜁니다.")
            self._set_last_run_stats(total_chunks=len(texts))
            return "\n\n".join(texts)

        corrected_parts: List[str] = []
        total_attempts = 0
        last_used_model: Optional[str] = None
        fallback_used = False
        for index, current_text in enumerate(texts):
            prev_tail = self._tail(texts[index - 1]) if index > 0 else ""
            next_head = self._head(texts[index + 1]) if index < len(texts) - 1 else ""
            page_info = self._page_info(chunks[index])

            corrected_text = await self._correct_single_chunk(
                current_text=current_text,
                prev_tail=prev_tail,
                next_head=next_head,
                page_info=page_info,
            )
            corrected_parts.append(corrected_text)
            total_attempts += self._last_attempt_count
            if self._last_model_used:
                last_used_model = self._last_model_used
            fallback_used = fallback_used or self._last_fallback_used
            if on_chunk_progress:
                await on_chunk_progress(index + 1, len(texts))

        self._set_last_run_stats(
            total_chunks=len(texts),
            total_attempts=total_attempts,
            last_used_model=last_used_model,
            fallback_used=fallback_used,
        )
        return "\n\n".join(corrected_parts)

    async def reflow_document_text(
        self,
        text: str,
        *,
        mode: str = "plain",
        on_segment_progress: Optional[Callable[[int, int], Awaitable[None]]] = None,
    ) -> str:
        """문서 전체 흐름을 다시 정리합니다."""
        if not text.strip():
            self._set_last_run_stats(total_chunks=0)
            return text

        segments = self._split_document_segments(text)
        if not self.enabled:
            logger.info("LLM API 키가 없어 문서 흐름 재정리를 건너뜁니다.")
            self._set_last_run_stats(total_chunks=len(segments))
            return text

        reflowed_segments: List[str] = []
        total_attempts = 0
        last_used_model: Optional[str] = None
        fallback_used = False

        for index, segment in enumerate(segments):
            prev_tail = self._tail(segments[index - 1]) if index > 0 else ""
            next_head = (
                self._head(segments[index + 1]) if index < len(segments) - 1 else ""
            )
            reflowed = await self._reflow_single_segment(
                current_text=segment,
                prev_tail=prev_tail,
                next_head=next_head,
                mode=mode,
            )
            reflowed_segments.append(reflowed)
            total_attempts += self._last_attempt_count
            if self._last_model_used:
                last_used_model = self._last_model_used
            fallback_used = fallback_used or self._last_fallback_used
            if on_segment_progress:
                await on_segment_progress(index + 1, len(segments))

        self._set_last_run_stats(
            total_chunks=len(segments),
            total_attempts=total_attempts,
            last_used_model=last_used_model,
            fallback_used=fallback_used,
        )
        return "\n\n".join(reflowed_segments)

    async def _correct_single_chunk(
        self,
        *,
        current_text: str,
        prev_tail: str,
        next_head: str,
        page_info: str,
    ) -> str:
        if not current_text.strip():
            return current_text

        prompt = self._build_prompt(
            current_text=current_text,
            prev_tail=prev_tail,
            next_head=next_head,
            page_info=page_info,
        )

        try:
            corrected = await self._request_correction(prompt=prompt)
            if corrected.strip():
                return corrected.strip()
            return current_text
        except Exception:
            logger.exception("청크 문맥 보정 실패. 원문을 사용합니다.")
            return current_text

    async def _reflow_single_segment(
        self,
        *,
        current_text: str,
        prev_tail: str,
        next_head: str,
        mode: str,
    ) -> str:
        if not current_text.strip():
            return current_text

        try:
            self._last_model_used = None
            self._last_attempt_count = 0
            self._last_fallback_used = False
            reflowed = await self._request_document_reflow(
                current_text=current_text,
                prev_tail=prev_tail,
                next_head=next_head,
                mode=mode,
            )
            if reflowed.strip():
                if self._last_attempt_count == 0:
                    self._last_attempt_count = 1
                return reflowed.strip()
            return current_text
        except Exception:
            logger.exception("문서 흐름 재정리 실패. 원문 구간을 사용합니다.")
            return current_text

    async def _request_correction(self, *, prompt: str) -> str:
        errors: List[str] = []
        tried_models: List[str] = []
        for model in [self.model_name, self.fallback_model_name]:
            if not model:
                continue
            tried_models.append(model)
            try:
                logger.info("문맥 보정 모델 호출 시도", extra={"model": model})
                corrected = await self._request_correction_with_model(
                    prompt=prompt, model_name=model
                )
                if corrected.strip():
                    logger.info("문맥 보정 모델 호출 성공", extra={"model": model})
                    self._last_model_used = model
                    self._last_attempt_count = len(tried_models)
                    self._last_fallback_used = (
                        model == self.fallback_model_name
                        and len(tried_models) > 1
                        and bool(self.fallback_model_name)
                    )
                    return corrected
                errors.append(f"{model}: empty response")
            except Exception as exc:
                logger.warning(
                    "문맥 보정 모델 호출 실패",
                    extra={"model": model, "error": str(exc)},
                )
                errors.append(f"{model}: {exc}")

        self._last_model_used = None
        self._last_attempt_count = len(tried_models)
        self._last_fallback_used = False
        raise RuntimeError(" / ".join(errors) or "all models failed")

    async def _request_document_reflow(
        self,
        *,
        current_text: str,
        prev_tail: str,
        next_head: str,
        mode: str,
    ) -> str:
        prompt = self._build_document_reflow_prompt(
            current_text=current_text,
            prev_tail=prev_tail,
            next_head=next_head,
            mode=mode,
        )
        return await self._request_with_fallback(
            prompt=prompt,
            system_message=(
                "당신은 전자책 편집자입니다. "
                "문장 연결과 문단 구조를 자연스럽게 다듬되 의미를 바꾸지 마세요."
            ),
        )

    async def _request_with_fallback(
        self,
        *,
        prompt: str,
        system_message: str,
    ) -> str:
        errors: List[str] = []
        tried_models: List[str] = []
        for model in [self.model_name, self.fallback_model_name]:
            if not model:
                continue
            tried_models.append(model)
            try:
                logger.info("문맥 보정 모델 호출 시도", extra={"model": model})
                corrected = await self._request_prompt_with_model(
                    prompt=prompt,
                    model_name=model,
                    system_message=system_message,
                )
                if corrected.strip():
                    logger.info("문맥 보정 모델 호출 성공", extra={"model": model})
                    self._last_model_used = model
                    self._last_attempt_count = len(tried_models)
                    self._last_fallback_used = (
                        model == self.fallback_model_name
                        and len(tried_models) > 1
                        and bool(self.fallback_model_name)
                    )
                    return corrected
                errors.append(f"{model}: empty response")
            except Exception as exc:
                logger.warning(
                    "문맥 보정 모델 호출 실패",
                    extra={"model": model, "error": str(exc)},
                )
                errors.append(f"{model}: {exc}")

        self._last_model_used = None
        self._last_attempt_count = len(tried_models)
        self._last_fallback_used = False
        raise RuntimeError(" / ".join(errors) or "all models failed")

    async def _request_prompt_with_model(
        self,
        *,
        prompt: str,
        model_name: str,
        system_message: str,
    ) -> str:
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "system",
                    "content": system_message,
                },
                {"role": "user", "content": prompt},
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
            response.raise_for_status()
            data = response.json()
            content = str(data["choices"][0]["message"]["content"])

        return self._strip_markdown_fence(content)

    async def _request_correction_with_model(
        self, *, prompt: str, model_name: str
    ) -> str:
        return await self._request_prompt_with_model(
            prompt=prompt,
            model_name=model_name,
            system_message=(
                "당신은 한국어 문서 편집자입니다. "
                "현재 청크의 내용만 자연스럽게 보정하고 의미를 바꾸지 마세요."
            ),
        )

    def _build_prompt(
        self,
        *,
        current_text: str,
        prev_tail: str,
        next_head: str,
        page_info: str,
    ) -> str:
        return f"""아래는 PDF 본문에서 분할된 텍스트 청크입니다.
목표: 현재 청크만 자연스럽게 보정하세요.

[주의]
- 의미 추가/삭제 금지
- 제목/본문 구조 유지
- 현재 청크 외 문장을 끌어오지 말고, 경계 어색함만 완화
- 출력은 보정된 본문만 반환

[청크 정보]
{page_info}

[이전 청크 끝부분 참고]
{prev_tail or "(없음)"}

[현재 청크 원문]
{current_text}

[다음 청크 시작부분 참고]
{next_head or "(없음)"}
"""

    def _head(self, text: str) -> str:
        return text[: self.max_context_chars].strip()

    def _tail(self, text: str) -> str:
        return text[-self.max_context_chars :].strip()

    def _page_info(self, chunk: Dict[str, Any]) -> str:
        start_page = chunk.get("start_page")
        end_page = chunk.get("end_page")
        if start_page is None or end_page is None:
            return "페이지 정보 없음"
        return f"{start_page}~{end_page}페이지"

    def _strip_markdown_fence(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if "\n" in cleaned:
                cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    def _build_document_reflow_prompt(
        self,
        *,
        current_text: str,
        prev_tail: str,
        next_head: str,
        mode: str,
    ) -> str:
        structure_rules = [
            "- 의미 추가/삭제 금지",
            "- 잘린 문장을 자연스럽게 연결",
            "- 제목, 문단, 목록 구조 유지",
        ]
        if mode == "markdown":
            structure_rules.extend(
                [
                    "- 마크다운 제목/목록/강조 문법 유지",
                    "- [[VERSE]], [[LINE:n]], [[MATHIMG:...]] 표식 보존",
                    "- 출력은 마크다운 본문만 반환",
                ]
            )
        else:
            structure_rules.extend(
                [
                    "- 필요 없는 줄바꿈만 정리하고 문단 경계는 살리기",
                    "- 출력은 정리된 본문만 반환",
                ]
            )

        rules = "\n".join(structure_rules)
        return f"""아래는 EPUB로 변환할 문서의 일부 구간입니다.
목표: 현재 구간만 다듬어 문장 흐름과 구조를 읽기 좋게 정리하세요.

[주의]
{rules}

[이전 구간 끝부분 참고]
{prev_tail or "(없음)"}

[현재 구간 원문]
{current_text}

[다음 구간 시작부분 참고]
{next_head or "(없음)"}
"""

    def _split_document_segments(self, text: str) -> List[str]:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not normalized:
            return []

        paragraphs = [
            part.strip()
            for part in re.split(r"\n{2,}", normalized)
            if part and part.strip()
        ]
        if not paragraphs:
            return [normalized]

        segments: List[str] = []
        current_parts: List[str] = []
        current_length = 0

        for paragraph in paragraphs:
            paragraph_parts = self._split_long_paragraph(paragraph)
            for part in paragraph_parts:
                addition = len(part) if not current_parts else len(part) + 2
                if (
                    current_parts
                    and current_length + addition > self.document_segment_chars
                ):
                    segments.append("\n\n".join(current_parts))
                    current_parts = [part]
                    current_length = len(part)
                    continue

                current_parts.append(part)
                current_length += addition

        if current_parts:
            segments.append("\n\n".join(current_parts))

        return segments or [normalized]

    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        if len(paragraph) <= self.document_segment_chars:
            return [paragraph]

        sentence_like_parts = [
            part.strip()
            for part in re.split(r"(?<=[.!?다요])\s+", paragraph)
            if part and part.strip()
        ]
        if len(sentence_like_parts) <= 1:
            return [
                paragraph[i : i + self.document_segment_chars].strip()
                for i in range(0, len(paragraph), self.document_segment_chars)
                if paragraph[i : i + self.document_segment_chars].strip()
            ]

        chunks: List[str] = []
        current = ""
        for part in sentence_like_parts:
            candidate = part if not current else f"{current} {part}"
            if current and len(candidate) > self.document_segment_chars:
                chunks.append(current)
                current = part
            else:
                current = candidate

        if current:
            chunks.append(current)
        return chunks

    def _set_last_run_stats(
        self,
        *,
        total_chunks: int,
        total_attempts: int = 0,
        last_used_model: Optional[str] = None,
        fallback_used: bool = False,
    ) -> None:
        self.last_run_stats = {
            "total_chunks": total_chunks,
            "total_attempts": total_attempts,
            "last_used_model": last_used_model,
            "fallback_used": fallback_used,
        }


def create_text_context_corrector(
    settings: Optional[Settings] = None,
) -> TextContextCorrector:
    return TextContextCorrector(settings)
