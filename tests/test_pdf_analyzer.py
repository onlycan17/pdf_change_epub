"""PDF 분석기 테스트"""

import pytest

from app.services.pdf_service import (
    PDFAnalyzer,
    PDFExtractor,
    create_pdf_analyzer,
    create_pdf_extractor,
    PDFType,
    PageAnalysisResult,
    PDFAnalysisResult,
)


class TestPDFAnalyzer:
    """PDF 분석기 테스트 클래스"""

    def setup_method(self):
        """테스트 메서드 실행 전 초기화"""
        self.settings = None
        self.analyzer = PDFAnalyzer(self.settings)

    def test_analyzer_initialization(self):
        """분석기 초기화 테스트"""
        assert self.analyzer.text_density_threshold == 0.1
        # image_text_ratio_threshold는 더 이상 사용되지 않음 (로직에 직접 포함)
        assert hasattr(self.analyzer, "settings")

    def test_pdf_type_enum(self):
        """PDF 유형 enum 테스트"""
        assert PDFType.TEXT_BASED.value == "text_based"
        assert PDFType.SCANNED.value == "scanned"
        assert PDFType.MIXED.value == "mixed"

    def test_page_analysis_result(self):
        """페이지 분석 결과 테스트"""
        result = PageAnalysisResult(
            page_number=1,
            has_text=True,
            text_content="테스트 텍스트",
            image_count=2,
            is_scanned_page=False,
            confidence_score=0.8,
        )

        assert result.page_number == 1
        assert result.has_text is True
        assert result.text_content == "테스트 텍스트"
        assert result.image_count == 2
        assert result.is_scanned_page is False
        assert result.confidence_score == 0.8

        # to_dict 메서드 테스트
        result_dict = result.to_dict()
        assert "page_number" in result_dict
        assert "has_text" in result_dict
        assert "text_content_length" in result_dict

    def test_pdf_analysis_result(self):
        """전체 PDF 분석 결과 테스트"""
        pages = [
            PageAnalysisResult(page_number=1, has_text=True),
            PageAnalysisResult(page_number=2, is_scanned_page=True),
        ]

        analysis_result = PDFAnalysisResult(
            pdf_type=PDFType.MIXED,
            total_pages=2,
            pages_analysis=pages,
            overall_confidence=0.75,
            mixed_ratio=0.5,
        )

        assert analysis_result.pdf_type == PDFType.MIXED
        assert analysis_result.total_pages == 2
        assert len(analysis_result.pages_analysis) == 2

        # 텍스트 페이지 테스트
        text_pages = analysis_result.get_text_pages()
        assert 1 in text_pages

        # 스캔 페이지 테스트
        scanned_pages = analysis_result.get_scanned_pages()
        assert 2 in scanned_pages

        # to_dict 메서드 테스트
        result_dict = analysis_result.to_dict()
        assert "pdf_type" in result_dict
        assert "total_pages" in result_dict

    def test_determine_pdf_type(self):
        """PDF 유형 결정 테스트"""
        # 텍스트 기반 PDF
        pdf_type, mixed_ratio = self.analyzer._determine_pdf_type(
            total_pages=10, text_pages_count=9, scanned_pages_count=1  # 90% 텍스트
        )
        assert pdf_type == PDFType.TEXT_BASED
        assert mixed_ratio == 0.0

        # 스캔 기반 PDF
        pdf_type, mixed_ratio = self.analyzer._determine_pdf_type(
            total_pages=10, text_pages_count=1, scanned_pages_count=9  # 10% 텍스트
        )
        assert pdf_type == PDFType.SCANNED
        assert mixed_ratio == 0.0

        # 혼합 타입 PDF
        pdf_type, mixed_ratio = self.analyzer._determine_pdf_type(
            total_pages=10, text_pages_count=5, scanned_pages_count=5  # 50% 텍스트
        )
        assert pdf_type == PDFType.MIXED
        assert mixed_ratio == 0.5

    def test_calculate_overall_confidence(self):
        """전체 신뢰도 계산 테스트"""
        pages = [
            PageAnalysisResult(page_number=1, confidence_score=0.8),
            PageAnalysisResult(page_number=2, confidence_score=0.7),
        ]

        confidence = self.analyzer._calculate_overall_confidence(pages)
        assert 0.7 <= confidence <= 0.8

        # 빈 목록 테스트
        empty_confidence = self.analyzer._calculate_overall_confidence([])
        assert empty_confidence == 0.0


class TestPDFExtractor:
    """PDF 추출기 테스트 클래스"""

    def setup_method(self):
        """테스트 메서드 실행 전 초기화"""
        self.settings = None
        self.extractor = PDFExtractor(self.settings)

    def test_extractor_initialization(self):
        """추출기 초기화 테스트"""
        assert self.extractor.settings is not None
        assert hasattr(self.extractor, "settings")


def test_create_pdf_analyzer():
    """PDF 분석기 생성 함수 테스트"""
    analyzer = create_pdf_analyzer()
    assert isinstance(analyzer, PDFAnalyzer)


def test_create_pdf_extractor():
    """PDF 추출기 생성 함수 테스트"""
    extractor = create_pdf_extractor()
    assert isinstance(extractor, PDFExtractor)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
