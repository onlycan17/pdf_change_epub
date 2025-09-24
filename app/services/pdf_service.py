"""PDF 분석 및 처리 서비스"""

from __future__ import annotations

import io
import logging
import os
import tempfile
from pathlib import Path
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple, Union, cast, Iterator
from enum import Enum

import fitz  # PyMuPDF

# pypdf와 pdfminer.six 임포트
from pypdf import PdfReader
from pdfminer.high_level import extract_text as pdfminer_extract_text
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument

# OCR 관련 임포트는 필요 시 동적 로딩
from app.core.config import Settings, get_settings
from app.services.image_service import optimize_image_to_webp

logger = logging.getLogger(__name__)

PDFContentSource = Union[bytes, bytearray, io.IOBase, str, Path]


@contextmanager
def _pdf_file_from_source(
    pdf_source: PDFContentSource, settings: Optional["Settings"] = None
) -> Iterator[Path]:
    """Context manager that yields a Path to a PDF file on disk.

    - If the source is already a file path, yield it directly.
    - If the source is an IO stream, write it to a temporary file in chunks
      (avoids loading the whole stream into memory).
    - If the source is bytes/bytearray and its size exceeds the configured
      max_file_size, write to a temp file and delete the in-memory reference.

    The temp file is removed on context exit when created by this helper.
    """
    tmp_path: Optional[str] = None
    created = False
    try:
        # path-like input
        if isinstance(pdf_source, (str, Path)):
            p = Path(pdf_source)
            if not p.exists():
                raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {p}")
            yield p
            return

        # optional: read configured max_file_size, but don't keep unused locals
        if settings is not None:
            try:
                _ = int(50)  # 기본값 50MB
            except Exception:
                pass

        # bytes-like: if small, write to a temp file anyway to allow stream-based libs
        if isinstance(pdf_source, (bytes, bytearray)):
            data = bytes(pdf_source)
            # write to temp file when large or always (to avoid keeping large bytes)
            # create a NamedTemporaryFile, write bytes, capture its path, then close
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tf:
                tf.write(data)
                tf.flush()
                tmp_path = tf.name
            created = True
            # drop reference to large bytes to free memory
            del data
            yield Path(tmp_path)
            return

        # io.IOBase: stream to temp file in chunks to avoid loading into memory
        if isinstance(pdf_source, io.IOBase):
            # try to use an existing file path if available
            name = getattr(pdf_source, "name", None)
            if isinstance(name, str):
                p = Path(name)
                if p.exists():
                    yield p
                    return

            # stream to a temp file in chunks to avoid loading into memory
            try:
                pdf_source.seek(0)
            except Exception:
                pass

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tf:
                tmp_path = tf.name
                # write in chunks to the temp file
                while True:
                    chunk = pdf_source.read(1024 * 1024)
                    if not chunk:
                        break
                    if isinstance(chunk, str):
                        chunk = chunk.encode("utf-8")
                    tf.write(chunk)
                tf.flush()

            created = True
            yield Path(tmp_path)
            return

        raise TypeError(f"지원하지 않는 PDF 입력 타입: {type(pdf_source)!r}")

    finally:
        if created and tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def _read_pdf_bytes(pdf_source: PDFContentSource) -> bytes:
    """호환용: PDF 입력을 바이트로 반환(메모리 사용이 허용되는 작은 파일에만 사용).

    NOTE: For large files prefer using `_pdf_file_from_source` which yields a file path
    so callers can stream from disk instead of keeping bytes in memory.
    """
    if isinstance(pdf_source, (bytes, bytearray)):
        return bytes(pdf_source)

    if isinstance(pdf_source, io.IOBase):
        try:
            if pdf_source.seekable():
                pdf_source.seek(0)
        except (OSError, ValueError):
            pass

        data = pdf_source.read()
        if isinstance(data, (bytes, bytearray)):
            return bytes(data)

        raise TypeError("PDF 스트림에서 바이트 데이터를 읽을 수 없습니다.")

    if isinstance(pdf_source, (str, Path)):
        # load from file path
        return Path(pdf_source).read_bytes()

    raise TypeError(f"지원하지 않는 PDF 입력 타입: {type(pdf_source)!r}")


