from datetime import datetime, timezone
from sqlalchemy import (
    String, Boolean, DateTime, ForeignKey, Text, JSON, Integer, Enum as SQLEnum, Float, UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base
import uuid
import enum


class UserRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    plan: Mapped[str] = mapped_column(String(50), default="free")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    workspaces: Mapped[list["Workspace"]] = relationship(
        "Workspace", back_populates="tenant"
    )


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"))
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="workspaces")
    members: Mapped[list["WorkspaceMember"]] = relationship(
        "WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan"
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    memberships: Mapped[list["WorkspaceMember"]] = relationship(
        "WorkspaceMember", back_populates="user"
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user"
    )


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id")
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(20), default="member")
    invited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    joined_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    workspace: Mapped["Workspace"] = relationship(
        "Workspace", back_populates="members"
    )
    user: Mapped["User"] = relationship("User", back_populates="memberships")


class Invitation(Base):
    __tablename__ = "invitations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id")
    )
    email: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="member")
    state: Mapped[str] = mapped_column(String(20), default="pending")
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(
        String(512), unique=True, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id")
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id")
    )
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    session: Mapped["Session"] = relationship("Session", back_populates="messages")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id")
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    agent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=True, index=True
    )
    memory_type: Mapped[str] = mapped_column(String(50), default="procedural_memory")
    content: Mapped[str] = mapped_column(Text)
    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    temporal_status: Mapped[str] = mapped_column(String(50), default="current", index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    authority: Mapped[float] = mapped_column(Float, default=1.0)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    tenant: Mapped["Tenant"] = relationship("Tenant")


class IngestJob(Base):
    __tablename__ = "ingest_jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(String(36))
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id")
    )
    source_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="queued")
    stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_records: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# ── Sprint 3: Memory Pipeline Models ─────────────────────────────────────


class Source(Base):
    """Represents an ingested conversation/document (M0 input)."""

    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(String(36), nullable=False)
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id"), nullable=False
    )
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    content_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_content_path: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    normalized_messages: Mapped[list["NormalizedMessage"]] = relationship(
        "NormalizedMessage",
        back_populates="source",
        cascade="all, delete-orphan",
    )
    facts: Mapped[list["Fact"]] = relationship("Fact", back_populates="source")
    decisions: Mapped[list["Decision"]] = relationship(
        "Decision", back_populates="source"
    )
    graph_edges: Mapped[list["GraphEdge"]] = relationship(
        "GraphEdge", back_populates="source"
    )

    __table_args__ = (
        Index("ix_sources_workspace_tenant", "workspace_id", "tenant_id"),
        Index("ix_sources_project_status", "project_id", "status"),
    )


class NormalizedMessage(Base):
    """Individual message from an ingested source (M0 output / M1 input)."""

    __tablename__ = "normalized_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sources.id"), nullable=False
    )
    session_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sessions.id"), nullable=True
    )
    message_index: Mapped[int] = mapped_column(Integer, nullable=False)
    external_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    extra_metadata: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
    timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    source: Mapped["Source"] = relationship(
        "Source", back_populates="normalized_messages"
    )

    __table_args__ = (
        UniqueConstraint(
            "source_id", "message_index", name="uq_normalized_msg_source_idx"
        ),
        UniqueConstraint(
            "source_id", "external_id", name="uq_normalized_msg_source_ext"
        ),
    )


class Fact(Base):
    """Extracted factual statement (M2 output)."""

    __tablename__ = "facts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id"), nullable=False
    )
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sources.id"), nullable=True
    )
    session_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sessions.id"), nullable=True
    )
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    predicate: Mapped[str] = mapped_column(String(100), nullable=False)
    object: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    authority: Mapped[float] = mapped_column(Float, default=1.0)
    temporal_status: Mapped[str] = mapped_column(
        String(20), default="current"
    )
    superseded_by_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="active")
    extra_metadata: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    source: Mapped["Source"] = relationship("Source", back_populates="facts")

    __table_args__ = (
        Index("ix_facts_workspace_project", "workspace_id", "project_id"),
        Index("ix_facts_subject", "subject"),
        Index("ix_facts_temporal_status", "temporal_status"),
    )


class Decision(Base):
    """Extracted decision record (M2 output)."""

    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id"), nullable=False
    )
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sources.id"), nullable=True
    )
    session_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sessions.id"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    authority: Mapped[float] = mapped_column(Float, default=1.0)
    temporal_status: Mapped[str] = mapped_column(
        String(20), default="current"
    )
    superseded_by_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="active")
    extra_metadata: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    source: Mapped["Source"] = relationship(
        "Source", back_populates="decisions"
    )

    __table_args__ = (
        Index("ix_decisions_workspace_project", "workspace_id", "project_id"),
        Index("ix_decisions_temporal_status", "temporal_status"),
    )


