"""PDF to EPUB 변환 API 라우트"""

from __future__ import annotations

import os
import uuid
import logging
from typing import Dict
from io import BytesIO
import zipfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse  # type: ignore

from app.core.config import Settings, get_settings
from app.core.dependencies import api_key_header
from app.services.pdf_service import (
    create_pdf_analyzer,
    create_pdf_metadata_extractor,
    PDFType,
)
from app.services.epub_validator import validate_epub_bytes
from app.services.async_queue_service import get_async_queue_service

# 로거 설정
logger = logging.getLogger(__name__)


router = APIRouter(
    tags=["Conversion"],
)


def validate_file_type(file: UploadFile) -> bool:
    """업로드된 파일 형식 검증

    Args:
        file: 업로드된 파일

    Returns:
        bool: 유효성 검사 결과
    """
    if not file.filename:
        return False

    # 파일 확장자 검사
    allowed_extensions = {".pdf"}
    file_ext = os.path.splitext(file.filename)[1].lower()

    return file_ext in allowed_extensions


def validate_file_size(file: UploadFile, max_size: int) -> bool:
    """파일 크기 검증

    Args:
        file: 업로드된 파일
        max_size: 최대 허용 크기 (바이트)

    Returns:
        bool: 유효성 검사 결과
    """
    # 파일 크기 확인 (Content-Length 헤더)
    content_length = file.size

    if content_length is None:
        # 파일 크기를 확인할 수 없는 경우 임시 처리
        return True

    return content_length <= max_size


# 의존성 함수
async def get_conversion_settings(settings: Settings = Depends(get_settings)) -> Dict:
    """변환 설정 정보를 반환하는 의존성 함수

    Args:
        settings: 애플리케이션 설정

    Returns:
        Dict: 변환 설정 정보
    """
    return {
        "max_file_size": 50 * 1024 * 1024,  # 기본값 50MB
        "supported_formats": [".pdf"],
        "output_format": "epub",
    }


# 파일 업로드 및 변환 시작 엔드포인트
@router.post("/start", response_model=Dict)
async def start_conversion(
    file: UploadFile = File(..., description="변환할 PDF 파일"),
    ocr_enabled: bool = Form(False, description="OCR 처리 활성화 여부"),
    api_key: str = Depends(api_key_header),
    settings: Settings = Depends(get_settings),
):
    """PDF 파일 업로드 및 변환 시작 엔드포인트

    Args:
        file: 업로드된 PDF 파일
        ocr_enabled: OCR 처리 옵션
        api_key: API 키
        settings: 애플리케이션 설정

    Returns:
        Dict: 변환 작업 정보
    """
    # 파일 형식 검증
    if not validate_file_type(file):
        raise HTTPException(
            status_code=422,
            detail="지원하지 않는 파일 형식입니다. PDF 파일만 업로드 가능합니다.",
        )

    # 파일 크기 검증
    if not validate_file_size(file, 50 * 1024 * 1024):  # 기본값 50MB
        raise HTTPException(
            status_code=413,
            detail="파일 크기가 너무 큽니다. 최대 50MB까지 업로드 가능합니다.",
        )

    # 변환 작업 ID 생성 및 PDF 로드
    conversion_id = str(uuid.uuid4())
    pdf_bytes = await file.read()

    # 비동기 작업 큐 서비스 시작
    async_queue_service = get_async_queue_service()
    job = await async_queue_service.start_conversion(
        conversion_id=conversion_id,
        filename=file.filename or "uploaded.pdf",
        file_size=len(pdf_bytes),
        ocr_enabled=ocr_enabled,
        pdf_bytes=pdf_bytes,
    )

    return {
        "success": True,
        "message": "변환 작업이 시작되었습니다.",
        "data": {
            "conversion_id": job.conversion_id,
            "filename": job.filename,
            "file_size": job.file_size,
            "ocr_enabled": job.ocr_enabled,
            "status": job.state.value,
            "progress": job.progress,
            "created_at": job.created_at,
            "result_path": job.result_path,
        },
    }