class PDFType(Enum):
    """PDF 문서 유형 정의"""

    TEXT_BASED = "text_based"  # 텍스트 기반 PDF
    SCANNED = "scanned"  # 스캔된 PDF (이미지 중심)
    MIXED = "mixed"  # 텍스트와 이미지가 혼합된 PDF


class PageAnalysisResult:
    """페이지 분석 결과"""

    def __init__(
        self,
        page_number: int,
        has_text: bool = False,
        text_content: str = "",
        image_count: int = 0,
        is_scanned_page: bool = False,
        confidence_score: float = 0.0,
    ):
        """페이지 분석 결과 초기화"""
        self.page_number = page_number
        self.has_text = has_text
        self.text_content = text_content
        self.image_count = image_count
        self.is_scanned_page = is_scanned_page
        self.confidence_score = confidence_score

    def to_dict(self) -> Dict:
        """결과를 딕셔너리로 변환"""
        return {
            "page_number": self.page_number,
            "has_text": self.has_text,
            "text_content_length": len(self.text_content),
            "image_count": self.image_count,
            "is_scanned_page": self.is_scanned_page,
            "confidence_score": self.confidence_score,
        }


class PDFAnalysisResult:
    """전체 PDF 분석 결과"""

    def __init__(
        self,
        pdf_type: PDFType,
        total_pages: int,
        pages_analysis: List[PageAnalysisResult],
        overall_confidence: float = 0.0,
        mixed_ratio: float = 0.0,
    ):
        """전체 PDF 분석 결과 초기화"""
        self.pdf_type = pdf_type
        self.total_pages = total_pages
        self.pages_analysis = pages_analysis
        self.overall_confidence = overall_confidence
        self.mixed_ratio = mixed_ratio

    def get_text_pages(self) -> List[int]:
        """텍스트가 포함된 페이지 번호 목록 반환"""
        return [
            page.page_number
            for page in self.pages_analysis
            if page.has_text and not page.is_scanned_page
        ]

    def get_scanned_pages(self) -> List[int]:
        """스캔된 페이지 번호 목록 반환"""
        return [
            page.page_number for page in self.pages_analysis if page.is_scanned_page
        ]

    def get_text_content(self) -> str:
        """모든 텍스트 페이지의 내용을 병합하여 반환"""
        text_parts = []
        for page in self.pages_analysis:
            if page.has_text and not page.is_scanned_page:
                text_parts.append(
                    f"=== 페이지 {page.page_number} ===\n{page.text_content}"
                )

        return "\n\n".join(text_parts)

    def to_dict(self) -> Dict:
        """결과를 딕셔너리로 변환"""
        return {
            "pdf_type": self.pdf_type.value,
            "total_pages": self.total_pages,
            "overall_confidence": self.overall_confidence,
            "mixed_ratio": (
                self.mixed_ratio if self.pdf_type == PDFType.MIXED else None
            ),
            "text_pages_count": len(self.get_text_pages()),
            "scanned_pages_count": len(self.get_scanned_pages()),
            "pages_analysis": [page.to_dict() for page in self.pages_analysis],
        }


