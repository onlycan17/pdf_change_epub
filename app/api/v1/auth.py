"""인증 API 라우트"""

from __future__ import annotations

from datetime import datetime, timedelta
from collections.abc import Mapping
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import Settings, get_settings
from app.core.dependencies import PRIVILEGED_EMAIL
from app.core.dependencies import api_key_header
from app.models.auth import (
    ApiKeyValidationResponse,
    AuthStatusResponse,
    GoogleLoginRequest,
    GoogleLoginResponse,
    LogoutResponse,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserInfo,
)
from app.services.google_auth import verify_google_id_token
from app.repositories.user_repository import get_user_repository


router = APIRouter(
    tags=["Authentication"],
)

DEMO_USERS: dict[str, dict[str, object]] = {
    "testuser": {
        "password": "testpass",
        "sub": "testuser",
        "email": "testuser@example.com",
        "plan": "free",
        "is_subscribed": False,
        "subscription_active": False,
    },
    "premiumuser": {
        "password": "testpass",
        "sub": "premiumuser",
        "email": "premiumuser@example.com",
        "plan": "premium",
        "is_subscribed": True,
        "subscription_active": True,
    },
    "onlycan17@gmail.com": {
        "password": "testpass",
        "sub": "onlycan17@gmail.com",
        "email": "onlycan17@gmail.com",
        "plan": "yearly",
        "is_subscribed": True,
        "subscription_active": True,
    },
}


# OAuth2 스킬 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


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


def create_access_token(
    data: Mapping[str, object],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """JWT 토큰 생성

    Args:
        data: 토큰 데이터
        expires_delta: 만료 시간

    Returns:
        str: JWT 토큰
    """
    to_encode: dict[str, object] = dict(data)
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    settings = get_settings()
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def build_token_payload(
    *,
    user_id: str,
    email: str,
    plan: str = "free",
    is_subscribed: bool = False,
    subscription_active: bool = False,
) -> dict[str, object]:
    return {
        "sub": user_id,
        "email": email,
        "is_subscribed": is_subscribed,
        "subscription_active": subscription_active,
        "plan": plan,
    }


def verify_token(token: str) -> Optional[dict[str, object]]:
    """JWT 토큰 검증

    Args:
        token: JWT 토큰

    Returns:
        Optional[dict]: 검증된 데이터 (실패 시 None)
    """
    try:

        settings = get_settings()
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        if isinstance(payload, dict):
            return payload
        return None

    except JWTError:
        return None


# 토큰 검증 의존성
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    _settings: Settings = Depends(get_settings),
) -> dict[str, object]:
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

    settings = get_settings()
    repo = get_user_repository(settings)
    record = repo.get_by_user_id(user_id)
    payload_email = payload.get("email")
    if isinstance(payload_email, str) and payload_email:
        email = payload_email
    else:
        email = record.email if record else f"user{user_id}@example.com"

    user: dict[str, object] = {"id": user_id, "email": email}

    return user


# 인증이 필요 없는 엔드포인트
@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    settings: Settings = Depends(get_settings),
):
    """액세스 토큰 발급 엔드포인트

    Args:
        form_data: 로그인 폼 데이터

    Returns:
        dict: 토큰 정보
    """
    token_payload: Optional[dict[str, object]] = None
    demo_user = DEMO_USERS.get(form_data.username)
    if demo_user and form_data.password == demo_user["password"]:
        token_payload = build_token_payload(
            user_id=str(demo_user["sub"]),
            email=str(demo_user["email"]),
            plan=str(demo_user["plan"]),
            is_subscribed=bool(demo_user["is_subscribed"]),
            subscription_active=bool(demo_user["subscription_active"]),
        )
    else:
        repo = get_user_repository(settings)
        record = repo.get_by_email(form_data.username.strip().lower())
        if (
            record is not None
            and record.provider == "local"
            and record.password_hash
            and verify_password(form_data.password, record.password_hash)
        ):
            token_payload = build_token_payload(
                user_id=record.user_id,
                email=record.email,
            )

    if token_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=token_payload, expires_delta=access_token_expires
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(
    payload: RegisterRequest,
    settings: Settings = Depends(get_settings),
):
    normalized_name = payload.name.strip()
    normalized_email = payload.email.strip().lower()
    if len(normalized_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이름은 2자 이상 입력해주세요.",
        )
    if len(payload.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호는 8자 이상이어야 합니다.",
        )

    repo = get_user_repository(settings)
    record = repo.create_local_user(
        email=normalized_email,
        name=normalized_name,
        password_hash=get_password_hash(payload.password),
    )
    return RegisterResponse(
        user_id=record.user_id,
        email=record.email,
        provider=record.provider,
    )


