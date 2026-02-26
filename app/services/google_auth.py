from __future__ import annotations

import importlib
from typing import Any, Dict

from fastapi import HTTPException, status


def verify_google_id_token(*, id_token: str, client_id: str) -> Dict[str, Any]:
    if not client_id.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google client id가 설정되지 않았습니다.",
        )
    if not id_token.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="id_token이 비어있습니다.",
        )

    try:
        transport_requests = importlib.import_module("google.auth.transport.requests")
        oauth2_id_token = importlib.import_module("google.oauth2.id_token")
        req = transport_requests.Request()
        payload = oauth2_id_token.verify_oauth2_token(id_token, req, client_id)
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google 토큰 검증에 실패했습니다.",
            )
        return payload
    except HTTPException:
        raise
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="google-auth 라이브러리가 설치되지 않았습니다.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google 토큰 검증에 실패했습니다: {exc}",
        ) from exc
