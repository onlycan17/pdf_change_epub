from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.v1.auth import verify_token
from app.core.auth_session import extract_access_token, is_privileged_email
from app.core.config import Settings, get_settings
from app.core.dependencies import get_api_key
from app.models.admin import AdminDashboardResponse
from app.repositories.user_repository import get_user_repository
from app.services.admin_dashboard_service import get_admin_dashboard_service


router = APIRouter(tags=["Admin"])


def _extract_bearer_token(request: Request) -> str | None:
    return extract_access_token(request)


def _ensure_privileged_user(request: Request, settings: Settings) -> str:
    token = _extract_bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="유효한 로그인 정보가 아닙니다.")

    email_raw = payload.get("email")
    if isinstance(email_raw, str) and email_raw:
        email = email_raw
    else:
        user_id = payload.get("sub")
        if not isinstance(user_id, str) or not user_id:
            raise HTTPException(
                status_code=401, detail="유효한 로그인 정보가 아닙니다."
            )
        record = get_user_repository(settings).get_by_user_id(user_id)
        email = record.email if record else ""

    if not is_privileged_email(email):
        raise HTTPException(status_code=403, detail="운영자만 접근할 수 있습니다.")

    return email


@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    request: Request,
    api_key: str | None = Depends(get_api_key),
    settings: Settings = Depends(get_settings),
):
    del api_key
    _ensure_privileged_user(request, settings)

    service = get_admin_dashboard_service(settings)
    dashboard = await service.build_dashboard()
    return AdminDashboardResponse(
        message="운영자 대시보드 데이터를 불러왔습니다.",
        data=dashboard,
    )
