"""Create audit_events table (Sprint 7 — Phase 4).

Revision ID: 010_add_audit_events
Revises: 009_add_policy_engine
Create Date: 2026-09-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "010_add_audit_events"
down_revision: Union[str, None] = "009_add_policy_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("workspace_id", sa.String(36), nullable=True),
        sa.Column("project_id", sa.String(36), nullable=True),
        sa.Column("principal_id", sa.String(36), nullable=True),
        sa.Column("principal_type", sa.String(20), nullable=True),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("action", sa.String(50), nullable=True),
        sa.Column("decision", sa.String(20), nullable=True),
        sa.Column("policy_id", sa.String(36), nullable=True),
        sa.Column("policy_version", sa.Integer, nullable=True),
        sa.Column("request_id", sa.String(36), nullable=True),
        sa.Column("correlation_id", sa.String(36), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("result_status", sa.String(20), nullable=False),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("limits", sa.JSON, nullable=True),
        sa.Column("provenance_reference", sa.String(255), nullable=True),
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    # Indexes for common query patterns
    op.create_index("ix_audit_events_tenant_id", "audit_events", ["tenant_id"])
    op.create_index("ix_audit_events_workspace_id", "audit_events", ["workspace_id"])
    op.create_index("ix_audit_events_principal_id", "audit_events", ["principal_id"])
    op.create_index("ix_audit_events_resource_type", "audit_events", ["resource_type"])
    op.create_index("ix_audit_events_action", "audit_events", ["action"])
    op.create_index("ix_audit_events_decision", "audit_events", ["decision"])
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])
    op.create_index("ix_audit_events_result_status", "audit_events", ["result_status"])
    op.create_index("ix_audit_events_timestamp", "audit_events", ["timestamp"])
    op.create_index("ix_audit_events_request_id", "audit_events", ["request_id"])
    op.create_index("ix_audit_events_correlation_id", "audit_events", ["correlation_id"])

    # Composite indexes for tenant-scoped time-range queries (audit log view)
    op.create_index(
        "ix_audit_events_tenant_timestamp",
        "audit_events",
        ["tenant_id", "timestamp"],
    )
    op.create_index(
        "ix_audit_events_principal_timestamp",
        "audit_events",
        ["principal_id", "timestamp"],
    )
    op.create_index(
        "ix_audit_events_resource_timestamp",
        "audit_events",
        ["resource_type", "timestamp"],
    )
    op.create_index(
        "ix_audit_events_correlation",
        "audit_events",
        ["correlation_id", "timestamp"],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_events_correlation", table_name="audit_events")
    op.drop_index("ix_audit_events_resource_timestamp", table_name="audit_events")
    op.drop_index("ix_audit_events_principal_timestamp", table_name="audit_events")
    op.drop_index("ix_audit_events_tenant_timestamp", table_name="audit_events")
    op.drop_index("ix_audit_events_timestamp", table_name="audit_events")
    op.drop_index("ix_audit_events_result_status", table_name="audit_events")
    op.drop_index("ix_audit_events_event_type", table_name="audit_events")
    op.drop_index("ix_audit_events_decision", table_name="audit_events")
    op.drop_index("ix_audit_events_action", table_name="audit_events")
    op.drop_index("ix_audit_events_resource_type", table_name="audit_events")
    op.drop_index("ix_audit_events_request_id", table_name="audit_events")
    op.drop_index("ix_audit_events_correlation_id", table_name="audit_events")
    op.drop_index("ix_audit_events_principal_id", table_name="audit_events")
    op.drop_index("ix_audit_events_workspace_id", table_name="audit_events")
    op.drop_index("ix_audit_events_tenant_id", table_name="audit_events")
    op.drop_table("audit_events")
