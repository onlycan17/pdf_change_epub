from __future__ import annotations

import logging
import os
from typing import Awaitable, Callable, List, Optional

import httpx

from app.core.config import Settings, get_settings


logger = logging.getLogger(__name__)


class TextTranslator:
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
        self.model_name = self.settings.llm.translation_model
        self.fallback_model_name = self.settings.llm.translation_fallback_model
        self.max_tokens = self.settings.llm.max_tokens
        self.temperature = self.settings.llm.temperature
        self.timeout = self.settings.llm.timeout
        self.enabled = bool(self.api_key)

    async def translate_english_to_korean(
        self,
        text: str,
        *,
        on_chunk_progress: Optional[Callable[[int, int], Awaitable[None]]] = None,
    ) -> str:
        if not text.strip():
            return text

        if not self.enabled:
            logger.info("LLM API 키가 없어 번역을 건너뜁니다.")
            return text

        segments = _split_markdown_code_fences(text)
        translatable_segment_indices = [
            idx for idx, (_, translatable) in enumerate(segments) if translatable
        ]
        total_chunks = sum(
            len(_split_text_into_chunks(segments[idx][0]))
            for idx in translatable_segment_indices
        )

        completed_chunks = 0
        out: List[str] = []
        for segment, translatable in segments:
            if not translatable:
                out.append(segment)
                continue

            segment_chunks = _split_text_into_chunks(segment)
            translated_segment_chunks: List[str] = []
            for chunk in segment_chunks:
                translated_segment_chunks.append(await self._translate_chunk(chunk))
                completed_chunks += 1
                if on_chunk_progress:
                    await on_chunk_progress(completed_chunks, max(1, total_chunks))
            out.append("".join(translated_segment_chunks))

        return "".join(out)

    async def _translate_chunk(self, text: str) -> str:
        errors: List[str] = []
        for model in [self.model_name, self.fallback_model_name]:
            if not model:
                continue
            try:
                return await self._request_translation_with_model(
                    text=text,
                    model_name=model,
                )
            except Exception as exc:
                errors.append(f"{model}: {exc}")
                logger.warning(
                    "번역 모델 호출 실패",
                    extra={"model": model, "error": str(exc)},
                )

        raise RuntimeError(" / ".join(errors) or "all models failed")

    async def _request_translation_with_model(
        self, *, text: str, model_name: str
    ) -> str:
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "당신은 전문 번역가입니다. "
                        "입력된 영어 텍스트를 자연스러운 한국어로 번역하세요. "
                        "형식(줄바꿈, 공백), 숫자, URL, 파일 경로, 코드, 고유명사는 가능한 한 유지하세요. "
                        "추가 설명 없이 번역 결과만 반환하세요."
                    ),
                },
                {
                    "role": "user",
                    "content": """아래 텍스트를 한국어로 번역하세요.

[규칙]
- 원문의 줄바꿈/단락 구조를 유지
- URL/이메일/파일경로/버전/해시/코드 블록은 번역하지 않기
- 단위(GB, MB, %, $ 등)와 숫자 형식 유지
- 결과는 번역문만 출력

[텍스트]
```\n"""
                    + text
                    + "\n```",
                },
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

        return _strip_markdown_fence(content)


def create_text_translator(settings: Optional[Settings] = None) -> TextTranslator:
    return TextTranslator(settings)


def _strip_markdown_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if "\n" in cleaned:
            cleaned = cleaned.split("\n", 1)[1]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def _split_markdown_code_fences(text: str) -> List[tuple[str, bool]]:
    parts: List[tuple[str, bool]] = []
    cursor = 0
    in_fence = False
    while cursor < len(text):
        fence_index = text.find("```", cursor)
        if fence_index == -1:
            parts.append((text[cursor:], not in_fence))
            break
        if fence_index > cursor:
            parts.append((text[cursor:fence_index], not in_fence))
        parts.append(("```", False))
        cursor = fence_index + 3
        in_fence = not in_fence
    return parts


def _split_text_into_chunks(text: str, max_chars: int = 6000) -> List[str]:
    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n\n")
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0
    for paragraph in paragraphs:
        piece = paragraph if paragraph else ""
        extra_len = len(piece) + (2 if current else 0)
        if current and current_len + extra_len > max_chars:
            chunks.append("\n\n".join(current))
            current = [piece]
            current_len = len(piece)
            continue
        if current:
            current_len += 2
        current.append(piece)
        current_len += len(piece)

    if current:
        chunks.append("\n\n".join(current))

    return chunks
