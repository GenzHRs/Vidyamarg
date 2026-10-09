"""
VidyamargAI — Safe Additive Migration
Storage-Efficient Job-Specific Resume Architecture

Migration: Add new columns to resume_optimizations and applications tables.

All operations are safe:
- Uses ADD COLUMN IF NOT EXISTS (PostgreSQL) / tries each alter and ignores duplicates (SQLite).
- Does NOT drop any existing columns or indexes.
- Does NOT alter existing data.
- Idempotent: can be run multiple times safely.

Run:
  python backend/migrations/add_resume_snapshot_fields.py
"""

import sys
import os
import logging
from pathlib import Path

# Add backend dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("migration")

from app.core.database import engine, Base
from sqlalchemy import text, inspect


def column_exists(conn, table: str, column: str) -> bool:
    """Check if a column exists in the given table."""
    insp = inspect(conn)
    cols = [c["name"] for c in insp.get_columns(table)]
    return column in cols


def index_exists(conn, index_name: str) -> bool:
    """Check if an index exists (PostgreSQL / SQLite compatible)."""
    try:
        result = conn.execute(
            text("SELECT 1 FROM sqlite_master WHERE type='index' AND name=:name"),
            {"name": index_name}
        ).fetchone()
        return result is not None
    except Exception:
        # PostgreSQL
        try:
            result = conn.execute(
                text("SELECT 1 FROM pg_indexes WHERE indexname=:name"),
                {"name": index_name}
            ).fetchone()
            return result is not None
        except Exception:
            return False


def unique_constraint_exists(conn, constraint_name: str) -> bool:
    """Check if a named unique constraint already exists."""
    try:
        # SQLite
        result = conn.execute(
            text("SELECT 1 FROM sqlite_master WHERE type='index' AND name=:name"),
            {"name": constraint_name}
        ).fetchone()
        return result is not None
    except Exception:
        try:
            # PostgreSQL
            result = conn.execute(
                text("SELECT 1 FROM pg_constraint WHERE conname=:name"),
                {"name": constraint_name}
            ).fetchone()
            return result is not None
        except Exception:
            return False


def safe_add_column(conn, table: str, column: str, col_def: str):
    """Add a column only if it does not already exist."""
    if column_exists(conn, table, column):
        logger.info(f"  SKIP: Column '{table}.{column}' already exists.")
        return
    try:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}"))
        logger.info(f"  OK: Added column '{table}.{column}'")
    except Exception as e:
        logger.warning(f"  WARN: Could not add '{table}.{column}': {e}")


def safe_create_index(conn, index_name: str, table: str, columns: str, unique: bool = False):
    """Create an index only if it does not already exist."""
    if index_exists(conn, index_name):
        logger.info(f"  SKIP: Index '{index_name}' already exists.")
        return
    try:
        unique_kw = "UNIQUE" if unique else ""
        conn.execute(text(f"CREATE {unique_kw} INDEX IF NOT EXISTS {index_name} ON {table} ({columns})"))
        logger.info(f"  OK: Created index '{index_name}' on {table}({columns})")
    except Exception as e:
        logger.warning(f"  WARN: Could not create index '{index_name}': {e}")


