from pydantic import BaseModel, EmailStr, Field
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


# Memory
class MemoryCreate(BaseModel):
    content: str = Field(..., min_length=1)
    memory_type: str = Field(default="procedural_memory", max_length=50)
    agent_id: str | None = None
    run_id: str | None = None
    extra_metadata: dict[str, Any] | None = None


class MemoryOut(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    agent_id: str | None
    run_id: str | None
    memory_type: str
    content: str
    extra_metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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
