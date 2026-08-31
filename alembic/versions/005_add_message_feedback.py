"""005_add_message_feedback — add user feedback on chat responses."""

from alembic import op
import sqlalchemy as sa


revision = "005_add_message_feedback"
down_revision: str | None = "004_add_memory_sprint4_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "message_feedback",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provenance_id", sa.String(36), sa.ForeignKey("message_provenance.id"), nullable=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("sessions.id"), nullable=True),
        sa.Column("rating", sa.String(20), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f("ix_feedback_workspace"), "message_feedback", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_feedback_user"), "message_feedback", ["user_id"], unique=False)
    op.create_index(op.f("ix_feedback_session"), "message_feedback", ["session_id"], unique=False)
    op.create_index(op.f("ix_feedback_provenance"), "message_feedback", ["provenance_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_feedback_provenance"), table_name="message_feedback")
    op.drop_index(op.f("ix_feedback_session"), table_name="message_feedback")
    op.drop_index(op.f("ix_feedback_user"), table_name="message_feedback")
    op.drop_index(op.f("ix_feedback_workspace"), table_name="message_feedback")
    op.drop_table("message_feedback")
