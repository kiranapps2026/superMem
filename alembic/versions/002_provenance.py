"""Add provenance table for Sprint 2."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Float, Integer, JSON, String, DateTime
from sqlalchemy.sql import func

revision = "002_provenance"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "message_provenance",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("project_id", sa.String(36), nullable=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("sessions.id"), nullable=True),
        sa.Column("user_message_id", sa.String(36), sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("assistant_message_id", sa.String(36), sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("retrieval_method", sa.String(50), server_default="hybrid"),
        sa.Column("memory_ids_used", JSON, nullable=True),
        sa.Column("prompt_tokens", Integer, server_default="0"),
        sa.Column("completion_tokens", Integer, server_default="0"),
        sa.Column("total_tokens", Integer, server_default="0"),
        sa.Column("latency_ms", Integer, nullable=True),
        sa.Column("confidence", Float, nullable=True),
        sa.Column("created_at", DateTime(timezone=True), server_default=func.now()),
    )
    op.create_index("ix_provenance_workspace_id", "message_provenance", ["workspace_id"])
    op.create_index("ix_provenance_session_id", "message_provenance", ["session_id"])
    op.create_index("ix_provenance_created_at", "message_provenance", ["created_at"])


def downgrade():
    op.drop_index("ix_provenance_created_at", table_name="message_provenance")
    op.drop_index("ix_provenance_session_id", table_name="message_provenance")
    op.drop_index("ix_provenance_workspace_id", table_name="message_provenance")
    op.drop_table("message_provenance")
