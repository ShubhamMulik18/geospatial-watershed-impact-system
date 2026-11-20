import importlib.util
import logging
import os
import pathlib
import sys

# Ensure repository root is on sys.path for geospatial package imports
_repo_root = str(pathlib.Path(__file__).resolve().parents[2])
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

# Ensure PROJ_LIB points to rasterio's bundled proj_data to prevent conflicts with PostgreSQL's proj.db
_rasterio_spec = importlib.util.find_spec("rasterio")
if _rasterio_spec and _rasterio_spec.origin:
    _proj_dir = str(pathlib.Path(_rasterio_spec.origin).parent / "proj_data")
    if os.path.exists(_proj_dir):
        os.environ["PROJ_LIB"] = _proj_dir
        os.environ["PROJ_DATA"] = _proj_dir

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes.auth import router as auth_router
from app.api.routes.datasets import router as datasets_router
from app.api.routes.analyses import router as analyses_router
from app.api.routes.photos import router as photos_router
from app.core.config import get_settings
from app.core.constants import API_PREFIX, APP_NAME, HEALTH_PATH
from app.core.error_handlers import app_error_handler
from app.core.exceptions import AppError

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=APP_NAME,
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppError, app_error_handler)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server exception on %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_server_error",
                    "message": "An internal server error occurred.",
                }
            },
        )

    app.include_router(
        auth_router,
        prefix=API_PREFIX,
    )

    app.include_router(
        photos_router,
        prefix=API_PREFIX,
    )

    app.include_router(
        datasets_router,
        prefix=API_PREFIX,
    )

    app.include_router(
        analyses_router,
        prefix=API_PREFIX,
    )

    @app.get("/", tags=["status"])
    async def root() -> dict[str, str]:
        return {
            "status": "online",
            "message": f"{APP_NAME} API is running",
            "version": "0.1.0",
            "docs_url": "/docs",
            "health_url": f"{API_PREFIX}{HEALTH_PATH}",
        }

    @app.get(HEALTH_PATH, tags=["status"], include_in_schema=False)
    async def health_root() -> dict[str, str]:
        return {"status": "ok"}

    @app.get(f"{API_PREFIX}{HEALTH_PATH}", tags=["status"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
