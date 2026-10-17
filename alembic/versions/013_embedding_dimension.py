"""Add embedding versioning columns to memories table.

Revision ID: 013_embedding_dimension
Revises: 012_add_invitations
Create Date: 2026-09-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "013_embedding_dimension"
down_revision: Union[str, None] = "012_add_invitations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("memories", sa.Column("embedding_model", sa.String(100), nullable=True))
    op.add_column("memories", sa.Column("embedding_dimension", sa.Integer(), nullable=True))
    op.add_column("memories", sa.Column("embedding_version", sa.String(100), nullable=True))
    op.add_column("memories", sa.Column("embedded_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_memories_embedding_version", "memories", ["embedding_version"])


def downgrade() -> None:
    op.drop_index("ix_memories_embedding_version", table_name="memories")
    op.drop_column("memories", "embedded_at")
    op.drop_column("memories", "embedding_version")
    op.drop_column("memories", "embedding_dimension")
    op.drop_column("memories", "embedding_model")
