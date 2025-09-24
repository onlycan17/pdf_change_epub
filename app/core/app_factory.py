from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging_config import (
    setup_logging,
    configure_debug_logging,
    setup_performance_logging,
)
from app.api.v1 import auth, conversion


def create_app(*, lifespan=None) -> FastAPI:
    settings = get_settings()

    # logging
    setup_logging(
        settings=settings,
        log_level=getattr(settings, "log_level", "INFO"),
        json_logs=not False,
    )  # debug 기본값 False
    if False:  # debug 기본값 False
        configure_debug_logging()
    setup_performance_logging()

    app = FastAPI(
        title="PDF to EPUB Converter API",  # 기본값
        description="PDF 문서를 EPUB 전자책으로 변환하는 RESTful API 서비스",
        version="1.0.0",  # 기본값
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8080"],  # 기본값
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # include routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(
        conversion.router, prefix="/api/v1/conversion", tags=["Conversion"]
    )

    return app