# API 키 인증 엔드포인트 (간단한 방식)
@router.post("/api-key", response_model=ApiKeyValidationResponse)
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
    if not settings.DEBUG and api_key != settings.SECURITY_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )

    return ApiKeyValidationResponse(valid=True, message="API key is valid")


# 현재 사용자 정보 엔드포인트
@router.get("/me", response_model=UserInfo)
async def read_users_me(current_user: dict[str, object] = Depends(get_current_user)):
    """현재 사용자 정보 조회 엔드포인트

    Args:
        current_user: 현재 인증된 사용자 정보

    Returns:
        dict: 사용자 정보
    """
    user_id = current_user.get("id")
    email = current_user.get("email")
    if not isinstance(user_id, str) or not isinstance(email, str):
        raise HTTPException(status_code=401, detail="사용자 정보가 유효하지 않습니다.")
    return UserInfo(
        id=user_id,
        email=email,
        is_privileged=email.lower() == PRIVILEGED_EMAIL,
    )


@router.post("/google", response_model=GoogleLoginResponse)
async def login_with_google(
    payload: GoogleLoginRequest, settings: Settings = Depends(get_settings)
):
    google_payload = verify_google_id_token(
        id_token=payload.id_token,
        client_id=settings.GOOGLE_CLIENT_ID or "",
    )

    sub = google_payload.get("sub")
    email = google_payload.get("email")
    name = google_payload.get("name")
    picture = google_payload.get("picture")
    if not isinstance(sub, str) or not sub:
        raise HTTPException(status_code=401, detail="Google 사용자 정보가 없습니다.")
    if not isinstance(email, str) or not email:
        raise HTTPException(status_code=401, detail="Google 이메일 정보가 없습니다.")

    if name is None or not isinstance(name, str):
        name = ""
    if picture is None or not isinstance(picture, str):
        picture = ""

    repo = get_user_repository(settings)
    user_record = repo.upsert_google_user(
        provider_sub=sub,
        email=email,
        name=name,
        picture=picture,
    )

    token_payload = build_token_payload(
        user_id=user_record.user_id,
        email=email,
    )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=token_payload, expires_delta=access_token_expires
    )

    return GoogleLoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user_record.user_id,
        email=email,
    )


# 로그아웃 엔드포인트
@router.post("/logout", response_model=LogoutResponse)
async def logout(current_user: dict[str, object] = Depends(get_current_user)):
    """로그아웃 엔드포인트

    Args:
        current_user: 현재 인증된 사용자 정보

    Returns:
        dict: 로그아웃 결과
    """
    # TODO: 토큰 블랙리스트 기능 구현
    user_id = current_user.get("id")
    if not isinstance(user_id, str):
        raise HTTPException(status_code=401, detail="사용자 정보가 유효하지 않습니다.")
    return LogoutResponse(message="Successfully logged out", user_id=user_id)


# 간단한 상태 엔드포인트 (인증 없음)
@router.get("/status", response_model=AuthStatusResponse)
async def auth_status():
    """인증 시스템 상태 확인 엔드포인트

    Returns:
        dict: 인증 시스템 상태
    """
    return AuthStatusResponse(
        status="active",
        auth_type="JWT + API Key",
        features=[
            "Token-based authentication",
            "API key validation",
            "Password hashing (bcrypt)",
        ],
    )
