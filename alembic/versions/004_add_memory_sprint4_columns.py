"""004_add_memory_sprint4_columns

Revision ID: 004_add_memory_sprint4_columns
Revises: 003_sprint3_pipeline
Create Date: 2026-08-31 08:34:17.570846
"""
from alembic import op
import sqlalchemy as sa


revision = "004_add_memory_sprint4_columns"
down_revision: str | None = "003_sprint3_pipeline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add sprint-4 columns to existing memories table
    op.add_column("memories", sa.Column("project_id", sa.String(length=36), nullable=True))
    op.add_column("memories", sa.Column("temporal_status", sa.String(length=50), nullable=False, server_default="current"))
    op.add_column("memories", sa.Column("confidence", sa.Float(), nullable=False, server_default="0.7"))
    op.add_column("memories", sa.Column("authority", sa.Float(), nullable=False, server_default="1.0"))
    op.add_column("memories", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    # Create indexes
    op.create_index(op.f("ix_memories_project_id"), "memories", ["project_id"], unique=False)
    op.create_index(op.f("ix_memories_temporal_status"), "memories", ["temporal_status"], unique=False)
    op.create_index(op.f("ix_memories_deleted_at"), "memories", ["deleted_at"], unique=False)

    # Add foreign key
    op.create_foreign_key(None, "memories", "projects", ["project_id"], ["id"])

    # Add sprint-4 columns to existing message_provenance table
    op.add_column("message_provenance", sa.Column("retrieval_sources", sa.JSON(), nullable=True))
    op.add_column("message_provenance", sa.Column("user_message_preview", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("message_provenance", "user_message_preview")
    op.drop_column("message_provenance", "retrieval_sources")
    op.drop_constraint(None, "memories", type_="foreignkey")
    op.drop_index(op.f("ix_memories_temporal_status"), table_name="memories")
    op.drop_index(op.f("ix_memories_project_id"), table_name="memories")
    op.drop_index(op.f("ix_memories_deleted_at"), table_name="memories")
    op.drop_column("memories", "deleted_at")
    op.drop_column("memories", "authority")
    op.drop_column("memories", "confidence")
    op.drop_column("memories", "temporal_status")
    op.drop_column("memories", "project_id")
