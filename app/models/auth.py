"""인증 관련 Pydantic 모델"""

from typing import List

from pydantic import BaseModel, EmailStr


class TokenResponse(BaseModel):
    """액세스 토큰 응답"""

    access_token: str
    token_type: str
    expires_in: int


class ApiKeyValidationResponse(BaseModel):
    """API 키 검증 응답"""

    valid: bool
    message: str


class UserInfo(BaseModel):
    """사용자 정보 응답"""

    id: str
    email: EmailStr


class LogoutResponse(BaseModel):
    """로그아웃 응답"""

    message: str
    user_id: str


class AuthStatusResponse(BaseModel):
    """인증 시스템 상태 응답"""

    status: str
    auth_type: str
    features: List[str]
