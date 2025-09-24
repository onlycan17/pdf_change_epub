"""인증 API 라우트"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import Settings, get_settings
from app.core.dependencies import api_key_header


router = APIRouter(
    tags=["Authentication"],
)


# OAuth2 스킬 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증

    Args:
        plain_password: 평문 비밀번호
        hashed_password: 해시된 비밀번호

    Returns:
        bool: 검증 결과
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """비밀번호 해시 생성

    Args:
        password: 평문 비밀번호

    Returns:
        str: 해시된 비밀번호
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """JWT 토큰 생성

    Args:
        data: 토큰 데이터
        expires_delta: 만료 시간

    Returns:
        str: JWT 토큰
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        "your-jwt-secret-key",  # 기본값
        algorithm="HS256",
    )

    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """JWT 토큰 검증

    Args:
        token: JWT 토큰

    Returns:
        Optional[dict]: 검증된 데이터 (실패 시 None)
    """
    try:

        payload = jwt.decode(
            token,
            "your-jwt-secret-key",  # 기본값
            algorithms=["HS256"],
        )

        return payload

    except JWTError:
        return None


# 토큰 검증 의존성
async def get_current_user(
    token: str = Depends(oauth2_scheme), settings: Settings = Depends(get_settings)
):
    """현재 사용자 정보를 반환하는 의존성 함수

    Args:
        token: JWT 토큰
        settings: 애플리케이션 설정

    Returns:
        dict: 사용자 정보

    Raises:
        HTTPException: 토큰이 유효하지 않은 경우
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    sub = payload.get("sub")
    if not isinstance(sub, str):
        raise credentials_exception
    user_id: str = sub

    # TODO: 실제 사용자 정보 조회 로직 구현
    user = {
        "id": user_id,
        "email": f"user{user_id}@example.com",
    }

    return user


# 인증이 필요 없는 엔드포인트
@router.post("/token", response_model=dict)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """액세스 토큰 발급 엔드포인트

    Args:
        form_data: 로그인 폼 데이터

    Returns:
        dict: 토큰 정보
    """
    # TODO: 실제 사용자 인증 로직 구현
    if form_data.username != "testuser" or form_data.password != "testpass":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 1800,  # 30분
    }


# API 키 인증 엔드포인트 (간단한 방식)
@router.post("/api-key", response_model=dict)
async def validate_api_key(
    api_key: str = Depends(api_key_header), settings: Settings = Depends(get_settings)
):
    """API 키 유효성 검증 엔드포인트

    Args:
        api_key: 클라이언트에서 전달된 API 키
        settings: 애플리케이션 설정

    Returns:
        dict: 유효성 검증 결과
    """
    if (
        not False and api_key != "your-api-key-here"  # debug 기본값 False
    ):  # TODO: 환경 변수에서 로드
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )

    return {
        "valid": True,
        "message": "API key is valid",
    }


# 현재 사용자 정보 엔드포인트
@router.get("/me", response_model=dict)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """현재 사용자 정보 조회 엔드포인트

    Args:
        current_user: 현재 인증된 사용자 정보

    Returns:
        dict: 사용자 정보
    """
    return {
        "id": current_user["id"],
        "email": current_user["email"],
    }


# 로그아웃 엔드포인트
@router.post("/logout", response_model=dict)
async def logout(current_user: dict = Depends(get_current_user)):
    """로그아웃 엔드포인트

    Args:
        current_user: 현재 인증된 사용자 정보

    Returns:
        dict: 로그아웃 결과
    """
    # TODO: 토큰 블랙리스트 기능 구현
    return {
        "message": "Successfully logged out",
        "user_id": current_user["id"],
    }


# 간단한 상태 엔드포인트 (인증 없음)
@router.get("/status", response_model=dict)
async def auth_status():
    """인증 시스템 상태 확인 엔드포인트

    Returns:
        dict: 인증 시스템 상태
    """
    return {
        "status": "active",
        "auth_type": "JWT + API Key",
        "features": [
            "Token-based authentication",
            "API key validation",
            "Password hashing (bcrypt)",
        ],
    }
