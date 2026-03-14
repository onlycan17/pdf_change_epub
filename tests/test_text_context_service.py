"""TextContextCorrector 단위 테스트."""

from __future__ import annotations

import pytest

from app.services.text_context_service import TextContextCorrector


@pytest.mark.asyncio
async def test_correct_chunk_entries_returns_raw_text_when_disabled() -> None:
    service = TextContextCorrector()
    service.enabled = False

    chunks = [
        {"start_page": 1, "end_page": 2, "total_text": "첫 번째 청크"},
        {"start_page": 3, "end_page": 4, "total_text": "두 번째 청크"},
    ]

    result = await service.correct_chunk_entries(chunks)
    assert result == "첫 번째 청크\n\n두 번째 청크"


@pytest.mark.asyncio
async def test_correct_chunk_entries_uses_context_and_merges() -> None:
    service = TextContextCorrector()
    service.enabled = True

    chunks = [
        {"start_page": 1, "end_page": 2, "total_text": "첫 청크 원문"},
        {"start_page": 3, "end_page": 4, "total_text": "둘 청크 원문"},
    ]

    seen_prompts = []

    async def fake_request_correction(*, prompt: str) -> str:
        seen_prompts.append(prompt)
        if "1~2페이지" in prompt:
            return "첫 청크 보정"
        return "둘 청크 보정"

    service._request_correction = fake_request_correction  # type: ignore[method-assign]

    result = await service.correct_chunk_entries(chunks)
    assert result == "첫 청크 보정\n\n둘 청크 보정"
    assert len(seen_prompts) == 2
    assert "1~2페이지" in seen_prompts[0]
    assert "3~4페이지" in seen_prompts[1]


@pytest.mark.asyncio
async def test_correct_chunk_entries_fallbacks_on_request_error() -> None:
    service = TextContextCorrector()
    service.enabled = True

    chunks = [{"start_page": 1, "end_page": 1, "total_text": "원문 유지"}]

    async def failing_request(*, prompt: str) -> str:
        raise RuntimeError("network fail")

    service._request_correction = failing_request  # type: ignore[method-assign]

    result = await service.correct_chunk_entries(chunks)
    assert result == "원문 유지"


@pytest.mark.asyncio
async def test_request_correction_uses_fallback_model() -> None:
    service = TextContextCorrector()
    service.enabled = True
    service.model_name = "deepseek/deepseek-v3.2"
    service.fallback_model_name = "nvidia/nemotron-3-nano-30b-a3b"

    calls = []

    async def fake_request_with_model(*, prompt: str, model_name: str) -> str:
        calls.append(model_name)
        if model_name == "deepseek/deepseek-v3.2":
            raise RuntimeError("primary failed")
        return "fallback success"

    service._request_correction_with_model = fake_request_with_model  # type: ignore[method-assign]

    result = await service._request_correction(prompt="test prompt")
    assert result == "fallback success"
    assert calls == [
        "deepseek/deepseek-v3.2",
        "nvidia/nemotron-3-nano-30b-a3b",
    ]


@pytest.mark.asyncio
async def test_correct_chunk_entries_reports_progress_and_stats() -> None:
    service = TextContextCorrector()
    service.enabled = True
    service.model_name = "deepseek/deepseek-v3.2"
    service.fallback_model_name = "nvidia/nemotron-3-nano-30b-a3b"

    async def fake_request_with_model(*, prompt: str, model_name: str) -> str:
        return f"{model_name}-ok"

    service._request_correction_with_model = fake_request_with_model  # type: ignore[method-assign]

    progress_events = []

    async def on_progress(processed: int, total: int) -> None:
        progress_events.append((processed, total))

    result = await service.correct_chunk_entries(
        [
            {"start_page": 1, "end_page": 1, "total_text": "첫 청크"},
            {"start_page": 2, "end_page": 2, "total_text": "둘 청크"},
        ],
        on_chunk_progress=on_progress,
    )

    assert "deepseek/deepseek-v3.2-ok" in result
    assert progress_events == [(1, 2), (2, 2)]
    assert service.last_run_stats["total_chunks"] == 2
    assert service.last_run_stats["total_attempts"] == 2
    assert service.last_run_stats["last_used_model"] == "deepseek/deepseek-v3.2"
    assert service.last_run_stats["fallback_used"] is False


@pytest.mark.asyncio
async def test_reflow_document_text_returns_raw_text_when_disabled() -> None:
    service = TextContextCorrector()
    service.enabled = False

    original = "첫 문단\n\n둘째 문단"

    result = await service.reflow_document_text(original)

    assert result == original


@pytest.mark.asyncio
async def test_reflow_document_text_uses_segment_context_and_progress() -> None:
    service = TextContextCorrector()
    service.enabled = True
    service.document_segment_chars = 18
    service.max_context_chars = 8

    seen_segments = []
    progress_events = []

    async def fake_request_document_reflow(
        *,
        current_text: str,
        prev_tail: str,
        next_head: str,
        mode: str,
    ) -> str:
        seen_segments.append((current_text, prev_tail, next_head, mode))
        return f"[{mode}]{current_text.strip()}"

    service._request_document_reflow = fake_request_document_reflow  # type: ignore[method-assign]

    async def on_progress(processed: int, total: int) -> None:
        progress_events.append((processed, total))

    source = "첫 문단은 길게 이어집니다.\n\n둘째 문단도 이어집니다.\n\n셋째 문단입니다."
    result = await service.reflow_document_text(
        source,
        on_segment_progress=on_progress,
    )

    assert result.count("[plain]") == 3
    assert progress_events == [(1, 3), (2, 3), (3, 3)]
    assert seen_segments[0][1] == ""
    assert seen_segments[0][3] == "plain"
    assert "둘째 문단" in seen_segments[0][2]
    assert "이어집니다." in seen_segments[1][1]
    assert service.last_run_stats["total_chunks"] == 3
    assert service.last_run_stats["total_attempts"] == 3


@pytest.mark.asyncio
async def test_reflow_document_text_falls_back_to_original_segment() -> None:
    service = TextContextCorrector()
    service.enabled = True
    service.document_segment_chars = 20

    async def failing_request_document_reflow(
        *,
        current_text: str,
        prev_tail: str,
        next_head: str,
        mode: str,
    ) -> str:
        raise RuntimeError("reflow failed")

    service._request_document_reflow = failing_request_document_reflow  # type: ignore[method-assign]

    source = "첫 문단입니다.\n\n둘째 문단입니다."
    result = await service.reflow_document_text(source, mode="markdown")

    assert result == source
