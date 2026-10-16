"""016_memory_source_provenance

Adds source provenance columns to Memory:
  - source_id: FK to sources table
  - source_session_id: ID of the originating session
  - source_message_id: ID of the specific message that produced this memory

These close the "provenance — PARTIAL: created_at only" gap in the
architecture. Every Memory created after this phase carries a traceable
origin.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "016_memory_source_provenance"
down_revision: Union[str, None] = "015_execution_identity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("memories") as batch_op:
        batch_op.add_column(sa.Column("source_id", sa.String(36), nullable=True))
        batch_op.add_column(sa.Column("source_session_id", sa.String(36), nullable=True))
        batch_op.add_column(sa.Column("source_message_id", sa.String(36), nullable=True))
        batch_op.create_index("ix_memories_source_id", ["source_id"])
        batch_op.create_index("ix_memories_source_session", ["source_session_id"])
        batch_op.create_index("ix_memories_source_message", ["source_message_id"])
        batch_op.create_foreign_key(
            "fk_memories_source", "sources",
            ["source_id"], ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("memories") as batch_op:
        batch_op.drop_constraint("fk_memories_source", type_="foreignkey")
        batch_op.drop_index("ix_memories_source_message")
        batch_op.drop_index("ix_memories_source_session")
        batch_op.drop_index("ix_memories_source_id")
        batch_op.drop_column("source_message_id")
        batch_op.drop_column("source_session_id")
        batch_op.drop_column("source_id")
