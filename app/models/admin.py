from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.conversion import ConversionStatus, DataResponse


class AdminDashboardSummary(BaseModel):
    total_users: int = Field(0, ge=0)
    local_users: int = Field(0, ge=0)
    google_users: int = Field(0, ge=0)
    today_free_conversions: int = Field(0, ge=0)
    total_large_file_requests: int = Field(0, ge=0)
    pending_large_file_requests: int = Field(0, ge=0)
    processing_large_file_requests: int = Field(0, ge=0)
    runtime_pending_jobs: int = Field(0, ge=0)
    runtime_processing_jobs: int = Field(0, ge=0)
    runtime_completed_jobs: int = Field(0, ge=0)
    runtime_failed_jobs: int = Field(0, ge=0)
    persisted_total_conversions: int = Field(0, ge=0)
    persisted_failed_conversions: int = Field(0, ge=0)
    persisted_completed_conversions: int = Field(0, ge=0)


class AdminDashboardDailyUsageItem(BaseModel):
    date: str
    count: int = Field(0, ge=0)


class AdminDashboardLargeFileRequestItem(BaseModel):
    request_id: str
    requester_email: str
    attachment_filename: str
    attachment_size: int = Field(0, ge=0)
    status: str
    created_at: datetime
    updated_at: datetime
    handled_by_email: str | None = None


class AdminDashboardConversionItem(BaseModel):
    conversion_id: str
    filename: str
    file_size: int = Field(0, ge=0)
    status: ConversionStatus
    progress: int = Field(0, ge=0, le=100)
    created_at: datetime
    updated_at: datetime
    current_step: str | None = None
    error_message: str | None = None


class AdminDashboardFailureCategoryItem(BaseModel):
    code: str
    label: str
    count: int = Field(0, ge=0)


class AdminDashboardData(BaseModel):
    summary: AdminDashboardSummary
    daily_free_usage: list[AdminDashboardDailyUsageItem]
    daily_conversion_counts: list[AdminDashboardDailyUsageItem]
    recent_large_file_requests: list[AdminDashboardLargeFileRequestItem]
    recent_runtime_conversions: list[AdminDashboardConversionItem]
    recent_failed_conversions: list[AdminDashboardConversionItem]
    failure_category_counts: list[AdminDashboardFailureCategoryItem]


class AdminDashboardResponse(DataResponse[AdminDashboardData]):
    """운영자 대시보드 응답"""
