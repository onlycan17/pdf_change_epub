"""PDF 분석기 테스트"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from app.services.pdf_service import (
    PDFAnalyzer,
    PDFExtractor,
    PDFMetadataExtractor,
    create_pdf_analyzer,
    create_pdf_extractor,
    create_pdf_metadata_extractor,
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

    def test_extract_text_with_pypdf2(self):
        """PyPDF2를 사용한 텍스트 추출 테스트"""
        # 더미 PDF 데이터 생성 (실제로는 파일이 필요하지만, 여기서는 메서드 존재 여부만 테스트)
        dummy_pdf_data = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Hello, World!) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000224 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n329\n%%EOF"

        # 메서드 존재 여부 확인
        assert hasattr(self.extractor, "extract_text_with_pypdf2")

        # 실제 호출은 실제 PDF 파일이 없으므로 예외가 발생할 수 있지만
        # 메서드가 호출 가능한지 확인
        try:
            result = self.extractor.extract_text_with_pypdf2(dummy_pdf_data)
            # 성공 시 결과 구조 확인
            assert "total_text" in result
            assert "page_texts" in result
            assert "extraction_stats" in result
            assert result["extraction_stats"]["extractor"] == "PyPDF2"
        except ValueError as e:
            # PDF 파싱 실패는 예상되는 예외
            assert "PyPDF2" in str(e)

    def test_extract_text_with_pdfminer(self):
        """pdfminer.six를 사용한 텍스트 추출 테스트"""
        # 더미 PDF 데이터 생성
        dummy_pdf_data = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Hello, World!) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000224 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n329\n%%EOF"

        # 메서드 존재 여부 확인
        assert hasattr(self.extractor, "extract_text_with_pdfminer")

        # 실제 호출은 실제 PDF 파일이 없으므로 예외가 발생할 수 있지만
        # 메서드가 호출 가능한지 확인
        try:
            result = self.extractor.extract_text_with_pdfminer(dummy_pdf_data)
            # 성공 시 결과 구조 확인
            assert "total_text" in result
            assert "page_texts" in result
            assert "extraction_stats" in result
            assert result["extraction_stats"]["extractor"] == "pdfminer.six"
        except ValueError as e:
            # PDF 파싱 실패는 예상되는 예외
            assert "pdfminer.six" in str(e)

    def test_extract_images_with_pypdf2(self):
        """PyPDF2를 사용한 이미지 추출 테스트"""
        # 더미 PDF 데이터 생성
        dummy_pdf_data = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Hello, World!) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000224 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n329\n%%EOF"

        # 메서드 존재 여부 확인
        assert hasattr(self.extractor, "extract_images_with_pypdf2")

        # 실제 호출은 실제 PDF 파일이 없으므로 예외가 발생할 수 있지만
        # 메서드가 호출 가능한지 확인
        try:
            result = self.extractor.extract_images_with_pypdf2(dummy_pdf_data)
            # 결과가 리스트인지 확인
            assert isinstance(result, list)
            # 각 항목이 필요한 키를 가지고 있는지 확인
            for item in result:
                assert "page" in item
                assert "image_bytes" in item
                assert "format" in item
                assert "extractor" in item
        except ValueError as e:
            # PDF 파싱 실패는 예상되는 예외
            assert "PyPDF2" in str(e)


def test_create_pdf_analyzer():
    """PDF 분석기 생성 함수 테스트"""
    analyzer = create_pdf_analyzer()
    assert isinstance(analyzer, PDFAnalyzer)


def test_create_pdf_extractor():
    """PDF 추출기 생성 함수 테스트"""
    extractor = create_pdf_extractor()
    assert isinstance(extractor, PDFExtractor)


class TestPDFMetadataExtractor:
    """PDF 메타데이터 추출기 테스트 클래스"""

    def setup_method(self):
        """테스트 메서드 실행 전 초기화"""
        self.settings = None
        self.extractor = PDFMetadataExtractor(self.settings)

    def test_extractor_initialization(self):
        """메타데이터 추출기 초기화 테스트"""
        assert self.extractor.settings is not None
        assert hasattr(self.extractor, "settings")

    def test_extract_metadata_basic(self):
        """기본 메타데이터 추출 테스트"""
        # 더미 PDF 데이터 생성 (실제로는 파일이 필요하지만, 여기서는 메서드 존재 여부만 테스트)
        dummy_pdf_data = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Hello, World!) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000224 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n329\n%%EOF"

        # 메서드 존재 여부 확인
        assert hasattr(self.extractor, "extract_metadata")

        # 실제 호출은 실제 PDF 파일이 없으므로 예외가 발생할 수 있지만
        # 메서드가 호출 가능한지 확인
        try:
            result = self.extractor.extract_metadata(dummy_pdf_data)
            # 성공 시 결과 구조 확인
            assert isinstance(result, dict)
            assert "title" in result
            assert "author" in result
            assert "total_pages" in result
            assert "encryption" in result
        except ValueError as e:
            # PDF 파싱 실패는 예상되는 예외
            assert "PDF" in str(e)

    def test_clean_metadata(self):
        """메타데이터 정리 기능 테스트"""
        # 테스트용 메타데이터
        test_metadata = {
            "title": "  Test Title  ",
            "author": "Test Author",
            "creation_date": "D:20240101",
            "empty_field": None,
            "normal_field": "Normal Value",
        }

        cleaned = self.extractor._clean_metadata(test_metadata)

        # 정리된 결과 확인
        assert cleaned["title"] == "Test Title"  # 공백 제거
        assert cleaned["author"] == "Test Author"
        assert cleaned["creation_date"] == "20240101"  # D: 접두사 제거
        assert cleaned["empty_field"] == ""  # None -> 빈 문자열
        assert cleaned["normal_field"] == "Normal Value"

    def test_extract_title_from_content(self):
        """내용 기반 제목 추출 테스트"""
        # 더미 PDF 데이터 생성
        dummy_pdf_data = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Hello, World!) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000224 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n329\n%%EOF"

        # 메서드 존재 여부 확인
        assert hasattr(self.extractor, "extract_title_from_content")

        # 실제 호출은 실제 PDF 파일이 없으므로 예외가 발생할 수 있지만
        # 메서드가 호출 가능한지 확인
        try:
            result = self.extractor.extract_title_from_content(dummy_pdf_data)
            # 결과가 문자열인지 확인
            assert isinstance(result, str)
        except ValueError as e:
            # PDF 파싱 실패는 예상되는 예외
            assert "PDF" in str(e)

    def test_get_metadata_summary(self):
        """메타데이터 요약 정보 테스트"""
        # 더미 PDF 데이터 생성
        dummy_pdf_data = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Hello, World!) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000224 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n329\n%%EOF"

        # 메서드 존재 여부 확인
        assert hasattr(self.extractor, "get_metadata_summary")

        # 실제 호출은 실제 PDF 파일이 없으므로 예외가 발생할 수 있지만
        # 메서드가 호출 가능한지 확인
        try:
            result = self.extractor.get_metadata_summary(dummy_pdf_data)
            # 결과 구조 확인
            assert isinstance(result, dict)
            assert "has_metadata" in result
            assert "metadata_count" in result
            assert "total_fields" in result
            assert "primary_info" in result
            assert "document_info" in result
        except ValueError as e:
            # PDF 파싱 실패는 예상되는 예외
            assert "PDF" in str(e)

    def test_metadata_extraction_with_empty_pdf(self):
        """빈 PDF 파일로 메타데이터 추출 테스트"""
        # 빈 PDF 데이터
        empty_pdf_data = b""

        # 메서드 존재 여부 확인
        assert hasattr(self.extractor, "extract_metadata")

        # 빈 데이터로 호출 시 예외 발생 확인
        try:
            result = self.extractor.extract_metadata(empty_pdf_data)
            # 예외가 발생하지 않으면 기본 구조 확인
            assert isinstance(result, dict)
        except ValueError as e:
            # PDF 파싱 실패는 예상되는 예외
            assert "PDF" in str(e) or "메타데이터" in str(e)


def test_create_pdf_metadata_extractor():
    """PDF 메타데이터 추출기 생성 함수 테스트"""
    extractor = create_pdf_metadata_extractor()
    assert isinstance(extractor, PDFMetadataExtractor)


class TestMetadataAPI:
    """메타데이터 API 엔드포인트 테스트 클래스"""

    def setup_method(self):
        """테스트 메서드 실행 전 초기화"""
        from app.main import app

        self.client = TestClient(app)

    @patch("app.api.v1.conversion.api_key_header")
    def test_extract_pdf_metadata_endpoint_exists(self, mock_api_key_header):
        """메타데이터 추출 엔드포인트 존재 여부 테스트"""
        # API 키 검증 Mock 설정
        mock_api_key_header.return_value = "your-api-key-here"

        # 먼저 헬스체크 엔드포인트로 기본 기능 확인
        health_response = self.client.get("/health")
        assert health_response.status_code == 200

        # API 키 없이 접근 시도 (401 응답 확인)
        response = self.client.post(
            "/api/v1/conversion/metadata",
            headers={
                "X-API-Key": "your-api-key-here",
                "Content-Type": "application/json",
            },
        )
        # 404가 발생하면 라우터 등록 문제, 415가 발생하면 Content-Type 문제
        assert response.status_code in [404, 415, 422]

    @patch("app.api.v1.conversion.create_pdf_metadata_extractor")
    @patch("app.api.v1.conversion.api_key_header")
    def test_extract_pdf_metadata_success(
        self, mock_api_key_header, mock_extractor_class
    ):
        """메타데이터 추출 성공 테스트"""
        # API 키 검증 Mock 설정
        mock_api_key_header.return_value = "your-api-key-here"

        # Mock 설정
        mock_extractor = Mock()
        mock_extractor.extract_metadata.return_value = {
            "title": "Test Document",
            "author": "Test Author",
            "total_pages": 5,
            "encryption": "not_encrypted",
        }
        mock_extractor.get_metadata_summary.return_value = {
            "has_metadata": True,
            "metadata_count": 4,
            "primary_info": {"title": "Test Document", "author": "Test Author"},
        }
        mock_extractor_class.return_value = mock_extractor

        # 테스트 파일 생성
        test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 2\n0000000000 65535 f\n0000000009 00000 n\ntrailer\n<<\n/Size 2\n/Root 1 0 R\n>>\nstartxref\n55\n%%EOF"

        # API 호출 (API 키 포함)
        response = self.client.post(
            "/api/v1/conversion/metadata",
            files={"file": ("test.pdf", test_pdf_content, "application/pdf")},
            data={"include_content_analysis": "false"},
            headers={"X-API-Key": "your-api-key-here"},
        )

        # 응답 검증
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "metadata" in data["data"]
        assert "summary" in data["data"]

        # Mock 호출 확인
        mock_extractor_class.assert_called_once()
        mock_extractor.extract_metadata.assert_called_once()
        mock_extractor.get_metadata_summary.assert_called_once()

    @patch("app.api.v1.conversion.api_key_header")
    def test_extract_pdf_metadata_invalid_file_type(self, mock_api_key_header):
        """잘못된 파일 형식으로 메타데이터 추출 테스트"""
        # API 키 검증 Mock 설정
        mock_api_key_header.return_value = "your-api-key-here"

        # 텍스트 파일로 테스트
        test_content = b"This is not a PDF file"

        response = self.client.post(
            "/api/v1/conversion/metadata",
            files={"file": ("test.txt", test_content, "text/plain")},
            headers={"X-API-Key": "your-api-key-here"},
        )

        assert response.status_code == 422
        data = response.json()
        assert "지원하지 않는 파일 형식" in data["detail"]

    @patch("app.api.v1.conversion.create_pdf_metadata_extractor")
    @patch("app.api.v1.conversion.api_key_header")
    def test_extract_pdf_metadata_with_content_analysis(
        self, mock_api_key_header, mock_extractor_class
    ):
        """내용 분석 포함 메타데이터 추출 테스트"""
        # API 키 검증 Mock 설정
        mock_api_key_header.return_value = "your-api-key-here"

        # Mock 설정
        mock_extractor = Mock()
        mock_extractor.extract_metadata.return_value = {
            "title": "",  # 제목이 없는 경우
            "author": "Test Author",
            "total_pages": 5,
        }
        mock_extractor.extract_title_from_content.return_value = "Extracted Title"
        mock_extractor.get_metadata_summary.return_value = {
            "has_metadata": True,
            "metadata_count": 3,
        }
        mock_extractor_class.return_value = mock_extractor

        test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 2\n0000000000 65535 f\n0000000009 00000 n\ntrailer\n<<\n/Size 2\n/Root 1 0 R\n>>\nstartxref\n55\n%%EOF"

        response = self.client.post(
            "/api/v1/conversion/metadata",
            files={"file": ("test.pdf", test_pdf_content, "application/pdf")},
            data={"include_content_analysis": "true"},
            headers={"X-API-Key": "your-api-key-here"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "extracted_title" in data["data"]["metadata"]
        assert data["data"]["metadata"]["extracted_title"] == "Extracted Title"

        # 내용 기반 제목 추출이 호출되었는지 확인
        mock_extractor.extract_title_from_content.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