# 변환 상태 조회 엔드포인트
@router.get("/status/{conversion_id}", response_model=Dict)
async def get_conversion_status(
    conversion_id: str, api_key: str = Depends(api_key_header)
):
    """변환 상태 조회 엔드포인트

    Args:
        conversion_id: 변환 작업 ID
        api_key: API 키

    Returns:
        Dict: 변환 상태 정보
    """
    try:
        async_queue_service = get_async_queue_service()
        job = await async_queue_service.get_status(conversion_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="변환 작업을 찾을 수 없습니다.")

    return {
        "success": True,
        "data": {
            "conversion_id": job.conversion_id,
            "status": job.state.value,
            "progress": job.progress,
            "steps": [
                {"name": s.name, "progress": s.progress, "message": s.message}
                for s in job.steps
            ],
            "current_step": job.current_step,
            "filename": job.filename,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "error_message": job.error_message,
            "result_path": job.result_path,
        },
    }


# 변환 결과 다운로드 엔드포인트
@router.get("/download/{conversion_id}")
async def download_result(conversion_id: str, api_key: str = Depends(api_key_header)):
    """변환 결과 EPUB 파일 다운로드 엔드포인트

    Args:
        conversion_id: 변환 작업 ID
        api_key: API 키

    Returns:
        StreamingResponse: EPUB 파일 스트리밍 응답
    """
    # 비동기 작업 큐 서비스에서 결과 조회
    async_queue_service = get_async_queue_service()
    try:
        job = await async_queue_service.get_status(conversion_id)
        if job.state.value != "completed" or not job.result_bytes:
            raise HTTPException(status_code=404, detail="결과가 준비되지 않았습니다.")
        epub_content = job.result_bytes
    except HTTPException as e:
        raise e
    except KeyError:
        raise HTTPException(status_code=404, detail="변환 작업을 찾을 수 없습니다.")

    # EPUB 유효성 검증 수행
    validation = validate_epub_bytes(epub_content)
    if not validation.valid:
        logger.warning(
            "EPUB 유효성 검증 실패",
            extra={
                "conversion_id": conversion_id,
                "errors": [e.code for e in validation.errors],
            },
        )

    return StreamingResponse(
        BytesIO(epub_content),
        media_type="application/epub+zip",
        headers={
            "Content-Disposition": f'attachment; filename="{conversion_id}.epub"',
            "X-EPUB-Valid": "true" if validation.valid else "false",
            "X-EPUB-Version": validation.metadata.get("version", ""),
        },
    )


# 지원 언어 목록 엔드포인트
@router.get("/languages", response_model=Dict)
async def get_supported_languages(
    api_key: str = Depends(api_key_header), settings: Settings = Depends(get_settings)
):
    """지원 언어 목록 조회 엔드포인트

    Args:
        api_key: API 키
        settings: 애플리케이션 설정

    Returns:
        Dict: 지원 언어 목록
    """
    supported_languages = [
        {
            "code": "ko",
            "name": "한국어",
            "description": "한국어 OCR 처리 (PaddleOCR)",
        },
        {
            "code": "en",
            "name": "English",
            "description": "영어 OCR 처리 (Tesseract)",
        },
        {
            "code": "ko-en",
            "name": "한영 혼합",
            "description": "한국어와 영어가 섞인 텍스트 처리",
        },
    ]

    return {
        "success": True,
        "data": supported_languages,
        "default_language": "kor+eng",
    }


# 변환 작업 취소 엔드포인트
@router.delete("/cancel/{conversion_id}", response_model=Dict)
async def cancel_conversion(conversion_id: str, api_key: str = Depends(api_key_header)):
    """변환 작업 취소 엔드포인트

    Args:
        conversion_id: 변환 작업 ID
        api_key: API 키

    Returns:
        Dict: 취소 결과
    """
    async_queue_service = get_async_queue_service()
    try:
        success = await async_queue_service.cancel_conversion(conversion_id)
        if not success:
            raise HTTPException(status_code=404, detail="변환 작업을 찾을 수 없습니다.")
    except KeyError:
        raise HTTPException(status_code=404, detail="변환 작업을 찾을 수 없습니다.")

    return {
        "success": True,
        "message": "변환 작업이 취소되었습니다.",
        "conversion_id": conversion_id,
    }


