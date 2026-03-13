from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sqlite_path_from_db_url(db_url: str) -> str:
    if not db_url.startswith("sqlite:///"):
        raise ValueError("현재는 sqlite DB만 지원합니다.")
    db_path = db_url.removeprefix("sqlite:///")
    if not db_path:
        raise ValueError("DB 경로가 비어있습니다.")
    return db_path


class ConversionMetricsService:
    def __init__(self, *, db_url: str) -> None:
        self._db_path = _sqlite_path_from_db_url(db_url)
        self._lock = Lock()

        db_dir = os.path.dirname(self._db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversion_job_snapshots (
                  conversion_id TEXT PRIMARY KEY,
                  filename TEXT NOT NULL,
                  file_size INTEGER NOT NULL,
                  ocr_enabled INTEGER NOT NULL,
                  translate_to_korean INTEGER NOT NULL,
                  status TEXT NOT NULL,
                  progress INTEGER NOT NULL,
                  current_step TEXT NOT NULL,
                  error_message TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cjs_created_at ON conversion_job_snapshots(created_at DESC)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cjs_status ON conversion_job_snapshots(status)"
            )

    def upsert_job(self, job: Any) -> None:
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO conversion_job_snapshots(
                      conversion_id,
                      filename,
                      file_size,
                      ocr_enabled,
                      translate_to_korean,
                      status,
                      progress,
                      current_step,
                      error_message,
                      created_at,
                      updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(conversion_id) DO UPDATE SET
                      filename=excluded.filename,
                      file_size=excluded.file_size,
                      ocr_enabled=excluded.ocr_enabled,
                      translate_to_korean=excluded.translate_to_korean,
                      status=excluded.status,
                      progress=excluded.progress,
                      current_step=excluded.current_step,
                      error_message=excluded.error_message,
                      updated_at=excluded.updated_at
                    """,
                    (
                        str(job.conversion_id),
                        str(job.filename),
                        int(job.file_size),
                        1 if bool(job.ocr_enabled) else 0,
                        1 if bool(getattr(job, "translate_to_korean", False)) else 0,
                        str(getattr(job.state, "value", job.state)),
                        int(job.progress),
                        str(job.current_step or ""),
                        (
                            str(job.error_message)
                            if getattr(job, "error_message", None)
                            else None
                        ),
                        str(job.created_at or _utc_now_iso()),
                        str(job.updated_at or _utc_now_iso()),
                    ),
                )

    def get_recent_daily_counts(self, *, days: int = 30) -> list[dict[str, int | str]]:
        normalized_days = max(1, days)
        start_date = (
            datetime.now(timezone.utc).date() - timedelta(days=normalized_days - 1)
        ).isoformat()

        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT substr(created_at, 1, 10) AS created_date, COUNT(*) AS total
                    FROM conversion_job_snapshots
                    WHERE substr(created_at, 1, 10) >= ?
                    GROUP BY created_date
                    ORDER BY created_date ASC
                    """,
                    (start_date,),
                ).fetchall()

        counts_by_date = {
            str(row["created_date"]): int(row["total"] or 0) for row in rows
        }
        today = datetime.now(timezone.utc).date()
        return [
            {
                "date": (today - timedelta(days=offset)).isoformat(),
                "count": counts_by_date.get(
                    (today - timedelta(days=offset)).isoformat(),
                    0,
                ),
            }
            for offset in range(normalized_days - 1, -1, -1)
        ]

    def get_status_counts(self) -> dict[str, int]:
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT status, COUNT(*) AS total
                    FROM conversion_job_snapshots
                    GROUP BY status
                    """
                ).fetchall()

        counts = {
            "total": 0,
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
        }
        for row in rows:
            status = str(row["status"])
            total = int(row["total"])
            counts["total"] += total
            if status in counts:
                counts[status] = total
        return counts

    def list_recent_failures(self, *, limit: int = 5) -> list[dict[str, Any]]:
        normalized_limit = max(1, limit)
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT conversion_id, filename, file_size, progress, current_step,
                           error_message, created_at, updated_at
                    FROM conversion_job_snapshots
                    WHERE status = 'failed'
                    ORDER BY updated_at DESC
                    LIMIT ?
                    """,
                    (normalized_limit,),
                ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def classify_failure_reason(
        *,
        error_message: str | None,
        current_step: str | None,
    ) -> tuple[str, str]:
        raw_error = (error_message or "").strip().lower()
        raw_step = (current_step or "").strip().lower()
        merged = f"{raw_step} {raw_error}".strip()

        if any(keyword in merged for keyword in ("ocr", "tesseract", "paddle")):
            return ("ocr", "OCR 처리")
        if any(
            keyword in merged
            for keyword in ("413", "파일", "pdf", "upload", "지원하지 않는", "invalid")
        ):
            return ("file", "파일 문제")
        if any(
            keyword in merged
            for keyword in (
                "openai",
                "openrouter",
                "model",
                "llm",
                "gemini",
                "deepseek",
            )
        ):
            return ("ai", "AI/외부 모델")
        if any(
            keyword in merged
            for keyword in ("timeout", "network", "connection", "502", "503", "gateway")
        ):
            return ("network", "네트워크/외부 연결")
        if any(keyword in merged for keyword in ("cancel", "취소")):
            return ("cancelled", "사용자 취소")
        return ("other", "기타")

    def get_failure_category_counts(self) -> list[dict[str, Any]]:
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT error_message, current_step
                    FROM conversion_job_snapshots
                    WHERE status = 'failed'
                    """
                ).fetchall()

        counts: dict[tuple[str, str], int] = {}
        for row in rows:
            code, label = self.classify_failure_reason(
                error_message=(
                    str(row["error_message"])
                    if row["error_message"] is not None
                    else None
                ),
                current_step=(
                    str(row["current_step"])
                    if row["current_step"] is not None
                    else None
                ),
            )
            key = (code, label)
            counts[key] = counts.get(key, 0) + 1

        ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0][0]))
        return [
            {"code": code, "label": label, "count": count}
            for (code, label), count in ordered
        ]


_service_instance: ConversionMetricsService | None = None


def get_conversion_metrics_service(db_url: str) -> ConversionMetricsService:
    global _service_instance
    normalized_db_path = _sqlite_path_from_db_url(db_url)
    if _service_instance is None or _service_instance._db_path != normalized_db_path:
        _service_instance = ConversionMetricsService(db_url=db_url)
    return _service_instance
