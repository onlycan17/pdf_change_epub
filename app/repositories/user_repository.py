from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status

from app.core.config import Settings


@dataclass(frozen=True)
class UserRecord:
    user_id: str
    provider: str
    provider_sub: str
    email: str
    name: str
    picture: str
    created_at: datetime
    updated_at: datetime


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _sqlite_path_from_db_url(db_url: str) -> str:
    if not db_url.startswith("sqlite:///"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="현재는 sqlite DB만 지원합니다.",
        )
    path = db_url.removeprefix("sqlite:///")
    if not path:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DB 경로가 비어있습니다.",
        )
    return path


class UserRepository:
    def __init__(self, settings: Settings) -> None:
        self._db_path = _sqlite_path_from_db_url(settings.database.url)
        dir_name = os.path.dirname(self._db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema_with_conn(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
              user_id TEXT PRIMARY KEY,
              provider TEXT NOT NULL,
              provider_sub TEXT NOT NULL,
              email TEXT NOT NULL,
              name TEXT NOT NULL,
              picture TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_provider ON users(provider, provider_sub)"
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)"
        )

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            self._ensure_schema_with_conn(conn)

    def get_by_user_id(self, user_id: str) -> Optional[UserRecord]:
        with self._connect() as conn:
            try:
                row = conn.execute(
                    "SELECT * FROM users WHERE user_id = ?",
                    (user_id,),
                ).fetchone()
            except sqlite3.OperationalError:
                self._ensure_schema_with_conn(conn)
                row = conn.execute(
                    "SELECT * FROM users WHERE user_id = ?",
                    (user_id,),
                ).fetchone()
            if not row:
                return None
            return self._row_to_record(row)

    def get_by_provider(self, provider: str, provider_sub: str) -> Optional[UserRecord]:
        with self._connect() as conn:
            try:
                row = conn.execute(
                    "SELECT * FROM users WHERE provider = ? AND provider_sub = ?",
                    (provider, provider_sub),
                ).fetchone()
            except sqlite3.OperationalError:
                self._ensure_schema_with_conn(conn)
                row = conn.execute(
                    "SELECT * FROM users WHERE provider = ? AND provider_sub = ?",
                    (provider, provider_sub),
                ).fetchone()
            if not row:
                return None
            return self._row_to_record(row)

    def get_by_email(self, email: str) -> Optional[UserRecord]:
        with self._connect() as conn:
            try:
                row = conn.execute(
                    "SELECT * FROM users WHERE email = ?",
                    (email,),
                ).fetchone()
            except sqlite3.OperationalError:
                self._ensure_schema_with_conn(conn)
                row = conn.execute(
                    "SELECT * FROM users WHERE email = ?",
                    (email,),
                ).fetchone()
            if not row:
                return None
            return self._row_to_record(row)

    def upsert_google_user(
        self,
        *,
        provider_sub: str,
        email: str,
        name: str = "",
        picture: str = "",
    ) -> UserRecord:
        provider = "google"
        existing_by_email = self.get_by_email(email)
        if existing_by_email and (
            existing_by_email.provider != provider
            or existing_by_email.provider_sub != provider_sub
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 다른 계정과 연결된 이메일입니다.",
            )

        user_id = f"google:{provider_sub}"
        now = _utcnow().isoformat()

        with self._connect() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO users(
                      user_id, provider, provider_sub, email, name, picture, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                      email=excluded.email,
                      name=excluded.name,
                      picture=excluded.picture,
                      updated_at=excluded.updated_at
                    """,
                    (user_id, provider, provider_sub, email, name, picture, now, now),
                )
            except sqlite3.OperationalError:
                self._ensure_schema_with_conn(conn)
                conn.execute(
                    """
                    INSERT INTO users(
                      user_id, provider, provider_sub, email, name, picture, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                      email=excluded.email,
                      name=excluded.name,
                      picture=excluded.picture,
                      updated_at=excluded.updated_at
                    """,
                    (user_id, provider, provider_sub, email, name, picture, now, now),
                )

        record = self.get_by_user_id(user_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="사용자 저장에 실패했습니다.",
            )
        return record

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> UserRecord:
        return UserRecord(
            user_id=str(row["user_id"]),
            provider=str(row["provider"]),
            provider_sub=str(row["provider_sub"]),
            email=str(row["email"]),
            name=str(row["name"]),
            picture=str(row["picture"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )


_user_repository: Optional[UserRepository] = None


def get_user_repository(settings: Settings) -> UserRepository:
    global _user_repository
    if _user_repository is None:
        _user_repository = UserRepository(settings)
    return _user_repository
