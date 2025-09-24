from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List, Generic, TypeVar

from pydantic import BaseModel, Field, field_validator


class ConversionStatus(str, Enum):
    """변환 작업 상태"""

    PENDING = "pending"  # 대기 중
    PROCESSING = "processing"  # 진행 중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"  # 실패
    CANCELLED = "cancelled"  # 취소됨


class ConversionRequest(BaseModel):
    """변환 요청 모델"""

    file_path: str = Field(..., description="PDF 파일 경로")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    options: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="변환 옵션 (OCR, 품질 등)"
    )
    priority: int = Field(default=1, ge=1, le=10, description="우선순위 (1-10)")
    max_retries: int = Field(default=3, ge=0, le=10, description="최대 재시도 횟수")


class ConversionResponse(BaseModel):
    """변환 응답 모델"""

    conversion_id: str = Field(..., description="변환 작업 ID")
    status: ConversionStatus = Field(..., description="변환 상태")
    progress: int = Field(0, ge=0, le=100, description="진행률 (%)")
    message: str = Field(..., description="상태 메시지")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="생성 시간"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="수정 시간"
    )
    estimated_time: Optional[int] = Field(None, description="예상 소요 시간 (초)")
    result_path: Optional[str] = Field(None, description="결과 파일 경로")
    error_message: Optional[str] = Field(None, description="오류 메시지")


class ConversionProgress(BaseModel):
    """변환 진행률 모델"""

    conversion_id: str = Field(..., description="변환 작업 ID")
    status: ConversionStatus = Field(..., description="변환 상태")
    progress: int = Field(..., ge=0, le=100, description="진행률 (%)")
    current_step: str = Field(..., description="현재 처리 단계")
    message: str = Field(..., description="진행 메시지")
    estimated_remaining_time: Optional[int] = Field(
        None, description="예상 남은 시간 (초)"
    )


class QueueStats(BaseModel):
    """큐 통계 모델"""

    total_tasks: int = Field(..., description="총 작업 수")
    pending_tasks: int = Field(..., description="대기 중인 작업 수")
    progressing_tasks: int = Field(..., description="진행 중인 작업 수")
    completed_tasks: int = Field(..., description="완료된 작업 수")
    failed_tasks: int = Field(..., description="실패한 작업 수")
    average_processing_time: Optional[float] = Field(
        None, description="평균 처리 시간 (초)"
    )
    tasks_per_hour: Optional[float] = Field(None, description="시간당 작업 수")


class TaskRetry(BaseModel):
    """작업 재시도 모델"""

    task_id: str = Field(..., description="작업 ID")
    retry_count: int = Field(..., ge=0, description="재시도 횟수")
    max_retries: int = Field(..., ge=0, description="최대 재시도 횟수")
    retry_delay: int = Field(..., ge=0, description="재시도 지연 시간 (초)")
    last_error: Optional[str] = Field(None, description="마지막 오류 메시지")
    next_retry_time: Optional[datetime] = Field(None, description="다음 재시도 시간")


class ConversionLog(BaseModel):
    """변환 로그 모델"""

    id: Optional[int] = None
    conversion_id: str = Field(..., description="변환 작업 ID")
    level: str = Field(..., description="로그 레벨 (INFO, WARNING, ERROR)")
    message: str = Field(..., description="로그 메시지")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="로그 시간"
    )
    details: Optional[Dict[str, Any]] = Field(None, description="상세 정보")


class FileMetadata(BaseModel):
    """파일 메타데이터 모델"""

    file_path: str = Field(..., description="파일 경로")
    file_size: int = Field(..., description="파일 크기 (바이트)")
    file_type: str = Field(..., description="파일 타입")
    page_count: Optional[int] = Field(None, description="페이지 수")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="파일 생성 시간"
    )
    modified_at: datetime = Field(
        default_factory=datetime.utcnow, description="파일 수정 시간"
    )


