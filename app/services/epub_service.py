"""ebooklib을 활용한 EPUB 생성 서비스"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import tempfile
from pathlib import Path

from ebooklib import epub  # type: ignore


@dataclass
class Chapter:
    title: str
    content: str  # XHTML body innerHTML (본문 문자열)
    file_name: str = "chapter.xhtml"


class EpubGenerator:
    """ebooklib 기반 EPUB 생성기"""

    def __init__(self, language: str = "ko") -> None:
        self.language = language

    def create_epub_bytes(
        self,
        title: str,
        author: str,
        chapters: List[Chapter],
        uid: Optional[str] = None,
        include_legacy_ncx: bool = True,
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

        # 챕터 추가
        epub_chapters = []
        for idx, ch in enumerate(chapters, start=1):
            c = epub.EpubHtml(
                title=ch.title, file_name=ch.file_name or f"chapter{idx}.xhtml"
            )
            c.content = f"""
                <?xml version=\"1.0\" encoding=\"utf-8\"?>
                <!DOCTYPE html>
                <html xmlns=\"http://www.w3.org/1999/xhtml\" xml:lang=\"{self.language}\" lang=\"{self.language}\">
                  <head><meta charset=\"utf-8\" /><title>{ch.title}</title></head>
                  <body>{ch.content}</body>
                </html>
                """
            book.add_item(c)
            epub_chapters.append(c)

        # 기본 nav
        nav = epub.EpubNav()
        book.add_item(nav)

        # 호환용 NCX (옵션)
        if include_legacy_ncx:
            ncx = epub.EpubNcx()
            book.add_item(ncx)

        # TOC 구성(간단히 챕터 리스트)
        book.toc = tuple(epub_chapters)

        # Spine 구성(nav 포함)
        book.spine = ["nav", *epub_chapters]

        # 파일로 쓴 후 바이트 로드 (ebooklib API 특성상 파일 경로 사용)
        with tempfile.TemporaryDirectory() as td:
            out_path = Path(td) / "output.epub"
            epub.write_epub(str(out_path), book)
            data = out_path.read_bytes()

        return data
