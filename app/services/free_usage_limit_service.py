from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from threading import Lock


def _today_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


class FreeUsageLimitService:
    def __init__(self, *, db_url: str, daily_limit: int = 2) -> None:
        self._db_path = self._sqlite_path_from_db_url(db_url)
        self._daily_limit = daily_limit
        self._lock = Lock()

        db_dir = os.path.dirname(self._db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._ensure_schema()

    @staticmethod
    def _sqlite_path_from_db_url(db_url: str) -> str:
        if not db_url.startswith("sqlite:///"):
            raise ValueError("현재는 sqlite DB만 지원합니다.")
        db_path = db_url.removeprefix("sqlite:///")
        if not db_path:
            raise ValueError("DB 경로가 비어있습니다.")
        return db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS free_usage_daily_limits (
                  user_id TEXT NOT NULL,
                  usage_date TEXT NOT NULL,
                  usage_count INTEGER NOT NULL,
                  updated_at TEXT NOT NULL,
                  PRIMARY KEY (user_id, usage_date)
                )
                """
            )

    def try_consume(self, user_id: str) -> bool:
        if not user_id.strip():
            return False

        usage_date = _today_utc()
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    """
                    SELECT usage_count
                    FROM free_usage_daily_limits
                    WHERE user_id = ? AND usage_date = ?
                    """,
                    (user_id, usage_date),
                ).fetchone()

                current_count = int(row["usage_count"]) if row else 0
                if current_count >= self._daily_limit:
                    return False

                if row:
                    conn.execute(
                        """
                        UPDATE free_usage_daily_limits
                        SET usage_count = usage_count + 1, updated_at = ?
                        WHERE user_id = ? AND usage_date = ?
                        """,
                        (now_iso, user_id, usage_date),
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO free_usage_daily_limits(
                          user_id,
                          usage_date,
                          usage_count,
                          updated_at
                        ) VALUES (?, ?, ?, ?)
                        """,
                        (user_id, usage_date, 1, now_iso),
                    )

                return True

    def get_recent_daily_usage(self, *, days: int = 7) -> list[dict[str, int | str]]:
        normalized_days = max(1, days)
        start_date = (
            datetime.now(timezone.utc).date() - timedelta(days=normalized_days - 1)
        ).isoformat()

        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT usage_date, SUM(usage_count) AS total_usage
                    FROM free_usage_daily_limits
                    WHERE usage_date >= ?
                    GROUP BY usage_date
                    ORDER BY usage_date ASC
                    """,
                    (start_date,),
                ).fetchall()

        usage_by_date = {
            str(row["usage_date"]): int(row["total_usage"] or 0) for row in rows
        }
        today = datetime.now(timezone.utc).date()
        return [
            {
                "date": (today - timedelta(days=offset)).isoformat(),
                "count": usage_by_date.get(
                    (today - timedelta(days=offset)).isoformat(),
                    0,
                ),
            }
            for offset in range(normalized_days - 1, -1, -1)
        ]


_service_instance: FreeUsageLimitService | None = None


def get_free_usage_limit_service(db_url: str) -> FreeUsageLimitService:
    global _service_instance
    if _service_instance is None:
        _service_instance = FreeUsageLimitService(db_url=db_url)
    return _service_instance
