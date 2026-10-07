from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


BACKEND_DIR = Path(__file__).resolve().parents[2]


def test_alembic_configuration_and_head() -> None:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    script = ScriptDirectory.from_config(config)

    heads = script.get_heads()

    assert len(heads) == 1
    assert heads[0] == "31ab98d5eac4"


def test_initial_migration_contains_postgis_setup() -> None:
    migration = (
        BACKEND_DIR
        / "alembic"
        / "versions"
        / "e4848f47f4f6_create_initial_watershed_schema.py"
    )

    content = migration.read_text(encoding="utf-8")

    assert "CREATE EXTENSION IF NOT EXISTS postgis" in content
    assert "spatial_ref_sys" not in content
    assert "geoalchemy2.types.Geometry" not in content