# 실패한 작업 재시도(수동)
@router.post("/retry/{conversion_id}", response_model=Dict)
async def retry_conversion(conversion_id: str, api_key: str = Depends(api_key_header)):
    """실패한 변환 작업을 수동으로 재시도합니다."""
    async_queue_service = get_async_queue_service()
    try:
        job = await async_queue_service.retry_conversion(conversion_id)
    except KeyError:
        raise HTTPException(
            status_code=404, detail="재시도 가능한 작업을 찾을 수 없습니다."
        )

    return {
        "success": True,
        "message": "재시도가 시작되었습니다.",
        "conversion_id": job.conversion_id,
    }


# PDF 분석 엔드포인트
@router.post("/analyze", response_model=Dict)
async def analyze_pdf_structure(
    file: UploadFile = File(..., description="분석할 PDF 파일"),
    api_key: str = Depends(api_key_header),
):
    """PDF 구조 및 유형 분석 엔드포인트

    Args:
        file: 분석할 PDF 파일
        api_key: API 키

    Returns:
        Dict: PDF 분석 결과
    """
    # 파일 형식 검증
    if not validate_file_type(file):
        raise HTTPException(
            status_code=422,
            detail="지원하지 않는 파일 형식입니다. PDF 파일만 업로드 가능합니다.",
        )

    # 파일 크기 검증
    if not validate_file_size(file, 50 * 1024 * 1024):  # 기본값 50MB
        raise HTTPException(
            status_code=413,
            detail="파일 크기가 너무 큽니다. 최대 50MB까지 업로드 가능합니다.",
        )

    try:
        # PDF 파일 읽기
        pdf_content = await file.read()

        # 분석기 생성
        analyzer = create_pdf_analyzer(get_settings())

        # PDF 분석 수행
        analysis_result = analyzer.analyze_pdf(pdf_content)

        return {
            "success": True,
            "message": "PDF 분석이 완료되었습니다.",
            "data": {
                "pdf_type": analysis_result.pdf_type.value,
                "total_pages": analysis_result.total_pages,
                "overall_confidence": analysis_result.overall_confidence,
                "text_based": {
                    "pages_count": len(analysis_result.get_text_pages()),
                    "page_numbers": analysis_result.get_text_pages(),
                },
                "scanned_based": {
                    "pages_count": len(analysis_result.get_scanned_pages()),
                    "page_numbers": analysis_result.get_scanned_pages(),
                },
                "mixed_ratio": (
                    analysis_result.mixed_ratio
                    if analysis_result.pdf_type == PDFType.MIXED
                    else None
                ),
                "pages_analysis": [
                    page.to_dict() for page in analysis_result.pages_analysis
                ],
            },
        }

    except Exception as e:
        logger.error(f"PDF 분석 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"PDF 분석 중 오류가 발생했습니다: {str(e)}"
        )


