from __future__ import annotations

from datetime import datetime

from app.models.admin import (
    AdminDashboardConversionItem,
    AdminDashboardDailyUsageItem,
    AdminDashboardData,
    AdminDashboardFailureCategoryItem,
    AdminDashboardLargeFileRequestItem,
    AdminDashboardSummary,
)
from app.models.conversion import ConversionStatus
from app.repositories.user_repository import get_user_repository
from app.services.async_queue_service import get_async_queue_service
from app.services.conversion_metrics_service import get_conversion_metrics_service
from app.services.free_usage_limit_service import get_free_usage_limit_service
from app.services.large_file_request_service import get_large_file_request_service
from app.core.config import Settings


def _parse_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


class AdminDashboardService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def build_dashboard(self) -> AdminDashboardData:
        user_repository = get_user_repository(self._settings)
        free_usage_service = get_free_usage_limit_service(self._settings.database.url)
        conversion_metrics_service = get_conversion_metrics_service(
            self._settings.database.url
        )
        large_file_request_service = get_large_file_request_service()
        async_queue_service = get_async_queue_service()

        provider_counts = user_repository.get_provider_counts()
        daily_usage = free_usage_service.get_recent_daily_usage(days=7)
        daily_conversion_counts = conversion_metrics_service.get_recent_daily_counts(
            days=30
        )
        persisted_conversion_counts = conversion_metrics_service.get_status_counts()
        recent_failed_conversions = conversion_metrics_service.list_recent_failures(
            limit=5
        )
        failure_category_counts = (
            conversion_metrics_service.get_failure_category_counts()
        )
        large_file_request_counts = large_file_request_service.get_status_counts()
        recent_large_file_requests = large_file_request_service.list_requests(limit=5)
        recent_jobs = await async_queue_service.list_recent_jobs(limit=6)

        runtime_counts = {
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
        }
        for job in recent_jobs:
            state_value = getattr(job.state, "value", str(job.state))
            if state_value in runtime_counts:
                runtime_counts[state_value] += 1

        return AdminDashboardData(
            summary=AdminDashboardSummary(
                total_users=provider_counts["total"],
                local_users=provider_counts["local"],
                google_users=provider_counts["google"],
                today_free_conversions=(
                    int(daily_usage[-1]["count"]) if daily_usage else 0
                ),
                total_large_file_requests=large_file_request_counts["total"],
                pending_large_file_requests=large_file_request_counts["requested"],
                processing_large_file_requests=large_file_request_counts["processing"],
                runtime_pending_jobs=runtime_counts["pending"],
                runtime_processing_jobs=runtime_counts["processing"],
                runtime_completed_jobs=runtime_counts["completed"],
                runtime_failed_jobs=runtime_counts["failed"],
                persisted_total_conversions=persisted_conversion_counts["total"],
                persisted_failed_conversions=persisted_conversion_counts["failed"],
                persisted_completed_conversions=persisted_conversion_counts[
                    "completed"
                ],
            ),
            daily_free_usage=[
                AdminDashboardDailyUsageItem(
                    date=str(item["date"]),
                    count=int(item["count"]),
                )
                for item in daily_usage
            ],
            daily_conversion_counts=[
                AdminDashboardDailyUsageItem(
                    date=str(item["date"]),
                    count=int(item["count"]),
                )
                for item in daily_conversion_counts
            ],
            recent_large_file_requests=[
                AdminDashboardLargeFileRequestItem(
                    request_id=item.request_id,
                    requester_email=item.requester_email,
                    attachment_filename=item.attachment_filename,
                    attachment_size=item.attachment_size,
                    status=item.status,
                    created_at=_parse_datetime(item.created_at),
                    updated_at=_parse_datetime(item.updated_at),
                    handled_by_email=item.handled_by_email,
                )
                for item in recent_large_file_requests
            ],
            recent_runtime_conversions=[
                AdminDashboardConversionItem(
                    conversion_id=job.conversion_id,
                    filename=job.filename,
                    file_size=job.file_size,
                    status=ConversionStatus(getattr(job.state, "value", job.state)),
                    progress=job.progress,
                    created_at=_parse_datetime(job.created_at),
                    updated_at=_parse_datetime(job.updated_at),
                    current_step=job.current_step or None,
                    error_message=job.error_message,
                )
                for job in recent_jobs
            ],
            recent_failed_conversions=[
                AdminDashboardConversionItem(
                    conversion_id=str(item["conversion_id"]),
                    filename=str(item["filename"]),
                    file_size=int(item["file_size"]),
                    status=ConversionStatus.FAILED,
                    progress=int(item["progress"]),
                    created_at=_parse_datetime(str(item["created_at"])),
                    updated_at=_parse_datetime(str(item["updated_at"])),
                    current_step=(
                        str(item["current_step"]) if item.get("current_step") else None
                    ),
                    error_message=(
                        str(item["error_message"])
                        if item.get("error_message")
                        else None
                    ),
                )
                for item in recent_failed_conversions
            ],
            failure_category_counts=[
                AdminDashboardFailureCategoryItem(
                    code=str(item["code"]),
                    label=str(item["label"]),
                    count=int(item["count"]),
                )
                for item in failure_category_counts
            ],
        )


def get_admin_dashboard_service(settings: Settings) -> AdminDashboardService:
    return AdminDashboardService(settings)
