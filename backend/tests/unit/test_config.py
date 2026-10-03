from app.core.config import Settings


def test_default_settings() -> None:
    settings = Settings()

    assert settings.app_env == "development"
    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.cors_origins == [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    assert settings.dataset_storage_root == "uploads/datasets"
    assert settings.max_dataset_size_bytes == 1024 * 1024 * 1024
    assert settings.max_processing_pixels == 2_000_000
    assert settings.allowed_dataset_extensions == [".tif", ".tiff"]


def test_settings_accept_environment_values() -> None:
    settings = Settings(
        app_env="test",
        database_url="postgresql+psycopg://user:pass@localhost/testdb",
        cors_origins=["http://localhost:8000"],
    )

    assert settings.app_env == "test"
    assert settings.database_url.endswith("@localhost/testdb")
    assert settings.cors_origins == ["http://localhost:8000"]