# PDF 메타데이터 추출 엔드포인트
@router.post("/metadata", response_model=Dict)
async def extract_pdf_metadata(
    file: UploadFile = File(..., description="메타데이터를 추출할 PDF 파일"),
    include_content_analysis: bool = Form(
        False, description="내용 기반 제목 추출 포함 여부"
    ),
    api_key: str = Depends(api_key_header),
):
    """PDF 메타데이터 추출 엔드포인트

    Args:
        file: 메타데이터를 추출할 PDF 파일
        include_content_analysis: 내용 기반 제목 추출 포함 여부
        api_key: API 키

    Returns:
        Dict: PDF 메타데이터 정보
    """
    # 파일 형식 검증
    if not validate_file_type(file):
        raise HTTPException(
            status_code=422,
            detail="지원하지 않는 파일 형식입니다. PDF 파일만 업로드 가능합니다.",
        )

    # 파일 크기 검증
    if not validate_file_size(file, 50 * 1024 * 1024):  # 기본값 50MB
        raise HTTPException(
            status_code=413,
            detail="파일 크기가 너무 큽니다. 최대 50MB까지 업로드 가능합니다.",
        )

    try:
        # PDF 파일 읽기
        pdf_content = await file.read()

        # 메타데이터 추출기 생성
        metadata_extractor = create_pdf_metadata_extractor(get_settings())

        # 메타데이터 추출
        metadata = metadata_extractor.extract_metadata(pdf_content)

        # 내용 기반 제목 추출 (옵션)
        if include_content_analysis and not metadata.get("title"):
            content_title = metadata_extractor.extract_title_from_content(pdf_content)
            if content_title:
                metadata["extracted_title"] = content_title

        # 메타데이터 요약 정보 생성
        metadata_summary = metadata_extractor.get_metadata_summary(pdf_content)

        return {
            "success": True,
            "message": "PDF 메타데이터 추출이 완료되었습니다.",
            "data": {
                "metadata": metadata,
                "summary": metadata_summary,
                "filename": file.filename,
                "file_size": len(pdf_content),
                "extraction_method": "PyMuPDF + PyPDF2 + pdfminer.six",
            },
        }

    except Exception as e:
        logger.error(f"PDF 메타데이터 추출 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"PDF 메타데이터 추출 중 오류가 발생했습니다: {str(e)}",
        )


# 변환 작업 목록 조회 엔드포인트
@router.get("/list", response_model=Dict)
async def list_conversions(
    limit: int = 10, offset: int = 0, api_key: str = Depends(api_key_header)
):
    """변환 작업 목록 조회 엔드포인트

    Args:
        limit: 반환할 결과 수
        offset: 건너뛰기 개수
        api_key: API 키

    Returns:
        Dict: 변환 작업 목록
    """
    # TODO: 실제 데이터베이스 조회 로직 구현

    # 모의 데이터 생성
    mock_list = []

    for i in range(limit):
        conversion_id = str(uuid.uuid4())
        mock_list.append(
            {
                "conversion_id": conversion_id,
                "filename": f"document_{i + 1}.pdf",
                "status": ["pending", "processing", "completed"][i % 3],
                "created_at": "2024-09-18T11:30:00Z",
            }
        )

    return {
        "success": True,
        "data": mock_list,
        "total_count": len(mock_list),
        "limit": limit,
        "offset": offset,
    }


# 변환 설정 정보 엔드포인트
@router.get("/settings", response_model=Dict)
async def get_conversion_settings_info(
    api_key: str = Depends(api_key_header),
    settings_data: Dict = Depends(get_conversion_settings),
):
    """변환 설정 정보 조회 엔드포인트

    Args:
        api_key: API 키
        settings_data: 변환 설정 데이터

    Returns:
        Dict: 변환 설정 정보
    """
    return {
        "success": True,
        "data": settings_data,
    }


# 모의 EPUB 파일 생성 함수 (실제 구현에서는 제거)
def create_mock_epub(conversion_id: str) -> bytes:
    """EPUB3 표준에 맞춘 최소 구조의 EPUB 생성 (테스트용)

    - mimetype 파일은 반드시 첫 항목이며 비압축으로 저장
    - META-INF/container.xml에서 OEBPS/content.opf를 가리킴
    - content.opf는 version="3.0"이며 nav.xhtml을 포함
    - nav 문서는 properties="nav"를 갖는 XHTML로 생성
    """
    epub_buffer = BytesIO()

    with zipfile.ZipFile(epub_buffer, "w") as zipf:
        # 1) mimetype: 첫 항목, 비압축(ZIP_STORED)
        zipf.writestr(
            zipfile.ZipInfo("mimetype"),
            b"application/epub+zip",
            compress_type=zipfile.ZIP_STORED,
        )

        # 2) META-INF/container.xml
        zipf.writestr(
            "META-INF/container.xml",
            create_container_xml().encode("utf-8"),
            compress_type=zipfile.ZIP_DEFLATED,
        )

        # 3) OEBPS/content.opf
        zipf.writestr(
            "OEBPS/content.opf",
            create_content_opf(conversion_id).encode("utf-8"),
            compress_type=zipfile.ZIP_DEFLATED,
        )

        # 4) OEBPS/nav.xhtml (EPUB3 네비게이션 문서)
        zipf.writestr(
            "OEBPS/nav.xhtml",
            create_nav_xhtml().encode("utf-8"),
            compress_type=zipfile.ZIP_DEFLATED,
        )

        # 5) OEBPS/chapter1.xhtml (샘플 컨텐츠)
        zipf.writestr(
            "OEBPS/chapter1.xhtml",
            create_chapter_xhtml(conversion_id).encode("utf-8"),
            compress_type=zipfile.ZIP_DEFLATED,
        )

    return epub_buffer.getvalue()