class PDFAnalyzer:
    """PDF 분석기 클래스"""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """PDF 분석기 초기화"""
        self.settings = settings or get_settings()
        self.text_density_threshold = 0.1
        logger.info("PDF Analyzer 초기화 완료")

    def analyze_pdf(self, pdf_content: PDFContentSource) -> PDFAnalysisResult:
        """PDF 문서 유형 자동 감지 및 분석"""
        try:
            # use file-backed open to reduce memory for large inputs
            with _pdf_file_from_source(pdf_content, self.settings) as pdf_path:
                doc = fitz.open(str(pdf_path))

                total_pages = len(doc)

                if total_pages == 0:
                    raise ValueError("PDF 페이지가 없습니다")

                logger.info(f"PDF 분석 시작: {total_pages}페이지")

                # 각 페이지별 분석
                pages_analysis = []

                for page_num in range(total_pages):
                    try:
                        page_result = self._analyze_page(doc, page_num)
                        pages_analysis.append(page_result)

                    except Exception as e:
                        logger.error(f"페이지 {page_num + 1} 분석 실패: {str(e)}")
                        # 오류 발생 시 기본값으로 생성
                        page_result = PageAnalysisResult(
                            page_number=page_num,
                            has_text=False,
                            image_count=0,
                            is_scanned_page=True,
                            confidence_score=0.5,
                        )
                        pages_analysis.append(page_result)

            # PDF 유형 결정
            text_pages_count = len([p for p in pages_analysis if not p.is_scanned_page])
            scanned_pages_count = len([p for p in pages_analysis if p.is_scanned_page])

            pdf_type, mixed_ratio = self._determine_pdf_type(
                total_pages, text_pages_count, scanned_pages_count
            )

            # 전체 신뢰도 계산
            overall_confidence = self._calculate_overall_confidence(pages_analysis)

            logger.info(
                f"PDF 분석 완료: {pdf_type.value}, 전체 신뢰도: {overall_confidence:.2f}"
            )

            return PDFAnalysisResult(
                pdf_type=pdf_type,
                total_pages=total_pages,
                pages_analysis=pages_analysis,
                overall_confidence=overall_confidence,
                mixed_ratio=mixed_ratio,
            )

        except Exception as e:
            logger.error(f"PDF 분석 중 오류 발생: {str(e)}")
            raise ValueError(f"PDF 분석 실패: {str(e)}")

    def _analyze_page(self, doc: fitz.Document, page_num: int) -> PageAnalysisResult:
        """단일 페이지 분석"""
        # PyMuPDF의 Page 타입은 런타임에 속성이 동적으로 제공되므로
        # Pylance가 속성(get_text 등)을 모를 때 경고를 냅니다. 그 경고를 억제하기 위해
        # 명시적으로 Any로 캐스팅합니다.
        page = cast(Any, doc[page_num])

        # 텍스트 추출 및 분석
        text_content = page.get_text()  # type: ignore[attr-defined]
        has_text = (
            len(text_content.strip()) > 0 if isinstance(text_content, str) else False
        )

        # 페이지 이미지 분석
        image_count = self._count_page_images(page)

        # 텍스트 밀도 분석
        text_density = self._calculate_text_density(page, text_content)

        # 스캔 여부 판단
        is_scanned = self._is_scanned_page(
            has_text, text_density, image_count, len(text_content)
        )

        # 신뢰도 점수 계산
        confidence = self._calculate_page_confidence(
            has_text, text_density, image_count, is_scanned
        )

        return PageAnalysisResult(
            page_number=page_num + 1,
            has_text=has_text,
            text_content=text_content if not is_scanned else "",
            image_count=image_count,
            is_scanned_page=is_scanned,
            confidence_score=confidence,
        )

    def _count_page_images(self, page: Any) -> int:
        """페이지 내 이미지 수 카운트"""
        try:
            image_list = page.get_images()  # type: ignore[attr-defined]
            unique_images = set()

            for img_info in image_list:
                if len(img_info) >= 1:
                    xref = img_info[0]
                    unique_images.add(xref)

            return len(unique_images)
        except Exception as e:
            logger.warning(f"이미지 카운트 실패: {str(e)}")
            return 0

    def _calculate_text_density(self, page: Any, text_content: str) -> float:
        """텍스트 밀도 계산"""
        try:
            # page.rect의 속성도 정적 타입 정보가 없을 수 있으므로 type: ignore 사용
            page_area = page.rect.width * page.rect.height  # type: ignore[attr-defined]

            if page_area <= 0:
                return 0.0

            text_length = len(text_content)
            text_area = text_length * 100
            density = min(text_area / page_area, 1.0)

            return density
        except Exception as e:
            logger.warning(f"텍스트 밀도 계산 실패: {str(e)}")
            return 0.0

    def _is_scanned_page(
        self, has_text: bool, text_density: float, image_count: int, text_length: int
    ) -> bool:
        """스캔된 페이지 여부 판단"""
        if not has_text or text_density < self.text_density_threshold:
            return True

        if image_count > 0 and text_length < image_count * 100:
            return True

        # 이미지만 있는 경우 (text_content 변수는 이 메서드의 스코프에 없으므로 text_length 사용)
        if has_text and text_length == 0 and image_count > 0:
            return True

        if text_density < self.text_density_threshold:
            return True

        if image_count > 0 and text_length / max(image_count, 1) < 50:
            return True

        return False

    def _calculate_page_confidence(
        self, _has_text: bool, text_density: float, image_count: int, is_scanned: bool
    ) -> float:
        """페이지별 신뢰도 점수 계산"""
        confidence = 0.5

        if is_scanned:
            if image_count > 0:
                confidence = min(confidence + (image_count * 0.1), 0.9)
            if text_density > 0:
                confidence = min(confidence + (text_density * 0.5), 0.9)
        else:
            confidence = min(confidence + (text_density * 0.8), 0.95)

        return round(confidence, 2)

    def _determine_pdf_type(
        self, total_pages: int, text_pages_count: int, scanned_pages_count: int
    ) -> Tuple[PDFType, float]:
        """전체 PDF 유형 결정"""
        if total_pages == 0:
            return PDFType.TEXT_BASED, 0.0

        text_ratio = text_pages_count / total_pages
        scanned_ratio = scanned_pages_count / total_pages

        if text_ratio >= 0.8:
            return PDFType.TEXT_BASED, 0.0

        if scanned_ratio >= 0.8:
            return PDFType.SCANNED, 0.0

        return PDFType.MIXED, scanned_ratio

    def _calculate_overall_confidence(
        self, pages_analysis: List[PageAnalysisResult]
    ) -> float:
        """전체 PDF 분석 신뢰도 계산"""
        if not pages_analysis:
            return 0.0

        total_confidence = sum(page.confidence_score for page in pages_analysis)
        average_confidence = total_confidence / len(pages_analysis)

        low_confidence_pages = [
            page for page in pages_analysis if page.confidence_score < 0.6
        ]

        if low_confidence_pages:
            penalty = len(low_confidence_pages) / len(pages_analysis) * 0.2
            average_confidence = max(0, average_confidence - penalty)

        return round(average_confidence, 2)


