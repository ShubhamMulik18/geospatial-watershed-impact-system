from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.datasets import router as datasets_router

from app.api.routes.photos import router as photos_router
from app.core.config import get_settings
from app.core.constants import API_PREFIX, APP_NAME, HEALTH_PATH
from app.core.error_handlers import app_error_handler
from app.core.exceptions import AppError


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=APP_NAME,
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppError, app_error_handler)

    app.include_router(
        photos_router,
        prefix=API_PREFIX,
    )

    app.include_router(
        datasets_router,
        prefix=API_PREFIX,
    )

    @app.get(f"{API_PREFIX}{HEALTH_PATH}")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
