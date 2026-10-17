"""015_execution_identity

Adds execution identity tables for Phase 4:
  - agents: AI agent instances
  - agent_versions: deployed versions of agents
  - runs: single execution runs
  - run_steps: steps within a run
  - tool_executions: tool calls within a step

Adds agent_id / run_id foreign keys to Memory and MemoryContradiction
(non-breaking: columns are nullable, existing rows unaffected).

Also adds detected_by_agent_id / detected_by_run_id to MemoryContradiction.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "015_execution_identity"
down_revision: Union[str, None] = "014_add_memory_contradictions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── agents table ────────────────────────────────────────────────────────
    op.create_table(
        "agents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("version", sa.String(50), server_default="1.0.0"),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_agents_tenant", "agents", ["tenant_id"])
    op.create_index("ix_agents_workspace", "agents", ["workspace_id"])

    # ── agent_versions table ────────────────────────────────────────────────
    op.create_table(
        "agent_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("config", postgresql.JSONB, nullable=True),
        sa.Column("prompt_hash", sa.String(64), nullable=True),
        sa.Column("deployed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deployed_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("is_current", sa.Boolean, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_agent_versions_agent", "agent_versions", ["agent_id"])

    # ── runs table ──────────────────────────────────────────────────────────
    op.create_table(
        "runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("agent_version_id", sa.String(36), sa.ForeignKey("agent_versions.id"), nullable=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("trace_id", sa.String(36), nullable=True),
        sa.Column("correlation_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(20), server_default="running"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_runs_tenant", "runs", ["tenant_id"])
    op.create_index("ix_runs_workspace", "runs", ["workspace_id"])
    op.create_index("ix_runs_project", "runs", ["project_id"])
    op.create_index("ix_runs_agent", "runs", ["agent_id"])
    op.create_index("ix_runs_user", "runs", ["user_id"])
    op.create_index("ix_runs_trace", "runs", ["trace_id"])
    op.create_index("ix_runs_correlation", "runs", ["correlation_id"])

    # ── run_steps table ─────────────────────────────────────────────────────
    op.create_table(
        "run_steps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("step_type", sa.String(30), nullable=False),
        sa.Column("step_index", sa.Integer, nullable=False),
        sa.Column("parent_step_id", sa.String(36), nullable=True),
        sa.Column("input_data", postgresql.JSONB, nullable=True),
        sa.Column("output_data", postgresql.JSONB, nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("status", sa.String(20), server_default="completed"),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_run_steps_run", "run_steps", ["run_id"])
    op.create_index("ix_run_steps_parent", "run_steps", ["parent_step_id"])

    # ── tool_executions table ───────────────────────────────────────────────
    op.create_table(
        "tool_executions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("step_id", sa.String(36), sa.ForeignKey("run_steps.id"), nullable=False),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("tool_input", postgresql.JSONB, nullable=True),
        sa.Column("tool_output", postgresql.JSONB, nullable=True),
        sa.Column("status", sa.String(20), server_default="completed"),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_tool_executions_run", "tool_executions", ["run_id"])
    op.create_index("ix_tool_executions_step", "tool_executions", ["step_id"])

    # ── Add provenance columns to memory_contradictions ─────────────────────
    # Already created by 014; these are additive FK columns
    with op.batch_alter_table("memory_contradictions") as batch_op:
        batch_op.add_column(sa.Column("detected_by_agent_id", sa.String(36), nullable=True))
        batch_op.add_column(sa.Column("detected_by_run_id", sa.String(36), nullable=True))
        batch_op.create_index("ix_contradictions_detected_agent", ["detected_by_agent_id"])
        batch_op.create_index("ix_contradictions_detected_run", ["detected_by_run_id"])
        batch_op.create_foreign_key(
            "fk_contradictions_agent", "agents",
            ["detected_by_agent_id"], ["id"],
        )
        batch_op.create_foreign_key(
            "fk_contradictions_run", "runs",
            ["detected_by_run_id"], ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("memory_contradictions") as batch_op:
        batch_op.drop_constraint("fk_contradictions_run", type_="foreignkey")
        batch_op.drop_constraint("fk_contradictions_agent", type_="foreignkey")
        batch_op.drop_index("ix_contradictions_detected_run")
        batch_op.drop_index("ix_contradictions_detected_agent")
        batch_op.drop_column("detected_by_run_id")
        batch_op.drop_column("detected_by_agent_id")

    op.drop_table("tool_executions")
    op.drop_table("run_steps")
    op.drop_table("runs")
    op.drop_table("agent_versions")
    op.drop_table("agents")