class PDFExtractor:
    """PDF 텍스트 및 이미지 추출기"""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """PDF 추출기 초기화"""
        self.settings = settings or get_settings()

    def extract_text_from_pdf(
        self,
        pdf_content: PDFContentSource,
        page_numbers: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """PDF에서 텍스트 추출"""
        try:
            page_texts: List[Dict[str, str]] = []
            total_text_parts = []

            with _pdf_file_from_source(pdf_content, self.settings) as pdf_path:
                doc = fitz.open(str(pdf_path))
                target_pages = page_numbers or list(range(1, len(doc) + 1))

                for page_num in target_pages:
                    if 0 < page_num <= len(doc):
                        # 캐스트하여 Pylance 경고를 억제
                        page = cast(Any, doc[page_num - 1])
                        text = page.get_text()  # type: ignore[attr-defined]

                        if isinstance(text, str) and text.strip():
                            total_text_parts.append(
                                f"=== 페이지 {page_num} ===\n{text}"
                            )
                            page_texts.append({"page": str(page_num), "text": text})

                return {
                    "total_text": "\n\n".join(total_text_parts),
                    "page_texts": page_texts,
                    "extraction_stats": {
                        "total_pages": str(len(doc)),
                        "extracted_pages": str(len(page_texts)),
                    },
                }

        except Exception as e:
            logger.error(f"텍스트 추출 실패: {str(e)}")
            raise ValueError(f"PDF 텍스트 추출 실패: {str(e)}")

    def extract_text_in_chunks(
        self,
        pdf_content: PDFContentSource,
        chunk_chars: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """PDF 문서를 텍스트 청크 단위로 분할하여 반환합니다.

        각 청크는 연속된 페이지 범위의 텍스트를 하나의 항목으로 가지며
        메모리 사용을 낮추기 위해 큰 문서를 처리할 때 사용합니다.

        반환 형식:
            [
                {
                    "start_page": int,
                    "end_page": int,
                    "total_text": str,
                    "page_texts": [{"page": str, "text": str}, ...]
                },
                ...
            ]
        """
        try:
            max_chars = int(chunk_chars or 10000)  # 기본값 10000
            chunks: List[Dict[str, Any]] = []

            current_parts: List[str] = []
            current_page_texts: List[Dict[str, str]] = []
            current_chars = 0
            start_page = 1

            with _pdf_file_from_source(pdf_content, self.settings) as pdf_path:
                doc = fitz.open(str(pdf_path))
                total_pages = len(doc)
                if total_pages == 0:
                    return []

                for page_num in range(1, total_pages + 1):
                    page = cast(Any, doc[page_num - 1])
                    text = page.get_text()  # type: ignore[attr-defined]
                    if isinstance(text, str) and text.strip():
                        snippet = f"=== 페이지 {page_num} ===\n{text}"
                        current_parts.append(snippet)
                        current_page_texts.append({"page": str(page_num), "text": text})
                        current_chars += len(text)

                    # 현재 누적된 문자가 최대치에 도달하면 청크로 저장
                    if current_chars >= max_chars:
                        chunks.append(
                            {
                                "start_page": start_page,
                                "end_page": page_num,
                                "total_text": "\n\n".join(current_parts),
                                "page_texts": list(current_page_texts),
                            }
                        )
                        # 초기화
                        start_page = page_num + 1
                        current_parts = []
                        current_page_texts = []
                        current_chars = 0

            # 남아있는 파트가 있으면 마지막 청크로 추가
            if current_parts:
                chunks.append(
                    {
                        "start_page": start_page,
                        "end_page": total_pages,
                        "total_text": "\n\n".join(current_parts),
                        "page_texts": list(current_page_texts),
                    }
                )

            return chunks

        except Exception as e:
            logger.error(f"청크 단위 텍스트 추출 중 오류: {str(e)}")
            raise ValueError(f"PDF 청크 추출 오류: {str(e)}")

    def extract_images_from_pdf(
        self, pdf_content: PDFContentSource
    ) -> List[Dict[str, Union[int, bytes, str]]]:
        """PDF에서 이미지 추출"""
        try:
            images_data: List[Dict[str, Union[int, bytes, str]]] = []
            extracted_images: Dict[int, Dict[str, Union[int, bytes, str]]] = {}

            with _pdf_file_from_source(pdf_content, self.settings) as pdf_path:
                doc = fitz.open(str(pdf_path))

                for page_num in range(len(doc)):
                    # 캐스트하여 Pylance 경고를 억제
                    page = cast(Any, doc[page_num])

                    try:
                        image_list = page.get_images()

                        for img_info in image_list:
                            if len(img_info) >= 1:
                                xref = img_info[0]

                                if xref not in extracted_images:
                                    base_image = doc.extract_image(xref)
                                    image_bytes = base_image["image"]
                                    original_ext = str(base_image.get("ext", "unknown"))

                                    # 이미지 최적화 및 WebP 변환(설정 시)
                                    if (
                                        False
                                    ):  # image_optimize 기능은 일시적으로 비활성화
                                        try:
                                            optimized = optimize_image_to_webp(
                                                image_bytes,
                                                max_width=1920,
                                                max_height=1080,
                                                quality=85,
                                            )
                                            extracted_images[xref] = {
                                                "page": page_num + 1,
                                                "xref": xref,
                                                "image_bytes": optimized.data,
                                                "format": optimized.format,
                                                "original_format": original_ext,
                                            }
                                        except Exception as _:
                                            # 최적화 실패 시 원본 그대로 사용
                                            extracted_images[xref] = {
                                                "page": page_num + 1,
                                                "xref": xref,
                                                "image_bytes": image_bytes,
                                                "format": original_ext,
                                            }
                                    else:
                                        extracted_images[xref] = {
                                            "page": page_num + 1,
                                            "xref": xref,
                                            "image_bytes": image_bytes,
                                            "format": original_ext,
                                        }

                    except Exception as e:
                        logger.warning(
                            f"페이지 {page_num + 1} 이미지 추출 실패: {str(e)}"
                        )
                        continue

            images_data = list(extracted_images.values())
            logger.info(f"이미지 추출 완료: {len(images_data)}개")

            return images_data

        except Exception as e:
            logger.error(f"이미지 추출 실패: {str(e)}")
            raise ValueError(f"PDF 이미지 추출 실패: {str(e)}")

    def extract_text_with_pypdf2(
        self,
        pdf_content: PDFContentSource,
        page_numbers: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """pypdf를 사용한 텍스트 추출"""
        try:
            # Prefer file-backed reader to avoid building large in-memory bytes
            with _pdf_file_from_source(pdf_content, self.settings) as pdf_path:
                pdf_reader = PdfReader(str(pdf_path))

            page_texts: List[Dict[str, str]] = []
            total_text_parts = []

            target_pages = page_numbers or list(range(1, len(pdf_reader.pages) + 1))

            for page_num in target_pages:
                if 0 < page_num <= len(pdf_reader.pages):
                    page = pdf_reader.pages[page_num - 1]
                    text = page.extract_text()

                    if text and text.strip():
                        total_text_parts.append(f"=== 페이지 {page_num} ===\n{text}")
                        page_texts.append({"page": str(page_num), "text": text})

            return {
                "total_text": "\n\n".join(total_text_parts),
                "page_texts": page_texts,
                "extraction_stats": {
                    "total_pages": str(len(pdf_reader.pages)),
                    "extracted_pages": str(len(page_texts)),
                    "extractor": "pypdf",
                },
            }

        except Exception as e:
            logger.error(f"pypdf 텍스트 추출 실패: {str(e)}")
            raise ValueError(f"pypdf 텍스트 추출 실패: {str(e)}")

    def extract_text_with_pdfminer(
        self,
        pdf_content: PDFContentSource,
        page_numbers: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """pdfminer.six를 사용한 텍스트 추출"""
        try:
            # use file-backed path for pdfminer to avoid in-memory bytes
            with _pdf_file_from_source(pdf_content, self.settings) as pdf_path:
                # pdfminer accepts filename
                text = pdfminer_extract_text(str(pdf_path))

            # 페이지별로 텍스트를 분리 (간단한 페이지 구분 로직)
            pages = text.split("\f")  # Form Feed 문자로 페이지 구분

            page_texts: List[Dict[str, str]] = []
            total_text_parts = []

            target_pages = page_numbers or list(range(1, len(pages) + 1))

            for i, page_text in enumerate(pages):
                page_num = i + 1
                if page_num in target_pages and page_text.strip():
                    total_text_parts.append(f"=== 페이지 {page_num} ===\n{page_text}")
                    page_texts.append({"page": str(page_num), "text": page_text})

            return {
                "total_text": "\n\n".join(total_text_parts),
                "page_texts": page_texts,
                "extraction_stats": {
                    "total_pages": str(len(pages)),
                    "extracted_pages": str(len(page_texts)),
                    "extractor": "pdfminer.six",
                },
            }

        except Exception as e:
            logger.error(f"pdfminer.six 텍스트 추출 실패: {str(e)}")
            raise ValueError(f"pdfminer.six 텍스트 추출 실패: {str(e)}")

    def extract_images_with_pypdf2(
        self, pdf_content: PDFContentSource
    ) -> List[Dict[str, Union[int, bytes, str]]]:
        """pypdf를 사용한 이미지 추출"""
        try:
            with _pdf_file_from_source(pdf_content, self.settings) as pdf_path:
                pdf_reader = PdfReader(str(pdf_path))

            images_data: List[Dict[str, Union[int, bytes, str]]] = []

            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    # pypdf에서는 직접적인 이미지 추출이 제한적이므로
                    # 텍스트에서 이미지 관련 정보를 추출
                    text = page.extract_text()

                    # 이미지 관련 키워드가 있는지 확인
                    if any(
                        keyword in text.lower()
                        for keyword in ["image", "img", "picture", "photo", "figure"]
                    ):
                        # 실제 이미지 데이터는 PyMuPDF에서 추출하는 것이 더 정확하므로
                        # 플레이스홀더로 처리
                        images_data.append(
                            {
                                "page": page_num + 1,
                                "image_bytes": b"placeholder_image_data",
                                "format": "placeholder",
                                "extractor": "pypdf",
                            }
                        )

                except Exception as e:
                    logger.warning(f"페이지 {page_num + 1} 이미지 추출 실패: {str(e)}")
                    continue

            logger.info(f"pypdf 이미지 추출 완료: {len(images_data)}개")
            return images_data

        except Exception as e:
            logger.error(f"pypdf 이미지 추출 실패: {str(e)}")
            raise ValueError(f"pypdf 이미지 추출 실패: {str(e)}")


class PDFMetadataExtractor:
    """PDF 메타데이터 추출기"""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """PDF 메타데이터 추출기 초기화"""
        self.settings = settings or get_settings()
        logger.info("PDF Metadata Extractor 초기화 완료")

    def extract_metadata(self, pdf_content: PDFContentSource) -> Dict[str, Any]:
        """PDF 문서에서 메타데이터 추출"""
        try:
            readable_content = _read_pdf_bytes(pdf_content)
            doc = fitz.open(stream=readable_content, filetype="pdf")

            # PyMuPDF를 통한 메타데이터 추출
            metadata = doc.metadata or {}

            # 추가 정보 추출
            doc_info = doc.get_xml_metadata()

            # 기본 메타데이터
            extracted_metadata = {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "keywords": metadata.get("keywords", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", ""),
                "total_pages": len(doc),
                "format": metadata.get("format", "PDF"),
                "encryption": "encrypted" if doc.is_encrypted else "not_encrypted",
            }

            # XML 메타데이터에서 추가 정보 추출
            if doc_info:
                try:
                    # XML 메타데이터 파싱 (간단한 추출)
                    if "Title" in doc_info:
                        if not extracted_metadata["title"]:
                            extracted_metadata["title"] = doc_info.get("Title", "")

                    if "Author" in doc_info:
                        if not extracted_metadata["author"]:
                            extracted_metadata["author"] = doc_info.get("Author", "")

                    if "Subject" in doc_info:
                        if not extracted_metadata["subject"]:
                            extracted_metadata["subject"] = doc_info.get("Subject", "")

                    if "Keywords" in doc_info:
                        if not extracted_metadata["keywords"]:
                            extracted_metadata["keywords"] = doc_info.get(
                                "Keywords", ""
                            )

                except Exception as e:
                    logger.warning(f"XML 메타데이터 파싱 실패: {str(e)}")

            # pypdf를 통한 추가 메타데이터 추출
            try:
                pdf_bytes = _read_pdf_bytes(pdf_content)
                pdf_reader = PdfReader(io.BytesIO(pdf_bytes))

                if pdf_reader.metadata:
                    # pypdf 메타데이터로 보완
                    if not extracted_metadata["title"] and pdf_reader.metadata.title:
                        extracted_metadata["title"] = pdf_reader.metadata.title

                    if not extracted_metadata["author"] and pdf_reader.metadata.author:
                        extracted_metadata["author"] = pdf_reader.metadata.author

                    if (
                        not extracted_metadata["subject"]
                        and pdf_reader.metadata.subject
                    ):
                        extracted_metadata["subject"] = pdf_reader.metadata.subject

                    if not extracted_metadata["keywords"] and pdf_reader.metadata.get(
                        "/Keywords"
                    ):
                        extracted_metadata["keywords"] = pdf_reader.metadata.get(
                            "/Keywords"
                        )

                    if (
                        not extracted_metadata["creator"]
                        and pdf_reader.metadata.creator
                    ):
                        extracted_metadata["creator"] = pdf_reader.metadata.creator

                    if (
                        not extracted_metadata["producer"]
                        and pdf_reader.metadata.producer
                    ):
                        extracted_metadata["producer"] = pdf_reader.metadata.producer

                    # 생성일/수정일 처리
                    if pdf_reader.metadata.get("/CreationDate"):
                        extracted_metadata["creation_date"] = pdf_reader.metadata.get(
                            "/CreationDate"
                        )

                    if pdf_reader.metadata.get("/ModDate"):
                        extracted_metadata["modification_date"] = (
                            pdf_reader.metadata.get("/ModDate")
                        )

            except Exception as e:
                logger.warning(f"pypdf 메타데이터 추출 실패: {str(e)}")

            # pdfminer를 통한 추가 메타데이터 추출 시도
            try:
                pdf_bytes = _read_pdf_bytes(pdf_content)

                with io.BytesIO(pdf_bytes) as pdf_file:
                    parser = PDFParser(pdf_file)
                    document = PDFDocument(parser)

                    if document.info:
                        for key, value in document.info[0].items():
                            if isinstance(value, bytes):
                                try:
                                    value = value.decode("utf-8", errors="ignore")
                                except Exception:
                                    continue

                            # 기존 값이 비어있는 경우에만 업데이트
                            key_str = key.lower().replace("/", "")
                            if key_str == "title" and not extracted_metadata["title"]:
                                extracted_metadata["title"] = str(value)
                            elif (
                                key_str == "author" and not extracted_metadata["author"]
                            ):
                                extracted_metadata["author"] = str(value)
                            elif (
                                key_str == "subject"
                                and not extracted_metadata["subject"]
                            ):
                                extracted_metadata["subject"] = str(value)
                            elif (
                                key_str == "keywords"
                                and not extracted_metadata["keywords"]
                            ):
                                extracted_metadata["keywords"] = str(value)
                            elif (
                                key_str == "creator"
                                and not extracted_metadata["creator"]
                            ):
                                extracted_metadata["creator"] = str(value)
                            elif (
                                key_str == "producer"
                                and not extracted_metadata["producer"]
                            ):
                                extracted_metadata["producer"] = str(value)
                            elif (
                                key_str == "creationdate"
                                and not extracted_metadata["creation_date"]
                            ):
                                extracted_metadata["creation_date"] = str(value)
                            elif (
                                key_str == "moddate"
                                and not extracted_metadata["modification_date"]
                            ):
                                extracted_metadata["modification_date"] = str(value)

            except Exception as e:
                logger.warning(f"pdfminer 메타데이터 추출 실패: {str(e)}")

            # 메타데이터 정리 및 반환
            cleaned_metadata = self._clean_metadata(extracted_metadata)

            logger.info(
                f"메타데이터 추출 완료: {len([v for v in cleaned_metadata.values() if v])}개 항목"
            )
            return cleaned_metadata

        except Exception as e:
            logger.error(f"메타데이터 추출 실패: {str(e)}")
            raise ValueError(f"PDF 메타데이터 추출 실패: {str(e)}")

    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """메타데이터 정리 및 정규화"""
        cleaned = {}

        for key, value in metadata.items():
            if value is None:
                cleaned[key] = ""
            elif isinstance(value, str):
                # 문자열 정리
                cleaned_value = value.strip()
                # 날짜 문자열 정규화 (간단한 형식)
                if key.endswith("_date") and cleaned_value.startswith("D:"):
                    cleaned_value = cleaned_value[2:]  # 'D:' 접두사 제거
                cleaned[key] = cleaned_value
            else:
                cleaned[key] = str(value)

        return cleaned

    def extract_title_from_content(self, pdf_content: PDFContentSource) -> str:
        """PDF 내용에서 제목 추출 (메타데이터에 제목이 없는 경우)"""
        try:
            extractor = PDFExtractor(self.settings)
            text_result = extractor.extract_text_from_pdf(pdf_content, page_numbers=[1])

            if text_result["total_text"]:
                # 첫 번째 페이지의 첫 번째 줄을 제목으로 사용
                lines = text_result["total_text"].split("\n")
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 10 and len(line) < 100:
                        # 제목처럼 보이는 줄 찾기 (짧고 내용이 있는 줄)
                        if not line.isdigit() and not line.startswith("="):
                            return line

            return ""

        except Exception as e:
            logger.warning(f"내용 기반 제목 추출 실패: {str(e)}")
            return ""

    def get_metadata_summary(self, pdf_content: PDFContentSource) -> Dict[str, Any]:
        """메타데이터 요약 정보 반환"""
        try:
            metadata = self.extract_metadata(pdf_content)

            # 메타데이터 존재 여부 확인
            has_metadata = any(
                [
                    metadata.get("title", ""),
                    metadata.get("author", ""),
                    metadata.get("subject", ""),
                    metadata.get("keywords", ""),
                ]
            )

            # 주요 메타데이터 항목 수
            metadata_count = len([v for v in metadata.values() if v])

            return {
                "has_metadata": has_metadata,
                "metadata_count": metadata_count,
                "total_fields": len(metadata),
                "primary_info": {
                    "title": metadata.get("title", ""),
                    "author": metadata.get("author", ""),
                    "total_pages": metadata.get("total_pages", 0),
                },
                "document_info": {
                    "creator": metadata.get("creator", ""),
                    "producer": metadata.get("producer", ""),
                    "creation_date": metadata.get("creation_date", ""),
                    "is_encrypted": metadata.get("encryption") == "encrypted",
                },
            }

        except Exception as e:
            logger.error(f"메타데이터 요약 생성 실패: {str(e)}")
            return {
                "has_metadata": False,
                "metadata_count": 0,
                "total_fields": 0,
                "primary_info": {},
                "document_info": {},
                "error": str(e),
            }


# PDF 처리 팩토리 함수
def create_pdf_analyzer(settings: Optional[Settings] = None) -> PDFAnalyzer:
    """PDF 분석기 생성 함수"""
    return PDFAnalyzer(settings)


def create_pdf_extractor(settings: Optional[Settings] = None) -> PDFExtractor:
    """PDF 추출기 생성 함수"""
    return PDFExtractor(settings)


def create_pdf_metadata_extractor(
    settings: Optional[Settings] = None,
) -> PDFMetadataExtractor:
    """PDF 메타데이터 추출기 생성 함수"""
    return PDFMetadataExtractor(settings)
