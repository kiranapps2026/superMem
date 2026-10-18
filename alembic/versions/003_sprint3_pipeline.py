"""Add Sprint 3 memory pipeline tables."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Float, Integer, JSON, String, DateTime, Index, UniqueConstraint
from sqlalchemy.sql import func

revision = "003_sprint3_pipeline"
down_revision = "002_provenance"
branch_labels = None
depends_on = None


def upgrade():
    # ── sources ─────────────────────────────────────────────────────────
    op.create_table(
        "sources",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), nullable=False),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("raw_content_path", sa.String, nullable=True),
        sa.Column("message_count", sa.Integer, server_default="0"),
        sa.Column("status", sa.String(20), server_default="queued"),
        sa.Column("stage", sa.String(50), nullable=True),
        sa.Column("progress", sa.Integer, server_default="0"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("config", JSON, nullable=True),
        sa.Column("started_at", DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", DateTime(timezone=True), nullable=True),
        sa.Column("created_at", DateTime(timezone=True), server_default=func.now()),
        sa.Column("updated_at", DateTime(timezone=True), server_default=func.now()),
        sa.Column("deleted_at", DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sources_external_id", "sources", ["external_id"])
    op.create_index("ix_sources_workspace_tenant", "sources", ["workspace_id", "tenant_id"])
    op.create_index("ix_sources_project_status", "sources", ["project_id", "status"])

    # ── normalized_messages ─────────────────────────────────────────────
    op.create_table(
        "normalized_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("sessions.id"), nullable=True),
        sa.Column("message_index", sa.Integer, nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column("timestamp", DateTime(timezone=True), nullable=True),
        sa.Column("created_at", DateTime(timezone=True), server_default=func.now()),
    )
    op.create_index("ix_norm_msg_external_id", "normalized_messages", ["external_id"])
    op.create_index("ix_norm_msg_source", "normalized_messages", ["source_id"])
    op.create_unique_constraint(
        "uq_normalized_msg_source_idx",
        "normalized_messages",
        ["source_id", "message_index"],
    )
    op.create_unique_constraint(
        "uq_normalized_msg_source_ext",
        "normalized_messages",
        ["source_id", "external_id"],
    )

    # ── facts ───────────────────────────────────────────────────────────
    op.create_table(
        "facts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("project_id", sa.String(36), nullable=True),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("sources.id"), nullable=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("sessions.id"), nullable=True),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("predicate", sa.String(100), nullable=False),
        sa.Column("object", sa.String(500), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("confidence", sa.Float, server_default="1.0"),
        sa.Column("authority", sa.Float, server_default="1.0"),
        sa.Column("temporal_status", sa.String(20), server_default="current"),
        sa.Column("superseded_by_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column("created_at", DateTime(timezone=True), server_default=func.now()),
        sa.Column("updated_at", DateTime(timezone=True), server_default=func.now()),
        sa.Column("deleted_at", DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_facts_workspace_project", "facts", ["workspace_id", "project_id"])
    op.create_index("ix_facts_subject", "facts", ["subject"])
    op.create_index("ix_facts_temporal_status", "facts", ["temporal_status"])
    op.create_index("ix_facts_superseded_by", "facts", ["superseded_by_id"])

    # ── decisions ───────────────────────────────────────────────────────
    op.create_table(
        "decisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("project_id", sa.String(36), nullable=True),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("sources.id"), nullable=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("sessions.id"), nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("context", sa.Text, nullable=True),
        sa.Column("confidence", sa.Float, server_default="1.0"),
        sa.Column("authority", sa.Float, server_default="1.0"),
        sa.Column("temporal_status", sa.String(20), server_default="current"),
        sa.Column("superseded_by_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column("created_at", DateTime(timezone=True), server_default=func.now()),
        sa.Column("updated_at", DateTime(timezone=True), server_default=func.now()),
        sa.Column("deleted_at", DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_decisions_workspace_project", "decisions", ["workspace_id", "project_id"])
    op.create_index("ix_decisions_temporal_status", "decisions", ["temporal_status"])
    op.create_index("ix_decisions_superseded_by", "decisions", ["superseded_by_id"])

    # ── graph_nodes ─────────────────────────────────────────────────────
    op.create_table(
        "graph_nodes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("project_id", sa.String(36), nullable=True),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("label", sa.String(500), nullable=False),
        sa.Column("node_type", sa.String(50), server_default="entity"),
        sa.Column("properties", JSON, nullable=True),
        sa.Column("created_at", DateTime(timezone=True), server_default=func.now()),
        sa.Column("updated_at", DateTime(timezone=True), server_default=func.now()),
        sa.Column("deleted_at", DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_graph_nodes_workspace_type", "graph_nodes", ["workspace_id", "node_type"])
    op.create_unique_constraint(
        "uq_graph_node_ws_ext",
        "graph_nodes",
        ["workspace_id", "external_id"],
    )

    # ── graph_edges ─────────────────────────────────────────────────────
    op.create_table(
        "graph_edges",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("project_id", sa.String(36), nullable=True),
        sa.Column("source_node_id", sa.String(36), sa.ForeignKey("graph_nodes.id"), nullable=False),
        sa.Column("target_node_id", sa.String(36), sa.ForeignKey("graph_nodes.id"), nullable=False),
        sa.Column("relationship_type", sa.String(100), nullable=False),
        sa.Column("properties", JSON, nullable=True),
        sa.Column("confidence", sa.Float, server_default="1.0"),
        sa.Column("temporal_status", sa.String(20), server_default="current"),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("sources.id"), nullable=True),
        sa.Column("created_at", DateTime(timezone=True), server_default=func.now()),
        sa.Column("updated_at", DateTime(timezone=True), server_default=func.now()),
        sa.Column("deleted_at", DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_graph_edges_source_target", "graph_edges", ["source_node_id", "target_node_id"])
    op.create_index("ix_graph_edges_workspace", "graph_edges", ["workspace_id", "temporal_status"])
    op.create_index("ix_graph_edges_source_id", "graph_edges", ["source_id"])


def downgrade():
    op.drop_table("graph_edges")
    op.drop_table("graph_nodes")
    op.drop_table("decisions")
    op.drop_table("facts")
    op.drop_table("normalized_messages")
    op.drop_table("sources")
