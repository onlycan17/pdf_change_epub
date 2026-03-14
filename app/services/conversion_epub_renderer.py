from __future__ import annotations

import logging
import re
from html import escape
from io import BytesIO
from typing import Any, Dict, List, Optional

from app.services.epub_service import EpubImage
from app.services.mathml_service import render_block_with_math, render_text_with_math
from app.services.text_cleanup import clean_text_for_epub_body

logger = logging.getLogger(__name__)


def build_epub_image_assets(
    pdf_extractor: Any,
    pdf_bytes: bytes,
) -> tuple[List[EpubImage], Dict[int, str], Dict[int, List[str]]]:
    try:
        raw_images = pdf_extractor.extract_images_from_pdf(pdf_bytes)
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
        page_value = image_info.get("page")
        image_bytes = image_info.get("image_bytes")
        image_format = str(image_info.get("format", "png")).lower()
        if not isinstance(image_bytes, bytes) or not image_bytes:
            continue

        normalized = normalize_image_for_epub(image_bytes, image_format)
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
        if isinstance(page_value, int):
            image_file_by_page.setdefault(page_value, []).append(file_name)

    return assets, image_file_by_xref, image_file_by_page


def is_page_sized_scan_image(image_info: Dict[str, Any]) -> bool:
    full_page_flag = image_info.get("is_full_page_scan")
    if isinstance(full_page_flag, str):
        return full_page_flag.strip().lower() == "true"
    if isinstance(full_page_flag, bool):
        return full_page_flag

    coverage_ratio = image_info.get("coverage_ratio")
    if isinstance(coverage_ratio, (int, float)):
        return float(coverage_ratio) >= 0.95

    return False


def extract_content_flow_pages(
    pdf_extractor: Any,
    pdf_bytes: bytes,
) -> List[Dict[str, Any]]:
    try:
        flow = pdf_extractor.extract_content_flow_with_images(pdf_bytes)
    except Exception:
        logger.exception("콘텐츠 흐름 추출 실패. 기본 렌더링으로 진행합니다.")
        return []
    pages = flow.get("pages") if isinstance(flow, dict) else None
    if not isinstance(pages, list):
        return []
    return [page for page in pages if isinstance(page, dict)]


def resolve_page_image_refs(
    content_flow: List[Dict[str, Any]],
    image_file_by_xref: Dict[int, str],
    image_file_by_page: Dict[int, List[str]],
    *,
    scanned_pages: Optional[set[int]] = None,
) -> Dict[int, List[str]]:
    page_refs: Dict[int, List[str]] = {}
    if not scanned_pages:
        page_refs = {page: list(refs) for page, refs in image_file_by_page.items()}

    for page_entry in content_flow:
        page_num = page_entry.get("page")
        elements = page_entry.get("elements")
        if not isinstance(page_num, int) or not isinstance(elements, list):
            continue
        refs: List[str] = []
        for element in elements:
            if not isinstance(element, dict) or element.get("type") != "image":
                continue
            if (
                scanned_pages
                and page_num in scanned_pages
                and is_page_sized_scan_image(element)
            ):
                continue
            xref = element.get("xref")
            if isinstance(xref, int):
                file_name = image_file_by_xref.get(xref)
                if file_name:
                    refs.append(file_name)
        if refs:
            page_refs[page_num] = refs
    return page_refs


def filter_epub_images_by_usage(
    epub_images: List[EpubImage],
    page_image_refs: Dict[int, List[str]],
) -> List[EpubImage]:
    used_file_names = {
        file_name for refs in page_image_refs.values() for file_name in refs
    }
    if not used_file_names:
        return []
    return [image for image in epub_images if image.file_name in used_file_names]


