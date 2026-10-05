from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://watershed:watershed@localhost:5432/watershed"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    dataset_storage_root: str = "uploads/datasets"
    artifact_storage_root: str = "artifacts"
    max_dataset_size_bytes: int = 1024 * 1024 * 1024
    max_processing_pixels: int = 2_000_000
    allowed_dataset_extensions: list[str] = [".tif", ".tiff"]

    worker_poll_interval_seconds: float = 2.0
    worker_lease_seconds: int = 300
    worker_heartbeat_interval_seconds: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
