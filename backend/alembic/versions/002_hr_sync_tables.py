"""HR synchronization tables migration

Revision ID: 002_hr_sync_tables
Revises: 001_initial_schema
Create Date: 2026-10-04 13:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_hr_sync_tables'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. hr_synced_jobs table
    op.create_table(
        'hr_synced_jobs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('hr_job_id', sa.String(length=100), nullable=False, unique=True),
        sa.Column('tenant_slug', sa.String(length=100), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('salary_min', sa.Float(), nullable=True),
        sa.Column('salary_max', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=20), nullable=True),
        sa.Column('employment_type', sa.String(length=100), nullable=True),
        sa.Column('location_type', sa.String(length=100), nullable=True),
        sa.Column('requirements', sa.Text(), nullable=True),
        sa.Column('skills', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('synced_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True)
    )
    op.create_index('idx_synced_jobs_slug', 'hr_synced_jobs', ['tenant_slug'], unique=False)

    # 2. hr_synced_applications table
    op.create_table(
        'hr_synced_applications',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('hr_application_id', sa.String(length=100), nullable=False, unique=True),
        sa.Column('candidate_email', sa.String(length=320), nullable=False),
        sa.Column('hr_job_id', sa.String(length=100), nullable=True),
        sa.Column('job_title', sa.String(length=255), nullable=True),
        sa.Column('current_status', sa.String(length=50), server_default='APPLIED', nullable=False),
        sa.Column('synced_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True)
    )
    op.create_index('idx_synced_apps_email', 'hr_synced_applications', ['candidate_email'], unique=False)

    # 3. hr_application_stages table
    op.create_table(
        'hr_application_stages',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('hr_application_id', sa.String(length=100), nullable=False),
        sa.Column('stage_number', sa.Integer(), nullable=False),
        sa.Column('stage_name', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=30), server_default='LOCKED', nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.UniqueConstraint('hr_application_id', 'stage_number', name='uq_hr_stage_app_num')
    )
    op.create_index('idx_synced_stages_appid', 'hr_application_stages', ['hr_application_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_synced_stages_appid', table_name='hr_application_stages')
    op.drop_table('hr_application_stages')

    op.drop_index('idx_synced_apps_email', table_name='hr_synced_applications')
    op.drop_table('hr_synced_applications')

    op.drop_index('idx_synced_jobs_slug', table_name='hr_synced_jobs')
    op.drop_table('hr_synced_jobs')