def render_content_flow_to_xhtml(
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
                text = clean_text_for_epub_body(str(element.get("text", ""))).strip()
                if not text:
                    continue
                for paragraph in split_text_to_paragraphs(text):
                    html_parts.append(wrap_text_block(paragraph))
                continue

            if element_type == "image":
                xref = element.get("xref")
                if isinstance(xref, int):
                    file_name = image_file_by_xref.get(xref)
                    if file_name:
                        html_parts.append(render_image_figure(file_name))
        html_parts.append("</section>")
    return "".join(html_parts)


def render_text_with_page_images(
    total_text: str,
    page_image_refs: Dict[int, List[str]],
) -> str:
    page_sections = re.split(r"===\s*페이지\s*(\d+)\s*===", total_text)
    html_parts: List[str] = []
    inserted_pages: set[int] = set()

    if len(page_sections) <= 1:
        for line in total_text.split("\n"):
            if line.strip():
                html_parts.append(wrap_text_block(line))
        for page in sorted(page_image_refs.keys()):
            html_parts.append(render_image_figure_group(page_image_refs[page]))
        return "".join(html_parts)

    leading = page_sections[0].strip()
    if leading:
        for line in leading.split("\n"):
            if line.strip():
                html_parts.append(wrap_text_block(line))

    for idx in range(1, len(page_sections), 2):
        page_str = page_sections[idx].strip()
        body = page_sections[idx + 1] if idx + 1 < len(page_sections) else ""
        if not page_str.isdigit():
            continue
        page_num = int(page_str)
        for line in body.split("\n"):
            if line.strip():
                html_parts.append(wrap_text_block(line))
        if page_num in page_image_refs:
            html_parts.append(render_image_figure_group(page_image_refs[page_num]))
            inserted_pages.add(page_num)

    for page in sorted(page_image_refs.keys()):
        if page in inserted_pages:
            continue
        html_parts.append(render_image_figure_group(page_image_refs[page]))

    return "".join(html_parts)


def render_markdown_to_xhtml_body(
    markdown_text: str,
    page_image_refs: Dict[int, List[str]],
    *,
    math_image_refs: Optional[Dict[str, Dict[str, str]]] = None,
) -> str:
    lines = markdown_text.splitlines()
    html_parts: List[str] = []
    paragraph_buf: List[str] = []
    list_items: List[str] = []
    list_type: Optional[str] = None
    in_code_block = False
    code_lines: List[str] = []
    in_verse_block = False
    verse_lines: List[tuple[int, str]] = []
    inserted_pages: set[int] = set()

    def flush_paragraph() -> None:
        if paragraph_buf:
            html_parts.append(wrap_text_block(" ".join(paragraph_buf)))
            paragraph_buf.clear()

    def flush_list() -> None:
        nonlocal list_items, list_type
        if not list_items or not list_type:
            return
        html_parts.append(f"<{list_type}>")
        for item in list_items:
            html_parts.append(f"<li>{render_text_with_math(item)}</li>")
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

    def flush_verse() -> None:
        nonlocal verse_lines
        if verse_lines:
            html_parts.append(render_preserved_lines_block(verse_lines))
            verse_lines = []

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("<!--") and stripped.endswith("-->"):
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            flush_verse()
            if in_code_block:
                flush_code()
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        if stripped == "[[VERSE]]":
            flush_paragraph()
            flush_list()
            flush_verse()
            in_verse_block = True
            continue

        if stripped == "[[/VERSE]]":
            flush_verse()
            in_verse_block = False
            continue

        if in_verse_block:
            verse_match = re.match(r"^\[\[LINE:(\d+)\]\](.*)$", line)
            if verse_match:
                verse_lines.append(
                    (int(verse_match.group(1)), verse_match.group(2).strip())
                )
            elif stripped:
                verse_lines.append((0, stripped))
            continue

        if not stripped:
            flush_paragraph()
            flush_list()
            flush_verse()
            continue

        math_marker = extract_math_image_marker(stripped)
        if math_marker and math_image_refs and math_marker in math_image_refs:
            math_image = math_image_refs[math_marker]
            flush_paragraph()
            flush_list()
            flush_verse()
            html_parts.append(
                render_image_figure(
                    str(math_image.get("file_name", "")),
                    alt_text=str(math_image.get("alt_text", "수식 이미지")),
                    caption_text=str(math_image.get("alt_text", "")).strip(),
                    css_class="math-figure",
                )
            )
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            flush_list()
            flush_verse()
            level = len(heading.group(1))
            title = heading.group(2).strip()
            html_parts.append(f"<h{level}>{render_text_with_math(title)}</h{level}>")
            page_match = re.search(r"페이지\s*(\d+)", title)
            if page_match:
                page_num = int(page_match.group(1))
                if page_num in page_image_refs and page_num not in inserted_pages:
                    html_parts.append(
                        render_image_figure_group(page_image_refs[page_num])
                    )
                    inserted_pages.add(page_num)
            continue

        ordered = re.match(r"^\d+\.\s+(.+)$", stripped)
        unordered = re.match(r"^[-*]\s+(.+)$", stripped)
        if ordered or unordered:
            flush_paragraph()
            flush_verse()
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
            flush_verse()
            html_parts.append(
                f"<blockquote>{render_text_with_math(stripped[1:].strip())}</blockquote>"
            )
            continue

        paragraph_buf.append(stripped)

    flush_paragraph()
    flush_list()
    flush_verse()
    if in_code_block:
        flush_code()

    for page_num, refs in sorted(page_image_refs.items()):
        if page_num in inserted_pages:
            continue
        html_parts.append(render_image_figure_group(refs))

    return "".join(html_parts)


def split_text_to_paragraphs(text: str) -> List[str]:
    parts = [segment.strip() for segment in text.split("\n") if segment.strip()]
    return parts if parts else [text]


def wrap_text_block(text: str) -> str:
    rendered = render_block_with_math(text)
    if rendered.startswith('<div class="math-display"'):
        return rendered
    return f"<p>{rendered}</p>"


def render_preserved_lines_block(lines: List[tuple[int, str]]) -> str:
    rendered_lines: List[str] = []
    for indent_level, text in lines:
        safe_text = render_text_with_math(text)
        indent_prefix = "&nbsp;" * max(indent_level, 0) * 2
        rendered_lines.append(f"{indent_prefix}{safe_text}")
    return f'<p class="verse">{"<br/>".join(rendered_lines)}</p>'


def render_image_figure_group(image_refs: List[str]) -> str:
    return "".join(render_image_figure(file_name) for file_name in image_refs)


def render_image_figure(
    file_name: str,
    *,
    alt_text: str = "문서 이미지",
    caption_text: Optional[str] = None,
    css_class: Optional[str] = None,
) -> str:
    safe_name = escape(file_name)
    class_attr = f' class="{escape(css_class)}"' if css_class else ""
    figcaption = (
        f"<figcaption>{escape(caption_text)}</figcaption>" if caption_text else ""
    )
    return (
        f"<figure{class_attr}>"
        f'<img src="{safe_name}" alt="{escape(alt_text)}" />'
        f"{figcaption}"
        "</figure>"
    )


def extract_math_image_marker(line: str) -> Optional[str]:
    match = re.fullmatch(r"(\[\[MATHIMG:[^\]]+\]\])", line.strip())
    return match.group(1) if match else None


def build_scan_math_image_assets(
    raw_images: Any,
    assets: List[EpubImage],
) -> Dict[str, Dict[str, str]]:
    marker_to_file: Dict[str, Dict[str, str]] = {}
    if not isinstance(raw_images, list):
        return marker_to_file

    start_index = len(assets) + 1
    for offset, image_info in enumerate(raw_images, start=start_index):
        if not isinstance(image_info, dict):
            continue
        marker = image_info.get("marker")
        image_bytes = image_info.get("image_bytes")
        image_format = str(image_info.get("format", "png")).lower()
        if not isinstance(marker, str) or not isinstance(image_bytes, bytes):
            continue
        normalized = normalize_image_for_epub(image_bytes, image_format)
        if normalized is None:
            continue
        ext, media_type, normalized_bytes = normalized
        file_name = f"images/scan-math-{offset}.{ext}"
        assets.append(
            EpubImage(
                file_name=file_name,
                media_type=media_type,
                data=normalized_bytes,
            )
        )
        marker_to_file[marker] = {
            "file_name": file_name,
            "alt_text": str(image_info.get("alt_text", "수식 이미지")),
        }
    return marker_to_file


def resolve_image_format(image_format: str) -> tuple[str, str]:
    mapping = {
        "jpg": ("jpg", "image/jpeg"),
        "jpeg": ("jpg", "image/jpeg"),
        "png": ("png", "image/png"),
        "webp": ("webp", "image/webp"),
        "gif": ("gif", "image/gif"),
        "bmp": ("bmp", "image/bmp"),
    }
    return mapping.get(image_format, ("png", "image/png"))


def normalize_image_for_epub(
    image_bytes: bytes,
    image_format: str,
) -> Optional[tuple[str, str, bytes]]:
    ext, media_type = resolve_image_format(image_format)
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
