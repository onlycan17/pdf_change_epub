"""ebooklib을 활용한 EPUB 생성 서비스"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple, Any
import tempfile
from pathlib import Path

from ebooklib import epub  # type: ignore
from lxml import html  # type: ignore


@dataclass
class Chapter:
    title: str
    content: str  # XHTML body innerHTML (본문 문자열)
    file_name: str = "chapter.xhtml"


class EpubGenerator:
    """ebooklib 기반 EPUB 생성기"""

    def __init__(self, language: str = "ko") -> None:
        self.language = language
        # 기본 가독성 스타일 (EPUB 전용)
        # 용어(설명: 가독성 – 눈이 덜 피로하고 읽기 쉬운 글꼴/간격/여백 설정)
        self._default_css = """
            /* 본문 기본 설정 */
            html, body { margin: 0; padding: 0; }
            body {
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", "Helvetica Neue", Arial, sans-serif;
              font-size: 1rem; /* 약 16px */
              line-height: 1.65;
              color: #111;
              background: #fff;
              word-break: keep-all; /* 한국어 단어 단위 줄바꿈 개선 */
              -webkit-font-smoothing: antialiased;
              -moz-osx-font-smoothing: grayscale;
              padding: 0 6%;
            }

            /* 제목 계층 */
            h1, h2, h3, h4 { line-height: 1.35; margin: 1.2em 0 0.6em; font-weight: 700; }
            h1 { font-size: 1.6rem; }
            h2 { font-size: 1.35rem; }
            h3 { font-size: 1.2rem; }
            h4 { font-size: 1.05rem; }

            /* 문단 */
            p { margin: 0.8em 0; }
            strong { font-weight: 700; }
            em { font-style: italic; }

            /* 리스트 */
            ul, ol { margin: 0.8em 0 0.8em 1.2em; }
            li { margin: 0.3em 0; }

            /* 이미지 */
            img { max-width: 100%; height: auto; display: block; margin: 0.6em auto; }
            figure { margin: 1em 0; }
            figcaption { font-size: 0.9rem; color: #555; text-align: center; }

            /* 코드/인라인 */
            pre, code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }
            pre { background: #f6f8fa; padding: 0.8em; border-radius: 6px; overflow-x: auto; }
            code { background: #f6f8fa; padding: 0.15em 0.35em; border-radius: 4px; }

            /* 표 */
            table { border-collapse: collapse; width: 100%; margin: 1em 0; }
            th, td { border: 1px solid #ddd; padding: 0.5em; }
            th { background: #fafafa; font-weight: 600; }

            /* 인용문 */
            blockquote {
              border-left: 4px solid #ddd;
              padding: 0.4em 0 0.4em 1em;
              color: #555;
              margin: 1em 0;
              background: #fcfcfc;
            }
            """

    def create_epub_bytes(
        self,
        title: str,
        author: str,
        chapters: List[Chapter],
        uid: Optional[str] = None,
        include_legacy_ncx: bool = True,
        auto_toc_from_headings: bool = True,
    ) -> bytes:
        """EPUB 바이트 생성

        Args:
            title: 책 제목
            author: 저자명
            chapters: 챕터 목록
            uid: 식별자(UUID 등)
            include_legacy_ncx: NCX 포함 여부(일부 리더 호환)
        """
        book = epub.EpubBook()

        if uid:
            book.set_identifier(uid)
        book.set_title(title)
        book.set_language(self.language)
        book.add_author(author)

        # 공용 스타일 추가
        style_item = epub.EpubItem(
            uid="style_default",
            file_name="style/reader.css",
            media_type="text/css",
            content=self._default_css,
        )

        # 챕터 추가
        epub_chapters = []
        for idx, ch in enumerate(chapters, start=1):
            file_name = ch.file_name or f"chapter{idx}.xhtml"
            body_html = ch.content

            # 본문 내 제목(h1-h3)에 id 자동 부여
            body_html, _ = self._inject_heading_ids(body_html, file_name)

            c = epub.EpubHtml(title=ch.title, file_name=file_name)
            c.content = f"""
                <?xml version=\"1.0\" encoding=\"utf-8\"?>
                <!DOCTYPE html>
                <html xmlns=\"http://www.w3.org/1999/xhtml\" xml:lang=\"{self.language}\" lang=\"{self.language}\">
                  <head>
                    <meta charset=\"utf-8\" />
                    <title>{ch.title}</title>
                    <link rel=\"stylesheet\" type=\"text/css\" href=\"style/reader.css\" />
                  </head>
                  <body>{body_html}</body>
                </html>
                """
            book.add_item(c)
            epub_chapters.append(c)

        # 기본 nav
        nav = epub.EpubNav()
        book.add_item(nav)
        book.add_item(style_item)

        # 호환용 NCX (옵션)
        if include_legacy_ncx:
            ncx = epub.EpubNcx()
            book.add_item(ncx)

        # TOC 구성: 제목 자동 분석 또는 기본 챕터 리스트
        if auto_toc_from_headings:
            toc = self._build_toc_from_headings(chapters)
            book.toc = toc if toc else tuple(epub_chapters)
        else:
            book.toc = tuple(epub_chapters)

        # Spine 구성(nav 포함)
        book.spine = ["nav", *epub_chapters]

        # 파일로 쓴 후 바이트 로드 (ebooklib API 특성상 파일 경로 사용)
        with tempfile.TemporaryDirectory() as td:
            out_path = Path(td) / "output.epub"
            epub.write_epub(str(out_path), book)
            data = out_path.read_bytes()

        return data

    def _inject_heading_ids(
        self, body_html: str, file_name: str
    ) -> Tuple[str, List[Tuple[int, str, str]]]:
        """본문의 h1-h3에 id를 부여하고, (level, title, href) 목록 반환.

        Args:
            body_html: 본문(innerHTML)
            file_name: 챕터 파일명

        Returns:
            (updated_html, headings)
        """
        try:
            root = html.fromstring(f"<div>{body_html}</div>")
        except Exception:
            return body_html, []

        headings: List[Tuple[int, str, str]] = []
        counters = {1: 0, 2: 0, 3: 0}

        for level in (1, 2, 3):
            for el in root.findall(f".//h{level}"):
                text = (el.text_content() or "").strip()
                if not text:
                    continue
                hid = el.get("id")
                if not hid:
                    counters[level] += 1
                    hid = f"h{level}-{counters[level]}"
                    el.set("id", hid)
                href = f"{file_name}#{hid}"
                headings.append((level, text, href))

        try:
            updated_html = html.tostring(root, encoding="unicode")
            if updated_html.startswith("<div>") and updated_html.endswith("</div>"):
                updated_html = updated_html[5:-6]
        except Exception:
            updated_html = body_html

        return updated_html, headings

    def _build_toc_from_headings(self, chapters: List[Chapter]) -> List[Any]:
        """챕터 본문 내 h1-h3를 기반으로 nav TOC 생성.

        ebooklib는 (item, [subitems]) 형태의 트리 구조를 지원합니다.
        """
        all_headings: List[Tuple[int, str, str]] = []
        for idx, ch in enumerate(chapters, start=1):
            file_name = ch.file_name or f"chapter{idx}.xhtml"
            _, heads = self._inject_heading_ids(ch.content, file_name)
            all_headings.extend(heads)

        if not all_headings:
            return []

        toc: List[Any] = []
        stack: List[Tuple[int, int]] = []  # (level, index_in_toc)

        for level, text, href in all_headings:
            link = epub.Link(href, text, href)
            if not stack:
                toc.append(link)
                stack.append((level, len(toc) - 1))
                continue

            # 스택 조정: 현재 레벨보다 크거나 같은 레벨은 팝
            while stack and stack[-1][0] >= level:
                stack.pop()

            if not stack:
                toc.append(link)
                stack.append((level, len(toc) - 1))
            else:
                # 부모 항목 가져오기
                parent_level, parent_idx = stack[-1]
                parent = toc[parent_idx]
                if (
                    isinstance(parent, tuple)
                    and len(parent) == 2
                    and isinstance(parent[1], list)
                ):
                    parent[1].append(link)  # type: ignore[index]
                else:
                    toc[parent_idx] = (parent, [link])
                stack.append((level, parent_idx))

        return toc
