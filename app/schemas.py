from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Any, Literal


# Auth
class UserRegister(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8)
    workspace_name: str = Field(..., min_length=1, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    is_active: bool
    email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Workspace
class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


class WorkspaceOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    slug: str
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class WorkspaceMemberOut(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    user_name: str
    user_email: str
    role: str
    joined_at: datetime | None = None
    invited_at: datetime | None = None
    expires: datetime | None = None


class WorkspaceMemberUpdate(BaseModel):
    role: Literal["owner", "admin", "member", "viewer"] | None = None
    expires: datetime | None = None


class WorkspaceMemberInvite(BaseModel):
    email: EmailStr
    role: Literal["owner", "admin", "member", "viewer"] = "member"
    message: str | None = None
    invitation_expires: datetime | None = None


class InvitationOut(BaseModel):
    id: str
    workspace_id: str
    email: str
    role: str
    state: str
    created_at: datetime | None = None
    expires_at: datetime | None = None


class InvitationUpdate(BaseModel):
    state: Literal["pending", "accepted", "declined", "expired", "revoked"] | None = None
    role: Literal["owner", "admin", "member", "viewer"] | None = None
    expires: datetime | None = None


# Projects
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None


class ProjectOut(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Sessions
class SessionCreate(BaseModel):
    title: str | None = None
    extra_metadata: dict[str, Any] | None = None


class SessionOut(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    title: str | None
    extra_metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1)
    metadata: dict[str, Any] | None = None


class MessageOut(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    metadata: dict[str, Any] | None
    created_at: datetime

    class Config:
        from_attributes = True


# Chat
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str | None = None
    project_id: str | None = None


class ChatResponse(BaseModel):
    message_id: str
    session_id: str
    response: str
    model: str = "mock"
    usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0}
    memory_ids_used: list[str] | None = None
    retrieval_method: str | None = None
    retrieval_sources: list[dict] | None = None
    latency_ms: int | None = None
    confidence: float | None = None
    provider: str | None = None


# Memory
class MemoryCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1_000_000)
    memory_type: str = Field(default="procedural_memory", max_length=50)
    agent_id: str | None = None
    run_id: str | None = None
    project_id: str | None = None
    extra_metadata: dict[str, Any] | None = None

    @field_validator("content")
    @classmethod
    def no_null_bytes(cls, v: str) -> str:
        if "\x00" in v:
            raise ValueError("Content contains null bytes")
        return v

    @field_validator("content")
    @classmethod
    def strip_whitespace_only(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Content cannot be whitespace only")
        return v


class MemoryUpdate(BaseModel):
    content: str | None = None
    memory_type: str | None = None
    project_id: str | None = None
    temporal_status: str | None = None

    @field_validator("content")
    @classmethod
    def no_null_bytes(cls, v: str | None) -> str | None:
        if v is not None and "\x00" in v:
            raise ValueError("Content contains null bytes")
        return v


class MemoryOut(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    agent_id: str | None
    run_id: str | None
    project_id: str | None
    memory_type: str
    content: str
    extra_metadata: dict[str, Any] | None
    temporal_status: str
    confidence: float
    authority: float
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MemoryReferenceOut(BaseModel):
    """Memory reference exposed in provenance expansion."""
    memory_id: str
    content: str
    memory_type: str
    confidence: float
    authority: float
    temporal_status: str
    created_at: datetime
    project_id: str | None


class MemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    memory_type: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


# Ingest
class IngestQueued(BaseModel):
    project_id: str
    source_type: str
    config: dict[str, Any] | None = None


class IngestJobOut(BaseModel):
    id: str
    project_id: str
    workspace_id: str
    source_type: str
    status: str
    stage: str | None
    progress: int
    error_message: str | None
    estimated_records: int | None
    config: dict[str, Any] | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    class Config:
        from_attributes = True


class IngestJobListResponse(BaseModel):
    items: list[IngestJobOut]
    total: int


# Provenance
class ProvenanceCreate(BaseModel):
    model: str
    provider: str
    retrieval_method: str = "hybrid"
    memory_ids_used: list[str] | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int | None = None
    confidence: float | None = None


class ProvenanceOut(BaseModel):
    id: str
    workspace_id: str
    project_id: str | None
    session_id: str | None
    user_message_id: str | None
    assistant_message_id: str | None
    model: str
    provider: str
    retrieval_method: str
    memory_ids_used: list[str] | None
    retrieval_sources: list[dict] | None
    user_message_preview: str | None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int | None
    confidence: float | None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Sprint 3: Pipeline Schemas ──────────────────────────────────────────


# Sources
class SourceOut(BaseModel):
    id: str
    project_id: str
    workspace_id: str
    tenant_id: str
    source_type: str
    external_id: str | None
    title: str | None
    description: str | None
    message_count: int
    status: str
    stage: str | None
    progress: int
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class SourceDetail(SourceOut):
    normalized_messages: list["NormalizedMessageOut"] = []


class NormalizedMessageOut(BaseModel):
    id: str
    source_id: str
    session_id: str | None
    message_index: int
    external_id: str | None
    role: str
    content: str
    extra_metadata: dict[str, Any] | None
    timestamp: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class IngestUploadRequest(BaseModel):
    """Upload a conversation for ingestion."""
    project_id: str
    source_type: str = Field(..., pattern="^(text|json|jsonl|chatgpt)$")
    title: str | None = None
    content: str = Field(..., min_length=1, max_length=1_000_000)
    config: dict[str, Any] | None = None


class IngestUploadResponse(BaseModel):
    """Response from starting an ingestion."""
    source_id: str
    session_id: str | None = None
    status: str | None = None
    stage: str | None = None
    messages_processed: int = 0
    facts_created: int = 0
    decisions_created: int = 0
    graph_nodes_created: int = 0
    graph_edges_created: int = 0
    topics: list[str] = []
    entities: list[str] = []
    message: str | None = None


# Facts
class FactOut(BaseModel):
    id: str
    workspace_id: str
    project_id: str | None
    source_id: str | None
    subject: str
    predicate: str
    object: str
    content: str
    confidence: float
    authority: float
    temporal_status: str
    superseded_by_id: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FactListResponse(BaseModel):
    items: list[FactOut]
    total: int


# Decisions
class DecisionOut(BaseModel):
    id: str
    workspace_id: str
    project_id: str | None
    source_id: str | None
    content: str
    context: str | None
    confidence: float
    authority: float
    temporal_status: str
    superseded_by_id: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DecisionListResponse(BaseModel):
    items: list[DecisionOut]
    total: int


# Graph
class GraphNodeOut(BaseModel):
    id: str
    workspace_id: str
    project_id: str | None
    external_id: str | None
    label: str
    node_type: str
    properties: dict[str, Any] | None
    created_at: datetime

    class Config:
        from_attributes = True


class GraphEdgeOut(BaseModel):
    id: str
    workspace_id: str
    project_id: str | None
    source_node_id: str
    target_node_id: str
    relationship_type: str
    properties: dict[str, Any] | None
    confidence: float
    temporal_status: str
    source_id: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class GraphResponse(BaseModel):
    nodes: list[GraphNodeOut]
    edges: list[GraphEdgeOut]


# Timeline
class TimelineItem(BaseModel):
    item_type: str  # "fact", "decision", "memory", "source"
    id: str
    title: str
    timestamp: datetime | None
    temporal_status: str | None
    content: str | None


class TimelineResponse(BaseModel):
    items: list[TimelineItem]
    total: int


# Search
class SearchResultItem(BaseModel):
    item_type: str
    id: str
    score: float
    content: str
    temporal_status: str | None
    created_at: datetime


class SearchResponse(BaseModel):
    items: list[SearchResultItem]
    total: int
    query: str


# Source list response
class SourceListResponse(BaseModel):
    items: list[SourceOut]
    total: int


# ── Feedback (Sprint 4) ────────────────────────────────────────────────────


class FeedbackCreate(BaseModel):
    provenance_id: str | None = None
    session_id: str | None = None
    rating: str = Field(..., pattern="^(thumbs_up|thumbs_down)$")
    comment: str | None = Field(None, max_length=2000)


class FeedbackOut(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    provenance_id: str | None
    session_id: str | None
    rating: str
    comment: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackListResponse(BaseModel):
    items: list[FeedbackOut]
    total: int


# ── Dashboard (Sprint 4) ───────────────────────────────────────────────────


class DashboardOverview(BaseModel):
    workspace_id: str
    total_memories: int
    total_sources: int
    total_sessions: int
    total_facts: int
    total_decisions: int
    total_graph_nodes: int
    total_graph_edges: int
    recent_memories: int  # last 7 days
    recent_sessions: int  # last 7 days
    memory_types: dict[str, int]


class ProjectDashboard(BaseModel):
    project_id: str
    project_name: str
    total_memories: int
    total_sources: int
    total_facts: int
    total_decisions: int
    total_graph_nodes: int
    total_feedback: int
    memory_types: dict[str, int]


# ── API Keys (Sprint 6) ──────────────────────────────────────────────────


class ApiKeyOut(BaseModel):
    """API key list item — raw key is never exposed."""
    id: str
    name: str
    description: str | None = None
    key_prefix: str
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    created_at: datetime
    revoked_at: datetime | None = None
    key_extra: dict[str, str] | None = None

    class Config:
        from_attributes = True
