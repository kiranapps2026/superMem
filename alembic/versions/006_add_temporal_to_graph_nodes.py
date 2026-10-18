"""006_add_temporal_to_graph_nodes — add temporal_status to graph_nodes table."""

from alembic import op
import sqlalchemy as sa


revision = "006_add_temporal_to_graph_nodes"
down_revision: str | None = "005_add_message_feedback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "graph_nodes",
        sa.Column("temporal_status", sa.String(length=20), nullable=False, server_default="current"),
    )
    op.create_index(
        op.f("ix_graph_nodes_temporal_status"),
        "graph_nodes",
        ["temporal_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_graph_nodes_temporal_status"), table_name="graph_nodes")
    op.drop_column("graph_nodes", "temporal_status")
