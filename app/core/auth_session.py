from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Request, Response

if TYPE_CHECKING:
    from app.core.config import Settings

PRIVILEGED_EMAIL = "onlycan17@gmail.com"
AUTH_COOKIE_NAME = "pdf_to_epub_access_token"
AUTH_SESSION_COOKIE_NAME = "pdf_to_epub_session"
AUTH_PLAN_COOKIE_NAME = "pdf_to_epub_plan"
DEFAULT_SECRET_KEY = "your-secret-key-here"
DEFAULT_API_KEY = "your-api-key-here"


def is_privileged_email(email: str | None) -> bool:
    normalized = (email or "").strip().lower()
    return normalized == PRIVILEGED_EMAIL


def extract_access_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization", "").strip()
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        if token:
            return token

    cookie_token = request.cookies.get(AUTH_COOKIE_NAME, "").strip()
    if cookie_token:
        return cookie_token
    return None


def set_auth_cookies(
    response: Response,
    *,
    token: str,
    plan_code: str,
    expires_in_seconds: int,
    settings: Settings,
) -> None:
    secure = settings.is_production
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=expires_in_seconds,
        path="/",
    )
    response.set_cookie(
        key=AUTH_SESSION_COOKIE_NAME,
        value="1",
        httponly=False,
        secure=secure,
        samesite="lax",
        max_age=expires_in_seconds,
        path="/",
    )
    response.set_cookie(
        key=AUTH_PLAN_COOKIE_NAME,
        value=plan_code,
        httponly=False,
        secure=secure,
        samesite="lax",
        max_age=expires_in_seconds,
        path="/",
    )


def clear_auth_cookies(response: Response, settings: Settings) -> None:
    secure = settings.is_production
    for key in (AUTH_COOKIE_NAME, AUTH_SESSION_COOKIE_NAME, AUTH_PLAN_COOKIE_NAME):
        response.delete_cookie(
            key=key,
            path="/",
            secure=secure,
            samesite="lax",
        )