class ConversionResult(BaseModel):
    """변환 결과 모델"""

    conversion_id: str = Field(..., description="변환 작업 ID")
    status: ConversionStatus = Field(..., description="변환 상태")
    result_path: str = Field(..., description="결과 파일 경로")
    file_size: int = Field(..., description="결과 파일 크기 (바이트)")
    processing_time: float = Field(..., description="처리 시간 (초)")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="생성 시간"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 메타데이터")


T = TypeVar("T")


class BaseResponse(BaseModel):
    """기본 응답 모델"""

    success: bool = True
    message: Optional[str] = None


class DataResponse(BaseModel, Generic[T]):
    """데이터를 포함하는 응답 래퍼"""

    success: bool = True
    message: Optional[str] = None
    data: T


class JobStepModel(BaseModel):
    """변환 작업 단계 정보"""

    name: str
    progress: int = Field(0, ge=0, le=100)
    message: Optional[str] = None


class ConversionJobSummary(BaseModel):
    """변환 작업 요약 정보"""

    conversion_id: str
    filename: str
    file_size: int = Field(..., ge=0)
    ocr_enabled: bool
    status: ConversionStatus
    progress: int = Field(..., ge=0, le=100)
    created_at: datetime
    updated_at: datetime
    result_path: Optional[str] = None
    error_message: Optional[str] = None

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _parse_datetime(cls, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            return datetime.fromisoformat(value)
        raise TypeError("Invalid datetime value")


class ConversionJobDetail(ConversionJobSummary):
    """세부 변환 작업 정보"""

    current_step: Optional[str] = None
    steps: List[JobStepModel] = Field(default_factory=list)


class ConversionOperationData(BaseModel):
    """작업 처리 결과 데이터"""

    conversion_id: str


class ConversionOperationResponse(DataResponse[ConversionOperationData]):
    """작업 처리 응답"""


class ConversionStartResponse(DataResponse[ConversionJobSummary]):
    """변환 시작 응답"""


class ConversionStatusResponse(DataResponse[ConversionJobDetail]):
    """변환 상태 응답"""


class LanguageInfo(BaseModel):
    """지원 언어 정보"""

    code: str
    name: str
    description: str


class SupportedLanguagesData(BaseModel):
    """지원 언어 응답 데이터"""

    languages: List[LanguageInfo]
    default_language: str


class SupportedLanguagesResponse(DataResponse[SupportedLanguagesData]):
    """지원 언어 응답"""


class PdfAnalysisData(BaseModel):
    """PDF 분석 데이터"""

    pdf_type: str
    total_pages: int
    overall_confidence: float
    text_based: Dict[str, Any]
    scanned_based: Dict[str, Any]
    mixed_ratio: Optional[float] = None
    pages_analysis: List[Dict[str, Any]] = Field(default_factory=list)


class PdfAnalysisResponse(DataResponse[PdfAnalysisData]):
    """PDF 분석 응답"""


class PdfMetadataData(BaseModel):
    """PDF 메타데이터 응답 데이터"""

    metadata: Dict[str, Any]
    summary: Dict[str, Any]
    filename: Optional[str]
    file_size: int
    extraction_method: str


class PdfMetadataResponse(DataResponse[PdfMetadataData]):
    """PDF 메타데이터 응답"""


class ConversionListItem(BaseModel):
    """변환 목록 항목"""

    conversion_id: str
    filename: str
    status: ConversionStatus
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def _parse_created_at(cls, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            return datetime.fromisoformat(value)
        raise TypeError("Invalid datetime value")


class ConversionListData(BaseModel):
    """변환 목록 응답 데이터"""

    items: List[ConversionListItem]
    total_count: int
    limit: int
    offset: int


class ConversionListResponse(DataResponse[ConversionListData]):
    """변환 목록 응답"""


class ConversionSettingsData(BaseModel):
    """변환 설정 데이터"""

    max_file_size: int
    supported_formats: List[str]
    output_format: str


class ConversionSettingsResponse(DataResponse[ConversionSettingsData]):
    """변환 설정 응답"""
