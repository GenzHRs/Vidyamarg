import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool, create_engine

# Add root backend directory to sys.path so app modules can be loaded
backend_dir = str(Path(__file__).resolve().parents[1])
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.core.database import Base
import app.models  # Ensure all models are registered with Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_target_url() -> str:
    return os.environ.get("DATABASE_URL") or settings.DATABASE_URL


def run_migrations_offline() -> None:
    url = get_target_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    target_url = get_target_url()
    if target_url.startswith("sqlite"):
        connectable = create_engine(target_url, connect_args={"check_same_thread": False}, poolclass=pool.NullPool)
    else:
        connectable = create_engine(
            target_url.replace("postgres://", "postgresql://", 1).replace("postgresql+asyncpg://", "postgresql://", 1).replace("postgresql://", "postgresql+psycopg2://", 1),
            poolclass=pool.NullPool,
            connect_args={"options": "-c search_path=vidyamarg -c idle_in_transaction_session_timeout=120000 -c lock_timeout=5000"}
        )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
