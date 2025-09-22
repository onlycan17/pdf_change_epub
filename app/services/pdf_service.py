"""PDF 분석 및 처리 서비스"""

from __future__ import annotations

import io
import logging
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from enum import Enum

import fitz  # PyMuPDF

# OCR 관련 임포트는 필요 시 동적 로딩
from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

PDFContentSource = Union[bytes, bytearray, io.IOBase]


def _read_pdf_bytes(pdf_source: PDFContentSource) -> bytes:
    """PDF 입력을 바이트 데이터로 변환"""
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
            readable_content = _read_pdf_bytes(pdf_content)
            doc = fitz.open(stream=readable_content, filetype="pdf")
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
            doc = fitz.open(stream=_read_pdf_bytes(pdf_content), filetype="pdf")

            page_texts: List[Dict[str, str]] = []
            total_text_parts = []

            target_pages = page_numbers or list(range(1, len(doc) + 1))

            for page_num in target_pages:
                if 0 < page_num <= len(doc):
                    # 캐스트하여 Pylance 경고를 억제
                    page = cast(Any, doc[page_num - 1])
                    text = page.get_text()  # type: ignore[attr-defined]

                    if isinstance(text, str) and text.strip():
                        total_text_parts.append(f"=== 페이지 {page_num} ===\n{text}")
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

    def extract_images_from_pdf(
        self, pdf_content: PDFContentSource
    ) -> List[Dict[str, Union[int, bytes]]]:
        """PDF에서 이미지 추출"""
        try:
            doc = fitz.open(stream=_read_pdf_bytes(pdf_content), filetype="pdf")
            images_data = []
            extracted_images = {}

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

                                extracted_images[xref] = {
                                    "page": page_num + 1,
                                    "xref": xref,
                                    "image_bytes": image_bytes,
                                    "format": base_image.get("ext", "unknown"),
                                }

                except Exception as e:
                    logger.warning(f"페이지 {page_num + 1} 이미지 추출 실패: {str(e)}")
                    continue

            images_data = list(extracted_images.values())
            logger.info(f"이미지 추출 완료: {len(images_data)}개")

            return images_data

        except Exception as e:
            logger.error(f"이미지 추출 실패: {str(e)}")
            raise ValueError(f"PDF 이미지 추출 실패: {str(e)}")


# PDF 처리 팩토리 함수
def create_pdf_analyzer(settings: Optional[Settings] = None) -> PDFAnalyzer:
    """PDF 분석기 생성 함수"""
    return PDFAnalyzer(settings)


def create_pdf_extractor(settings: Optional[Settings] = None) -> PDFExtractor:
    """PDF 추출기 생성 함수"""
    return PDFExtractor(settings)
