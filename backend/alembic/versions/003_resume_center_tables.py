"""Resume Center tables migration

Revision ID: 003_resume_center_tables
Revises: 002_hr_sync_tables
Create Date: 2026-10-04 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_resume_center_tables'
down_revision: Union[str, None] = '002_hr_sync_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # 1. resume_templates table
    if 'resume_templates' not in existing_tables:
        op.create_table(
            'resume_templates',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('slug', sa.String(length=100), nullable=False, unique=True),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('preview_image', sa.String(length=500), nullable=True),
            sa.Column('latex_template', sa.Text(), nullable=False),
            sa.Column('category', sa.String(length=50), server_default='Classic', nullable=False),
            sa.Column('license_name', sa.String(length=100), server_default='MIT', nullable=False),
            sa.Column('license_url', sa.String(length=500), nullable=True),
            sa.Column('ats_score', sa.Integer(), server_default='95', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index('idx_resume_templates_slug', 'resume_templates', ['slug'], unique=True)

    # 2. resumes table
    if 'resumes' not in existing_tables:
        op.create_table(
            'resumes',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('candidate_id', sa.Integer(), sa.ForeignKey('candidates.id', ondelete='CASCADE'), nullable=False),
            sa.Column('title', sa.String(length=255), server_default='Untitled Resume', nullable=False),
            sa.Column('source_type', sa.String(length=50), server_default='builder', nullable=False),
            sa.Column('template_id', sa.Integer(), sa.ForeignKey('resume_templates.id', ondelete='SET NULL'), nullable=True),
            sa.Column('current_version_id', sa.Integer(), nullable=True),
            sa.Column('original_file_url', sa.String(length=500), nullable=True),
            sa.Column('latest_pdf_url', sa.String(length=500), nullable=True),
            sa.Column('latest_tex_url', sa.String(length=500), nullable=True),
            sa.Column('status', sa.String(length=50), server_default='active', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
        )
        op.create_index('idx_resumes_candidate_id', 'resumes', ['candidate_id'], unique=False)
        op.create_index('idx_resumes_candidate_deleted', 'resumes', ['candidate_id', 'deleted_at'], unique=False)

    # 3. resume_document_versions table
    if 'resume_document_versions' not in existing_tables:
        op.create_table(
            'resume_document_versions',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('resume_id', sa.Integer(), sa.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False),
            sa.Column('version_number', sa.Integer(), nullable=False),
            sa.Column('structured_data', sa.JSON(), nullable=False),
            sa.Column('latex_source', sa.Text(), nullable=True),
            sa.Column('pdf_file_url', sa.String(length=500), nullable=True),
            sa.Column('change_summary', sa.Text(), nullable=True),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint('resume_id', 'version_number', name='uq_resume_version_num'),
        )
        op.create_index('idx_resume_versions_resume_id', 'resume_document_versions', ['resume_id'], unique=False)

    # 4. job_descriptions table
    if 'job_descriptions' not in existing_tables:
        op.create_table(
            'job_descriptions',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('candidate_id', sa.Integer(), sa.ForeignKey('candidates.id', ondelete='CASCADE'), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('company', sa.String(length=255), nullable=True),
            sa.Column('raw_text', sa.Text(), nullable=False),
            sa.Column('extracted_requirements', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index('idx_job_descriptions_candidate', 'job_descriptions', ['candidate_id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if 'job_descriptions' in existing_tables:
        try:
            op.drop_index('idx_job_descriptions_candidate', table_name='job_descriptions')
        except Exception:
            pass
        op.drop_table('job_descriptions')

    if 'resume_document_versions' in existing_tables:
        try:
            op.drop_index('idx_resume_versions_resume_id', table_name='resume_document_versions')
        except Exception:
            pass
        op.drop_table('resume_document_versions')

    if 'resumes' in existing_tables:
        try:
            op.drop_index('idx_resumes_candidate_deleted', table_name='resumes')
            op.drop_index('idx_resumes_candidate_id', table_name='resumes')
        except Exception:
            pass
        op.drop_table('resumes')

    if 'resume_templates' in existing_tables:
        try:
            op.drop_index('idx_resume_templates_slug', table_name='resume_templates')
        except Exception:
            pass
        op.drop_table('resume_templates')