class GraphNode(Base):
    """Knowledge graph node (M4 output)."""

    __tablename__ = "graph_nodes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id"), nullable=False
    )
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    external_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    label: Mapped[str] = mapped_column(String(500), nullable=False)
    node_type: Mapped[str] = mapped_column(String(50), default="entity")
    properties: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    temporal_status: Mapped[str] = mapped_column(
        String(20), default="current"
    )

    __table_args__ = (
        Index("ix_graph_nodes_workspace", "workspace_id", "temporal_status"),
        UniqueConstraint(
            "workspace_id", "external_id", name="uq_graph_node_ws_ext"
        ),
        Index("ix_graph_nodes_workspace_type", "workspace_id", "node_type"),
    )


class GraphEdge(Base):
    """Knowledge graph edge/relationship (M4 output)."""

    __tablename__ = "graph_edges"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id"), nullable=False
    )
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_node_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("graph_nodes.id"), nullable=False
    )
    target_node_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("graph_nodes.id"), nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(String(100), nullable=False)
    properties: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    temporal_status: Mapped[str] = mapped_column(
        String(20), default="current"
    )
    source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sources.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    source: Mapped["Source"] = relationship("Source", back_populates="graph_edges")

    __table_args__ = (
        Index("ix_graph_edges_source_target", "source_node_id", "target_node_id"),
        Index("ix_graph_edges_workspace", "workspace_id", "temporal_status"),
    )


class MessageProvenance(Base):
    """Full provenance tracking for every chat response."""

    __tablename__ = "message_provenance"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id")
    )
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    session_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sessions.id"), nullable=True
    )
    user_message_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("messages.id"), nullable=True
    )
    assistant_message_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("messages.id"), nullable=True
    )
    model: Mapped[str] = mapped_column(String(100))
    provider: Mapped[str] = mapped_column(String(50))
    retrieval_method: Mapped[str] = mapped_column(
        String(50), default="hybrid"
    )
    memory_ids_used: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )
    retrieval_sources: Mapped[list[dict] | None] = mapped_column(
        JSON, nullable=True, default=None
    )
    user_message_preview: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    confidence: Mapped[float | None] = mapped_column(
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class MessageFeedback(Base):
    """User feedback on chat responses — thumbs up/down with optional comment."""

    __tablename__ = "message_feedback"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id")
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    provenance_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("message_provenance.id"), nullable=True
    )
    session_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sessions.id"), nullable=True
    )
    rating: Mapped[str] = mapped_column(String(20))  # "thumbs_up" | "thumbs_down"
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class ApiKey(Base):
    """API key for MCP server registration (Sprint 6)."""

    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    key_prefix: Mapped[str] = mapped_column(
        String(8), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    key_extra: Mapped[dict | None] = mapped_column("key_extra", JSON, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_api_keys_workspace", "workspace_id"),
        Index("ix_api_keys_user", "user_id"),
    )


# ── Sprint 7: Policy Engine ────────────────────────────────────────────────


class Policy(Base):
    """Top-level policy record (Sprint 7)."""

    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    versions: Mapped[list["PolicyVersion"]] = relationship(
        "PolicyVersion", back_populates="policy", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_policies_tenant_id", "tenant_id"),
        Index("ix_policies_status", "status"),
    )


class PolicyVersion(Base):
    """Versioned rule set for a policy (Sprint 7)."""

    __tablename__ = "policy_versions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    policy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    rules: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    policy: Mapped["Policy"] = relationship("Policy", back_populates="versions")

    __table_args__ = (
        Index("ix_policy_versions_policy_id", "policy_id"),
        UniqueConstraint("policy_id", "version", name="uq_policy_version"),
    )


class AuditEvent(Base):
    """Persistent audit event (Sprint 7 — Phase 4).

    Append-only from the application perspective.  Ordinary agents cannot
    modify or delete records.  Audit events are never updated — only
    inserted and queried.

    Sensitive fields (passwords, tokens, secrets) must never be stored.
    """

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("tenants.id"), nullable=True, index=True
    )
    workspace_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    principal_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    principal_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    action: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    decision: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    policy_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    policy_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    result_status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    limits: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    provenance_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # NOTE: SQLAlchemy reserves `metadata` — use `event_metadata` for
    # the ORM attribute, and map in AuditRepository when converting
    # from AuditEventDTO (which uses `metadata`).

    __table_args__ = (
        Index("ix_audit_events_tenant_timestamp", "tenant_id", "timestamp"),
        Index("ix_audit_events_principal_timestamp", "principal_id", "timestamp"),
        Index("ix_audit_events_resource_timestamp", "resource_type", "timestamp"),
        Index("ix_audit_events_correlation", "correlation_id", "timestamp"),
    )
