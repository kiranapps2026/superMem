"""008_add_source_content_hash

Revision ID: 008_add_source_content_hash
Revises: 007_add_api_keys
Create Date: 2026-08-29

Add content_hash to sources for ingestion deduplication.
"""
from alembic import op
import sqlalchemy as sa


revision = "008_add_source_content_hash"
down_revision: str | None = "007_add_api_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sources", sa.Column("content_hash", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_sources_content_hash"), "sources", ["content_hash"], unique=False)
    # Unique constraint: one source per hash per workspace
    op.create_unique_constraint("uq_source_ws_hash", "sources", ["workspace_id", "content_hash"])


def downgrade() -> None:
    op.drop_constraint("uq_source_ws_hash", "sources", type_="unique")
    op.drop_index(op.f("ix_sources_content_hash"), table_name="sources")
    op.drop_column("sources", "content_hash")
