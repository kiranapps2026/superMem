"""Add tenant_id to memories table (P0 security fix — cross-tenant isolation).

Revision ID: 011_add_tenant_to_memory
Revises: 010_add_audit_events
Create Date: 2026-09-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "011_add_tenant_to_memory"
down_revision: Union[str, None] = "010_add_audit_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add tenant_id column (nullable initially for backfill)
    with op.batch_alter_table("memories") as batch_op:
        batch_op.add_column(sa.Column("tenant_id", sa.String(36), nullable=True))
        batch_op.create_index("ix_memories_tenant_id", ["tenant_id"])

    # Step 2: Backfill tenant_id from workspace → tenant
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE memories
        SET tenant_id = (
            SELECT w.tenant_id
            FROM workspaces w
            WHERE w.id = memories.workspace_id
        )
        WHERE tenant_id IS NULL
    """))

    # Step 3: Set NOT NULL constraint (safe now that all rows are populated)
    with op.batch_alter_table("memories") as batch_op:
        batch_op.alter_column("tenant_id", nullable=False)
        batch_op.create_foreign_key(
            "fk_memories_tenant_id",
            "tenants",
            ["tenant_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("memories") as batch_op:
        batch_op.drop_constraint("fk_memories_tenant_id", type_="foreignkey")
        batch_op.drop_index("ix_memories_tenant_id")
        batch_op.drop_column("tenant_id")
