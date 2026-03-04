from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def resolve_frontend_dist_dir(*, project_root: Path) -> Optional[Path]:
    configured = os.getenv("APP_FRONTEND_DIST_DIR", "").strip()
    if configured:
        dist_dir = Path(configured)
        return dist_dir if dist_dir.exists() else None

    default = project_root / "frontend" / "dist"
    return default if default.exists() else None


def mount_frontend_if_enabled(app: FastAPI) -> None:
    if not _is_truthy(os.getenv("APP_SERVE_FRONTEND", "")):
        return

    project_root = Path(__file__).resolve().parents[2]
    dist_dir = resolve_frontend_dist_dir(project_root=project_root)
    if not dist_dir:
        return

    assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(assets_dir)),
            name="frontend-assets",
        )

    index_file = dist_dir / "index.html"
    if not index_file.exists():
        return

    @app.get("/", include_in_schema=False)
    async def _frontend_index():
        return FileResponse(index_file)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def _frontend_spa_fallback(full_path: str):
        candidate = dist_dir / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index_file)
