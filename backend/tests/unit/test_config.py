from app.core.config import Settings


def test_default_settings() -> None:
    settings = Settings()

    assert settings.app_env == "development"
    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.cors_origins == [
        "http://localhost:3000",
        "http://localhost:5173",
    ]


def test_settings_accept_environment_values() -> None:
    settings = Settings(
        app_env="test",
        database_url="postgresql+psycopg://user:pass@localhost/testdb",
        cors_origins=["http://localhost:8000"],
    )

    assert settings.app_env == "test"
    assert settings.database_url.endswith("@localhost/testdb")
    assert settings.cors_origins == ["http://localhost:8000"]