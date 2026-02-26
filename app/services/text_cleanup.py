"""Text cleanup for EPUB body."""

from __future__ import annotations

import re
from typing import List


_RE_KO_PAGE_ONLY = re.compile(r"^\s*페이지\s*\d{1,4}\s*$")
_RE_EN_PAGE_ONLY = re.compile(r"^\s*page\s*\d{1,4}\s*$", re.IGNORECASE)
_RE_FOOTER_DASH_PAGE = re.compile(
    r"^\s*[-\u2013\u2014]\s*\d{1,4}\s*[-\u2013\u2014]\s*$"
)
_RE_DIGITS_ONLY = re.compile(r"^\s*\d{1,3}\s*$")
_RE_HWP_FILENAME = re.compile(r"^\s*[^\n\r]{1,200}\.hwp\s*$", re.IGNORECASE)


def _is_watermark_line(line: str) -> bool:
    lowered = line.strip().lower()
    if not lowered:
        return False
    return (
        "pdftoepub converter" in lowered
        or "pdf to epub converter" in lowered
        or lowered == "pdftoepub"
    )


def _is_banner_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if "이 자료는 저작권에 의해 보호됩니다" in stripped:
        return True
    if stripped == "다음에서 발췌":
        return True
    return False


def clean_text_for_epub_body(text: str) -> str:
    if not text:
        return ""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    original_lines = normalized.split("\n")
    stripped_lines: List[str] = [ln.strip() for ln in original_lines]

    remove: set[int] = set()

    def mark_if(predicate, idx: int) -> None:
        if 0 <= idx < len(stripped_lines) and predicate(stripped_lines[idx]):
            remove.add(idx)

    def is_page_marker(ln: str) -> bool:
        return bool(
            _RE_KO_PAGE_ONLY.match(ln)
            or _RE_EN_PAGE_ONLY.match(ln)
            or _RE_FOOTER_DASH_PAGE.match(ln)
        )

    for i, ln in enumerate(stripped_lines):
        if not ln:
            continue

        if _is_watermark_line(ln) or _is_banner_line(ln):
            remove.add(i)
            continue

        if is_page_marker(ln):
            remove.add(i)
            mark_if(lambda s: bool(_RE_DIGITS_ONLY.match(s)), i - 1)
            mark_if(lambda s: bool(_RE_DIGITS_ONLY.match(s)), i + 1)
            mark_if(lambda s: bool(_RE_HWP_FILENAME.match(s)), i - 1)
            mark_if(lambda s: bool(_RE_HWP_FILENAME.match(s)), i + 1)
            continue

        if _RE_HWP_FILENAME.match(ln):
            remove.add(i)
            mark_if(lambda s: bool(_RE_DIGITS_ONLY.match(s)), i - 1)
            mark_if(lambda s: bool(_RE_DIGITS_ONLY.match(s)), i + 1)
            mark_if(is_page_marker, i - 1)
            mark_if(is_page_marker, i + 1)

    out: List[str] = []
    blank_run = 0

    for idx, raw in enumerate(original_lines):
        if idx in remove:
            continue

        ln = raw.strip()
        if not ln:
            blank_run += 1
            if blank_run <= 2:
                out.append("")
            continue

        blank_run = 0
        out.append(ln)

    while out and out[0] == "":
        out.pop(0)
    while out and out[-1] == "":
        out.pop()

    return "\n".join(out)