def create_container_xml() -> str:
    """EPUB3 container.xml 생성 (OEBPS/content.opf 참조)"""
    return """<?xml version="1.0" encoding="utf-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""


def create_content_opf(conversion_id: str) -> str:
    """EPUB3 content.opf 생성 (nav.xhtml 포함)"""
    return f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<package xmlns=\"http://www.idpf.org/2007/opf\" version=\"3.0\" unique-identifier=\"bookid\">
  <metadata xmlns:dc=\"http://purl.org/dc/elements/1.1/\">
    <dc:identifier id=\"bookid\">urn:uuid:{conversion_id}</dc:identifier>
    <dc:title>변환된 문서</dc:title>
    <dc:creator>PdfToEpub Converter</dc:creator>
    <dc:language>ko</dc:language>
    <meta property=\"dcterms:modified\">2024-09-18T11:30:00Z</meta>
  </metadata>
  <manifest>
    <item id=\"nav\" href=\"nav.xhtml\" media-type=\"application/xhtml+xml\" properties=\"nav\" />
    <item id=\"chapter1\" href=\"chapter1.xhtml\" media-type=\"application/xhtml+xml\" />
  </manifest>
  <spine>
    <itemref idref=\"chapter1\" />
  </spine>
</package>"""


def create_nav_xhtml() -> str:
    """EPUB3 네비게이션 문서(nav.xhtml) 생성"""
    return """<?xml version=\"1.0\" encoding=\"utf-8\"?>
<!DOCTYPE html>
<html xmlns=\"http://www.w3.org/1999/xhtml\" xmlns:epub=\"http://www.idpf.org/2007/ops\" xml:lang=\"ko\" lang=\"ko\">
  <head>
    <meta charset=\"utf-8\" />
    <title>목차</title>
  </head>
  <body>
    <nav epub:type=\"toc\" id=\"toc\">
      <h1>목차</h1>
      <ol>
        <li><a href=\"chapter1.xhtml\">Chapter 1</a></li>
      </ol>
    </nav>
  </body>
  </html>"""


def create_chapter_xhtml(conversion_id: str) -> str:
    """OEBPS/chapter1.xhtml 생성 (EPUB3 xhtml)"""
    return f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<!DOCTYPE html>
<html xmlns=\"http://www.w3.org/1999/xhtml\" xml:lang=\"ko\" lang=\"ko\">
  <head>
    <meta charset=\"utf-8\" />
    <title>Chapter 1</title>
  </head>
  <body>
    <h1>변환된 문서</h1>
    <p>이 문서는 PDF 파일에서 변환되었습니다.</p>
    <p>변환 ID: {conversion_id}</p>

    <h2>소개</h2>
    <p>이 문서는 PDF to EPUB 변환기로 생성되었습니다.</p>

    <h2>변환 과정</h2>
    <ol>
      <li>PDF 파일 분석 텍스트 및 이미지 추출</li>
      <li>텍스트 처리 및 정제</li>
      <li>EPUB 파일 생성</li>
      <li>유효성 검사 및 최종 출력</li>
    </ol>

    <h2>한글 테스트</h2>
    <p>이 문서는 한국어와 English 지원을 테스트합니다.</p>
    <p>한글 처리가 정상적으로 동작하는지 확인합니다.</p>
  </body>
  </html>"""