def run_migration():
    logger.info("=" * 60)
    logger.info("VidyamargAI Resume Snapshot Architecture Migration")
    logger.info("=" * 60)

    with engine.begin() as conn:

        # ─────────────────────────────────────────────────────────
        # Table: resume_optimizations
        # ─────────────────────────────────────────────────────────
        logger.info("\n[1] Upgrading resume_optimizations table...")

        safe_add_column(conn, "resume_optimizations", "job_id",
                        "INTEGER REFERENCES jobs(id) ON DELETE SET NULL")
        safe_add_column(conn, "resume_optimizations", "application_id",
                        "INTEGER REFERENCES applications(id) ON DELETE SET NULL")
        safe_add_column(conn, "resume_optimizations", "template_version",
                        "VARCHAR(50)")
        safe_add_column(conn, "resume_optimizations", "jd_hash",
                        "VARCHAR(64)")
        safe_add_column(conn, "resume_optimizations", "content_hash",
                        "VARCHAR(64)")
        safe_add_column(conn, "resume_optimizations", "is_submitted",
                        "BOOLEAN NOT NULL DEFAULT 0")
        safe_add_column(conn, "resume_optimizations", "submitted_at",
                        "DATETIME")
        safe_add_column(conn, "resume_optimizations", "submitted_artifact_url",
                        "VARCHAR(500)")
        safe_add_column(conn, "resume_optimizations", "is_immutable",
                        "BOOLEAN NOT NULL DEFAULT 0")
        safe_add_column(conn, "resume_optimizations", "rendering_mode",
                        "VARCHAR(50) NOT NULL DEFAULT 'template'")
        safe_add_column(conn, "resume_optimizations", "fidelity_tier",
                        "VARCHAR(50) DEFAULT 'template_fallback'")
        safe_add_column(conn, "resume_optimizations", "parent_optimization_id",
                        "INTEGER REFERENCES resume_optimizations(id) ON DELETE SET NULL")
        safe_add_column(conn, "resume_optimizations", "generation_state",
                        "VARCHAR(50) NOT NULL DEFAULT 'SUCCEEDED'")
        safe_add_column(conn, "resume_optimizations", "layout_validation_status",
                        "VARCHAR(50) NOT NULL DEFAULT 'PASSED'")
        safe_add_column(conn, "resume_optimizations", "layout_warnings",
                        "JSON")
        safe_add_column(conn, "resume_optimizations", "candidate_approved",
                        "BOOLEAN NOT NULL DEFAULT 0")
        safe_add_column(conn, "resume_optimizations", "approved_at",
                        "DATETIME")
        safe_add_column(conn, "resume_optimizations", "approval_hash",
                        "VARCHAR(64)")
        safe_add_column(conn, "resume_optimizations", "approval_notes",
                        "TEXT")

        # Indexes for resume_optimizations
        safe_create_index(conn, "idx_opt_candidate_job", "resume_optimizations", "candidate_id, job_id")
        safe_create_index(conn, "idx_opt_candidate_application", "resume_optimizations", "candidate_id, application_id")
        safe_create_index(conn, "idx_opt_candidate_created", "resume_optimizations", "candidate_id, created_at")
        safe_create_index(conn, "idx_opt_jd_hash", "resume_optimizations", "jd_hash")
        safe_create_index(conn, "idx_opt_content_hash", "resume_optimizations", "content_hash")
        safe_create_index(conn, "idx_opt_job_id", "resume_optimizations", "job_id")
        safe_create_index(conn, "idx_opt_application_id", "resume_optimizations", "application_id")

        # Unique constraint for idempotency: (candidate_id, master_resume_id, jd_hash)
        # Only enforce where jd_hash IS NOT NULL
        if not unique_constraint_exists(conn, "uq_optimization_candidate_resume_jd"):
            try:
                conn.execute(text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_optimization_candidate_resume_jd "
                    "ON resume_optimizations (candidate_id, master_resume_id, jd_hash) "
                    "WHERE jd_hash IS NOT NULL"
                ))
                logger.info("  OK: Created partial unique index 'uq_optimization_candidate_resume_jd'")
            except Exception as e:
                logger.warning(f"  WARN: Could not create unique index (may be PostgreSQL syntax): {e}")
                # PostgreSQL version:
                try:
                    conn.execute(text(
                        "CREATE UNIQUE INDEX IF NOT EXISTS uq_optimization_candidate_resume_jd "
                        "ON resume_optimizations (candidate_id, master_resume_id, jd_hash)"
                    ))
                    logger.info("  OK: Created unique index (PostgreSQL)")
                except Exception as e2:
                    logger.warning(f"  WARN: Unique index creation skipped: {e2}")

        # ─────────────────────────────────────────────────────────
        # Table: applications
        # ─────────────────────────────────────────────────────────
        logger.info("\n[2] Upgrading applications table...")

        safe_add_column(conn, "applications", "optimization_id",
                        "INTEGER REFERENCES resume_optimizations(id) ON DELETE SET NULL")
        safe_create_index(conn, "idx_application_optimization_id", "applications", "optimization_id")

    logger.info("\n" + "=" * 60)
    logger.info("Migration completed successfully.")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_migration()
