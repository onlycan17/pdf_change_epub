from __future__ import annotations

import json
import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class LargeFileRequestRecord:
    request_id: str
    requester_user_id: str
    requester_email: str
    request_note: str
    bank_transfer_note: str
    attachment_filename: str
    attachment_size: int
    attachment_path: str
    status: str
    created_at: str
    updated_at: str
    handled_by_email: str | None = None
    conversion_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "requester_user_id": self.requester_user_id,
            "requester_email": self.requester_email,
            "request_note": self.request_note,
            "bank_transfer_note": self.bank_transfer_note,
            "attachment_filename": self.attachment_filename,
            "attachment_size": self.attachment_size,
            "attachment_path": self.attachment_path,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "handled_by_email": self.handled_by_email,
            "conversion_id": self.conversion_id,
        }


class LargeFileRequestService:
    def __init__(
        self,
        *,
        db_url: str,
        storage_dir: str = "./uploads/large_file_requests",
    ) -> None:
        self._db_path = self._sqlite_path_from_db_url(db_url)
        self._storage_dir = Path(storage_dir)
        self._legacy_metadata_path = self._storage_dir / "requests.json"
        self._lock = Lock()

        db_dir = os.path.dirname(self._db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()
        self._migrate_legacy_json_if_needed()

    @staticmethod
    def _sqlite_path_from_db_url(db_url: str) -> str:
        if not db_url.startswith("sqlite:///"):
            raise ValueError("현재는 sqlite DB만 지원합니다.")
        path = db_url.removeprefix("sqlite:///")
        if not path:
            raise ValueError("DB 경로가 비어있습니다.")
        return path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS large_file_requests (
                  request_id TEXT PRIMARY KEY,
                  requester_user_id TEXT NOT NULL,
                  requester_email TEXT NOT NULL,
                  request_note TEXT NOT NULL,
                  bank_transfer_note TEXT NOT NULL,
                  attachment_filename TEXT NOT NULL,
                  attachment_size INTEGER NOT NULL,
                  attachment_path TEXT NOT NULL,
                  status TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  handled_by_email TEXT,
                  conversion_id TEXT
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_lfr_created_at ON large_file_requests(created_at DESC)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_lfr_requester_email ON large_file_requests(requester_email)"
            )

    def _row_to_record(self, row: sqlite3.Row) -> LargeFileRequestRecord:
        return LargeFileRequestRecord(
            request_id=str(row["request_id"]),
            requester_user_id=str(row["requester_user_id"]),
            requester_email=str(row["requester_email"]),
            request_note=str(row["request_note"]),
            bank_transfer_note=str(row["bank_transfer_note"]),
            attachment_filename=str(row["attachment_filename"]),
            attachment_size=int(row["attachment_size"]),
            attachment_path=str(row["attachment_path"]),
            status=str(row["status"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            handled_by_email=(
                str(row["handled_by_email"])
                if row["handled_by_email"] is not None
                else None
            ),
            conversion_id=(
                str(row["conversion_id"]) if row["conversion_id"] is not None else None
            ),
        )

    def _load_legacy_records(self) -> list[dict[str, Any]]:
        if not self._legacy_metadata_path.exists():
            return []
        try:
            raw = self._legacy_metadata_path.read_text(encoding="utf-8")
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
        return []

    def _migrate_legacy_json_if_needed(self) -> None:
        with self._lock:
            with self._connect() as conn:
                legacy_rows = self._load_legacy_records()
                for row in legacy_rows:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO large_file_requests(
                          request_id,
                          requester_user_id,
                          requester_email,
                          request_note,
                          bank_transfer_note,
                          attachment_filename,
                          attachment_size,
                          attachment_path,
                          status,
                          created_at,
                          updated_at,
                          handled_by_email,
                          conversion_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(row.get("request_id") or str(uuid.uuid4())),
                            str(row.get("requester_user_id") or ""),
                            str(row.get("requester_email") or ""),
                            str(row.get("request_note") or ""),
                            str(row.get("bank_transfer_note") or ""),
                            str(row.get("attachment_filename") or "uploaded.pdf"),
                            int(row.get("attachment_size") or 0),
                            str(row.get("attachment_path") or ""),
                            str(row.get("status") or "requested"),
                            str(row.get("created_at") or _utc_now_iso()),
                            str(row.get("updated_at") or _utc_now_iso()),
                            (
                                str(row["handled_by_email"])
                                if row.get("handled_by_email")
                                else None
                            ),
                            (
                                str(row["conversion_id"])
                                if row.get("conversion_id")
                                else None
                            ),
                        ),
                    )

    def get_storage_dir(self) -> Path:
        return self._storage_dir

    def create_request(
        self,
        *,
        requester_user_id: str,
        requester_email: str,
        request_note: str,
        bank_transfer_note: str,
        attachment_filename: str,
        attachment_bytes: bytes,
    ) -> LargeFileRequestRecord:
        with self._lock:
            request_id = str(uuid.uuid4())
            now_iso = _utc_now_iso()
            safe_name = attachment_filename.replace("/", "_").replace("\\", "_")
            stored_name = f"{request_id}_{safe_name or 'uploaded.pdf'}"
            attachment_path = self._storage_dir / stored_name
            attachment_path.write_bytes(attachment_bytes)

            record = LargeFileRequestRecord(
                request_id=request_id,
                requester_user_id=requester_user_id,
                requester_email=requester_email,
                request_note=request_note.strip(),
                bank_transfer_note=bank_transfer_note.strip(),
                attachment_filename=attachment_filename,
                attachment_size=len(attachment_bytes),
                attachment_path=str(attachment_path),
                status="requested",
                created_at=now_iso,
                updated_at=now_iso,
            )

            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO large_file_requests(
                      request_id,
                      requester_user_id,
                      requester_email,
                      request_note,
                      bank_transfer_note,
                      attachment_filename,
                      attachment_size,
                      attachment_path,
                      status,
                      created_at,
                      updated_at,
                      handled_by_email,
                      conversion_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.request_id,
                        record.requester_user_id,
                        record.requester_email,
                        record.request_note,
                        record.bank_transfer_note,
                        record.attachment_filename,
                        record.attachment_size,
                        record.attachment_path,
                        record.status,
                        record.created_at,
                        record.updated_at,
                        record.handled_by_email,
                        record.conversion_id,
                    ),
                )
            return record

    def list_requests(
        self,
        *,
        requester_email: str | None = None,
        status: str | None = None,
        keyword: str | None = None,
        limit: int | None = None,
    ) -> list[LargeFileRequestRecord]:
        with self._lock:
            conditions: list[str] = []
            params: list[object] = []

            normalized_requester_email = (requester_email or "").strip().lower()
            if normalized_requester_email:
                conditions.append("LOWER(requester_email) LIKE ?")
                params.append(f"%{normalized_requester_email}%")

            normalized_status = (status or "").strip().lower()
            if normalized_status:
                conditions.append("LOWER(status) = ?")
                params.append(normalized_status)

            normalized_keyword = (keyword or "").strip().lower()
            if normalized_keyword:
                conditions.append(
                    "(LOWER(request_note) LIKE ? OR LOWER(bank_transfer_note) LIKE ? OR LOWER(attachment_filename) LIKE ?)"
                )
                keyword_value = f"%{normalized_keyword}%"
                params.extend([keyword_value, keyword_value, keyword_value])

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            limit_clause = ""
            if limit is not None and limit > 0:
                limit_clause = " LIMIT ?"
                params.append(limit)
            with self._connect() as conn:
                rows = conn.execute(
                    f"SELECT * FROM large_file_requests {where_clause} ORDER BY created_at DESC{limit_clause}",
                    tuple(params),
                ).fetchall()
            return [self._row_to_record(row) for row in rows]

    def get_status_counts(self) -> dict[str, int]:
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT status, COUNT(*) AS total
                    FROM large_file_requests
                    GROUP BY status
                    """
                ).fetchall()

        counts = {"total": 0, "requested": 0, "processing": 0}
        for row in rows:
            status = str(row["status"])
            total = int(row["total"])
            counts["total"] += total
            counts[status] = total
        return counts

    def get_request(self, request_id: str) -> LargeFileRequestRecord | None:
        with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM large_file_requests WHERE request_id = ?",
                    (request_id,),
                ).fetchone()
            if row:
                return self._row_to_record(row)
        return None

    def mark_conversion_started(
        self,
        *,
        request_id: str,
        conversion_id: str,
        handled_by_email: str,
    ) -> LargeFileRequestRecord | None:
        with self._lock:
            now_iso = _utc_now_iso()
            with self._connect() as conn:
                conn.execute(
                    """
                    UPDATE large_file_requests
                    SET status = ?, conversion_id = ?, handled_by_email = ?, updated_at = ?
                    WHERE request_id = ?
                    """,
                    (
                        "processing",
                        conversion_id,
                        handled_by_email,
                        now_iso,
                        request_id,
                    ),
                )
                row = conn.execute(
                    "SELECT * FROM large_file_requests WHERE request_id = ?",
                    (request_id,),
                ).fetchone()
            if row is None:
                return None
            return self._row_to_record(row)


_service_instance: LargeFileRequestService | None = None


def get_large_file_request_service() -> LargeFileRequestService:
    global _service_instance
    if _service_instance is None:
        from app.core.config import get_settings

        settings = get_settings()
        _service_instance = LargeFileRequestService(db_url=settings.database.url)
    return _service_instance
