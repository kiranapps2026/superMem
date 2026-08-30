// ── Auth ────────────────────────────────────────────────────────────────────
export interface UserInfo { id: string; email: string; name: string | null; workspace_id: string; tenant_id: string; }
export interface TokenPair { access_token: string; refresh_token: string; expires_in: number; user: UserInfo; }
export interface RegisterRequest { email: string; password: string; name?: string; }

// ── Workspace ───────────────────────────────────────────────────────────────
export interface WorkspaceMemberOut { id: string; workspace_id: string; user_id: string; user_name: string; user_email: string; role: string; joined_at: string | null; invited_at: string | null; expires: string | null; }
export interface InvitationOut { id: string; workspace_id: string; email: string; role: string; state: string; message: string | null; created_at: string | null; expires_at: string | null; responded_at: string | null; }
export interface WorkspaceDetail { id: string; name: string; slug: string; tenant_id: string; description: string | null; created_at: string | null; }
export interface InviteMemberRequest { email: string; role?: string; message?: string; }
export interface MemberUpdatePayload { role?: string; expires?: string | null; }
export interface WorkspaceSummary { id: string; name: string; slug: string; role: string; }

// ── Projects ────────────────────────────────────────────────────────────────
export interface Project { id: string; name: string; description: string | null; session_count: number; memory_count?: number; created_at: string | null; }
export interface ProjectDetail { id: string; workspace_id: string; tenant_id: string; name: string; description: string | null; settings: Record<string, unknown>; created_at: string | null; }
export interface ProjectCreate { name: string; description?: string; }
export interface ProjectUpdate { name?: string; description?: string; }

// ── Sessions ────────────────────────────────────────────────────────────────
export interface SessionInfo { id: string; title: string | null; source: string; message_count: number; }
export interface MessageInfo { id: string; role: string; content: string; created_at: string | null; }
export interface SessionHistory { session_id: string; project_id: string; title: string | null; source: string; messages: MessageInfo[]; }

// ── Chat ────────────────────────────────────────────────────────────────────
export interface ChatRequest { project_id: string; message: string; conversation_id?: string; }
export interface EvidenceSource { memory_id: string; type: string; authority: string; confidence: number; status: string; source_id?: string; }
export interface ChatStreamToken { type: 'token'; content: string; }
export interface ChatStreamSources { type: 'sources'; items: EvidenceSource[]; }
export interface ChatStreamDone { type: 'done'; metadata: { tokens: number; memory_grounded: boolean }; }
export interface ChatStreamError { type: 'error'; detail: string; }
export type ChatStreamEvent = ChatStreamToken | ChatStreamSources | ChatStreamDone | ChatStreamError;

// ── Ingestion ────────────────────────────────────��──────────────────────────
export interface IngestJobDetail { job_id: string; project_id: string; source_type: string; status: string; stage: string | null; progress: number; error_message: string | null; estimated_records: number | null; created_at: string | null; started_at: string | null; completed_at: string | null; }
export interface IngestJobListResponse { jobs: IngestJobDetail[]; total: number; }
export interface IngestQueued { job_id: string; status: string; estimated_records: number; }

// ── Memory Items ────────────────────────────────────────────────────────────
export interface MemoryItemOut { id: string; workspace_id: string; project_id: string; type: string; content: string; tags: string[]; metadata: Record<string, unknown>; created_at: string; updated_at: string; }

// ── Memory ──────────────────────────────────────────────────────────────────
export interface FactInfo { id: string; statement: string; subject: string | null; predicate: string | null; object: string | null; confidence: number; authority: string; status: string; tags: string[]; created_at: string | null; updated_at: string | null; }
export interface DecisionInfo { id: string; title: string; context: string | null; outcome: string | null; rationale: string | null; confidence: number; tags: string[]; created_at: string | null; updated_at: string | null; }
export interface TimelineEvent { type: 'fact' | 'decision'; id: string; timestamp: string; content: string; authority?: string; confidence?: number; status?: string; outcome?: string; rationale?: string; }

// ── Search ──────────────────────────────────────────────────────────────────
export interface SearchResult { id: string; type: string; subtype: string; content: string; tags: string[]; authority: string; confidence: number; status: string; created_at: string | null; scores: { final_score: number; lexical: number; authority: number; confidence: number; recency: number; provenance: number; }; }
export interface SearchResponse { query: string; results: SearchResult[]; count: number; }
