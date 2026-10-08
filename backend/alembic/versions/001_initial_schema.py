"""Initial application schema migration

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-04 13:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Dynamically import and create all Base model tables
    from app.core.database import Base
    import app.models

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    from app.core.database import Base
    import app.models

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
