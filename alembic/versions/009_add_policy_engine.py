"""Create policy tables (policies + policy_versions).

Revision ID: 009_add_policy_engine
Revises: 008_add_source_content_hash
Create Date: 2026-09-01
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "009_add_policy_engine"
down_revision: Union[str, None] = "008_add_source_content_hash"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Policies: top-level policy record
    op.create_table(
        "policies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("current_version", sa.Integer, server_default="1"),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_policies_tenant_id", "policies", ["tenant_id"])
    op.create_index("ix_policies_status", "policies", ["status"])

    # Policy versions: versioned rule sets per policy
    op.create_table(
        "policy_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("policy_id", sa.String(36), sa.ForeignKey("policies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("rules", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_policy_versions_policy_id", "policy_versions", ["policy_id"])
    op.create_unique_constraint(
        "uq_policy_version",
        "policy_versions",
        ["policy_id", "version"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_policy_version", "policy_versions", type_="unique")
    op.drop_index("ix_policy_versions_policy_id", table_name="policy_versions")
    op.drop_table("policy_versions")
    op.drop_index("ix_policies_status", table_name="policies")
    op.drop_index("ix_policies_tenant_id", table_name="policies")
    op.drop_table("policies")
