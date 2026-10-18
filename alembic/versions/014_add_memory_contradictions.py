"""014_add_memory_contradictions

Adds the memory_contradictions table for Phase 5 contradiction detection.
Non-destructive: additive only, no changes to existing tables.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "014_add_memory_contradictions"
down_revision: Union[str, None] = "013_embedding_dimension"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create memory_contradictions table."""
    op.create_table(
        "memory_contradictions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("fact_a_id", sa.String(36), nullable=False),
        sa.Column("fact_b_id", sa.String(36), nullable=False),
        sa.Column("contradiction_type", sa.String(30), server_default="VALUE_CONFLICT"),
        sa.Column("confidence", sa.Float, server_default="1.0"),
        sa.Column("status", sa.String(20), server_default="UNDER_REVIEW"),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution", sa.Text, nullable=True),
        sa.Column("resolved_by", sa.String(36), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Indexes for common query patterns
    op.create_index(
        "ix_contradictions_workspace",
        "memory_contradictions",
        ["workspace_id", "status"],
    )
    op.create_index(
        "ix_contradictions_workspace_detected",
        "memory_contradictions",
        ["workspace_id", "detected_at"],
    )

    # Unique constraint for idempotency
    op.create_unique_constraint(
        "uq_contradiction_pair",
        "memory_contradictions",
        ["workspace_id", "fact_a_id", "fact_b_id"],
    )


def downgrade() -> None:
    """Drop memory_contradictions table."""
    op.drop_constraint("uq_contradiction_pair", "memory_contradictions", type_="unique")
    op.drop_index("ix_contradictions_workspace_detected", table_name="memory_contradictions")
    op.drop_index("ix_contradictions_workspace", table_name="memory_contradictions")
    op.drop_table("memory_contradictions")
