import os
from pathlib import Path
import pytest
from sqlalchemy import create_engine, inspect
from alembic.config import Config
from alembic import command

def test_migration_lifecycle(tmp_path):
    """
    Test starting from a completely empty database, upgrading to head,
    verifying all tables exist, and then verifying downgrade to base.
    """
    db_file = tmp_path / "test_migration.db"
    db_url = f"sqlite:///{db_file.as_posix()}"

    backend_dir = Path(__file__).resolve().parents[1]
    ini_path = backend_dir / "alembic.ini"
    alembic_cfg = Config(str(ini_path))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))

    # Override DATABASE_URL in environment for alembic runner
    old_db_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = db_url

    try:
        # Run upgrade to head
        command.upgrade(alembic_cfg, "head")

        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        # Verify core application tables
        required_tables = {
            "users",
            "candidates",
            "candidate_profiles",
            "candidate_resumes",
            "notifications",
            "otps",
            "user_refresh_tokens",
            "hr_synced_jobs",
            "hr_synced_applications",
            "hr_application_stages",
        }
        for table in required_tables:
            assert table in tables, f"Expected table '{table}' to be created by migrations"

        # Verify columns on hr_synced_jobs
        columns = {col["name"] for col in inspector.get_columns("hr_synced_jobs")}
        assert "hr_job_id" in columns
        assert "tenant_slug" in columns
        assert "salary_min" in columns

        # Run downgrade to base
        command.downgrade(alembic_cfg, "base")
        inspector_post = inspect(engine)
        tables_post = set(inspector_post.get_table_names())

        # Tables should be removed
        for table in required_tables:
            assert table not in tables_post, f"Expected table '{table}' to be removed after downgrade"

    finally:
        if old_db_url:
            os.environ["DATABASE_URL"] = old_db_url
        else:
            os.environ.pop("DATABASE_URL", None)
